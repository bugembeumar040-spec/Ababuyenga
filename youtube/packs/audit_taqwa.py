#!/usr/bin/env python3
"""Ten alignment passes over taqwa-prompt-pack.txt.

The pack carries three tracks keyed to one beat map. They drift the moment
one of them is edited alone, so every pass here is mechanical and re-runnable:

    python3 youtube/packs/audit_taqwa.py [--append]

--append writes the result block back into the pack under AUDIT LOG.
Exit status is non-zero if any pass fails.
"""
import re
import sys
import pathlib
import datetime

PACK = pathlib.Path(__file__).with_name("taqwa-prompt-pack.txt")
WPM = 145
BEATS = 14
TEXT = PACK.read_text()

fails, notes = [], []


def check(pass_no, name, ok, detail):
    (notes if ok else fails).append((pass_no, name, ok, detail))


def secs(t):
    m, s = t.split(":")
    return int(m) * 60 + float(s)


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


# ---------------------------------------------------------------- parsing
rows = re.findall(
    r"^ (\d\d) \| (\d:\d\d\.\d) \| (\d:\d\d\.\d) \| ([\d.]+)s \| ([\d.]+)s \|",
    TEXT, re.M)
MAP = {r[0]: dict(inp=secs(r[1]), out=secs(r[2]), ln=float(r[3]), hold=float(r[4]))
       for r in rows}

vo_blocks = re.findall(
    r"^--- (\d\d) · ([A-Z' ]+?) · budget (\d+) · actual (\d+) -+\n(.*?)(?=\n--- \d\d ·|\nTAG PALETTE)",
    TEXT, re.M | re.S)
VO = {b[0]: dict(name=b[1].strip(), budget=int(b[2]), actual=int(b[3]), body=b[4])
      for b in vo_blocks}

stills = re.findall(
    r"^F(\d\d) · (\d:\d\d\.\d)–(\d:\d\d\.\d) · ([^\n]*)\nMOVE: ([^\n]*)\n-+\n(.*?)(?=\n---------|\n=======)",
    TEXT, re.M | re.S)
ART = {a[0]: dict(inp=secs(a[1]), out=secs(a[2]), title=a[3], move=a[4], body=a[5])
       for a in stills}

_plate_table = TEXT.split("| CLAUSE (transliteration)")[1].split("PLATE SPEC.")[0]
plate_rows = re.findall(r"^ (\d\d) \| ([^|]+)\|", _plate_table, re.M)
PLATES, SUBS = [], set()
for b, raw in plate_rows:
    name = raw.strip()
    if name == "(none)":
        continue
    sub = name.startswith("\u21b3")
    name = name.lstrip("\u21b3").strip()
    PLATES.append((b, name))
    if sub:
        SUBS.add((b, name))

HOUSE = ("Pen-and-ink line drawing with muted watercolour wash on cream cold-press "
         "paper, visible paper tooth, a few soft bleed edges and one or two ink "
         "spatters; palette limited to sepia, warm ochre, dust brown and slate grey "
         "on cream; no lettering of any kind; 16:9.")


def vo_words(body):
    out = []
    for line in body.splitlines():
        line = line.strip()
        if not line or line.startswith(">>"):
            continue
        line = re.sub(r"\[[a-z]+\]", " ", line)
        line = re.sub(r"[—:>|]", " ", line)
        out += [w for w in re.findall(r"[A-Za-z'\-]+", line)]
    return out


# ------------------------------------------------------- 01 timing
prev, bad = 0.0, []
for i in range(1, BEATS + 1):
    k = f"{i:02d}"
    b = MAP.get(k)
    if not b:
        bad.append(f"{k} missing from beat map")
        continue
    if abs(b["inp"] - prev) > 1e-6:
        bad.append(f"{k} starts {b['inp']}, previous ends {prev}")
    if abs((b["out"] - b["inp"]) - b["ln"]) > 1e-6:
        bad.append(f"{k} LEN {b['ln']} != OUT-IN {b['out'] - b['inp']}")
    prev = b["out"]
total = prev
stated = 488.0 if "stated 488.0s" in TEXT else None
if stated and abs(total - stated) > 1e-6:
    bad.append(f"map total {total} != stated {stated}")
check(1, "TIMING", not bad, bad or f"14 beats contiguous, total {total}s = 8:08.0")

# ------------------------------------------------------- 02 parity
bad = []
for label, d in (("beat map", MAP), ("voiceover", VO), ("stills", ART)):
    missing = [f"{i:02d}" for i in range(1, BEATS + 1) if f"{i:02d}" not in d]
    if missing:
        bad.append(f"{label} missing {missing}")
rhyme = TEXT.split("RHYME MAP")[1].split("TRACK 3")[0]
missing = [f"F{i:02d}" for i in range(1, BEATS + 1) if f"F{i:02d}" not in rhyme]
if missing:
    bad.append(f"rhyme map missing {missing}")
for k, a in ART.items():
    if MAP[k]["inp"] != a["inp"] or MAP[k]["out"] != a["out"]:
        bad.append(f"F{k} timecode {a['inp']}-{a['out']} != map {MAP[k]['inp']}-{MAP[k]['out']}")
check(2, "PARITY", not bad, bad or "14 beats present and time-aligned in all four tracks")

# ------------------------------------------------------- 03 word budget
bad, spoken = [], 0
for k, v in sorted(VO.items()):
    words = len(vo_words(v["body"]))
    spoken += words
    budget = int((MAP[k]["ln"] - MAP[k]["hold"]) * WPM / 60)
    if v["budget"] != budget:
        bad.append(f"{k} printed budget {v['budget']} != computed {budget}")
    if v["actual"] != words:
        bad.append(f"{k} printed actual {v['actual']} != counted {words}")
    if words > budget:
        bad.append(f"{k} over budget: {words} > {budget}")
air = (total - sum(m["hold"] for m in MAP.values())) - spoken * 60 / WPM
check(3, "WORD BUDGET", not bad,
      bad or f"{spoken} words, every beat within budget, {air:.0f}s distributed pause")

# ------------------------------------------------------- 04 citations
NAMES = {"At-Tahrim": "Tahrim", "Al-Baqarah": "Baqarah", "Al-A'raf": "A'raf",
         "Al-Hujurat": "Hujurat", "At-Talaq": "Talaq", "Ali Imran": "Ali Imran",
         "Fatir": "Fatir", "At-Taghabun": "Taghabun"}
bad = []
for beat, cit in PLATES:
    surah = next((n for n in NAMES if cit.startswith(n)), None)
    if surah is None:
        bad.append(f"plate {beat} '{cit}' is not a known surah")
        continue
    if NAMES[surah] not in VO[beat]["body"]:
        bad.append(f"{surah} plated at beat {beat} but not spoken there")
plated = {(b, NAMES[n]) for b, c in PLATES for n in NAMES if c.startswith(n)}
for k, v in VO.items():
    for full, short in NAMES.items():
        if re.search(rf"\b{re.escape(short)}\b", v["body"]) and (k, short) not in plated:
            bad.append(f"beat {k} speaks {short} with no plate")
check(4, "CITATIONS", not bad, bad or f"{len(PLATES)} plates, spoken and plated agree both ways")

# ------------------------------------------------------- 05 holds
bad = []
for k, v in sorted(VO.items()):
    marks = [float(x) for x in re.findall(r">> ARABIC PLATE — ([\d.]+)s hold", v["body"])]
    plates_here = [p for p in PLATES if p[0] == k and p not in SUBS]
    if len(marks) != len(plates_here):
        bad.append(f"beat {k}: {len(marks)} hold markers for {len(plates_here)} plates")
    if abs(sum(marks) - MAP[k]["hold"]) > 1e-6:
        bad.append(f"beat {k}: markers sum {sum(marks)} != map HOLD {MAP[k]['hold']}")
check(5, "HOLDS", not bad, bad or "every plate has a silence marker summing to the map HOLD")

# ------------------------------------------------------- 06 art hygiene
BANNED = ["text", "lettering", "script", "calligraphy", "word", "inscription",
          "person", "figure", "face", "hand"]
bad = []
for k, a in sorted(ART.items()):
    body = norm(a["body"])
    if HOUSE not in body:
        bad.append(f"F{k} missing the house-style sentence verbatim")
    if not re.search(r"two-thirds|two-fifths|three-fifths|upper-centre|low-left", body):
        bad.append(f"F{k} has no composition rule")
    for w in BANNED:
        for m in re.finditer(rf"\b{w}s?\b(?!-)", body, re.I):
            ctx = body[max(0, m.start() - 14):m.start()].lower()
            if re.search(r"\b(no|without|nothing)\s*$", ctx):
                continue
            bad.append(f"F{k} requests '{w}' — {body[max(0,m.start()-40):m.start()+20]!r}")
neg = TEXT.split("NEGATIVE PROMPT — paste once, applies to all 14 stills:")[1][:600]
for req in ["Arabic script", "calligraphy", "lettering", "human figure", "face", "animals"]:
    if req not in neg:
        bad.append(f"negative prompt missing '{req}'")
check(6, "ART HYGIENE", not bad,
      bad or "14 prompts carry the house sentence, a composition rule, no text or figures")

# ------------------------------------------------------- 07 continuity
BURNED = ["sabr", "huzn", "ajal", "waqt", "ghayz", "ghadab", "kazm", "tumaninah",
          "jinn", "shaytan"]
vo_all = " ".join(VO[k]["body"] for k in sorted(VO))
bad = [w for w in BURNED if re.search(rf"\b{w}\b", vo_all, re.I)]
rizq = len(re.findall(r"\brizq\b", vo_all, re.I))
if rizq > 1:
    bad.append(f"rizq appears {rizq} times, budget is 1")
check(7, "CONTINUITY", not bad,
      bad or f"no burned topic in the VO; rizq referenced {rizq} times (<=1)")

# ------------------------------------------------------- 08 moves
bad = []
for k, a in sorted(ART.items()):
    mv = a["move"]
    pct = [int(x) for x in re.findall(r"(\d+)%", mv)]
    if k == "08":
        if not mv.lower().startswith("none"):
            bad.append("F08 must be the locked frame")
        continue
    if not pct and "drift" not in mv:
        bad.append(f"F{k} has no move")
    for p in pct:
        if not 3 <= p <= 9:
            bad.append(f"F{k} move {p}% outside 3-9%")
    if "bottom" in a["body"].lower() and "28%" not in TEXT:
        bad.append(f"F{k} band rule missing")
if "bottom 28% of frame" not in TEXT:
    bad.append("Arabic band zone not specified")
check(8, "MOVES", not bad, bad or "13 moves within 3-9%, F08 locked, band zone specified")

# ------------------------------------------------------- 09 posture
RULING = [r"\bharam\b", r"\bhalal\b", r"\bobligatory\b", r"\byou must\b",
          r"\bforbidden\b", r"\bsinful\b", r"\bmust not\b"]
bad = [r for r in RULING if re.search(r, vo_all, re.I)]
claims = re.findall(r"^\s*(\d)\. [\"A-Z]", TEXT.split("ACCURACY")[1], re.M)
if len(claims) < 7:
    bad.append(f"only {len(claims)} numbered accuracy entries")
check(9, "POSTURE", not bad,
      bad or f"no ruling language in the VO; {len(claims)} accuracy entries")

# ------------------------------------------------------- 10 packaging
bad = []
title = re.search(r"^TITLE     (.+)$", TEXT, re.M).group(1).strip()
if len(title) > 100:
    bad.append(f"title {len(title)} chars > 100")
desc = TEXT.split("DESCRIPTION  (600+ chars — the house template, filled)")[1].split("TAGS")[0].strip()
if len(desc) < 600:
    bad.append(f"description {len(desc)} chars < 600")
tags_block = TEXT.split("silently above it)")[1].split("METADATA")[0]
tags = [t.strip() for t in norm(tags_block).split(",") if t.strip()]
tag_chars = len(", ".join(tags))
if tag_chars >= 500:
    bad.append(f"tags {tag_chars} chars >= 500")
if f"{len(tags)} tags, {tag_chars} characters" not in TEXT:
    bad.append(f"printed tag count/chars wrong: actual {len(tags)} tags, {tag_chars} chars")
thumb = re.search(r'thumbnailText:  "([^"]+)"', TEXT).group(1)
if len(thumb.split(" / ")) != 3:
    bad.append(f"thumbnailText {thumb!r} is not three ' / ' lines")
check(10, "PACKAGING", not bad,
      bad or f"title {len(title)}c, description {len(desc)}c, {len(tags)} tags {tag_chars}c, thumb 3 lines")

# ---------------------------------------------------------------- report
out = [f"RUN {datetime.date.today().isoformat()} — 10 passes over "
       f"{PACK.name}", ""]
for no, name, ok, detail in sorted(notes + fails):
    if ok:
        out.append(f"  {no:02d} {name:<12} PASS  {detail}")
    else:
        for d in (detail if isinstance(detail, list) else [detail]):
            out.append(f"  {no:02d} {name:<12} FAIL  {d}")
out.append("")
out.append(f"  {'ALL TEN PASSES CLEAN' if not fails else str(len(fails)) + ' PASS(ES) FAILING'}")
report = "\n".join(out)
print(report)

if "--append" in sys.argv and not fails:
    body = TEXT.split("RESULTS ARE APPENDED BY THE SCRIPT")[0]
    tail = ("RESULTS ARE APPENDED BY THE SCRIPT, not by hand. If the block below is missing,\n"
            "the audit has not been run against the current version of this file.\n\n"
            + report + "\n")
    PACK.write_text(body + tail)
    print("\n[appended to pack]")

sys.exit(1 if fails else 0)
