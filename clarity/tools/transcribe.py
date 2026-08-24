#!/usr/bin/env python3
"""Transcribe a VO batch mp3 -> word-timestamped JSON, and report head/tail silence."""
import sys, json, os
from faster_whisper import WhisperModel

MODEL = None
def model():
    global MODEL
    if MODEL is None:
        MODEL = WhisperModel("small.en", device="cpu", compute_type="int8")
    return MODEL

def run(path, outdir="clarity/transcripts"):
    segs, info = model().transcribe(path, word_timestamps=True, vad_filter=False)
    out = []
    for s in segs:
        out.append({"s": round(s.start, 2), "e": round(s.end, 2), "t": s.text.strip(),
                    "w": [[round(w.start, 2), round(w.end, 2), w.word] for w in s.words]})
    os.makedirs(outdir, exist_ok=True)
    name = os.path.splitext(os.path.basename(path))[0]
    json.dump({"file": os.path.basename(path), "dur": round(info.duration, 3), "segs": out},
              open(f"{outdir}/{name}.json", "w"), indent=0)
    head = out[0]["w"][0][0] if out and out[0]["w"] else 0.0
    tail = round(info.duration - out[-1]["w"][-1][1], 2) if out and out[-1]["w"] else 0.0
    return {"name": name, "dur": round(info.duration, 2), "head": round(head, 2),
            "tail": tail, "segs": len(out), "text": " ".join(s["t"] for s in out)}

if __name__ == "__main__":
    for p in sys.argv[1:]:
        r = run(p)
        print(f'{r["name"]}  dur {r["dur"]:6.2f}s  head-sil {r["head"]:.2f}s  tail-sil {r["tail"]:.2f}s  segs {r["segs"]}')
