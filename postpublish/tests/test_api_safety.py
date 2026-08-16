"""The destructive-update guard.

videos.update replaces the entire snippet part. If a caller sends only the
field it wants to change, YouTube deletes every writable field the request
omitted -- the description, the tags and the category all vanish from a live
video. These tests pin the read-modify-write behaviour that prevents it.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from postpublish.api import ApiError, YouTube

LIVE = {
    "snippet": {
        "title": "Original title",
        "description": "Original description with real value.",
        "tags": ["alpha", "beta"],
        "categoryId": "27",
        "channelId": "UCowner",
        "defaultLanguage": "en",
        "thumbnails": {},
    }
}


class FakeCreds:
    def token(self):
        return "fake"


class RecordingYouTube(YouTube):
    """Captures the outgoing request instead of hitting the network."""

    def __init__(self, live=None):
        super().__init__(FakeCreds())
        self.sent = []
        self._live = live if live is not None else LIVE

    def _request(self, method, url, params=None, body=None, raw=None,
                 content_type=None):
        self.sent.append({"method": method, "url": url, "params": params,
                          "body": body})
        return {"ok": True}

    def video(self, video_id, parts="snippet"):
        import copy
        return copy.deepcopy(self._live)


class TestSnippetMergeIsNonDestructive(unittest.TestCase):
    def test_title_only_update_preserves_everything_else(self):
        yt = RecordingYouTube()
        yt.update_video_snippet("vid", {"title": "New title"})
        sent = yt.sent[0]["body"]["snippet"]

        self.assertEqual(sent["title"], "New title")
        # The fields we did NOT ask to change must still be in the payload,
        # otherwise YouTube clears them.
        self.assertEqual(sent["description"], LIVE["snippet"]["description"])
        self.assertEqual(sent["tags"], LIVE["snippet"]["tags"])
        self.assertEqual(sent["categoryId"], LIVE["snippet"]["categoryId"])

    def test_description_only_update_preserves_title_and_tags(self):
        yt = RecordingYouTube()
        yt.update_video_snippet("vid", {"description": "New body"})
        sent = yt.sent[0]["body"]["snippet"]
        self.assertEqual(sent["title"], LIVE["snippet"]["title"])
        self.assertEqual(sent["tags"], LIVE["snippet"]["tags"])
        self.assertEqual(sent["description"], "New body")

    def test_default_language_carried_through(self):
        yt = RecordingYouTube()
        yt.update_video_snippet("vid", {"title": "X"})
        self.assertEqual(yt.sent[0]["body"]["snippet"]["defaultLanguage"], "en")

    def test_readonly_fields_not_echoed_back(self):
        """channelId/thumbnails are not writable; sending them invites a 400."""
        yt = RecordingYouTube()
        yt.update_video_snippet("vid", {"title": "X"})
        sent = yt.sent[0]["body"]["snippet"]
        self.assertNotIn("channelId", sent)
        self.assertNotIn("thumbnails", sent)

    def test_missing_category_refuses_rather_than_wiping(self):
        live = {"snippet": {"title": "t", "description": "d", "tags": []}}
        yt = RecordingYouTube(live=live)
        with self.assertRaises(ApiError):
            yt.update_video_snippet("vid", {"title": "X"})
        self.assertEqual(yt.sent, [], "must not send a request it knows is bad")

    def test_part_parameter_is_snippet(self):
        yt = RecordingYouTube()
        yt.update_video_snippet("vid", {"title": "X"})
        self.assertEqual(yt.sent[0]["params"], {"part": "snippet"})
        self.assertEqual(yt.sent[0]["method"], "PUT")


class TestCommentPayload(unittest.TestCase):
    def test_required_fields_present(self):
        yt = RecordingYouTube()
        yt.post_comment("vid", "UCowner", "hello")
        snip = yt.sent[0]["body"]["snippet"]
        self.assertEqual(snip["videoId"], "vid")
        self.assertEqual(snip["channelId"], "UCowner")
        self.assertEqual(
            snip["topLevelComment"]["snippet"]["textOriginal"], "hello")


class TestPlaylistPayload(unittest.TestCase):
    def test_resource_id_shape(self):
        yt = RecordingYouTube()
        yt.add_to_playlist("PL123", "vid")
        snip = yt.sent[0]["body"]["snippet"]
        self.assertEqual(snip["playlistId"], "PL123")
        self.assertEqual(snip["resourceId"],
                         {"kind": "youtube#video", "videoId": "vid"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
