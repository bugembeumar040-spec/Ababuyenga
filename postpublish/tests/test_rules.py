import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from postpublish import pack as packlib
from postpublish import rules
from postpublish.rules import FAIL, PASS, WARN


def ctx(title="t", description="", tags=None, duration=600, **kw):
    base = {
        "video_id": "vid",
        "snippet": {"title": title, "description": description,
                    "tags": tags or [], "channelId": "UCowner",
                    "categoryId": "27", "thumbnails": {}},
        "duration_seconds": duration,
        "captions": [], "comment_threads": [], "playlist_membership": [],
    }
    base.update(kw)
    return base


class TestDurationParsing(unittest.TestCase):
    def test_forms(self):
        f = rules.iso8601_duration_seconds
        self.assertEqual(f("PT1M30S"), 90)
        self.assertEqual(f("PT1H2M3S"), 3723)
        self.assertEqual(f("PT45S"), 45)
        self.assertEqual(f("PT10M"), 600)
        self.assertIsNone(f("garbage"))


class TestTimestampParsing(unittest.TestCase):
    def test_extracts_chapters(self):
        desc = "intro\n0:00 Start\n1:30 Middle\n12:05 End\n"
        self.assertEqual(rules.parse_timestamps(desc),
                         [(0, "Start"), (90, "Middle"), (725, "End")])

    def test_handles_hours(self):
        self.assertEqual(rules.parse_timestamps("1:02:03 Late")[0][0], 3723)

    def test_ignores_prose(self):
        self.assertEqual(rules.parse_timestamps("no stamps here"), [])


class TestChapterRule(unittest.TestCase):
    def test_missing_chapters_fails_on_longform(self):
        self.assertEqual(rules.rule_chapters(ctx(duration=600)).status, FAIL)

    def test_chapters_skipped_on_short(self):
        self.assertEqual(rules.rule_chapters(ctx(duration=45)).status, PASS)

    def test_first_marker_must_be_zero(self):
        d = "0:10 A\n1:00 B\n2:00 C"
        f = rules.rule_chapters(ctx(description=d))
        self.assertEqual(f.status, FAIL)
        self.assertIn("0:00", f.message)

    def test_too_short_chapter_rejected(self):
        d = "0:00 A\n0:05 B\n2:00 C"
        f = rules.rule_chapters(ctx(description=d))
        self.assertEqual(f.status, FAIL)
        self.assertIn("under the 10s minimum", f.message)

    def test_valid_chapters_pass(self):
        d = "0:00 A\n1:00 B\n2:00 C"
        self.assertEqual(rules.rule_chapters(ctx(description=d)).status, PASS)


class TestHashtagRule(unittest.TestCase):
    def test_over_limit_fails(self):
        d = " ".join("#tag%d" % i for i in range(20))
        self.assertEqual(rules.rule_hashtags(ctx(description=d)).status, FAIL)

    def test_none_warns(self):
        self.assertEqual(rules.rule_hashtags(ctx(description="hi")).status, WARN)

    def test_three_pass(self):
        f = rules.rule_hashtags(ctx(description="hi #a #b #c"))
        self.assertEqual(f.status, PASS)


class TestTitleRules(unittest.TestCase):
    def test_over_100_fails(self):
        self.assertEqual(rules.rule_title_length(ctx(title="x" * 101)).status, FAIL)

    def test_over_70_warns(self):
        self.assertEqual(rules.rule_title_length(ctx(title="x" * 80)).status, WARN)

    def test_normal_passes(self):
        self.assertEqual(rules.rule_title_length(ctx(title="x" * 50)).status, PASS)

    def test_angle_bracket_fails(self):
        self.assertEqual(rules.rule_title_chars(ctx(title="a <b>")).status, FAIL)


class TestTagsRule(unittest.TestCase):
    def test_over_char_budget_fails(self):
        f = rules.rule_tags(ctx(tags=["x" * 100] * 6))
        self.assertEqual(f.status, FAIL)

    def test_empty_warns(self):
        self.assertEqual(rules.rule_tags(ctx(tags=[])).status, WARN)


class TestCommentRule(unittest.TestCase):
    def test_detects_owner_comment(self):
        threads = [{"snippet": {"topLevelComment": {"snippet": {
            "authorChannelId": {"value": "UCowner"}}}}}]
        f = rules.rule_channel_comment(ctx(comment_threads=threads))
        self.assertEqual(f.status, PASS)

    def test_other_authors_do_not_count(self):
        threads = [{"snippet": {"topLevelComment": {"snippet": {
            "authorChannelId": {"value": "UCsomeoneelse"}}}}}]
        f = rules.rule_channel_comment(ctx(comment_threads=threads))
        self.assertEqual(f.status, FAIL)


class TestDescriptionFold(unittest.TestCase):
    def test_empty_fails(self):
        self.assertEqual(rules.rule_description_fold(ctx()).status, FAIL)

    def test_leading_link_fails(self):
        f = rules.rule_description_fold(ctx(description="https://x.com hi"))
        self.assertEqual(f.status, FAIL)

    def test_hook_passes(self):
        f = rules.rule_description_fold(ctx(description="A real hook line."))
        self.assertEqual(f.status, PASS)


class TestPackValidation(unittest.TestCase):
    def make(self, **over):
        pk = packlib.new_skeleton("vid")
        pk["title"]["current"] = "A reasonable title"
        pk["description"]["hook"] = "A hook."
        pk["description"]["body"] = "Body."
        pk["tags"] = ["a", "b"]
        pk["pinned_comment"] = "Question?"
        for k, v in over.items():
            pk[k] = v
        return pk

    def test_clean_pack_has_no_failures(self):
        findings = packlib.validate(self.make())
        self.assertFalse(packlib.has_blocking_failure(findings), findings)

    def test_chapter_past_runtime_fails(self):
        pk = self.make()
        pk["description"]["chapters"] = [[0, "A"], [60, "B"], [120, "C"]]
        findings = packlib.validate(pk, duration_seconds=100)
        self.assertTrue(packlib.has_blocking_failure(findings))

    def test_unsorted_chapters_fail(self):
        pk = self.make()
        pk["description"]["chapters"] = [[0, "A"], [120, "B"], [60, "C"]]
        self.assertTrue(packlib.has_blocking_failure(
            packlib.validate(pk, duration_seconds=600)))

    def test_tag_budget_enforced(self):
        pk = self.make(tags=["y" * 90] * 7)
        self.assertTrue(packlib.has_blocking_failure(packlib.validate(pk)))

    def test_render_description_formats_chapters(self):
        pk = self.make()
        pk["description"]["chapters"] = [[0, "Start"], [95, "Mid"], [3725, "End"]]
        out = packlib.render_description(pk)
        self.assertIn("0:00 Start", out)
        self.assertIn("1:35 Mid", out)
        self.assertIn("1:02:05 End", out)

    def test_rendered_chapters_survive_reparse(self):
        """What we render must be what the live-video rule can read back."""
        pk = self.make()
        pk["description"]["chapters"] = [[0, "Start"], [95, "Mid"], [200, "End"]]
        out = packlib.render_description(pk)
        self.assertEqual([s for s, _ in rules.parse_timestamps(out)],
                         [0, 95, 200])

    def test_hashtags_render_and_count(self):
        pk = self.make()
        pk["description"]["hashtags"] = ["quran", "islam", "tafsir"]
        out = packlib.render_description(pk)
        self.assertIn("#quran", out)
        self.assertEqual(len(rules.HASHTAG_RE.findall(out)), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
