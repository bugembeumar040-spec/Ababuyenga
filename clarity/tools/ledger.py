#!/usr/bin/env python3
"""Rebuild the alignment ledger from whatever batches are transcribed so far."""
import json, re, glob, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from audit import batch_text, norm
import difflib

SCRIPT = "clarity/script/clarity-voiceover-script-v3-tagged.txt"

def targets():
    """Batch header timings from the script pack: {n: (in_s, out_s, chars)}."""
    t = {}
    for m in re.finditer(r"\[ BATCH (\d+) · (\d+):(\d+)–(\d+):(\d+) · (\d+) chars \]", open(SCRIPT).read()):
        n, i_m, i_s, o_m, o_s, ch = (int(x) for x in m.groups())
        t[n] = (i_m * 60 + i_s, o_m * 60 + o_s, ch)
    return t

def mmss(x):
    return f"{int(x//60)}:{x%60:05.2f}"

def build():
    T = targets()
    rows, cursor = [], 0.0
    for f in sorted(glob.glob("clarity/transcripts/batch-[0-9][0-9].json")):
        n = int(re.search(r"batch-(\d+)", f).group(1))
        tr = json.load(open(f))
        ws = [w for s in tr["segs"] for w in s["w"]]
        speak = sum(w[1] - w[0] for w in ws)
        heard = " ".join(s["t"] for s in tr["segs"])
        bt = batch_text(n)
        ratio = difflib.SequenceMatcher(None, norm(bt), heard and norm(heard)).ratio() if bt else 0
        tin, tout, ch = T.get(n, (0, 0, 0))
        rows.append(dict(n=n, dur=tr["dur"], cin=cursor, cout=cursor + tr["dur"],
                         tin=tin, tout=tout, tlen=tout - tin, drift=(cursor + tr["dur"]) - tout,
                         artic=len(ws) / speak if speak else 0, words=len(ws),
                         match=ratio, tail=round(tr["dur"] - ws[-1][1], 2) if ws else 0,
                         head=round(ws[0][0], 2) if ws else 0))
        cursor += tr["dur"]
    return rows, cursor

def report(rows, total):
    L = []
    L.append("# CLARITY IN THE QURAN — VO ALIGNMENT LEDGER\n")
    L.append(f"Batches delivered: **{len(rows)} / 28**  ·  runtime so far: **{mmss(total)}**  "
             f"·  script total target: **43:18**\n")
    L.append("| # | dur | actual IN–OUT | script IN–OUT | drift | artic w/s | script match |")
    L.append("|---|-----|---------------|---------------|-------|-----------|--------------|")
    for r in rows:
        d = f"{r['drift']:+.2f}s"
        L.append(f"| {r['n']:02d} | {r['dur']:.2f}s | {mmss(r['cin'])}–{mmss(r['cout'])} | "
                 f"{mmss(r['tin'])}–{mmss(r['tout'])} | {d} | {r['artic']:.2f} | {r['match']*100:.0f}% |")
    L.append("")
    if rows:
        a = [r["artic"] for r in rows]
        L.append(f"Articulation rate spread: {min(a):.2f}–{max(a):.2f} w/s "
                 f"(tight spread = one consistent reading; >0.20 drift is audible).\n")
        L.append("Head/tail silence per file (join spacing target ~350ms):\n")
        for r in rows:
            L.append(f"- batch {r['n']:02d}: head {r['head']:.2f}s · tail {r['tail']:.2f}s")
    return "\n".join(L) + "\n"

if __name__ == "__main__":
    rows, total = build()
    out = report(rows, total)
    open("clarity/ALIGNMENT.md", "w").write(out)
    print(out)
