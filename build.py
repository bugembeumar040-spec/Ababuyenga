#!/usr/bin/env python3
"""Assemble the JINN film from the shot stills, VO and shot pack.

Reads  : shots/<ID>.jpeg, media/vo-full.mp3, beats.json
Writes : out/jinn.mp4  (16:9, <20MB)

Timing is derived from the recorded VO length, then each cut is snapped to the
nearest natural pause so no cut lands mid-word.
"""
import json, os, re, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "out")
SEG = os.path.join(OUT, "seg")
CAP = os.path.join(OUT, "cap")
W, H, FPS = 1280, 720, 30

# --- Klarna caption spec, adapted 9:16 -> 16:9 -------------------------------
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf"
INK = (245, 240, 230, 255)      # #F5F0E6
EDGE = (10, 12, 16, 255)        # #0A0C10
ACCENT = (232, 95, 66, 255)     # #E85F42
CAP1_Y, CAP2_Y = 0.62, 0.76     # fraction of frame height
CAP1_PX, CAP2_PX = 44, 30
STROKE = 2

# words that take the accent colour when they appear in CAP 1
ACCENT_WORDS = {"JINN", "JANNA", "JANEEN", "MAJNOON", "JUNNA", "SHAYTAN",
                "IBLIS", "RIBA", "MARIJ", "CONCEALED", "HIDDEN"}


def sh(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"FAILED: {' '.join(cmd[:6])}...\n{r.stderr[-1500:]}")
    return r.stdout


# --- timing ------------------------------------------------------------------
def vo_duration(path):
    return float(sh(["ffprobe", "-v", "error", "-show_entries",
                     "format=duration", "-of", "csv=p=0", path]).strip())


def pauses(path):
    """Midpoints of every detected pause, for snapping cuts."""
    p = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", path, "-af",
         "silencedetect=noise=-35dB:d=0.30", "-f", "null", "-"],
        capture_output=True, text=True).stderr
    v = [float(m.group(1)) for m in
         re.finditer(r"silence_(?:start|end): ([0-9.]+)", p)]
    return sorted((v[i] + v[i + 1]) / 2 for i in range(0, len(v) - 1, 2)
                  if v[i + 1] > v[i])


def build_timeline(shots, total, snaps, tol=2.5):
    """Scale the pack's estimates to the real VO, then snap to pauses."""
    est = shots[-1]["out"]
    k = total / est
    bounds = [s["in"] * k for s in shots] + [total]
    for i in range(1, len(bounds) - 1):          # never move 0.0 or the end
        near = min(snaps, key=lambda p: abs(p - bounds[i]), default=None)
        if near is not None and abs(near - bounds[i]) <= tol:
            bounds[i] = near
    for i in range(1, len(bounds)):              # keep strictly increasing
        bounds[i] = max(bounds[i], bounds[i - 1] + 0.8)
    scale = total / bounds[-1]
    bounds = [b * scale for b in bounds]
    for i, s in enumerate(shots):
        s["vo_in"], s["vo_out"] = round(bounds[i], 3), round(bounds[i + 1], 3)
        s["vo_len"] = round(s["vo_out"] - s["vo_in"], 3)
    return k


# --- captions ----------------------------------------------------------------
def caption_text(shot):
    """CAP 1 = the line the image lands on. CAP 2 = the rest."""
    vo = shot["vo"]
    if not vo:
        return None, None
    landed = next((v for v in vo if v["land"]), vo[0])
    rest = [v for v in vo if v is not landed]
    clean = lambda t: re.sub(r"\[[a-z]+\]\s*", "", t).strip()
    c1 = clean(landed["text"])
    c2 = " ".join(clean(v["text"]) for v in rest).strip()
    return c1, c2


def wrap(draw, text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_line(d, cx, y, text, font, colour):
    """Centred, with the spec's 2px dark outline."""
    w = d.textlength(text, font=font)
    d.text((cx - w / 2, y), text, font=font, fill=colour,
           stroke_width=STROKE, stroke_fill=EDGE)


def render_caption(shot, path):
    c1, c2 = caption_text(shot)
    if not c1:
        return False
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f1 = ImageFont.truetype(FONT_BOLD, CAP1_PX)
    f2 = ImageFont.truetype(FONT_REG, CAP2_PX)
    maxw = int(W * 0.86)
    cx = W / 2

    l1 = wrap(d, c1.upper(), f1, maxw)[:3]
    y = H * CAP1_Y
    for ln in l1:
        # accent any reserved word inside CAP 1
        if any(a in ln for a in ACCENT_WORDS):
            parts = ln.split()
            widths = [d.textlength(p + " ", font=f1) for p in parts]
            x = cx - sum(widths) / 2
            for p, w in zip(parts, widths):
                col = ACCENT if p.strip(".,:—-").upper() in ACCENT_WORDS else INK
                d.text((x, y), p, font=f1, fill=col,
                       stroke_width=STROKE, stroke_fill=EDGE)
                x += w
        else:
            draw_line(d, cx, y, ln, f1, INK)
        y += CAP1_PX * 1.18

    if c2:
        y2 = max(H * CAP2_Y, y + 6)
        for ln in wrap(d, c2, f2, maxw)[:3]:
            draw_line(d, cx, y2, ln, f2, INK)
            y2 += CAP2_PX * 1.2

    img.save(path)
    return True


# --- motion ------------------------------------------------------------------
def move_expr(move, n):
    """Translate the pack's MOVE line into a zoompan expression."""
    m = (move or "").lower()
    z0, z1, dx, dy = 1.0, 1.0, 0.0, 0.0
    if (p := re.search(r"push in (\d+)%", m)):
        z1 = 1 + int(p.group(1)) / 100
    elif (p := re.search(r"pull back (\d+)%", m)):
        z0 = 1 + int(p.group(1)) / 100
    if (p := re.search(r"drift (right|left|up|down) (\d+)px", m)):
        d, px = p.group(1), int(p.group(2))
        if d == "right": dx = px
        elif d == "left": dx = -px
        elif d == "down": dy = px
        else: dy = -px
    # a still frame still gets a hair of zoom, else zoompan judders
    if z0 == z1 and not dx and not dy:
        z1 = 1.008
    t = f"(on/{max(n - 1, 1)})"
    z = f"{z0}+({z1 - z0})*{t}"
    x = f"iw/2-(iw/zoom/2)+({dx})*{t}"
    y = f"ih/2-(ih/zoom/2)+({dy})*{t}"
    return z, x, y


def render_shot(shot, img_path, cap_path, seg_path):
    n = max(int(round(shot["vo_len"] * FPS)), 2)
    z, x, y = move_expr(shot["move"], n)
    # 2x intermediate keeps the slow moves free of stair-stepping
    vf = (f"scale=-2:{H*2}:flags=lanczos,crop=ih*16/9:ih,"
          f"zoompan=z='{z}':x='{x}':y='{y}':d={n}:s={W}x{H}:fps={FPS}")
    cmd = ["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", img_path]
    if cap_path:
        cmd += ["-i", cap_path]
    cmd += ["-filter_complex" if cap_path else "-vf"]
    cmd += [(vf + "[v];[v][1:v]overlay=0:0,format=yuv420p") if cap_path
            else (vf + ",format=yuv420p")]
    cmd += ["-frames:v", str(n), "-c:v", "libx264", "-preset", "medium",
            "-crf", "20", "-r", str(FPS), seg_path]
    sh(cmd)


# --- main --------------------------------------------------------------------
def main():
    captions_on = "--no-captions" not in sys.argv
    for d in (OUT, SEG, CAP):
        os.makedirs(d, exist_ok=True)

    shots = json.load(open(os.path.join(ROOT, "beats.json")))
    vo = os.path.join(ROOT, "media", "vo-full.mp3")
    total = vo_duration(vo)
    snaps = pauses(vo)
    k = build_timeline(shots, total, snaps)
    print(f"VO {total:.2f}s  scale {k:.4f}  {len(snaps)} pauses available")

    have, missing, segs = [], [], []
    for s in shots:
        p = os.path.join(ROOT, "shots", s["id"] + ".jpeg")
        (have if os.path.exists(p) else missing).append(s["id"])
    if missing:
        print(f"missing stills ({len(missing)}): {' '.join(missing)}")
        print("  -> their time is absorbed by the preceding shot")

    # A missing shot's time is absorbed by the shot before it -- or, if it is
    # the opening shot, by the shot after it, so the film never starts adrift
    # of the voiceover.
    kept, pending_in = [], None
    for s in shots:
        if os.path.exists(os.path.join(ROOT, "shots", s["id"] + ".jpeg")):
            if pending_in is not None:
                s["vo_in"] = pending_in
                s["vo_len"] = round(s["vo_out"] - s["vo_in"], 3)
                pending_in = None
            kept.append(s)
        elif kept:
            kept[-1]["vo_out"] = s["vo_out"]
            kept[-1]["vo_len"] = round(kept[-1]["vo_out"] - kept[-1]["vo_in"], 3)
        elif pending_in is None:
            pending_in = s["vo_in"]
    if kept:
        kept[-1]["vo_out"] = total
        kept[-1]["vo_len"] = round(total - kept[-1]["vo_in"], 3)

    for i, s in enumerate(kept):
        img = os.path.join(ROOT, "shots", s["id"] + ".jpeg")
        cap = os.path.join(CAP, s["id"] + ".png")
        cap = cap if (captions_on and render_caption(s, cap)) else None
        seg = os.path.join(SEG, f"{i:03d}_{s['id']}.mp4")
        render_shot(s, img, cap, seg)
        segs.append(seg)
        print(f"  {s['id']:6s} {s['vo_in']:7.2f}-{s['vo_out']:7.2f} "
              f"({s['vo_len']:5.2f}s) {s['move'][:34]}")

    json.dump(kept, open(os.path.join(ROOT, "beats-vo.json"), "w"),
              indent=1, ensure_ascii=False)

    lst = os.path.join(OUT, "segs.txt")
    with open(lst, "w") as f:
        for s in segs:
            f.write(f"file '{s}'\n")

    # two-pass to land reliably under 20MB
    target_bits = 18.4 * 8 * 1024 * 1024
    abr = 64_000
    vbr = int((target_bits - abr * total) / total)
    print(f"video bitrate {vbr/1000:.0f}k + audio 64k")
    out = os.path.join(OUT, "jinn.mp4")
    base = ["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0",
            "-i", lst, "-i", vo, "-c:v", "libx264", "-preset", "slow",
            "-b:v", str(vbr), "-pix_fmt", "yuv420p"]
    sh(base + ["-pass", "1", "-an", "-f", "mp4", "/dev/null"])
    sh(base + ["-pass", "2", "-c:a", "aac", "-b:a", "64k", "-ac", "1",
               "-movflags", "+faststart", "-shortest", out])
    mb = os.path.getsize(out) / 1024 / 1024
    print(f"\n{out}  {mb:.2f} MB  {vo_duration(out):.2f}s")


if __name__ == "__main__":
    main()
