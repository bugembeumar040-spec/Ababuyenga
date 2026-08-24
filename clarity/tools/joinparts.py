#!/usr/bin/env python3
"""Join the parts of a split batch into one batch file.

A batch too large for the generator's policy check as a whole can be recorded in
parts and rejoined here. The seam sits at a paragraph boundary, so it is padded
to the paragraph-scale pause measured from the waveforms (0.43s median; the
overall median silence inside a batch is 0.28s). An earlier 1.00s figure here
was derived from whisper word gaps and was inflated by roughly 0.3s at each end
by its timestamp error.
"""
import argparse, glob, json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sil import bounds as speech      # waveform, not ASR -- see sil.py

FF, MARGIN = "ffmpeg", 0.08

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("batch", type=int)
    ap.add_argument("--gap", type=float, default=0.43,
                    help="seam gap; 0.43s is the median paragraph-scale silence "
                         "measured from the waveforms")
    ap.add_argument("--parts", default="clarity/vo/parts")
    a = ap.parse_args()

    files = sorted(glob.glob(f"{a.parts}/batch-{a.batch:02d}-p*.mp3"),
                   key=lambda f: int(re.search(r"-p(\d+)", f).group(1)))
    if not files: raise SystemExit(f"no parts found in {a.parts}")

    cut = []
    for f in files:
        sin, sout, dur = speech(f)
        st, en = max(0.0, sin - MARGIN), min(dur, sout + MARGIN)
        cut.append(dict(f=f, st=st, en=en, lead=sin - st, trail=en - sout))
        print(f"  {os.path.basename(f)}  {dur:.2f}s  speech {sin:.2f}-{sout:.2f}")

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
