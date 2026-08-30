#!/usr/bin/env python3
"""Typeset a thumbnail: artwork in, 1280x720 thumbnail out.

    python3 make_thumb.py <videoId> <source.png|url> [--side right|left|top]
                                                     [--theme cream|navy]

Text comes from the `thumbnailText` field in clarity-metadata.json,
lines separated by " / ". Type is auto-sized to fill the chosen zone,
because the whole point is that it survives a 168px-wide feed.

The last line is set in gold as the payoff; a lone "vs" or "!=" line is
always gold.
"""
import json
import sys
import pathlib
import urllib.request
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = pathlib.Path(__file__).parent
OUT = HERE / "thumbs"
W, H = 1280, 720
MARGIN = 56
GAP = 0.06          # line gap as a fraction of line height
SAFE = 0.92         # never let a line exceed this share of the zone width

CREAM, NAVY, GOLD = "#F4EDE0", "#1B2A4A", "#C8922A"
FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]


def font_path():
    for f in FONTS:
        if pathlib.Path(f).exists():
            return f
    raise SystemExit("No bold sans font found.")


def load(src):
    if src.startswith("http"):
        req = urllib.request.Request(src, headers={"User-Agent": "thumb/1.0"})
        with urllib.request.urlopen(req) as r:
            tmp = HERE / ".src.png"
            tmp.write_bytes(r.read())
            src = str(tmp)
    return Image.open(src).convert("RGB")


def cover(im):
    """Scale-and-crop to exactly 1280x720."""
    s = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    return im.crop(((im.width - W) // 2, (im.height - H) // 2,
                    (im.width - W) // 2 + W, (im.height - H) // 2 + H))


def fit(lines, box_w, box_h, fp):
    """Largest size at which every line fits the box."""
    lo, hi, best = 10, 400, 10
    while lo <= hi:
        mid = (lo + hi) // 2
        f = ImageFont.truetype(fp, mid)
        widest = max(f.getbbox(t)[2] - f.getbbox(t)[0] for t in lines)
        lh = mid * (1 + GAP)
        if widest <= box_w * SAFE and lh * len(lines) <= box_h:
            best, lo = mid, mid + 1
        else:
            hi = mid - 1
    return best


def scrim(im, box, dark):
    """Soften the artwork behind the type so contrast never depends on luck.

    Feathered, not a hard rectangle - a visible box edge reads as a
    pasted sticker and cheapens the whole frame.
    """
    pad = 64
    x0, y0 = max(0, box[0] - pad), max(0, box[1] - pad)
    x1, y1 = min(W, box[2] + pad), min(H, box[3] + pad)

    wash = Image.new("RGB", im.size, NAVY if dark else CREAM)
    blended = Image.blend(im.filter(ImageFilter.GaussianBlur(16)), wash, 0.78)

    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((x0, y0, x1, y1), radius=90, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(58))
    im.paste(Image.composite(blended, im, mask), (0, 0))


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    vid, src = sys.argv[1], sys.argv[2]
    side = "right"
    theme = "cream"
    for i, a in enumerate(sys.argv):
        if a == "--side":
            side = sys.argv[i + 1]
        if a == "--theme":
            theme = sys.argv[i + 1]

    meta = json.loads((HERE / "clarity-metadata.json").read_text())
    entry = next((v for v in meta["videos"] if v["videoId"] == vid), None)
    if not entry:
        raise SystemExit(f"{vid} not in clarity-metadata.json")
    lines = [s.strip().upper() for s in entry["thumbnailText"].split("/") if s.strip()]

    im = cover(load(src))
    dark = theme == "navy"
    body = CREAM if dark else NAVY

    half = (W - MARGIN * 3) // 2
    if side == "top":
        box = (MARGIN, MARGIN, W - MARGIN, round(H * 0.42))
    elif side == "left":
        box = (MARGIN, MARGIN, MARGIN + half, H - MARGIN)
    else:
        box = (W - MARGIN - half, MARGIN, W - MARGIN, H - MARGIN)

    bw, bh = box[2] - box[0], box[3] - box[1]
    fp = font_path()
    size = fit(lines, bw, bh, fp)
    f = ImageFont.truetype(fp, size)
    lh = size * (1 + GAP)
    total = lh * len(lines)

    scrim(im, (box[0], round(box[1] + (bh - total) / 2),
               box[2], round(box[1] + (bh + total) / 2)), dark)

    d = ImageDraw.Draw(im)
    y = box[1] + (bh - total) / 2
    for n, t in enumerate(lines):
        accent = (n == len(lines) - 1) or t in ("VS", "!=", "≠")
        bb = f.getbbox(t)
        x = box[0] + (bw - (bb[2] - bb[0])) / 2 - bb[0]
        d.text((x, y - bb[1]), t, font=f, fill=GOLD if accent else body)
        y += lh

    OUT.mkdir(exist_ok=True)
    dest = OUT / f"{vid}.jpg"
    im.save(dest, "JPEG", quality=88, optimize=True)
    kb = dest.stat().st_size / 1024
    print(f"{dest.name}  {size}px type  {kb:.0f} KB  {' / '.join(lines)}")


if __name__ == "__main__":
    main()
