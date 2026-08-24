#!/usr/bin/env python3
"""Join the parts of a split batch into one batch file.

A batch too large for the generator's policy check as a whole can be recorded in
parts and rejoined here. The seam sits at a paragraph boundary, so it is padded
to the natural paragraph pause measured across the other batches (1.00s median),
not the 350ms used between batches -- a 350ms gap mid-batch reads as a clipped
edit.
"""
import argparse, glob, json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from transcribe import run

FF, MARGIN = "ffmpeg", 0.08

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("batch", type=int)
    ap.add_argument("--gap", type=float, default=1.00, help="seam gap, seconds")
    ap.add_argument("--parts", default="clarity/vo/parts")
    a = ap.parse_args()

    files = sorted(glob.glob(f"{a.parts}/batch-{a.batch:02d}-p*.mp3"),
                   key=lambda f: int(re.search(r"-p(\d+)", f).group(1)))
    if not files: raise SystemExit(f"no parts found in {a.parts}")

    cut = []
    for f in files:
        r = run(f, outdir=f"{a.parts}/transcripts")
        tr = json.load(open(f"{a.parts}/transcripts/{r['name']}.json"))
        ws = [w for s in tr["segs"] for w in s["w"]]
        st, en = max(0.0, ws[0][0] - MARGIN), min(tr["dur"], ws[-1][1] + MARGIN)
        cut.append(dict(f=f, st=st, en=en, lead=ws[0][0] - st, trail=en - ws[-1][1]))
        print(f"  {os.path.basename(f)}  {tr['dur']:.2f}s  speech {ws[0][0]:.2f}-{ws[-1][1]:.2f}")

    for i, c in enumerate(cut):
        c["pad"] = 0.0 if i == len(cut) - 1 else \
            max(0.0, a.gap - c["trail"] - cut[i + 1]["lead"])

    cmd = [FF, "-y", "-hide_banner", "-loglevel", "error"]
    for c in cut: cmd += ["-i", c["f"]]
    fl, labels = [], []
    for i, c in enumerate(cut):
        fl.append(f"[{i}:a]atrim=start={c['st']:.3f}:end={c['en']:.3f},asetpts=PTS-STARTPTS,"
                  f"aformat=sample_rates=44100:channel_layouts=mono[a{i}]")
        labels.append(f"[a{i}]")
        if c["pad"] > 0:
            fl.append(f"aevalsrc=0:d={c['pad']:.3f}:s=44100:c=mono[s{i}]")
            labels.append(f"[s{i}]")
    fl.append("".join(labels) + f"concat=n={len(labels)}:v=0:a=1[out]")
    out = f"clarity/vo/batch-{a.batch:02d}.mp3"
    cmd += ["-filter_complex", ";".join(fl), "-map", "[out]",
            "-c:a", "libmp3lame", "-b:a", "128k", "-ar", "44100", "-ac", "1", out]
    subprocess.run(cmd, check=True)
    seams = [round(c["trail"] + c["pad"] + cut[i + 1]["lead"], 3)
             for i, c in enumerate(cut[:-1])]
    print(f"wrote {out} from {len(files)} parts; seams: "
          + ", ".join(f"{s:.3f}s" for s in seams))
    print("now: transcribe.py, audit.py, ledger.py, assemble.py, cuesheet.py")

main()
