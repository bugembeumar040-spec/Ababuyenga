"""Read a live video and score it against the playbook.

Strictly read-only. `audit` is the command you can safely run against
anything, including a channel you do not own -- which is also how you use it
to reverse-engineer what a channel bigger than yours is doing to its videos.
"""

import json

from . import rules
from .api import ApiError


def build_context(yt, video_id, check_playlists=True):
    """Gather everything the rules need in as few API calls as possible."""
    video = yt.video(video_id)
    snippet = video.get("snippet", {})
    ctx = {
        "video_id": video_id,
        "snippet": snippet,
        "status": video.get("status", {}),
        "statistics": video.get("statistics", {}),
        "duration_seconds": rules.iso8601_duration_seconds(
            video.get("contentDetails", {}).get("duration")
        ),
        "captions": None,
        "comment_threads": None,
        "playlist_membership": None,
    }

    try:
        ctx["captions"] = yt.captions(video_id)
    except ApiError:
        # captions.list needs ownership; on someone else's video this 403s,
        # which is information, not failure.
        ctx["captions"] = None

    ctx["comment_threads"] = yt.comment_threads(video_id)

    if check_playlists:
        try:
            member_of = []
            for pl in yt.playlists():
                items = yt.get("playlistItems", part="snippet",
                               playlistId=pl["id"], videoId=video_id,
                               maxResults=1).get("items") or []
                if items:
                    member_of.append(pl["snippet"]["title"])
            ctx["playlist_membership"] = member_of
        except ApiError:
            ctx["playlist_membership"] = None
    return ctx


def run(ctx, rule_list=None):
    findings = []
    for rule in (rule_list or rules.ALL_RULES):
        try:
            findings.append(rule(ctx))
        except Exception as exc:  # a broken rule must not sink the report
            findings.append(rules.Finding(
                getattr(rule, "__name__", "?"), rules.WARN,
                "rule raised %s: %s" % (type(exc).__name__, exc)))
    return findings


def score(findings):
    """Weighted share of automatable checks that pass. MANUAL is excluded."""
    scored = [f for f in findings if f.status in (rules.PASS, rules.FAIL)]
    if not scored:
        return 0.0
    earned = sum(f.weight for f in scored if f.status == rules.PASS)
    total = sum(f.weight for f in scored)
    return round(100.0 * earned / total, 1)


def format_report(ctx, findings, include_manual=True):
    sn = ctx["snippet"]
    st = ctx["statistics"]
    mark = {rules.PASS: "PASS", rules.FAIL: "FAIL",
            rules.WARN: "WARN", rules.MANUAL: "MANUAL"}
    lines = []
    lines.append("=" * 78)
    lines.append("POST-PUBLISH AUDIT  %s" % ctx["video_id"])
    lines.append("=" * 78)
    lines.append("title    : %s" % sn.get("title", ""))
    lines.append("channel  : %s (%s)" % (sn.get("channelTitle"), sn.get("channelId")))
    lines.append("published: %s" % sn.get("publishedAt"))
    lines.append("duration : %ss" % ctx.get("duration_seconds"))
    lines.append("stats    : %s views / %s likes / %s comments" % (
        st.get("viewCount", "?"), st.get("likeCount", "?"),
        st.get("commentCount", "?")))
    lines.append("")
    lines.append("AUTOMATABLE CHECKS")
    lines.append("-" * 78)
    for f in findings:
        lines.append("[%-6s] %-26s %s" % (mark[f.status], f.rule, f.message))
        if f.fix and f.status in (rules.FAIL, rules.WARN):
            lines.append("%-9s %-26s -> %s" % ("", "", f.fix))
    lines.append("")
    lines.append("SCORE: %.1f%% of automatable checks pass" % score(findings))
    if include_manual:
        lines.append("")
        lines.append("NOT AUTOMATABLE - the API cannot see or do these")
        lines.append("-" * 78)
        for name, text in rules.MANUAL_STEPS:
            lines.append("[MANUAL] %-22s %s" % (name, text))
    lines.append("=" * 78)
    return "\n".join(lines)


def to_json(ctx, findings):
    return json.dumps({
        "video_id": ctx["video_id"],
        "title": ctx["snippet"].get("title"),
        "channel_id": ctx["snippet"].get("channelId"),
        "duration_seconds": ctx.get("duration_seconds"),
        "score": score(findings),
        "findings": [f.as_dict() for f in findings],
        "manual_steps": [{"step": n, "detail": d}
                         for n, d in rules.MANUAL_STEPS],
    }, indent=2)
