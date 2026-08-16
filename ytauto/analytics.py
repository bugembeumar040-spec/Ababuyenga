"""Post-publish numbers: lifetime stats from the Data API, retention from the
Analytics API.

Analytics data lags real time by roughly 2-3 days, so recent uploads will show
thin or zero retention figures. That is the API, not a bug here.
"""

from __future__ import annotations

import datetime as dt

from .upload import channel_info


def recent_uploads(service, limit: int = 10) -> list[dict]:
    """The channel's most recent uploads with lifetime statistics."""
    channel = channel_info(service)
    uploads_playlist = channel["contentDetails"]["relatedPlaylists"]["uploads"]

    ids: list[str] = []
    page_token = None
    while len(ids) < limit:
        resp = (
            service.playlistItems()
            .list(
                part="contentDetails",
                playlistId=uploads_playlist,
                maxResults=min(50, limit - len(ids)),
                pageToken=page_token,
            )
            .execute()
        )
        ids.extend(i["contentDetails"]["videoId"] for i in resp.get("items", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    if not ids:
        return []

    videos = (
        service.videos()
        .list(part="snippet,statistics,contentDetails,status", id=",".join(ids[:limit]))
        .execute()
    ).get("items", [])

    rows = []
    for v in videos:
        stats = v.get("statistics", {})
        rows.append(
            {
                "id": v["id"],
                "title": v["snippet"]["title"],
                "published_at": v["snippet"]["publishedAt"],
                "privacy": v.get("status", {}).get("privacyStatus", "?"),
                "duration": v.get("contentDetails", {}).get("duration", ""),
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
            }
        )
    return rows


def retention(analytics_service, video_ids: list[str], days: int = 28) -> dict[str, dict]:
    """Per-video retention over the trailing window, keyed by video ID."""
    if not video_ids:
        return {}

    end = dt.date.today()
    start = end - dt.timedelta(days=days)

    resp = (
        analytics_service.reports()
        .query(
            ids="channel==MINE",
            startDate=start.isoformat(),
            endDate=end.isoformat(),
            metrics="views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,subscribersGained",
            dimensions="video",
            filters="video==" + ",".join(video_ids[:500]),
            maxResults=200,
        )
        .execute()
    )

    headers = [h["name"] for h in resp.get("columnHeaders", [])]
    out: dict[str, dict] = {}
    for row in resp.get("rows", []):
        record = dict(zip(headers, row))
        out[record.pop("video")] = record
    return out
