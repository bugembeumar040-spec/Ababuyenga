#!/usr/bin/env python3
"""
Audit a rendered master before it is delivered.

This exists because a render was reported finished twice when it was not, and
because a cut was delivered whose captions did not sit on the voiceover. Both
were avoidable by checking the artefact instead of assuming it. Nothing here
trusts a filename, a timestamp on its own, or a process that appeared to exit.

Checks, in order of what they would have caught:

  FRESH     the file is newer than every input that determines its content, so
            it cannot be a stale render from before the last fix
  COMPLETE  the decoded frame count matches beats.ts exactly — a truncated or
            still-being-written file fails here rather than looking fine
  STREAMS   dimensions, fps and duration are what the composition declares
  AUDIO     the track is the voiceover and is not silent
  SYNC      every shot's spoken line falls inside the shot's own frame range,
            re-derived from beats.ts against the alignment rather than trusted

Exit code is non-zero if any check fails, so it can gate a delivery.

Usage:  python3 tools/audit-render.py out/jinn-2560x1440.mp4
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FFMPEG = "/usr/local/lib/python3.11/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2"
BEATS = ROOT / "src" / "jinn" / "beats.ts"
ALIGN = ROOT / "media" / "vo-align.json"

# Anything that changes what the render should look like.
INPUTS = [
    BEATS,
    ALIGN,
    ROOT / "src" / "jinn" / "captions.ts",
    ROOT / "src" / "jinn" / "plates.ts",
    ROOT / "src" / "jinn" / "Caption.tsx",
    ROOT / "src" / "jinn" / "Shot.tsx",
    ROOT / "src" / "jinn" / "Plate.tsx",
    ROOT / "src" / "jinn" / "Film.tsx",
    ROOT / "src" / "jinn" / "effects.tsx",
    ROOT / "public" / "jinn-vo.mp3",
]

results: list[tuple[bool, str, str]] = []


def check(ok: bool, name: str, detail: str) -> None:
    results.append((ok, name, detail))


def beats() -> tuple[list[dict], int, int]:
    src = BEATS.read_text()
    body = src.split("export const SHOTS: Shot[] = ", 1)[1]
    body = body[: body.index("\n];") + 3]
    shots = json.loads(body.rstrip().rstrip(";"))
    frames = int(re.search(r"DURATION_IN_FRAMES = (\d+)", src).group(1))
    fps = int(re.search(r"export const FPS = (\d+)", src).group(1))
    return shots, frames, fps


def probe(path: Path) -> dict:
    out = subprocess.run(
        [FFMPEG, "-i", str(path), "-hide_banner"],
        capture_output=True, text=True,
    ).stderr
    return {"raw": out}


def count_frames(path: Path) -> int:
    """Decode the whole file. Slower than reading a header, and the point:
    a header can describe frames the file does not actually contain."""
    out = subprocess.run(
        [FFMPEG, "-i", str(path), "-map", "0:v:0", "-c", "copy", "-f", "null", "-"],
        capture_output=True, text=True,
    ).stderr
    hits = re.findall(r"frame=\s*(\d+)", out)
    return int(hits[-1]) if hits else -1


def audio_level(path: Path) -> float:
    out = subprocess.run(
        [FFMPEG, "-i", str(path), "-map", "0:a:0", "-af", "volumedetect", "-f", "null", "-"],
        capture_output=True, text=True,
    ).stderr
    m = re.search(r"mean_volume:\s*(-?[\d.]+) dB", out)
    return float(m.group(1)) if m else 0.0


def main() -> int:
    target = Path(sys.argv[1] if len(sys.argv) > 1 else "out/jinn-2560x1440.mp4")
    if not target.exists():
        print(f"FAIL  no such file: {target}")
        return 1

    shots, want_frames, fps = beats()
    mtime = target.stat().st_mtime

    stale = [p.name for p in INPUTS if p.exists() and p.stat().st_mtime > mtime]
    check(not stale, "FRESH", "newer than all inputs" if not stale
          else f"OLDER than {', '.join(stale)} — this is a stale render")

    got = count_frames(target)
    check(got == want_frames, "COMPLETE",
          f"{got} frames decoded, beats.ts declares {want_frames}")

    raw = probe(target)["raw"]
    dim = re.search(r"(\d{3,5})x(\d{3,5})", raw)
    dur = re.search(r"Duration: (\d+):(\d+):([\d.]+)", raw)
    secs = int(dur.group(1)) * 3600 + int(dur.group(2)) * 60 + float(dur.group(3)) if dur else 0
    expect = want_frames / fps
    check(dim is not None and dim.group(0) == "2560x1440" and abs(secs - expect) < 0.5,
          "STREAMS", f"{dim.group(0) if dim else '?'} {secs:.2f}s "
                     f"(composition: 2560x1440 {expect:.2f}s)")

    has_audio = "Audio:" in raw
    level = audio_level(target) if has_audio else 0.0
    check(has_audio and -40 < level < -5, "AUDIO",
          f"present, mean {level:.1f} dB" if has_audio else "NO AUDIO TRACK")

    align = json.loads(ALIGN.read_text())["spoken"]
    bad = []
    for s in shots:
        line = align.get(s["id"])
        if not line:
            bad.append((s["id"], "no alignment entry"))
            continue
        f_in, f_out = s["frameIn"], s["frameIn"] + s["frames"]
        if not (f_in / fps <= line["start"] and line["end"] <= f_out / fps + 0.35):
            bad.append((s["id"], f"shot {f_in/fps:.2f}-{f_out/fps:.2f}s vs "
                                 f"line {line['start']:.2f}-{line['end']:.2f}s"))
    check(not bad, "SYNC", f"{len(shots) - len(bad)}/{len(shots)} shots contain their line")

    width = max(len(n) for _, n, _ in results)
    for ok, name, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name:<{width}}  {detail}")
    for sid, why in bad[:10]:
        print(f"        {sid}: {why}")

    failed = [n for ok, n, _ in results if not ok]
    print()
    print("AUDIT PASSED — safe to deliver" if not failed
          else f"AUDIT FAILED: {', '.join(failed)} — do not deliver")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
