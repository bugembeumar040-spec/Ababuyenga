#!/usr/bin/env python3
"""Audit a transcribed VO batch against its batch text in the script pack."""
import json, re, sys, difflib

SCRIPT = "clarity/script/clarity-voiceover-script-v3-tagged.txt"
TAGS = ["quietly","curious","warmly","thoughtful","serious","solemn","emphatic","calm","excited","sad"]

UNITS = {w:i for i,w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen "
    "sixteen seventeen eighteen nineteen".split())}
TENS = {w:(i+2)*10 for i,w in enumerate("twenty thirty forty fifty sixty seventy eighty ninety".split())}

def _groups(toks):
    """Split a hundred/thousand-free run into its 0-99 groups."""
    g, cur, prev = [], 0, None
    for t in toks:
        if t == "and": continue
        if t in TENS:
            if prev is not None: g.append(cur); cur = 0
            cur, prev = TENS[t], "t"
        elif t in UNITS:
            if prev == "u" or (prev == "t" and UNITS[t] >= 10):
                g.append(cur); cur = 0
            cur, prev = cur + UNITS[t], "u"
    if prev is not None: g.append(cur)
    return g


def words2num(toks):
    """Fold a run of number-words into an integer.

    Year forms are read as spoken: "nineteen twenty-four" is 1924, not 43.
    Only applies when the run carries no hundred/thousand scale word.
    """
    if not any(t in ("hundred", "thousand") for t in toks):
        g = _groups(toks)
        if len(g) == 2 and 10 <= g[0] <= 99 and 0 <= g[1] <= 99:
            return g[0] * 100 + g[1]

    total = cur = 0
    for t in toks:
        if t in UNITS: cur += UNITS[t]
        elif t in TENS: cur += TENS[t]
        elif t == "hundred": cur = (cur or 1) * 100
        elif t == "thousand": total += (cur or 1) * 1000; cur = 0
        elif t == "and": continue
    return total + cur

NUMWORD = set(UNITS) | set(TENS) | {"hundred","thousand"}

def norm(text):
    """Lowercase, strip tags/punct, fold number-words into digits.

    Number runs absorb a joining 'and' ("six hundred and nineteen" -> 619) but
    are broken by punctuation, so "six hundred and nineteen, two things" folds
    to 619 2 rather than 621.
    """
    text = re.sub(r"\[[^\]]*\]", " ", text)
    text = text.replace("-", " ").replace("\u2019", "'").replace("\u2014", " ")
    text = re.sub(r"[,.;:!?]", " | ", text)
    toks = re.findall(r"[a-z0-9']+|\|", text.lower())

    out, run, i = [], [], 0
    def flush():
        if run: out.append(str(words2num(run))); run.clear()
    while i < len(toks):
        t = toks[i]
        if t == "|":
            flush()
        elif t in NUMWORD:
            run.append(t)
        elif t == "and" and run and i + 1 < len(toks) and toks[i + 1] in NUMWORD:
            run.append(t)                     # joining 'and' inside a number
        else:
            flush(); out.append(t)
        i += 1
    flush()
    return out


def batch_text(n):
    src = open(SCRIPT).read()
    m = re.search(rf"\[ BATCH {n:02d} ·.*?\]\n(.*?)(?=\n\[ BATCH |\n-{{20,}}|\Z)", src, re.S)
    return m.group(1).strip() if m else None

def audit(n):
    raw = batch_text(n)
    if raw is None: return f"batch {n:02d}: NOT FOUND in script"
    tr = json.load(open(f"clarity/transcripts/batch-{n:02d}.json"))
    heard = " ".join(s["t"] for s in tr["segs"])
    a, b = norm(raw), norm(heard)
    sm = difflib.SequenceMatcher(None, a, b)
    ratio = sm.ratio()
    # tag leakage: a tag word spoken where the script has it bracketed
    bracketed = set(re.findall(r"\[([a-z]+)\]", raw))
    # A tag word can also occur as ordinary prose ("instead of quietly deleting
    # it"), so a leak is an EXTRA occurrence beyond what the script text has.
    prose = re.sub(r"\[[^\]]*\]", " ", raw)
    leaked = [t for t in bracketed
              if len(re.findall(rf"\b{t}\b", heard, re.I))
               > len(re.findall(rf"\b{t}\b", prose, re.I))]
    diffs = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal": continue
        diffs.append((op, " ".join(a[i1:i2])[:70], " ".join(b[j1:j2])[:70]))
    return {"n": n, "ratio": ratio, "script_words": len(a), "heard_words": len(b),
            "dur": tr["dur"], "tags": sorted(bracketed), "leaked": leaked, "diffs": diffs}

if __name__ == "__main__":
    for n in [int(x) for x in sys.argv[1:]]:
        r = audit(n)
        if isinstance(r, str): print(r); continue
        flag = "OK " if r["ratio"] > 0.90 and not r["leaked"] else "!! "
        print(f'{flag}batch {r["n"]:02d}  match {r["ratio"]*100:5.1f}%  '
              f'script {r["script_words"]}w / heard {r["heard_words"]}w  {r["dur"]:.2f}s  '
              f'tags {r["tags"] or "-"}  leaked {r["leaked"] or "none"}')
        for op, x, y in r["diffs"][:12]:
            print(f'     {op:9s} script[{x}] -> heard[{y}]')
