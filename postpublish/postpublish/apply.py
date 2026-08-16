"""Execute the automatable steps against a live video.

Safety model, in order of strictness:

  1. Dry run is the default. Nothing mutates unless --apply is passed.
  2. Validation gates the run. A pack with any FAIL never reaches the API.
  3. Every write is preceded by a read of the current live value, and the
     before/after is printed. Mutating a live video is not reversible by
     this tool, so the operator sees the diff first.
  4. A backup of the live snippet is written to disk before the first write,
     so a bad run can be reverted by hand.
"""

import datetime
import json
import os

from . import pack as packlib
from . import rules
from .api import ApiError


class Step:
    def __init__(self, name, describe, run):
        self.name = name
        self.describe = describe
        self.run = run


def backup_live_state(yt, video_id, out_dir):
    live = yt.video(video_id, parts="snippet,status")
    os.makedirs(out_dir, exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = os.path.join(out_dir, "backup-%s.json" % stamp)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(live, fh, indent=2, ensure_ascii=False)
    return path, live


def plan(yt, video_id, pk, live_snippet):
    """Build the ordered list of steps, skipping ones already satisfied."""
    steps = []

    new_title = (pk.get("title") or {}).get("current", "")
    new_desc = packlib.render_description(pk)
    new_tags = pk.get("tags") or []

    snippet_changes = {}
    if new_title and new_title != live_snippet.get("title"):
        snippet_changes["title"] = new_title
    if new_desc and new_desc != live_snippet.get("description"):
        snippet_changes["description"] = new_desc
    if new_tags and new_tags != (live_snippet.get("tags") or []):
        snippet_changes["tags"] = new_tags

    if snippet_changes:
        def describe():
            out = []
            for key, value in snippet_changes.items():
                before = live_snippet.get(key)
                out.append("  %s:" % key)
                out.append("    before: %s" % _preview(before))
                out.append("    after : %s" % _preview(value))
            return "\n".join(out)

        def run():
            return yt.update_video_snippet(video_id, snippet_changes)

        steps.append(Step("videos.update (%s)" % ",".join(snippet_changes),
                          describe, run))

    comment = (pk.get("pinned_comment") or "").strip()
    if comment:
        channel_id = live_snippet.get("channelId")

        def describe_c():
            return "  post top-level comment (%d chars):\n    %s" % (
                len(comment), _preview(comment, 240))

        def run_c():
            return yt.post_comment(video_id, channel_id, comment)

        steps.append(Step("commentThreads.insert", describe_c, run_c))

    for playlist_id in pk.get("playlists") or []:
        def describe_p(pid=playlist_id):
            return "  add video to playlist %s" % pid

        def run_p(pid=playlist_id):
            return yt.add_to_playlist(pid, video_id)

        steps.append(Step("playlistItems.insert (%s)" % playlist_id,
                          describe_p, run_p))

    return steps


def _preview(value, limit=160):
    text = " / ".join(value) if isinstance(value, list) else str(value or "")
    text = text.replace("\n", "\\n")
    return text if len(text) <= limit else text[:limit] + "..."


def execute(yt, video_id, pk, out_dir, apply_changes=False,
            duration_seconds=None):
    report = []
    findings = packlib.validate(pk, duration_seconds=duration_seconds)
    report.append("PACK VALIDATION")
    for f in findings:
        report.append("  [%-4s] %-28s %s" % (f.status, f.rule, f.message))

    if packlib.has_blocking_failure(findings):
        report.append("")
        report.append("BLOCKED: pack has validation failures. Nothing was sent.")
        return "\n".join(report), False

    backup_path = None
    if apply_changes:
        backup_path, live = backup_live_state(yt, video_id, out_dir)
        report.append("")
        report.append("Backed up live snippet to %s" % backup_path)
        live_snippet = live.get("snippet", {})
    else:
        live_snippet = yt.video(video_id, parts="snippet")["snippet"]

    steps = plan(yt, video_id, pk, live_snippet)
    report.append("")
    report.append("PLAN (%d step%s)" % (len(steps), "" if len(steps) == 1 else "s"))
    if not steps:
        report.append("  nothing to do -- live video already matches the pack")
    for step in steps:
        report.append("- %s" % step.name)
        report.append(step.describe())

    if not apply_changes:
        report.append("")
        report.append("DRY RUN. Re-run with --apply to send these writes.")
        return "\n".join(report), True

    report.append("")
    report.append("EXECUTING")
    ok = True
    for step in steps:
        try:
            step.run()
            report.append("  [done] %s" % step.name)
        except ApiError as exc:
            ok = False
            report.append("  [FAIL] %s -> %s" % (step.name, exc))
            report.append("  stopping; remaining steps not attempted")
            if backup_path:
                report.append("  restore from %s" % backup_path)
            break

    report.append("")
    report.append("MANUAL STEPS REMAIN -- the API cannot do these:")
    for name, text in rules.MANUAL_STEPS:
        report.append("  [ ] %-22s %s" % (name, text))
    return "\n".join(report), ok
