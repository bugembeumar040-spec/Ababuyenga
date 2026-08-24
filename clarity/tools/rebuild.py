#!/usr/bin/env python3
"""Rebuild one batch from a mix of existing spans and newly recorded paragraphs.

Used when a batch cannot be re-recorded whole -- the generator refuses it -- but
individual paragraphs inside it can be. Each segment is either a span of the
original file or a replacement recording; the gap before each segment is stated
explicitly so the rebuilt batch keeps the pauses that were there.

Spec is JSON: [{"src": path, "start": s, "end": s, "gap": s}, ...]
"start"/"end" omitted on a replacement means trim to its own speech bounds.
"""
import argparse, json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sil import bounds

FF, MARGIN = "ffmpeg", 0.08

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    spec = json.load(open(a.spec))

    segs = []
    for s in spec:
        if "start" in s and "end" in s:
            st, en, lead, trail = s["start"], s["end"], 0.0, 0.0
        else:
            sin, sout, dur = bounds(s["src"])
            st, en = max(0.0, sin - MARGIN), min(dur, sout + MARGIN)
            lead, trail = sin - st, en - sout
        segs.append(dict(src=s["src"], st=st, en=en, lead=lead, trail=trail,
                         gap=s.get("gap", 0.0)))

    inputs, fl, labels = [], [], []
    for i, g in enumerate(segs):
        if g["gap"] > 0:
            pad = max(0.0, g["gap"] - g["lead"] - (segs[i-1]["trail"] if i else 0))
            if pad > 0:
                fl.append(f"aevalsrc=0:d={pad:.3f}:s=44100:c=mono[p{i}]")
                labels.append(f"[p{i}]")
            g["pad"] = pad
        inputs.append(g["src"])
        fl.append(f"[{i}:a]atrim=start={g['st']:.3f}:end={g['en']:.3f},asetpts=PTS-STARTPTS,"
                  f"aformat=sample_rates=44100:channel_layouts=mono[a{i}]")
        labels.append(f"[a{i}]")
    fl.append("".join(labels) + f"concat=n={len(labels)}:v=0:a=1[out]")

    cmd = [FF, "-y", "-hide_banner", "-loglevel", "error"]
    for p in inputs: cmd += ["-i", p]
    cmd += ["-filter_complex", ";".join(fl), "-map", "[out]",
            "-c:a", "libmp3lame", "-b:a", "128k", "-ar", "44100", "-ac", "1", a.out]
    subprocess.run(cmd, check=True)

    total = sum(g["en"] - g["st"] + g.get("pad", 0.0) for g in segs)
    print(f"wrote {a.out}  {total:.2f}s from {len(segs)} segments")
    t = 0.0
    for i, g in enumerate(segs):
        t += g.get("pad", 0.0)
        print(f"  [{i}] {os.path.basename(g['src']):24s} {g['st']:7.2f}-{g['en']:7.2f}"
              f"  -> {t:7.2f}s  gap before {g.get('pad', 0.0):.2f}s")
        t += g["en"] - g["st"]

main()
