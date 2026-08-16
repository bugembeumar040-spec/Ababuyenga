"""Authoring and validation for a per-video asset pack.

The split matters. The tool does NOT write the copy -- an algorithm that
generates titles produces the flat, interchangeable copy that the format is
already drowning in. What the tool does is:

  * define every slot the playbook needs filled, so nothing is forgotten,
  * validate authored copy against every hard platform limit *before* it
    touches the live video, because a rejected write mid-run leaves the
    video half-updated,
  * carry the manual steps with their copy pre-written, so the Studio-only
    work is mechanical rather than remembered.

A pack is a plain JSON file: reviewable in a diff, editable by hand.
"""

import json
import os

from . import constraints as C
from . import rules

SKELETON = {
    "video_id": "",
    "notes": "",
    "title": {
        "current": "",
        "variants": [],
        "_help": "variants[0] is the challenger for a Test & Compare run. "
                 "Keep the hook inside the first 70 chars.",
    },
    "description": {
        "hook": "",
        "body": "",
        "chapters": [],
        "links": [],
        "hashtags": [],
        "_help": "hook is the above-the-fold line (<=%d chars). chapters are "
                 "[seconds, label] and must start at 0." % C.DESCRIPTION_FOLD_CHARS,
    },
    "tags": [],
    "pinned_comment": "",
    "playlists": [],
    "community_post": "",
    "shorts_derivative": {"in": None, "out": None, "hook": "", "caption": ""},
    "cross_platform": {},
}


def new_skeleton(video_id):
    pack = json.loads(json.dumps(SKELETON))
    pack["video_id"] = video_id
    return pack


def load(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def save(pack, path):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(pack, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def render_description(pack):
    """Assemble the final description string from the pack's parts."""
    d = pack.get("description", {})
    blocks = []
    if d.get("hook"):
        blocks.append(d["hook"].strip())
    if d.get("body"):
        blocks.append(d["body"].strip())
    chapters = d.get("chapters") or []
    if chapters:
        lines = ["CHAPTERS"]
        for seconds, label in chapters:
            seconds = int(seconds)
            if seconds >= 3600:
                stamp = "%d:%02d:%02d" % (seconds // 3600,
                                          (seconds % 3600) // 60, seconds % 60)
            else:
                stamp = "%d:%02d" % (seconds // 60, seconds % 60)
            lines.append("%s %s" % (stamp, label))
        blocks.append("\n".join(lines))
    if d.get("links"):
        blocks.append("\n".join(d["links"]))
    if d.get("hashtags"):
        blocks.append(" ".join(
            h if h.startswith("#") else "#" + h for h in d["hashtags"]))
    return "\n\n".join(blocks).strip()


def validate(pack, duration_seconds=None):
    """Return a list of Findings. Any FAIL must block a live write."""
    out = []

    title = (pack.get("title") or {}).get("current", "")
    if not title:
        out.append(rules.Finding("pack.title", rules.FAIL, "no title set"))
    else:
        if len(title) > C.TITLE_MAX:
            out.append(rules.Finding(
                "pack.title", rules.FAIL,
                "title %d chars, over %d" % (len(title), C.TITLE_MAX)))
        elif len(title) > 70:
            out.append(rules.Finding(
                "pack.title", rules.WARN,
                "title %d chars; truncated in mobile browse" % len(title)))
        else:
            out.append(rules.Finding("pack.title", rules.PASS,
                                     "%d chars" % len(title)))
        if any(c in title for c in C.FORBIDDEN_TITLE_CHARS):
            out.append(rules.Finding("pack.title.chars", rules.FAIL,
                                     "contains a forbidden angle bracket"))

    for i, v in enumerate((pack.get("title") or {}).get("variants", [])):
        if len(v) > C.TITLE_MAX:
            out.append(rules.Finding(
                "pack.title.variant[%d]" % i, rules.FAIL,
                "variant %d chars, over %d" % (len(v), C.TITLE_MAX)))

    desc = render_description(pack)
    if not desc:
        out.append(rules.Finding("pack.description", rules.FAIL, "empty"))
    elif len(desc) > C.DESCRIPTION_MAX:
        out.append(rules.Finding(
            "pack.description", rules.FAIL,
            "%d chars, over %d" % (len(desc), C.DESCRIPTION_MAX)))
    else:
        out.append(rules.Finding("pack.description", rules.PASS,
                                 "%d chars" % len(desc)))

    hook = (pack.get("description") or {}).get("hook", "")
    if hook and len(hook) > C.DESCRIPTION_FOLD_CHARS:
        out.append(rules.Finding(
            "pack.description.hook", rules.WARN,
            "hook is %d chars; only ~%d survive above the fold"
            % (len(hook), C.DESCRIPTION_FOLD_CHARS)))

    tags_in_desc = rules.HASHTAG_RE.findall(desc)
    if len(tags_in_desc) > C.HASHTAGS_MAX:
        out.append(rules.Finding(
            "pack.hashtags", rules.FAIL,
            "%d hashtags; past %d YouTube ignores all of them"
            % (len(tags_in_desc), C.HASHTAGS_MAX)))
    else:
        out.append(rules.Finding("pack.hashtags", rules.PASS,
                                 "%d hashtags" % len(tags_in_desc)))

    tags = pack.get("tags") or []
    total = sum(len(t) for t in tags)
    if total > C.TAGS_TOTAL_CHARS_MAX:
        out.append(rules.Finding(
            "pack.tags", rules.FAIL,
            "tags total %d chars, over %d -- the API will reject this write"
            % (total, C.TAGS_TOTAL_CHARS_MAX)))
    else:
        out.append(rules.Finding(
            "pack.tags", rules.PASS,
            "%d tags, %d/%d chars" % (len(tags), total, C.TAGS_TOTAL_CHARS_MAX)))

    chapters = (pack.get("description") or {}).get("chapters") or []
    if chapters:
        secs = [int(s) for s, _ in chapters]
        if secs[0] != 0:
            out.append(rules.Finding("pack.chapters", rules.FAIL,
                                     "first chapter must be at 0:00"))
        if len(chapters) < C.CHAPTER_MIN_COUNT:
            out.append(rules.Finding(
                "pack.chapters", rules.FAIL,
                "%d chapters, need >=%d to render"
                % (len(chapters), C.CHAPTER_MIN_COUNT)))
        if secs != sorted(secs):
            out.append(rules.Finding("pack.chapters", rules.FAIL,
                                     "chapters are not in ascending order"))
        for (a, _), (b, lab) in zip(chapters, chapters[1:]):
            if int(b) - int(a) < C.CHAPTER_MIN_LENGTH_SECONDS:
                out.append(rules.Finding(
                    "pack.chapters", rules.FAIL,
                    "'%s' runs %ds, under the %ds minimum"
                    % (lab, int(b) - int(a), C.CHAPTER_MIN_LENGTH_SECONDS)))
        if duration_seconds and secs[-1] >= duration_seconds:
            out.append(rules.Finding(
                "pack.chapters", rules.FAIL,
                "last chapter at %ds is past the %ds runtime"
                % (secs[-1], duration_seconds)))

    comment = pack.get("pinned_comment") or ""
    if not comment.strip():
        out.append(rules.Finding("pack.pinned_comment", rules.WARN,
                                 "no pinned comment authored"))
    elif len(comment) > C.COMMENT_MAX:
        out.append(rules.Finding(
            "pack.pinned_comment", rules.FAIL,
            "%d chars, over %d" % (len(comment), C.COMMENT_MAX)))
    else:
        out.append(rules.Finding("pack.pinned_comment", rules.PASS,
                                 "%d chars" % len(comment)))

    return out


def has_blocking_failure(findings):
    return any(f.status == rules.FAIL for f in findings)
