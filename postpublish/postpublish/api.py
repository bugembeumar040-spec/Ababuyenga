"""A thin YouTube Data API v3 client over the standard library.

Deliberately small: this only wraps the calls the post-publish playbook
actually needs, and it wraps them in the safe order. The one piece of real
logic in here is update_video_snippet(), which exists because the naive
version of that call is destructive -- see the docstring.
"""

import json
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://www.googleapis.com/youtube/v3"
UPLOAD_BASE = "https://www.googleapis.com/upload/youtube/v3"


class ApiError(RuntimeError):
    def __init__(self, status, message, detail=None):
        super().__init__("YouTube API %s: %s" % (status, message))
        self.status = status
        self.detail = detail


class YouTube:
    def __init__(self, credentials, timeout=45):
        self.creds = credentials
        self.timeout = timeout

    # -- plumbing -----------------------------------------------------------

    def _request(self, method, url, params=None, body=None, raw=None,
                 content_type=None):
        if params:
            url = "%s?%s" % (url, urllib.parse.urlencode(params, doseq=True))
        data = raw
        headers = {"Authorization": "Bearer %s" % self.creds.token()}
        if body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        if content_type:
            headers["Content-Type"] = content_type
        req = urllib.request.Request(url, data=data, headers=headers,
                                     method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                text = resp.read().decode("utf-8", "replace")
                return json.loads(text) if text.strip() else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")
            message = detail[:500]
            try:
                message = json.loads(detail)["error"]["message"]
            except Exception:
                pass
            raise ApiError(exc.code, message, detail)

    def get(self, path, **params):
        return self._request("GET", "%s/%s" % (BASE, path), params=params)

    # -- reads --------------------------------------------------------------

    def video(self, video_id, parts="snippet,status,contentDetails,statistics"):
        data = self.get("videos", part=parts, id=video_id)
        items = data.get("items") or []
        if not items:
            raise ApiError(404, "video %s not found or not visible to this account"
                           % video_id)
        return items[0]

    def my_channel(self):
        data = self.get("channels", part="snippet,contentDetails,statistics",
                        mine="true")
        items = data.get("items") or []
        if not items:
            raise ApiError(404, "no channel on the authenticated account")
        return items[0]

    def captions(self, video_id):
        return (self.get("captions", part="snippet",
                         videoId=video_id).get("items") or [])

    def playlists(self, channel_id=None, max_results=50):
        params = {"part": "snippet,contentDetails", "maxResults": max_results}
        if channel_id:
            params["channelId"] = channel_id
        else:
            params["mine"] = "true"
        return self.get("playlists", **params).get("items") or []

    def comment_threads(self, video_id, max_results=50):
        try:
            return (self.get("commentThreads", part="snippet",
                             videoId=video_id, maxResults=max_results,
                             order="relevance").get("items") or [])
        except ApiError as exc:
            # Comments disabled is a legitimate state, not a crash.
            if exc.status in (403, 404):
                return []
            raise

    # -- writes -------------------------------------------------------------

    def update_video_snippet(self, video_id, changes):
        """Patch specific snippet fields without destroying the rest.

        videos.update replaces the whole snippet part. Any writable field the
        request omits is CLEARED, so sending {"title": ...} alone wipes the
        description, the tags and the category. The only safe form is
        read-modify-write: fetch the current snippet, apply the delta, send
        the merged object back. That is what this does, and it is the reason
        callers should never hand-roll a videos.update.
        """
        current = self.video(video_id, parts="snippet")["snippet"]
        merged = {
            "title": current.get("title", ""),
            "categoryId": current.get("categoryId"),
            "description": current.get("description", ""),
            "tags": current.get("tags", []),
        }
        if current.get("defaultLanguage"):
            merged["defaultLanguage"] = current["defaultLanguage"]
        if current.get("defaultAudioLanguage"):
            # Not writable via snippet, but keep it out of the payload rather
            # than silently sending it back.
            pass
        merged.update(changes)
        if not merged.get("categoryId"):
            raise ApiError(400, "categoryId is required on a snippet update "
                                "and the live video did not report one")
        return self._request("PUT", "%s/videos" % BASE, params={"part": "snippet"},
                             body={"id": video_id, "snippet": merged})

    def set_thumbnail(self, video_id, image_bytes, mime="image/jpeg"):
        return self._request(
            "POST", "%s/thumbnails/set" % UPLOAD_BASE,
            params={"videoId": video_id, "uploadType": "media"},
            raw=image_bytes, content_type=mime,
        )

    def post_comment(self, video_id, channel_id, text):
        """Post a top-level comment. NOTE: pinning is not exposed by the API."""
        return self._request(
            "POST", "%s/commentThreads" % BASE, params={"part": "snippet"},
            body={"snippet": {
                "channelId": channel_id,
                "videoId": video_id,
                "topLevelComment": {"snippet": {"textOriginal": text}},
            }},
        )

    def add_to_playlist(self, playlist_id, video_id, position=None):
        snippet = {
            "playlistId": playlist_id,
            "resourceId": {"kind": "youtube#video", "videoId": video_id},
        }
        if position is not None:
            snippet["position"] = position
        return self._request("POST", "%s/playlistItems" % BASE,
                             params={"part": "snippet"}, body={"snippet": snippet})
