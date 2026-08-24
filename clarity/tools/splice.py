#!/usr/bin/env python3
"""Replace the tail of a batch recording with a freshly recorded paragraph.

Used when a batch cannot be re-recorded whole -- the generator refuses it -- but
one paragraph inside it must be restored verbatim. Keeps the base audio up to a
cut point, then joins the replacement at a stated gap, measured end-of-speech to
start-of-speech so the seam matches the pause that was there before.
"""
import argparse, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sil import bounds as speech      # waveform, not ASR -- see sil.py

FF, MARGIN = "ffmpeg", 0.08

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, help="existing batch mp3")
    ap.add_argument("--cut", type=float, required=True,
                    help="keep base audio up to this second")
    ap.add_argument("--replacement", required=True, help="newly recorded mp3")
    ap.add_argument("--gap", type=float, default=0.28,
                    help="end-of-speech to start-of-speech gap; 0.28s is the median\n                         silence measured inside these batches")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    rin, rout, rdur = speech(a.replacement)
    rst, ren = max(0.0, rin - MARGIN), min(rdur, rout + MARGIN)
    lead = rin - rst

    # base is cut mid-file, so its own trailing silence past `cut` is discarded;
    # the whole gap has to be manufactured minus the replacement's own lead-in
    pad = max(0.0, a.gap - lead)

    fl = [f"[0:a]atrim=start=0:end={a.cut:.3f},asetpts=PTS-STARTPTS,"
          f"aformat=sample_rates=44100:channel_layouts=mono[a0]",
          f"[1:a]atrim=start={rst:.3f}:end={ren:.3f},asetpts=PTS-STARTPTS,"
          f"aformat=sample_rates=44100:channel_layouts=mono[a1]"]
    labels = "[a0]"
    if pad > 0:
        fl.append(f"aevalsrc=0:d={pad:.3f}:s=44100:c=mono[s]")
        labels += "[s]"
    labels += "[a1]"
    n = 3 if pad > 0 else 2
    fl.append(labels + f"concat=n={n}:v=0:a=1[out]")

    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error",
                    "-i", a.base, "-i", a.replacement,
                    "-filter_complex", ";".join(fl), "-map", "[out]",
                    "-c:a", "libmp3lame", "-b:a", "128k",
                    "-ar", "44100", "-ac", "1", a.out], check=True)

    total = a.cut + pad + (ren - rst)
    print(f"wrote {a.out}  {total:.2f}s")
    print(f"  base kept 0-{a.cut:.2f}s, replacement {rst:.2f}-{ren:.2f}s "
          f"({ren-rst:.2f}s), pad {pad:.3f}s")
    print(f"  seam gap = {pad + lead:.3f}s (target {a.gap:.2f}s)")

main()
