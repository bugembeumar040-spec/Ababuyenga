#!/usr/bin/env python3
"""
Caption burn-in for "You Sink to Your Room".

Follows CAPTION SPEC in companyyoukeeppromptpack.txt: heavy condensed sans,
uppercase CAP 1 at 62% height, CAP 2 at 76%, cream fill with a navy outline,
accent word in terracotta. Six caption moments, not sixteen. Scene 12 carries
the Ibn al-Qayyim attribution as a small lower-third, cream on navy, no accent.

Every caption clears 200ms before its cut.
"""
import os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BUILD = os.path.dirname(os.path.abspath(__file__))
CAP   = os.path.join(BUILD, "cap");  os.makedirs(CAP, exist_ok=True)
OUT   = os.path.join(BUILD, "out")

W, H = 1080, 1920
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
CONDENSE = 0.84                 # squeeze to emulate a heavy condensed face

CREAM      = (245, 239, 226, 255)   # #F5EFE2
NAVY       = (20,  36,  51, 255)    # #142433
TERRACOTTA = (232, 98,  47, 255)    # #E8622F

Y_CAP1 = int(0.62 * H)
Y_CAP2 = int(0.76 * H)
MAXW   = int(W * 0.90)

def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode != 0:
        print("FAILED:", cmd[:400], file=sys.stderr)
        print(r.stderr[-3000:], file=sys.stderr)
        sys.exit(1)
    return r.stdout


def fit_font(runs, max_w, start=132):
    """largest size whose condensed width fits max_w"""
    text = "".join(t for t, _ in runs)
    for size in range(start, 30, -2):
        f = ImageFont.truetype(FONT, size)
        w = f.getbbox(text)[2] - f.getbbox(text)[0]
        if w * CONDENSE <= max_w:
            return f, size
    return ImageFont.truetype(FONT, 30), 30


def render_line(runs, y_center, out_path, canvas=None, font=None,
                stroke=6, x_offsets=None, shadow=True):
    """
    runs: list of (text, fill). Drawn as one line, condensed, centred on y_center.
    Returns the canvas so several calls can compose onto one frame.
    """
    img = canvas if canvas is not None else Image.new("RGBA", (W, H), (0, 0, 0, 0))
    f = font or fit_font(runs, MAXW)[0]

    text  = "".join(t for t, _ in runs)
    bbox  = f.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad = stroke * 3

    # draw at full width on a scratch layer, then condense horizontally.
    # runs advance by their font advance so words never reflow between frames;
    # a fully transparent fill draws nothing at all (outline included).
    lay  = Image.new("RGBA", (tw + pad * 2, th + pad * 2), (0, 0, 0, 0))
    d    = ImageDraw.Draw(lay)
    x    = pad - bbox[0]
    ytop = pad - bbox[1]
    for t, fill in runs:
        if fill[3] > 0:
            d.text((x, ytop), t, font=f, fill=fill,
                   stroke_width=stroke, stroke_fill=NAVY)
        x += f.getlength(t)

    new_w = max(1, int(lay.width * CONDENSE))
    lay   = lay.resize((new_w, lay.height), Image.LANCZOS)

    px = (W - lay.width) // 2
    py = y_center - lay.height // 2

    if shadow:
        sh_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dark = Image.new("RGBA", lay.size, (0, 0, 0, 0))
        dark.paste((0, 0, 0, 190), (0, 0), lay.split()[3])
        sh_layer.paste(dark, (px, py + 8), dark)
        sh_layer = sh_layer.filter(ImageFilter.GaussianBlur(14))
        img = Image.alpha_composite(img, sh_layer)

    top = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    top.paste(lay, (px, py), lay)
    img = Image.alpha_composite(img, top)
    img.save(out_path)
    return img


def render_lower_third(text, out_path):
    """small cream-on-navy attribution slab, no accent colour"""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    f = ImageFont.truetype(FONT, 40)
    bbox = f.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    padx, pady = 34, 22
    bw, bh = tw + padx * 2, th + pady * 2
    slab = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    ImageDraw.Draw(slab).rounded_rectangle([0, 0, bw - 1, bh - 1], radius=10,
                                           fill=(20, 36, 51, 234))
    ImageDraw.Draw(slab).text((padx - bbox[0], pady - bbox[1]), text,
                              font=f, fill=CREAM)
    img.paste(slab, ((W - bw) // 2, int(0.83 * H)), slab)
    img.save(out_path)


# ------------------------------------------------------------------ moments --
# (png, start, end) — times are absolute on the finished timeline
M = []

render_line([("WATCH WHAT HAPPENED", CREAM)], Y_CAP1, f"{CAP}/c03.png")
M.append(("c03.png", 10.230, 11.906))

render_line([("HE STOPS", CREAM)], Y_CAP1, f"{CAP}/c05.png")
M.append(("c05.png", 17.610, 19.486))

# accent word is SINK
render_line([("YOU ", CREAM), ("SINK", TERRACOTTA), (" TO YOUR ROOM", CREAM)],
            Y_CAP1, f"{CAP}/c09.png")
M.append(("c09.png", 31.700, 33.444))

render_line([("COMFORTABLE IS CONTAGIOUS", CREAM)], Y_CAP1, f"{CAP}/c11.png")
M.append(("c11.png", 39.990, 41.785))

render_lower_third("Ibn al-Qayyim, al-Fawāʾid", f"{CAP}/c12.png")
M.append(("c12.png", 42.340, 48.249))

# scene 13 builds the three in sequence, at fixed positions so nothing reflows
BUILD_RUNS = [("TIME", CREAM), ("  →  ", TERRACOTTA), ("HEART", CREAM),
              ("  →  ", TERRACOTTA), ("EVERYTHING", CREAM)]
bfont, _ = fit_font(BUILD_RUNS, MAXW)
INVIS = (0, 0, 0, 0)
for k, (png, t0) in enumerate([("c13a.png", 49.348), ("c13b.png", 50.698),
                               ("c13c.png", 51.898)]):
    shown = 2 * k + 1
    runs = [(t, fill if i < shown else INVIS)
            for i, (t, fill) in enumerate(BUILD_RUNS)]
    # invisible runs keep their advance so visible words never move
    render_line(runs, Y_CAP1, f"{CAP}/{png}", font=bfont,
                stroke=6 if k >= 0 else 6)
    M.append((png, t0, 53.698))

render_line([("WHO DO I BECOME", CREAM)], Y_CAP1, f"{CAP}/c15a.png")
M.append(("c15a.png", 58.830, 61.595))
render_line([("IN THAT ROOM?", CREAM)], Y_CAP2, f"{CAP}/c15b.png")
M.append(("c15b.png", 60.352, 61.595))

# --------------------------------------------------------------- composite --
inputs = f'-i "{OUT}/picture.mp4" ' + " ".join(f'-i "{CAP}/{p}"' for p, _, _ in M)
chain, cur = [], "0:v"
for i, (p, t0, t1) in enumerate(M, start=1):
    nxt = f"v{i}"
    chain.append(f"[{cur}][{i}:v]overlay=0:0:enable='between(t,{t0:.3f},{t1:.3f})'[{nxt}]")
    cur = nxt
chain.append(f"[{cur}]fade=t=out:st=67.09:d=0.20[vout]")

sh(f'ffmpeg -y -v error {inputs} -filter_complex "{";".join(chain)}" '
   f'-map "[vout]" -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -r 24 '
   f'"{OUT}/picture_captioned.mp4"')
print("captioned picture written")
for p, t0, t1 in M:
    print(f"  {p:<10} {t0:>7.3f} -> {t1:>7.3f}")
