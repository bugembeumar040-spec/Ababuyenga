"""The post-publish playbook, encoded as checks.

Each rule is one thing top channels reliably do to a video *after* it is
live. A rule reports one of:

    PASS  - the live video already satisfies it
    FAIL  - it does not, and this is fixable
    WARN  - probably wrong, but the API cannot see enough to be sure
    MANUAL- the API genuinely cannot observe or perform this; a human must

The MANUAL tier is load-bearing. Roughly half of what a good channel does
after publishing is invisible to the Data API (pinning, end screens,
community posts, A/B tests). A tool that quietly dropped those would look
cleaner and would teach the operator the wrong checklist, so they stay in
the report as unautomatable work with the copy pre-written.
"""

import re

from . import constraints as C

PASS, FAIL, WARN, MANUAL = "PASS", "FAIL", "WARN", "MANUAL"

TIMESTAMP_RE = re.compile(r"^((?:\d+:)?\d{1,2}:\d{2})\s+(\S.*)$", re.M)
HASHTAG_RE = re.compile(r"(?<!\w)#(\w+)")


class Finding:
    def __init__(self, rule, status, message, fix=None, weight=1):
        self.rule = rule
        self.status = status
        self.message = message
        self.fix = fix
        self.weight = weight

    def __repr__(self):
        return "<%s %s>" % (self.rule, self.status)

    def as_dict(self):
        return {"rule": self.rule, "status": self.status,
                "message": self.message, "fix": self.fix, "weight": self.weight}


def parse_timestamps(description):
    """Return [(seconds, label)] for lines that look like chapter markers."""
    out = []
    for stamp, label in TIMESTAMP_RE.findall(description or ""):
        parts = [int(p) for p in stamp.split(":")]
        seconds = 0
        for p in parts:
            seconds = seconds * 60 + p
        out.append((seconds, label.strip()))
    return out


def iso8601_duration_seconds(value):
    """PT#H#M#S -> int seconds. Returns None if unparseable."""
    m = re.fullmatch(
        r"P(?:(\d+)D)?T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?", value or ""
    )
    if not m:
        return None
    d, h, mi, s = (float(x) if x else 0 for x in m.groups())
    return int(d * 86400 + h * 3600 + mi * 60 + s)


# --- individual rules -------------------------------------------------------

def rule_title_length(ctx):
    title = ctx["snippet"].get("title", "")
    n = len(title)
    if n > C.TITLE_MAX:
        return Finding("title.length", FAIL,
                       "title is %d chars, over YouTube's %d limit"
                       % (n, C.TITLE_MAX),
                       "cut %d chars" % (n - C.TITLE_MAX), weight=3)
    if n > 70:
        return Finding("title.length", WARN,
                       "title is %d chars; mobile browse truncates around 70, "
                       "so the back half is invisible where most impressions "
                       "are served" % n,
                       "front-load the hook into the first 70 chars")
    return Finding("title.length", PASS, "title is %d chars" % n)


def rule_title_chars(ctx):
    title = ctx["snippet"].get("title", "")
    bad = [c for c in C.FORBIDDEN_TITLE_CHARS if c in title]
    if bad:
        return Finding("title.chars", FAIL,
                       "title contains %s, which the API rejects" % bad,
                       "remove angle brackets", weight=3)
    return Finding("title.chars", PASS, "no forbidden characters")


def rule_description_fold(ctx):
    desc = ctx["snippet"].get("description", "")
    if not desc.strip():
        return Finding("description.fold", FAIL,
                       "description is empty; the first ~%d chars are the only "
                       "copy a browse viewer sees before '...more'"
                       % C.DESCRIPTION_FOLD_CHARS,
                       "write an above-the-fold hook", weight=3)
    fold = desc[:C.DESCRIPTION_FOLD_CHARS]
    if fold.strip().startswith(("http://", "https://", "Subscribe", "SUBSCRIBE")):
        return Finding("description.fold", FAIL,
                       "the above-the-fold description opens with a link or a "
                       "subscribe plea instead of the hook",
                       "move the hook to the first line", weight=2)
    return Finding("description.fold", PASS,
                   "above-the-fold copy present (%d chars before the fold)"
                   % len(fold))


def rule_description_length(ctx):
    desc = ctx["snippet"].get("description", "")
    if len(desc) > C.DESCRIPTION_MAX:
        return Finding("description.length", FAIL,
                       "description is %d chars, over the %d limit"
                       % (len(desc), C.DESCRIPTION_MAX),
                       "trim", weight=3)
    return Finding("description.length", PASS, "%d chars" % len(desc))


def rule_hashtags(ctx):
    desc = ctx["snippet"].get("description", "")
    tags = HASHTAG_RE.findall(desc)
    if len(tags) > C.HASHTAGS_MAX:
        return Finding("description.hashtags", FAIL,
                       "%d hashtags in the description; past %d YouTube ignores "
                       "ALL of them rather than the excess"
                       % (len(tags), C.HASHTAGS_MAX),
                       "cut to 3-5", weight=2)
    if not tags:
        return Finding("description.hashtags", WARN,
                       "no hashtags; the first %d render above the title and "
                       "are a cheap topical signal" % C.HASHTAGS_SHOWN_ABOVE_TITLE,
                       "add 3 tightly-scoped hashtags")
    return Finding("description.hashtags", PASS,
                   "%d hashtags, first %d shown above title: %s"
                   % (len(tags), C.HASHTAGS_SHOWN_ABOVE_TITLE,
                      tags[:C.HASHTAGS_SHOWN_ABOVE_TITLE]))


def rule_tags(ctx):
    tags = ctx["snippet"].get("tags") or []
    total = sum(len(t) for t in tags)
    if not tags:
        return Finding("tags.present", WARN,
                       "no tags set. Tags are a weak ranking signal now, but "
                       "they still disambiguate spelling and named entities",
                       "add 5-12 tags")
    if total > C.TAGS_TOTAL_CHARS_MAX:
        return Finding("tags.present", FAIL,
                       "tags total %d chars, over the %d budget; the API will "
                       "reject the write" % (total, C.TAGS_TOTAL_CHARS_MAX),
                       "drop the longest tags", weight=2)
    return Finding("tags.present", PASS,
                   "%d tags, %d/%d chars" % (len(tags), total,
                                             C.TAGS_TOTAL_CHARS_MAX))


def rule_chapters(ctx):
    duration = ctx.get("duration_seconds")
    desc = ctx["snippet"].get("description", "")
    stamps = parse_timestamps(desc)
    # Chapters are pointless on a Short and YouTube will not render them.
    if duration is not None and duration < 120:
        return Finding("description.chapters", PASS,
                       "video is %ss; chapters do not apply" % duration)
    if not stamps:
        return Finding("description.chapters", FAIL,
                       "no chapters. Chapters raise the odds of a re-watch of "
                       "the one segment a viewer wants and give the video "
                       "extra surface in search",
                       "add >=%d markers starting at 0:00" % C.CHAPTER_MIN_COUNT,
                       weight=2)
    problems = []
    if C.CHAPTER_FIRST_MUST_BE_ZERO and stamps[0][0] != 0:
        problems.append("first marker is at %ds, must be 0:00" % stamps[0][0])
    if len(stamps) < C.CHAPTER_MIN_COUNT:
        problems.append("only %d markers, need %d"
                        % (len(stamps), C.CHAPTER_MIN_COUNT))
    for (a, _), (b, lab) in zip(stamps, stamps[1:]):
        if b - a < C.CHAPTER_MIN_LENGTH_SECONDS:
            problems.append("'%s' is %ds long, under the %ds minimum"
                            % (lab, b - a, C.CHAPTER_MIN_LENGTH_SECONDS))
    if problems:
        return Finding("description.chapters", FAIL,
                       "chapters present but will not render: " + "; ".join(problems),
                       "fix the marker list", weight=2)
    return Finding("description.chapters", PASS, "%d valid chapters" % len(stamps))


def rule_captions(ctx):
    caps = ctx.get("captions")
    if caps is None:
        return Finding("captions", WARN, "could not read caption list")
    if not caps:
        return Finding("captions", FAIL,
                       "no caption track. Uploaded captions beat ASR on proper "
                       "nouns, and they are what translation and search index",
                       "upload an SRT", weight=2)
    langs = [c.get("snippet", {}).get("language") for c in caps]
    return Finding("captions", PASS, "caption tracks: %s" % langs)


def rule_thumbnail(ctx):
    thumbs = ctx["snippet"].get("thumbnails", {})
    if "maxres" in thumbs:
        return Finding("thumbnail.custom", PASS, "maxres thumbnail present")
    return Finding("thumbnail.custom", WARN,
                   "no maxres thumbnail. That usually means no custom "
                   "thumbnail was uploaded (auto-generated stills stop at "
                   "'high'), though it can also lag on a fresh upload",
                   "upload a 1280x720 custom thumbnail")


def rule_channel_comment(ctx):
    """Detect whether the uploader has posted their own top-level comment.

    The API does not expose whether a comment is pinned, so this can only
    prove the comment exists, not that it sits at the top. The pin itself
    is reported separately as MANUAL.
    """
    threads = ctx.get("comment_threads")
    if threads is None:
        return Finding("comment.authored", WARN,
                       "comments unreadable (disabled, or not yet indexed)")
    owner = ctx["snippet"].get("channelId")
    for t in threads:
        top = t.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
        author = (top.get("authorChannelId") or {}).get("value")
        if author and author == owner:
            return Finding("comment.authored", PASS,
                           "uploader has a top-level comment on the video")
    return Finding("comment.authored", FAIL,
                   "uploader has not commented. The pinned comment is the "
                   "highest-leverage free real estate on the watch page and "
                   "the standard place to seed the discussion prompt",
                   "post and pin the comment", weight=2)


def rule_playlist(ctx):
    member_of = ctx.get("playlist_membership")
    if member_of is None:
        return Finding("playlist.membership", WARN,
                       "playlist membership not checked")
    if not member_of:
        return Finding("playlist.membership", FAIL,
                       "not in any playlist. Playlists are the main mechanism "
                       "for turning one view into a session, and session "
                       "length is what the system actually optimises",
                       "add to a topical playlist", weight=2)
    return Finding("playlist.membership", PASS,
                   "in playlists: %s" % member_of)


def rule_category(ctx):
    cat = ctx["snippet"].get("categoryId")
    if not cat:
        return Finding("category", WARN, "no categoryId reported")
    return Finding("category", PASS, "categoryId=%s" % cat)


# --- things the API cannot see or do ---------------------------------------

MANUAL_STEPS = [
    ("comment.pinned",
     "Pin the uploader comment. commentThreads.insert can post it; nothing in "
     "the Data API can pin it. Do it in Studio or the app right after posting."),
    ("comment.hearted",
     "Heart 3-5 early real comments. Hearting sends a notification back to the "
     "commenter, which is the cheapest way to pull a second session."),
    ("endscreen",
     "Set the end screen: one 'best for viewer' slot plus one explicit next "
     "video. Not exposed by the Data API at all -- Studio only."),
    ("cards",
     "Add an info card at the point the video references another video. Also "
     "Studio only."),
    ("ab_test",
     "Start a Test & Compare title/thumbnail test if the channel is in YPP. "
     "Not in the API. Note: unavailable for Shorts, Premieres and scheduled "
     "live."),
    ("community_post",
     "Post to the Community tab within the first hour. No public API."),
    ("shorts_derivative",
     "Cut a 20-40s vertical derivative from the strongest segment and publish "
     "it as a Short pointing at the long-form."),
    ("cross_platform",
     "Syndicate the derivative off-platform. Early external traffic is "
     "uncorrelated with the browse signal, so it adds rather than dilutes."),
    ("first_hour_replies",
     "Reply to every comment in the first hour, then every comment for 48h."),
]


ALL_RULES = [
    rule_title_length,
    rule_title_chars,
    rule_description_fold,
    rule_description_length,
    rule_hashtags,
    rule_tags,
    rule_chapters,
    rule_captions,
    rule_thumbnail,
    rule_channel_comment,
    rule_playlist,
    rule_category,
]
