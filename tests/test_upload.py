"""Tests for the resumable-upload loop, including its retry behaviour.

This is the code path that spends 1600 quota units per call, so it is worth
exercising against a fake service rather than discovering its edges live.
"""

import http.client
import sys
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from googleapiclient.errors import HttpError  # noqa: E402

from ytauto import metadata, upload as upload_mod  # noqa: E402


class FakeStatus:
    def __init__(self, fraction):
        self._fraction = fraction

    def progress(self):
        return self._fraction


class FakeRequest:
    """Yields a scripted sequence of next_chunk() outcomes."""

    def __init__(self, script):
        self.script = list(script)
        self.calls = 0

    def next_chunk(self):
        self.calls += 1
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def http_error(status):
    resp = mock.Mock()
    resp.status = status
    return HttpError(resp, b'{"error": {"message": "boom"}}')


def meta_for(tmp_path):
    (tmp_path / "v.mp4").write_bytes(b"\x00" * 1024)
    sidecar = tmp_path / "v.yml"
    sidecar.write_text("video_file: v.mp4\ntitle: t\ndescription: d\n")
    return metadata.load(sidecar)


def run(tmp_path, script, progress=None):
    request = FakeRequest(script)
    service = mock.Mock()
    service.videos.return_value.insert.return_value = request
    with mock.patch.object(upload_mod, "MediaFileUpload"), \
         mock.patch.object(upload_mod.time, "sleep"):
        video_id = upload_mod.upload_video(service, meta_for(tmp_path), progress)
    return video_id, request, service


def test_successful_upload_reports_progress(tmp_path):
    seen = []
    video_id, _, service = run(
        tmp_path,
        [(FakeStatus(0.5), None), (None, {"id": "abc123"})],
        seen.append,
    )
    assert video_id == "abc123"
    assert seen[0] == 50 and seen[-1] == 100

    # the request is built with the parts the body actually populates
    kwargs = service.videos.return_value.insert.call_args.kwargs
    assert kwargs["part"] == "snippet,status,recordingDetails"
    assert kwargs["body"]["snippet"]["title"] == "t"


def test_retries_on_5xx_then_succeeds(tmp_path):
    video_id, request, _ = run(
        tmp_path,
        [http_error(503), http_error(500), (None, {"id": "ok"})],
    )
    assert video_id == "ok"
    assert request.calls == 3


def test_retries_on_socket_errors(tmp_path):
    video_id, request, _ = run(
        tmp_path,
        [http.client.IncompleteRead(b""), (None, {"id": "ok"})],
    )
    assert video_id == "ok"
    assert request.calls == 2


def test_4xx_is_not_retried(tmp_path):
    with pytest.raises(HttpError):
        run(tmp_path, [http_error(403)])


def test_gives_up_after_max_retries(tmp_path):
    script = [http_error(503)] * (upload_mod.MAX_RETRIES + 2)
    with pytest.raises(RuntimeError, match="after 10 retries"):
        run(tmp_path, script)


def test_missing_id_in_response_raises(tmp_path):
    with pytest.raises(RuntimeError, match="no video ID"):
        run(tmp_path, [(None, {"unexpected": "shape"})])


def test_playlist_insert_body(tmp_path):
    service = mock.Mock()
    upload_mod.add_to_playlist(service, "vid1", "PL123")
    kwargs = service.playlistItems.return_value.insert.call_args.kwargs
    assert kwargs["body"]["snippet"]["playlistId"] == "PL123"
    assert kwargs["body"]["snippet"]["resourceId"] == {
        "kind": "youtube#video",
        "videoId": "vid1",
    }


def test_channel_info_without_channel_raises(tmp_path):
    service = mock.Mock()
    service.channels.return_value.list.return_value.execute.return_value = {"items": []}
    with pytest.raises(RuntimeError, match="Brand Account"):
        upload_mod.channel_info(service)
