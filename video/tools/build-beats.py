#!/usr/bin/env python3
"""
Build the cut from the recorded VO.

Reads jinn-shot-pack-final.txt for each shot's MOVE spec and flags, and
media/vo-align.json for where every line is actually spoken. Each shot is placed
under its own line; the cut order is the recording's order.

This replaced an earlier version that scaled the pack's planned timings onto the
real duration and snapped boundaries to pauses. That was wrong in three ways at
once, and the captions drifted off the voiceover as a result:

  * the recording did not compress evenly -- group 1 came in at 107.00s against
    a planned 107s while the film overall came in 9% short;
  * eight shots are not in the recording at all (the pack's CUT 1 and CUT 2,
    applied at record time), so everything after them was displaced;
  * S29 and S29b are spoken in the opposite order to the pack.

None of that is recoverable from a silence map. A pause tells you someone
stopped talking, not which line they stopped in the middle of. Run
tools/align-vo.py first; this consumes its output.

Emits src/jinn/beats.ts.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "jinn-shot-pack-final.txt"
ALIGN = ROOT / "video" / "media" / "vo-align.json"
OUT = ROOT / "video" / "src" / "jinn" / "beats.ts"

VO_DURATION = float(sys.argv[1]) if len(sys.argv) > 1 else 613.91
FPS = 30
MIN_SHOT = 1.5
# Where the cut lands inside the gap between two lines. Early enough that the
# incoming plate is up before the next line starts, late enough that it does not
# steal the tail of the one before.
CUT_AT = 0.4

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


def solve(shots):
    """Place every shot under its own line, in the order the VO says them."""
    align = json.loads(ALIGN.read_text())
    spoken, dropped = align["spoken"], set(align["dropped"])

    by_id = {s["id"]: s for s in shots}
    for missing in dropped - by_id.keys():
        raise SystemExit(f"align names a shot the pack does not: {missing}")

    # The recording's order, not the pack's.
    order = [sid for sid in spoken if sid in by_id]

    cuts = [0.0]
    for a, b in zip(order, order[1:]):
        gap_start, gap_end = spoken[a]["end"], spoken[b]["start"]
        if gap_end <= gap_start:  # lines abut or overlap; cut on the boundary
            cut = gap_end
        else:
            cut = gap_start + (gap_end - gap_start) * CUT_AT
        cuts.append(max(cut, cuts[-1] + MIN_SHOT))
    cuts.append(VO_DURATION)

    out = []
    for idx, sid in enumerate(order):
        s = dict(by_id[sid])
        t_in, t_out = cuts[idx], cuts[idx + 1]
        s["tIn"], s["tOut"] = round(t_in, 3), round(t_out, 3)
        s["frameIn"] = round(t_in * FPS)
        s["frames"] = max(round(t_out * FPS) - round(t_in * FPS), 1)
        s["line"] = [spoken[sid]["start"], spoken[sid]["end"]]
        s["hit"] = spoken[sid]["hit"]
        out.append(s)
    return out, sorted(dropped)


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


def emit(shots, dropped):
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
                "line": s["line"],
                "plate": f"plates/{s['id']}.png",
            }
            for s in shots
        ],
        indent=2,
    )
    OUT.write_text(
        "// GENERATED by video/tools/build-beats.py — do not hand-edit.\n"
        "// Every shot is placed under its own line, force-aligned against\n"
        "// public/jinn-vo.mp3 by tools/align-vo.py. Order is the recording's,\n"
        "// not the pack's. Re-run both tools if the VO is recut.\n\n"
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
        "  /** [start, end] of this shot's spoken line, seconds into the VO. */\n"
        "  line: [number, number];\n"
        "  plate: string;\n"
        "};\n\n"
        f"export const FPS = {FPS};\n"
        f"export const VO_DURATION = {VO_DURATION};\n"
        f"export const DURATION_IN_FRAMES = {round(VO_DURATION * FPS)};\n"
        "export const WIDTH = 2560;\nexport const HEIGHT = 1440;\n\n"
        f"export const SHOTS: Shot[] = {body};\n\n"
        "// Shots the recording does not contain — the pack's CUT 1 and CUT 2,\n"
        "// applied when the VO was recorded. Their plates are still in\n"
        "// public/plates/ and they return automatically if a fuller VO lands.\n"
        f"export const DROPPED: string[] = {json.dumps(dropped)};\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    timed, dropped = solve(parse_pack())
    emit(timed, dropped)
    print(f"{len(timed)} shots in the cut, {len(dropped)} dropped: {', '.join(dropped)}")
    # Every shot must contain the line it is captioned with. This is the check
    # the previous version had no way to make.
    bad = [s for s in timed if not (s["tIn"] <= s["line"][0] and s["line"][1] <= s["tOut"] + 0.35)]
    print(f"lines fully inside their own shot: {len(timed) - len(bad)}/{len(timed)}")
    for s in bad:
        print(f"  !! {s['id']:6} shot {s['tIn']:.2f}-{s['tOut']:.2f} "
              f"line {s['line'][0]:.2f}-{s['line'][1]:.2f}")
