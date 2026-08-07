#!/usr/bin/env python3
"""Assemble the SALAAM short: Ken Burns stills -> crossfades -> captions
-> grade -> VO mix. Every stage writes an intermediate so it can be rerun."""
import os
import subprocess
import sys

from beats import SCENES, CUES, W, H, FPS, XF, TOTAL

OUT = "work/out"
os.makedirs(OUT, exist_ok=True)

# source is pre-scaled to 2x target so zoompan has real pixels to eat into
SW, SH = W * 2, H * 2


def run(args, label):
    print(f"  ... {label}", flush=True)
    p = subprocess.run(args, capture_output=True, text=True)
    if p.returncode:
        print(p.stderr[-4000:])
        sys.exit(f"FAILED: {label}")


def kenburns(move, n):
    """(z, x, y) zoompan expressions for a linear move over n frames."""
    t = f"(on/{n - 1})"
    cx = "iw/2-(iw/zoom/2)"
    cy = "ih/2-(ih/zoom/2)"
    if move == "pin":
        return f"1.00+0.12*{t}", cx, cy
    if move == "pout":
        return f"1.12-0.12*{t}", cx, cy
    # drifting moves start zoomed so there is margin to travel into
    z = f"1.10+0.10*{t}"
    d = f"0.045*({t}-0.5)"
    if move == "pl":
        return z, f"{cx}-{d}*iw", cy
    if move == "pr":
        return z, f"{cx}+{d}*iw", cy
    if move == "pu":
        return z, cx, f"{cy}-{d}*ih"
    if move == "pd":
        return z, cx, f"{cy}+{d}*ih"
    raise ValueError(move)


def stage_clips():
    print("[1/4] Ken Burns clips")
    for idx, t_in, t_out, img, move in SCENES:
        dur = (t_out - t_in) + XF
        n = round(dur * FPS)
        z, x, y = kenburns(move, n)
        vf = (
            f"scale={SW}:{SH}:force_original_aspect_ratio=increase:flags=lanczos,"
            f"crop={SW}:{SH},"
            f"zoompan=z='{z}':x='{x}':y='{y}':d={n}:s={W}x{H}:fps={FPS},"
            f"format=yuv420p"
        )
        run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", f"work/img/{img}.png",
             "-vf", vf, "-frames:v", str(n), "-c:v", "libx264", "-crf", "14",
             "-preset", "veryfast", f"{OUT}/clip{idx:02d}.mp4"], f"scene {idx:02d} {img} {move}")


def stage_xfade():
    print("[2/4] crossfade chain")
    args = ["ffmpeg", "-y", "-v", "error"]
    for idx, *_ in SCENES:
        args += ["-i", f"{OUT}/clip{idx:02d}.mp4"]
    parts, prev, acc = [], "0:v", 0.0
    for i in range(1, len(SCENES)):
        acc += SCENES[i - 1][2] - SCENES[i - 1][1]      # offset = scene i's t_in
        lab = f"x{i}"
        parts.append(f"[{prev}][{i}:v]xfade=transition=fade:duration={XF}:"
                     f"offset={acc:.3f}[{lab}]")
        prev = lab
    fc = ";".join(parts)
    run(args + ["-filter_complex", fc, "-map", f"[{prev}]", "-t", f"{TOTAL}",
                "-c:v", "libx264", "-crf", "15", "-preset", "veryfast",
                f"{OUT}/base.mp4"], f"{len(SCENES)} scenes")


def stage_captions():
    print("[3/4] captions")
    src = f"{OUT}/base.mp4"
    # two passes keeps each filter graph small and memory sane
    for p, chunk in enumerate([list(enumerate(CUES))[:19], list(enumerate(CUES))[19:]]):
        args = ["ffmpeg", "-y", "-v", "error", "-i", src]
        fc, prev = [], "0:v"
        for j, (i, (st, en, kind, _)) in enumerate(chunk):
            pad = min(0.35, st)     # itsoffset must never go negative,
                                    # or ffmpeg drops the cue entirely
            args += ["-loop", "1", "-framerate", str(FPS),
                     "-t", f"{en - st + 2 * pad:.3f}",
                     "-itsoffset", f"{st - pad:.3f}", "-i", f"work/caps/c{i:02d}.png"]
            fi, fo = 0.22, 0.26
            fc.append(f"[{j + 1}:v]format=rgba,"
                      f"fade=t=in:st={st:.3f}:d={fi}:alpha=1,"
                      f"fade=t=out:st={en - fo:.3f}:d={fo}:alpha=1[c{i}]")
            lab = f"o{i}"
            fc.append(f"[{prev}][c{i}]overlay=0:0:enable='between(t,{st - pad:.3f},"
                      f"{en + pad:.3f})'[{lab}]")
            prev = lab
        dst = f"{OUT}/caps{p}.mp4"
        run(args + ["-filter_complex", ";".join(fc), "-map", f"[{prev}]",
                    "-t", f"{TOTAL}", "-c:v", "libx264", "-crf", "15",
                    "-preset", "veryfast", dst], f"pass {p + 1}: {len(chunk)} cues")
        src = dst
    return src


def stage_final(src):
    print("[4/4] grade + audio")
    grade = (
        "eq=contrast=1.05:saturation=1.03,"
        "curves=r='0/0.015 0.5/0.525 1/1':g='0/0.010 0.5/0.505 1/1':b='0/0 0.5/0.478 1/0.985',"
        "vignette=PI/4.6,"
        "noise=alls=4:allf=t+u,"
        f"fade=t=in:st=0:d=0.35,fade=t=out:st={TOTAL - 1.2:.2f}:d=1.2,"
        "format=yuv420p"
    )
    # VO at broadcast-ish loudness + a near-inaudible air bed so the long
    # dramatic pauses do not read as dead file
    audio = (
        "[1:a]loudnorm=I=-14:TP=-1.5:LRA=11,"
        f"afade=t=in:st=0:d=0.25,afade=t=out:st={TOTAL - 1.5:.2f}:d=1.5[vo];"
        "[2:a]lowpass=f=200,highpass=f=45,volume=0.018[air];"
        "[vo][air]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[a]"
    )
    run(["ffmpeg", "-y", "-v", "error",
         "-i", src, "-i", "work/vo.mp3",
         "-f", "lavfi", "-t", f"{TOTAL}", "-i", "anoisesrc=color=brown:r=44100:a=0.9",
         "-filter_complex", f"[0:v]{grade}[v];{audio}",
         "-map", "[v]", "-map", "[a]",
         "-c:v", "libx264", "-profile:v", "high", "-level", "4.1", "-crf", "21",
         "-maxrate", "12M", "-bufsize", "24M",
         "-preset", "slow", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
         "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-t", f"{TOTAL}",
         f"{OUT}/salaam_final.mp4"], "final render")


if __name__ == "__main__":
    only = sys.argv[1] if len(sys.argv) > 1 else "all"
    if only in ("all", "clips"):
        stage_clips()
    if only in ("all", "xfade"):
        stage_xfade()
    if only in ("all", "caps", "final"):
        s = stage_captions() if only != "final" else f"{OUT}/caps1.mp4"
        stage_final(s)
    print("done ->", f"{OUT}/salaam_final.mp4")
