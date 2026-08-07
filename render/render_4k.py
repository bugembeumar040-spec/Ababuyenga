#!/usr/bin/env python3
"""Deadbeat short - 4K master. True condensed outlines, tracked type, always-downsample crops."""
import os, subprocess, shutil
from PIL import Image, ImageDraw, ImageFont
import render as R                      # reuse CUTS, CUES, KEEP, GEN, trim maths

SCRATCH = R.SCRATCH
FF = R.FF
S   = 2                                  # 1080x1920 design units -> 2160x3840 output
W, H = 1080 * S, 1920 * S
FPS = 30
M   = 1.45                               # base headroom so every crop downsamples

CREAM, CHARCOAL, BRICK = R.CREAM, R.CHARCOAL, R.BRICK
F_BOLD = f"{SCRATCH}/fonts/CondBold.ttf"
F_REG  = f"{SCRATCH}/fonts/CondReg.ttf"

_fc = {}
def font(p, s):
    k = (p, s)
    if k not in _fc: _fc[k] = ImageFont.truetype(p, s)
    return _fc[k]

def text_img(text, path, size, color, track=0.0, alpha=255):
    """Render with real per-glyph tracking. No raster squeezing."""
    f = font(path, size)
    ws = [f.getlength(c) for c in text]
    total = sum(ws) + track * max(0, len(text) - 1)
    asc, desc = f.getmetrics()
    pad = size
    img = Image.new("RGBA", (int(total) + pad * 2, asc + desc + pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x = float(pad)
    for c, w in zip(text, ws):
        d.text((x, 0), c, font=f, fill=color + (alpha,))
        x += w + track
    bb = img.getbbox()
    return img.crop(bb) if bb else None

def put(img, text, path, size, color, cx, top, track=0.0, alpha=255):
    t = text_img(text, path, size, color, track, alpha)
    if t is None: return 0
    img.alpha_composite(t, (int(cx - t.width / 2), int(top)))
    return t.height

def cap1(img, lines, top=270, color=CHARCOAL, size=96, accent=None):
    y = top * S
    for ln in lines:
        col = BRICK if (accent and ln in accent) else color
        put(img, ln, F_BOLD, size * S, col, W // 2, y, track=-0.015 * size * S)
        y += int(size * S * 1.02)

def cap2(img, text, top=400, color=CHARCOAL, size=46, alpha=210):
    put(img, text, F_REG, size * S, color, W // 2, top * S, track=0.01 * size * S, alpha=alpha)

def card_a(img, label, value, cx, cy, w=560, h=170):
    cx, cy, w, h = cx * S, cy * S, w * S, h * S
    x0, y0 = int(cx - w / 2), int(cy - h / 2)
    d = ImageDraw.Draw(img)
    d.rectangle([x0, y0, x0 + w, y0 + h], fill=CREAM + (255,),
                outline=CHARCOAL + (255,), width=3 * S)
    put(img, label, F_REG, 26 * S, CHARCOAL, x0 + w / 2, y0 + 24 * S, track=0.16 * 26 * S)
    put(img, value, F_BOLD, 66 * S, CHARCOAL, x0 + w / 2, y0 + 66 * S, track=-0.01 * 66 * S)
    d.line([x0 + 26 * S, y0 + h - 20 * S, x0 + w - 26 * S, y0 + h - 20 * S],
           fill=CHARCOAL + (255,), width=2 * S)

def card_b(img, l_lab, l_val, r_lab, r_val, cy=470, w=900, h=290):
    cx, cy, w, h = W / 2, cy * S, w * S, h * S
    x0, y0 = int(cx - w / 2), int(cy - h / 2)
    d = ImageDraw.Draw(img)
    d.rectangle([x0, y0, x0 + w, y0 + h], fill=CREAM + (255,),
                outline=CHARCOAL + (255,), width=3 * S)
    split = x0 + int(w * 0.38)
    d.line([split, y0 + 18 * S, split, y0 + h - 18 * S], fill=CHARCOAL + (255,), width=2 * S)
    put(img, l_lab, F_REG, 24 * S, CHARCOAL, (x0 + split) / 2, y0 + 26 * S, track=0.16 * 24 * S)
    put(img, r_lab, F_REG, 24 * S, CHARCOAL, (split + x0 + w) / 2, y0 + 26 * S, track=0.16 * 24 * S)
    put(img, l_val, F_BOLD, 62 * S, CHARCOAL, (x0 + split) / 2, y0 + 130 * S, track=-0.01 * 62 * S)
    put(img, r_val, F_BOLD, 150 * S, BRICK, (split + x0 + w) / 2, y0 + 92 * S, track=-0.02 * 150 * S)

def card_c(img, text, cy, size=78, rule=0.60):
    h = put(img, text, F_BOLD, size * S, CHARCOAL, W // 2, cy * S, track=-0.01 * size * S)
    d = ImageDraw.Draw(img)
    rw = int(W * rule)
    yy = cy * S + h + 20 * S
    d.line([W // 2 - rw // 2, yy, W // 2 + rw // 2, yy], fill=CHARCOAL + (255,), width=8 * S)

_base = {}
def base(gen, scale, dy):
    k = (gen, scale, dy)
    if k in _base: return _base[k]
    BW, BH = int(W * M), int(H * M)
    im = Image.open(R.GEN[gen]).convert("RGB")
    r = max(BW / im.width, BH / im.height) * scale
    im = im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)
    c = Image.new("RGB", (BW, BH), CREAM)
    c.paste(im, ((BW - im.width) // 2, (BH - im.height) // 2 + int(dy * S * M)))
    _base[k] = c
    return c

def ease(p): return 1 - (1 - p) ** 3

def frame_at(t_old):
    cut = next((c for c in R.CUTS if c[2] <= t_old < c[3]), R.CUTS[-1])
    _, gen, ti, to, bs, bdy, z0, z1, dx0, dx1, dy0, dy1 = cut
    p = ease(min(1.0, max(0.0, (t_old - ti) / max(1e-6, to - ti))))
    z  = z0 + (z1 - z0) * p
    dx = (dx0 + (dx1 - dx0) * p) * S
    dy = (dy0 + (dy1 - dy0) * p) * S
    B = base(gen, bs, bdy)
    cw, ch = W * M / z, H * M / z
    cx = (B.width - cw) / 2 + dx * M / z
    cy = (B.height - ch) / 2 + dy * M / z
    cx = max(0, min(B.width - cw, cx)); cy = max(0, min(B.height - ch, cy))
    im = B.crop((int(cx), int(cy), int(cx + cw), int(cy + ch))).resize((W, H), Image.LANCZOS).convert("RGBA")

    for (a, b, kind, kw) in R.CUES:
        if not (a <= t_old < b): continue
        if kind == "cap1":
            cap1(im, kw["lines"], kw.get("top", 270), kw.get("color", CHARCOAL),
                 kw.get("size", 96), kw.get("accent"))
        elif kind == "cap2":
            cap2(im, kw["text"], kw.get("top", 400), kw.get("color", CHARCOAL))
        elif kind == "acc":
            put(im, kw["text"], F_BOLD, 150 * S, BRICK, W // 2, kw["top"] * S, track=-0.02 * 150 * S)
        elif kind == "onc":
            put(im, kw["text"], F_BOLD, 112 * S, CHARCOAL, W // 2, kw["top"] * S, track=-0.015 * 112 * S)
        elif kind == "sml":
            sz = kw.get("size", 56)
            put(im, kw["text"], F_BOLD, sz * S, CHARCOAL, kw["cx"] * S, kw["top"] * S, track=0.02 * sz * S)
        elif kind == "cA":
            card_a(im, kw["label"], kw["value"], kw["cx"], kw["cy"], kw.get("w", 560))
        elif kind == "cB":
            card_b(im, kw["l_lab"], kw["l_val"], kw["r_lab"], kw["r_val"], kw.get("cy", 470))
        elif kind == "cC":
            card_c(im, kw["text"], kw["cy"], kw.get("size", 78))
    return im.convert("RGB")

def main():
    out = f"{SCRATCH}/frames4k"
    shutil.rmtree(out, ignore_errors=True); os.makedirs(out)
    inv, acc = [], 0.0
    for a, b in R.KEEP:
        inv.append((acc, acc + (b - a), a)); acc += b - a
    def to_old(tn):
        for s, e, a in inv:
            if s <= tn <= e: return a + (tn - s)
        return R.DUR
    n = int(R.NEWDUR * FPS)
    print(f"{W}x{H} @ {FPS}fps  {R.NEWDUR:.2f}s  {n} frames", flush=True)
    for i in range(n):
        frame_at(to_old(i / FPS)).save(f"{out}/f{i:05d}.jpg", quality=96, subsampling=0)
        if i % 150 == 0: print(f"  {i}/{n}", flush=True)
    subprocess.run([FF, "-y", "-framerate", str(FPS), "-i", f"{out}/f%05d.jpg",
                    "-i", f"{SCRATCH}/vo-trim.wav", "-c:v", "libx264", "-preset", "slow",
                    "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k",
                    "-movflags", "+faststart", "-shortest",
                    f"{SCRATCH}/deadbeat-short-4k.mp4"], check=True, capture_output=True)
    print("done", flush=True)

if __name__ == "__main__":
    main()
