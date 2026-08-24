#!/usr/bin/env python3
"""Transcribe staged files and identify which script batch each one is."""
import sys, os, json, glob, difflib
sys.path.insert(0, os.path.dirname(__file__))
from transcribe import run
from audit import batch_text, norm

CAND = range(1, 29)
def main():
    texts = {n: norm(batch_text(n)) for n in CAND if batch_text(n)}
    out = {}
    import os.path
    for p in sorted(glob.glob("clarity/stage/*.mp3")):
        nm = os.path.splitext(os.path.basename(p))[0]
        cache = f"clarity/stage/transcripts/{nm}.json"
        if os.path.exists(cache):
            d = json.load(open(cache))
            r = dict(name=nm, dur=d["dur"],
                     head=d["segs"][0]["w"][0][0] if d["segs"] else 0,
                     tail=round(d["dur"]-d["segs"][-1]["w"][-1][1], 2) if d["segs"] else 0,
                     text=" ".join(x["t"] for x in d["segs"]))
        else:
            r = run(p, outdir="clarity/stage/transcripts")
        h = norm(r["text"])
        scores = sorted(((difflib.SequenceMatcher(None, t, h).ratio(), n)
                         for n, t in texts.items()), reverse=True)
        best, second = scores[0], scores[1]
        out[r["name"]] = dict(dur=r["dur"], head=r["head"], tail=r["tail"],
                              best=best[1], score=round(best[0], 3),
                              runner=second[1], rscore=round(second[0], 3))
        print(f'{r["name"]:9s} {r["dur"]:7.2f}s -> b{best[1]:02d} {best[0]*100:5.1f}%   '
              f'(next b{second[1]:02d} {second[0]*100:.0f}%)', flush=True)
    json.dump(out, open("clarity/stage/idmap.json", "w"), indent=1)
main()
