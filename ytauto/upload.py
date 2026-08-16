"""Resumable upload, thumbnail, playlist insert.

Network failures mid-upload are normal on a long push. The resumable protocol
means a retry resumes rather than restarts, so transient 5xx and socket errors
are retried here with backoff instead of surfacing to the user.
"""

from __future__ import annotations

import http.client
import random
import socket
import ssl
import time
from typing import Callable

import httplib2
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from .metadata import VideoMeta

RETRIABLE_EXCEPTIONS = (
    httplib2.HttpLib2Error,
    IOError,
    ssl.SSLError,
    socket.timeout,
    http.client.NotConnected,
    http.client.IncompleteRead,
    http.client.ImproperConnectionState,
    http.client.CannotSendRequest,
    http.client.CannotSendHeader,
    http.client.ResponseNotReady,
    http.client.BadStatusLine,
)
RETRIABLE_STATUS_CODES = {500, 502, 503, 504}
MAX_RETRIES = 10


def youtube(creds):
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def analytics(creds):
    return build("youtubeAnalytics", "v2", credentials=creds, cache_discovery=False)


def _retry_sleep(attempt: int) -> None:
    # Exponential backoff with jitter, capped — matches Google's guidance.
    delay = min(2**attempt, 60) + random.random()
    time.sleep(delay)


def upload_video(
    service,
    meta: VideoMeta,
    on_progress: Callable[[int], None] | None = None,
) -> str:
    """Upload the file and return the new video ID."""
    media = MediaFileUpload(
        str(meta.video_file),
        chunksize=4 * 1024 * 1024,
        resumable=True,
        mimetype="video/*",
    )
    request = service.videos().insert(
        part="snippet,status,recordingDetails",
        body=meta.to_body(),
        media_body=media,
    )

    response = None
    attempt = 0
    last_error = None

    while response is None:
        try:
            status, response = request.next_chunk()
            if status and on_progress:
                on_progress(int(status.progress() * 100))
            attempt = 0
        except HttpError as exc:
            if exc.resp.status in RETRIABLE_STATUS_CODES:
                last_error = exc
            else:
                raise
        except RETRIABLE_EXCEPTIONS as exc:
            last_error = exc

        if response is None and last_error is not None:
            attempt += 1
            if attempt > MAX_RETRIES:
                raise RuntimeError(
                    f"Upload failed after {MAX_RETRIES} retries: {last_error}"
                )
            _retry_sleep(attempt)
            last_error = None

    if on_progress:
        on_progress(100)

    if "id" not in response:
        raise RuntimeError(f"Upload returned no video ID: {response}")
    return response["id"]


def set_thumbnail(service, video_id: str, path) -> None:
    service.thumbnails().set(
        videoId=video_id,
        media_body=MediaFileUpload(str(path)),
    ).execute()


def add_to_playlist(service, video_id: str, playlist_id: str) -> None:
    service.playlistItems().insert(
        part="snippet",
        body={
            "snippet": {
                "playlistId": playlist_id,
                "resourceId": {"kind": "youtube#video", "videoId": video_id},
            }
        },
    ).execute()


def set_privacy(service, video_id: str, privacy: str) -> dict:
    """Flip an existing video's privacy status (videos.update)."""
    return (
        service.videos()
        .update(part="status", body={"id": video_id, "status": {"privacyStatus": privacy}})
        .execute()
    )


def channel_info(service) -> dict:
    resp = (
        service.channels()
        .list(part="snippet,contentDetails,statistics", mine=True)
        .execute()
    )
    items = resp.get("items") or []
    if not items:
        raise RuntimeError(
            "No channel on this Google account. Authorise with the account that "
            "owns the channel — if it is a Brand Account, pick it on the consent screen."
        )
    return items[0]
