#!/usr/bin/env python3
"""Concatenate accepted VO batches into one master track with uniform joins.

Each batch is trimmed to its spoken content (keeping a small margin of room
tone either side so nothing is clipped), then a computed pad is inserted so
that EVERY join measures the same end-of-speech to start-of-speech gap --
default 350ms, per rule 3 of the script pack. Files whose own trailing silence
already exceeds the gap are trimmed back rather than left long, which is what
keeps the joins even.
"""
import argparse, json, os, subprocess, glob, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sil import bounds as pcm_bounds

FF = "ffmpeg"
MARGIN = 0.08          # room tone kept either side of speech, seconds

def bounds(name):
    """Speech bounds from the waveform, not from ASR.

    Whisper's word timestamps are unreliable at both ends: it ends final words
    up to 0.5s early and misses leading numerals entirely (batch 21 opens on
    "Six hundred and twenty-seven" at 0.04s; whisper reported the first word at
    1.00s). Trimming to those timestamps clipped real speech off 26 of 28
    batches.
    """
    return pcm_bounds(f"clarity/vo/{name}.mp3")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gap", type=float, default=0.35)
    ap.add_argument("--out", default="clarity/master/clarity-vo-master.mp3")
    ap.add_argument("--edl", default="clarity/master/edl.json")
    a = ap.parse_args()

    files = sorted(glob.glob("clarity/vo/batch-[0-9][0-9].mp3"))
    if not files: raise SystemExit("no batches in clarity/vo/")
    os.makedirs(os.path.dirname(a.out), exist_ok=True)

    cut = []
    for f in files:
        name = os.path.splitext(os.path.basename(f))[0]
        sin, sout, dur = bounds(name)
        st = max(0.0, sin - MARGIN)
        en = min(dur, sout + MARGIN)
        cut.append(dict(f=f, n=int(re.search(r"(\d+)", name).group(1)),
                        st=st, en=en, lead=sin - st, trail=en - sout, len=en - st))

    # pad between i and i+1 so trail_i + pad + lead_{i+1} == gap
    for i, c in enumerate(cut):
        c["pad"] = 0.0 if i == len(cut) - 1 else \
            max(0.0, a.gap - c["trail"] - cut[i + 1]["lead"])

    cmd = [FF, "-y", "-hide_banner", "-loglevel", "error"]
    for c in cut: cmd += ["-i", c["f"]]
    fl, labels = [], []
    for i, c in enumerate(cut):
        fl.append(f"[{i}:a]atrim=start={c['st']:.3f}:end={c['en']:.3f},"
                  f"asetpts=PTS-STARTPTS,aformat=sample_rates=44100:channel_layouts=mono[a{i}]")
        labels.append(f"[a{i}]")
        if c["pad"] > 0:
            fl.append(f"aevalsrc=0:d={c['pad']:.3f}:s=44100:c=mono[s{i}]")
            labels.append(f"[s{i}]")
    fl.append("".join(labels) + f"concat=n={len(labels)}:v=0:a=1[out]")
    cmd += ["-filter_complex", ";".join(fl), "-map", "[out]",
            "-c:a", "libmp3lame", "-b:a", "128k", "-ar", "44100", "-ac", "1", a.out]
    subprocess.run(cmd, check=True)

    edl, cur = [], 0.0
    for c in cut:
        edl.append(dict(batch=c["n"], file=os.path.basename(c["f"]),
                        start=round(cur, 3), end=round(cur + c["len"], 3),
                        speech_in=round(cur + c["lead"], 3),
                        speech_out=round(cur + c["len"] - c["trail"], 3),
                        src_trim=[round(c["st"], 3), round(c["en"], 3)],
                        pad_after=round(c["pad"], 3),
                        join_gap=round(c["trail"] + c["pad"] +
                                       (cut[cut.index(c) + 1]["lead"]
                                        if c is not cut[-1] else 0), 3)))
        cur += c["len"] + c["pad"]
    json.dump(dict(gap=a.gap, margin=MARGIN, total=round(cur, 3), batches=edl),
              open(a.edl, "w"), indent=1)
    print(f"wrote {a.out}  {int(cur//60)}:{cur%60:05.2f}  "
          f"({len(files)} batches, joins {a.gap*1000:.0f}ms)")
    joins = [e["join_gap"] for e in edl[:-1]]
    if joins: print("join gaps:", ", ".join(f"{j:.3f}s" for j in joins))

main()
