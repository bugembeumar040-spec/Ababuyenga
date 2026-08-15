#!/usr/bin/env python3
"""
Derive the real cut from the recorded VO.

Reads jinn-shot-pack-final.txt for the planned spine (64 shots, MOVE specs, VO
lines) and media/sil.txt for the silence map of the merged voiceover, then
re-times every shot boundary onto a real pause in the recording.

The shot pack's own instruction: "Timings are weighted per shot and derived from
the v3 word count at 135 wpm -- re-cut them against the recorded VO before you
generate anything." This is that re-cut, done arithmetically rather than by eye.

Emits src/jinn/beats.ts.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "jinn-shot-pack-final.txt"
SIL = ROOT / "video" / "media" / "sil.txt"
OUT = ROOT / "video" / "src" / "jinn" / "beats.ts"

VO_DURATION = float(sys.argv[1]) if len(sys.argv) > 1 else 613.91
FPS = 30
# Boundaries may travel this far from their scaled position to find a real pause.
SNAP_WINDOW = 2.6
MIN_SHOT = 1.8

SHOT_RE = re.compile(r"^(S\d+[a-z]?) · (\d+):(\d+)[–-](\d+):(\d+)\s*$")
VO_RE = re.compile(r"^VO(>|\s) ?(.*)$")


def parse_pack():
    lines = PACK.read_text(encoding="utf-8").splitlines()
    shots, beat = [], ""
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("BEAT "):
            beat = re.sub(r"\s*\*\*.*", "", line[5:]).strip()
        m = SHOT_RE.match(line)
        if m:
            sid = m.group(1)
            start = int(m.group(2)) * 60 + int(m.group(3))
            end = int(m.group(4)) * 60 + int(m.group(5))
            block = "\n".join(lines[i : i + 12])
            move = ""
            vo, lead = [], None
            j = i + 1
            while j < len(lines) and not lines[j].startswith("PROMPT"):
                if lines[j].startswith("MOVE:"):
                    move = lines[j][5:].strip()
                    k = j + 1
                    while k < len(lines) and not lines[k].startswith(("-----", "VO")):
                        move += " " + lines[k].strip()
                        k += 1
                vm = VO_RE.match(lines[j])
                if vm:
                    text = vm.group(2).strip()
                    k = j + 1
                    while k < len(lines) and lines[k].startswith("      "):
                        text += " " + lines[k].strip()
                        k += 1
                    text = re.sub(r"\s*<-.*", "", text).strip()
                    if vm.group(1) == ">" and lead is None:
                        lead = len(vo)
                    vo.append(text)
                j += 1
            shots.append(
                {
                    "id": sid,
                    "beat": beat,
                    "planIn": start,
                    "planOut": end,
                    "move": move,
                    "vo": vo,
                    "lead": lead if lead is not None else 0,
                    "silence": "SILENCE" in block,
                    "bloom": "WASH BLOOM" in move.upper(),
                    "lineReveal": "line-reveal" in move.lower(),
                    "peak": "** PEAK **" in block,
                    "locked": bool(re.match(r"^(none|hold)", move.lower())),
                }
            )
            i = j
            continue
        i += 1
    return shots


def parse_silences():
    """Return [(start, end)] pauses in the merged VO."""
    gaps, start = [], None
    for line in SIL.read_text().splitlines():
        if "silence_start" in line:
            start = float(line.split(":")[1].split()[0])
        elif "silence_end" in line and start is not None:
            end = float(line.split(":")[1].split("|")[0].strip())
            gaps.append((start, end))
            start = None
    return gaps


def solve(shots, gaps):
    """Scale the planned spine onto the real VO, then snap cuts onto pauses."""
    plan_total = shots[-1]["planOut"]
    scale = VO_DURATION / plan_total
    # Cut on the pause, not on the word: a cut lands 40% into the gap so the
    # incoming plate is already up when the next line starts.
    centres = [g[0] + (g[1] - g[0]) * 0.4 for g in gaps]

    cuts = [0.0]
    for s in shots[:-1]:
        target = s["planOut"] * scale
        near = [c for c in centres if abs(c - target) <= SNAP_WINDOW]
        chosen = min(near, key=lambda c: abs(c - target)) if near else target
        cuts.append(max(chosen, cuts[-1] + MIN_SHOT))
    cuts.append(VO_DURATION)

    out = []
    for idx, s in enumerate(shots):
        t_in, t_out = cuts[idx], cuts[idx + 1]
        s = dict(s)
        s["tIn"] = round(t_in, 3)
        s["tOut"] = round(t_out, 3)
        s["frameIn"] = round(t_in * FPS)
        s["frames"] = max(round(t_out * FPS) - round(t_in * FPS), 1)
        s["snapped"] = any(abs(t_in - c) < 0.001 for c in centres)
        s["drift"] = round(t_in - s["planIn"] * scale, 2)
        out.append(s)
    return out


MOVE_RE = re.compile(
    r"(push in|pull back|drift right|drift left|drift up|drift down)\s+(\d+)(%|px)"
)


def parse_move(move):
    """MOVE prose -> a Ken Burns transform. Percentages are total travel."""
    ops = MOVE_RE.findall(move.lower())
    zoom, dx, dy = 0.0, 0.0, 0.0
    for kind, amount, unit in ops:
        n = float(amount)
        if kind == "push in":
            zoom = n / 100
        elif kind == "pull back":
            zoom = -n / 100
        elif kind == "drift right":
            dx = n if unit == "px" else n * 12
        elif kind == "drift left":
            dx = -(n if unit == "px" else n * 12)
        elif kind == "drift up":
            dy = -(n if unit == "px" else n * 12)
        elif kind == "drift down":
            dy = n if unit == "px" else n * 12
    return {"zoom": round(zoom, 4), "dx": dx, "dy": dy}


def emit(shots):
    for s in shots:
        s["camera"] = parse_move(s["move"])
    body = json.dumps(
        [
            {
                "id": s["id"],
                "beat": s["beat"],
                "frameIn": s["frameIn"],
                "frames": s["frames"],
                "tIn": s["tIn"],
                "tOut": s["tOut"],
                "camera": s["camera"],
                "move": s["move"],
                "vo": s["vo"],
                "lead": s["lead"],
                "silence": s["silence"],
                "bloom": s["bloom"],
                "lineReveal": s["lineReveal"],
                "peak": s["peak"],
                "locked": s["locked"],
                "plate": f"plates/{s['id']}.png",
            }
            for s in shots
        ],
        indent=2,
    )
    OUT.write_text(
        "// GENERATED by video/tools/build-beats.py — do not hand-edit.\n"
        "// Cuts are snapped onto real pauses in media/jinn-vo.mp3, not the\n"
        "// shot pack's 135wpm estimates. Re-run the tool if the VO is recut.\n\n"
        "export type Camera = { zoom: number; dx: number; dy: number };\n\n"
        "export type Shot = {\n"
        "  id: string;\n"
        "  beat: string;\n"
        "  frameIn: number;\n"
        "  frames: number;\n"
        "  tIn: number;\n"
        "  tOut: number;\n"
        "  camera: Camera;\n"
        "  move: string;\n"
        "  vo: string[];\n"
        "  lead: number;\n"
        "  silence: boolean;\n"
        "  bloom: boolean;\n"
        "  lineReveal: boolean;\n"
        "  peak: boolean;\n"
        "  locked: boolean;\n"
        "  plate: string;\n"
        "};\n\n"
        f"export const FPS = {FPS};\n"
        f"export const VO_DURATION = {VO_DURATION};\n"
        f"export const DURATION_IN_FRAMES = {round(VO_DURATION * FPS)};\n"
        "export const WIDTH = 2560;\nexport const HEIGHT = 1440;\n\n"
        f"export const SHOTS: Shot[] = {body};\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    shots = parse_pack()
    gaps = parse_silences()
    timed = solve(shots, gaps)
    emit(timed)
    snapped = sum(1 for s in timed if s["snapped"])
    print(f"{len(timed)} shots, {len(gaps)} pauses, {snapped}/{len(timed)-1} cuts on a pause")
    print(f"worst drift from scaled plan: {max(abs(s['drift']) for s in timed):.2f}s")
    for s in timed:
        flag = "" if s["snapped"] else "  (no pause — held at scaled position)"
        print(f"  {s['id']:6} {s['tIn']:7.2f}->{s['tOut']:7.2f} {s['tOut']-s['tIn']:5.2f}s{flag}")
