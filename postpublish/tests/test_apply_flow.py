import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from postpublish import apply as applylib
from postpublish import pack as packlib
from tests.test_api_safety import RecordingYouTube


def good_pack():
    pk = packlib.new_skeleton("vid")
    pk["title"]["current"] = "A new and better title"
    pk["description"]["hook"] = "A hook that earns the click."
    pk["description"]["body"] = "Body copy."
    pk["tags"] = ["one", "two"]
    pk["pinned_comment"] = "What did you think?"
    return pk


class TestDryRunWritesNothing(unittest.TestCase):
    def test_dry_run_sends_no_requests(self):
        yt = RecordingYouTube()
        with tempfile.TemporaryDirectory() as tmp:
            report, ok = applylib.execute(yt, "vid", good_pack(), tmp,
                                          apply_changes=False)
        self.assertTrue(ok)
        self.assertEqual(yt.sent, [], "dry run must not touch the API")
        self.assertIn("DRY RUN", report)

    def test_dry_run_shows_before_and_after(self):
        yt = RecordingYouTube()
        with tempfile.TemporaryDirectory() as tmp:
            report, _ = applylib.execute(yt, "vid", good_pack(), tmp,
                                         apply_changes=False)
        self.assertIn("before:", report)
        self.assertIn("after :", report)
        self.assertIn("Original title", report)
        self.assertIn("A new and better title", report)


class TestValidationGate(unittest.TestCase):
    def test_invalid_pack_blocks_before_any_call(self):
        pk = good_pack()
        pk["title"]["current"] = "x" * 150  # over the 100 char limit
        yt = RecordingYouTube()
        with tempfile.TemporaryDirectory() as tmp:
            report, ok = applylib.execute(yt, "vid", pk, tmp,
                                          apply_changes=True)
        self.assertFalse(ok)
        self.assertIn("BLOCKED", report)
        self.assertEqual(yt.sent, [],
                         "a failing pack must never reach the API, even with --apply")


class TestApplyPath(unittest.TestCase):
    def test_apply_writes_backup_and_sends(self):
        yt = RecordingYouTube()
        with tempfile.TemporaryDirectory() as tmp:
            report, ok = applylib.execute(yt, "vid", good_pack(), tmp,
                                          apply_changes=True)
            backups = [f for f in os.listdir(tmp) if f.startswith("backup-")]
        self.assertTrue(ok)
        self.assertEqual(len(backups), 1, "must snapshot live state before writing")
        methods = [(s["method"], s["url"].rsplit("/", 1)[-1]) for s in yt.sent]
        self.assertIn(("PUT", "videos"), methods)
        self.assertIn(("POST", "commentThreads"), methods)
        self.assertIn("MANUAL STEPS REMAIN", report)

    def test_no_op_when_pack_matches_live(self):
        pk = packlib.new_skeleton("vid")
        pk["title"]["current"] = "Original title"
        pk["description"]["body"] = "Original description with real value."
        pk["tags"] = ["alpha", "beta"]
        yt = RecordingYouTube()
        with tempfile.TemporaryDirectory() as tmp:
            report, ok = applylib.execute(yt, "vid", pk, tmp,
                                          apply_changes=False)
        self.assertIn("nothing to do", report)


if __name__ == "__main__":
    unittest.main(verbosity=2)
