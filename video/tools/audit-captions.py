#!/usr/bin/env python3
"""
Check that no caption puts words on screen the narrator does not say.

The VO was read from a script that differs from the shot pack in wording as
well as in structure — "a lifeless man" not "a dead man", "a fallen king" not
"a corpse", "your future" not "your marriage", "owned" not "heavier". A viewer
hearing one word while reading another on the same frame is the most damaging
thing this film can do to its own credibility, and nothing else in the pipeline
was looking for it.

Two kinds of divergence are allowed and listed as EXEMPT rather than failed:
verse wording shown alongside its citation while the narrator paraphrases it,
and Arabic transliteration of a verse the narrator delivers in English.

Usage:  python3 tools/audit-captions.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Whisper's spelling of the proper nouns this script leans on.
ALIAS = {"jinn": "gin", "jin": "gin", "al-jinn": "gin", "majnoon": "magnun",
         "janeen": "janine", "rahaqa": "rahaka", "shayateen": "shaitin"}

# Quoted verse wording carried with its citation while the VO paraphrases.
EXEMPT = {
    "S09": "Arabic of Al-Kahf 18:50; the VO delivers it in English",
    "S17b": "verse wording of An-Naml 27:39; the VO paraphrases it",
}

STOP = set("the a an and or of to in it is was that this you your they them he "
           "she we us i for on at as but so no not with from by be been are what "
           "who how its their our".split())


def tokens(s: str) -> set[str]:
    return set(re.findall(r"[a-z']+", s.lower().replace("’", "'")))


def entries(src: str) -> dict[str, str]:
    """Split captions.ts into one blob per shot id.

    Deliberately not one regex per entry — an earlier version matched greedily
    into the following entry and reported six failures of which four were its
    own doing. Splitting on the key boundary cannot do that.
    """
    parts = re.split(r"\n  (S\d+[a-z]?): ", src)
    return {parts[i]: parts[i + 1] for i in range(1, len(parts) - 1, 2)}


def main() -> int:
    src = (ROOT / "src" / "jinn" / "beats.ts").read_text()
    body = src.split("export const SHOTS: Shot[] = ", 1)[1]
    shots = json.loads(body[: body.index("\n];") + 3].rstrip().rstrip(";"))
    caps = entries((ROOT / "src" / "jinn" / "captions.ts").read_text())
    words = json.loads((ROOT / "media" / "vo-words.json").read_text())

    failed, exempt = [], []
    for s in shots:
        blob = caps.get(s["id"], "")
        shown = " ".join(m.group(1) for m in
                         re.finditer(r'(?:text|sub|strike): "([^"]+)"', blob))
        if not shown.strip():
            continue
        heard = tokens(" ".join(w["w"] for w in words
                                if s["tIn"] <= w["s"] < s["tOut"]))
        want = {ALIAS.get(w, w) for w in tokens(shown) - STOP} - {""}
        absent = sorted(want - heard)
        if absent and len(absent) / len(want) > 0.5:
            (exempt if s["id"] in EXEMPT else failed).append(
                (s["id"], shown[:70], absent[:6]))

    for sid, shown, absent in exempt:
        print(f"EXEMPT  {sid}: {EXEMPT[sid]}")
    for sid, shown, absent in failed:
        print(f"FAIL    {sid}: {shown}\n          not spoken: {absent}")
    print()
    print(f"{len(failed)} caption(s) contradict the narration"
          f"{'' if failed else ' — clean'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
