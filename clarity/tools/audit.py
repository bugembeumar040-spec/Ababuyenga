#!/usr/bin/env python3
"""Audit a transcribed VO batch against its batch text in the script pack."""
import json, re, sys, difflib

SCRIPT = "clarity/script/clarity-voiceover-script-v3-tagged.txt"
TAGS = ["quietly","curious","warmly","thoughtful","serious","solemn","emphatic","calm","excited","sad"]

UNITS = {w:i for i,w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen "
    "sixteen seventeen eighteen nineteen".split())}
TENS = {w:(i+2)*10 for i,w in enumerate("twenty thirty forty fifty sixty seventy eighty ninety".split())}

def words2num(toks):
    """Fold a run of number-words into an integer."""
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
    """Lowercase, strip tags/punct, fold number-words into digits."""
    text = re.sub(r"\[[^\]]*\]", " ", text)
    text = text.replace("-", " ").replace("’", "'").replace("—", " ")
    toks = re.findall(r"[a-z0-9']+", text.lower())
    out, run = [], []
    for t in toks:
        if t in NUMWORD and not (t == "and" ):
            run.append(t)
            continue
        if run:
            # trailing 'and' belongs to the sentence, not the number
            out.append(str(words2num(run))); run = []
        out.append(t)
    if run: out.append(str(words2num(run)))
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
    leaked = [t for t in bracketed if re.search(rf"\b{t}\b", heard, re.I)]
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
