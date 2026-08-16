#!/usr/bin/env python3
"""
Audit the YouTube packaging before it goes anywhere.

Packaging is the one artefact nobody proofreads against the video, and it is
the one a viewer measures the video against. Two failure modes matter:

  * a mechanical limit silently eats the field — YouTube rejects the whole tag
    field over 500 characters without saying so, and truncates titles on mobile
  * the copy promises something the film does not deliver, or a timestamp
    points at the wrong moment

The second is the one worth automating. Every timestamp in the description is
checked against the cut in beats.ts, and every quoted phrase is checked against
the actual voiceover transcript.

Usage:  python3 tools/audit-packaging.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT.parent / "packaging" / "jinn-youtube-packaging.md"
WORDS = ROOT / "media" / "vo-words.json"
BEATS = ROOT / "src" / "jinn" / "beats.ts"

TITLE_SOFT, TITLE_HARD = 60, 100   # mobile truncation, YouTube limit
TAGS_LIMIT = 500                   # hard: YouTube silently drops the field
HASHTAG_SHOWN, HASHTAG_LIMIT = 3, 15
DESC_MIN, HOOK_CHARS = 600, 150

results: list[tuple[bool, str, str]] = []
fail = lambda n, d: results.append((False, n, d))
ok = lambda n, d: results.append((True, n, d))


def block(doc: str, heading: str, nth: int = 0) -> str:
    """Nth fenced code block after a heading."""
    tail = doc.split(heading, 1)[1]
    return re.findall(r"```(?:\w+)?\n(.*?)```", tail, re.S)[nth]


# Whisper's spelling of the proper nouns this script leans on. Without these
# the claim check reports phrases as unspoken that the narrator says plainly —
# a checker that cries wolf gets ignored, which is worse than not having one.
ALIAS = {"jinn": "gin", "majnoon": "magnun", "janeen": "janine",
         "rahaqa": "rahaka", "shayateen": "shaitin"}


def norm(s: str) -> str:
    s = re.sub(r"[^a-z0-9 ]", " ", s.lower())
    s = " ".join(ALIAS.get(w, w) for w in s.split())
    return s


def main() -> int:
    doc = DOC.read_text()
    words = json.loads(WORDS.read_text())
    heard = norm(" ".join(w["w"] for w in words))
    src = BEATS.read_text()
    body = src.split("export const SHOTS: Shot[] = ", 1)[1]
    shots = json.loads(body[: body.index("\n];") + 3].rstrip().rstrip(";"))
    film_end = max(s["tOut"] for s in shots)

    # --- title -----------------------------------------------------------
    title = block(doc, "## TITLE").strip()
    n = len(title)
    (ok if n <= TITLE_SOFT else fail)(
        "TITLE LEN", f"{n} chars (mobile truncates ~{TITLE_SOFT}, hard {TITLE_HARD})")

    stated_n = re.search(r"\n(\d+) characters — survives", doc)
    (ok if stated_n and int(stated_n.group(1)) == n else fail)(
        "TITLE STATED",
        f"document says {stated_n.group(1) if stated_n else '?'}, actual {n}")

    # Any "at M:SS" in the prose must point at a real moment in the cut.
    refs = [r for r in re.findall(r"\bat (\d{1,2}):(\d\d)\b", doc)]
    off = [f"{m}:{s}" for m, s in refs if int(m) * 60 + int(s) > film_end]
    (ok if not off else fail)(
        "PROSE TIMES", f"{len(refs)} in-text time reference(s), all inside the film"
        if not off else f"past the end: {off}")

    alts = re.findall(r"^\| \d+ \| `([^`]+)` \| (\d+) \|", doc, re.M)
    bad = [(t, int(c)) for t, c in alts if len(t) != int(c)]
    (ok if not bad else fail)(
        "ALT COUNTS", "stated char counts correct"
        if not bad else f"wrong: {[(t, len(t), c) for t, c in bad]}")
    over = [t for t, _ in alts if len(t) > TITLE_HARD]
    (ok if not over else fail)("ALT LEN", f"all alternates under {TITLE_HARD}"
                              if not over else f"over limit: {over}")

    # --- description -----------------------------------------------------
    desc = block(doc, "## DESCRIPTION").strip()
    (ok if len(desc) >= DESC_MIN else fail)(
        "DESC LEN", f"{len(desc)} chars (house minimum {DESC_MIN})")

    stamps = re.findall(r"^(\d\d):(\d\d)\s{2}(.+)$", desc, re.M)
    late = [f"{m}:{s}" for m, s, _ in stamps if int(m) * 60 + int(s) > film_end]
    (ok if stamps and not late else fail)(
        "CHAPTERS", f"{len(stamps)} timestamps, all inside {film_end:.0f}s"
        if stamps and not late else f"past the end of the film: {late}")
    first = stamps[0][0] + ":" + stamps[0][1] if stamps else ""
    (ok if first == "00:00" else fail)(
        "CHAPTER 1", "starts at 00:00 as YouTube requires"
        if first == "00:00" else f"first chapter is {first}, must be 00:00")

    # Claims quoted as the video's own words must actually be in the VO.
    quoted = [
        "paid money to have a jinn removed",
        "phone number",
        "named a price",
        "fallen angel",
        "different paths",
        "standing up",
        "leaning on his staff",
        "a small creature of the earth",
        "fallen king",
        "seek refuge",
    ]
    absent = [q for q in quoted if norm(q) not in heard]
    (ok if not absent else fail)(
        "CLAIMS", f"all {len(quoted)} quoted phrases are spoken in the VO"
        if not absent else f"NOT in the voiceover: {absent}")

    # --- hashtags --------------------------------------------------------
    shown = block(doc, "## HASHTAGS", 0).strip().split()
    allt = block(doc, "## HASHTAGS", 1).split()
    (ok if len(shown) == HASHTAG_SHOWN else fail)(
        "HASHTAG TOP", f"{len(shown)} above-title tags (YouTube shows {HASHTAG_SHOWN})")
    (ok if len(allt) <= HASHTAG_LIMIT else fail)(
        "HASHTAG N", f"{len(allt)} total (YouTube ignores all past {HASHTAG_LIMIT})")

    # --- tags ------------------------------------------------------------
    tags = " ".join(block(doc, "## TAGS").split())
    stated = re.search(r"This set is (\d+)", doc)
    n = len(tags)
    (ok if n <= TAGS_LIMIT else fail)(
        "TAGS LEN", f"{n} chars (hard limit {TAGS_LIMIT}, field silently dropped over)")
    (ok if stated and int(stated.group(1)) == n else fail)(
        "TAGS STATED", f"document says {stated.group(1) if stated else '?'}, actual {n}")

    # --- thumbnail prompts ----------------------------------------------
    prompts = re.findall(r"```\nPROMPT\n(.*?)```", doc, re.S)
    (ok if len(prompts) == 3 else fail)("THUMBS", f"{len(prompts)} prompt(s) present")
    for i, p in enumerate(prompts, 1):
        low = p.lower()
        needs = {"faceless": "no faces" in low or "no faces anywhere" in low
                 or "no figures" in low,
                 "16:9": "16:9" in p,
                 "text-negative": "text, lettering" in low or "STYLE — as" in p,
                 "palette": "#e8dcc8" in low or "as Concept A" in p}
        miss = [k for k, v in needs.items() if not v]
        (ok if not miss else fail)(f"THUMB {i}", "house-style constraints present"
                                   if not miss else f"missing: {miss}")

    width = max(len(n) for _, n, _ in results)
    for good, name, detail in results:
        print(f"{'PASS' if good else 'FAIL'}  {name:<{width}}  {detail}")
    bad_names = [n for g, n, _ in results if not g]
    print()
    print("PACKAGING AUDIT PASSED" if not bad_names
          else f"PACKAGING AUDIT FAILED: {', '.join(bad_names)}")
    return 1 if bad_names else 0


if __name__ == "__main__":
    sys.exit(main())
