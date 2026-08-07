#!/usr/bin/env python3
"""Deadbeat short - render stills + captions to frames, mux with trimmed VO."""
import os, subprocess, math, shutil
from PIL import Image, ImageDraw, ImageFont

SCRATCH = "/tmp/claude-0/-home-user-Ababuyenga/1a242984-1ffd-566d-b690-bc7ad725ab62/scratchpad"
UP = "/root/.claude/uploads/1a242984-1ffd-566d-b690-bc7ad725ab62"
FF = "/usr/local/lib/python3.11/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2"
VO = f"{UP}/25bf6850-ElevenLabs_20260807T02_21_51_Ahmed_new_1_gen_sp100_s50_sb86_v3.mp3"
W, H, FPS = 1080, 1920, 30

CREAM    = (245, 239, 220)
CHARCOAL = (62, 43, 35)
BRICK    = (179, 74, 50)
SAND     = (217, 184, 124)

F_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
F_REG  = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SQUEEZE = 0.74          # horizontal compression -> condensed look

GEN = {n: f"{UP}/{p}" for n, p in {
    1:"28bdf1db-IMG_6561.jpeg",  2:"76b77b31-IMG_6562.jpeg",  3:"5c819ba0-IMG_6563.jpeg",
    4:"963e9b67-IMG_6564.jpeg",  5:"42e275be-IMG_6565.jpeg",  6:"20a52469-IMG_6566.jpeg",
    7:"15f4ec58-IMG_6567.jpeg",  8:"9832a5c3-IMG_6568.jpeg",  9:"d7e5a955-IMG_6569.jpeg",
    10:"09047872-IMG_6570.jpeg", 11:"eeb27da0-IMG_6571.jpeg", 12:"63a1c65d-IMG_6572.jpeg",
    13:"a29aae9c-IMG_6573.jpeg", 14:"5314e6b6-IMG_6574.jpeg", 15:"e5e0c376-IMG_6575.jpeg",
    16:"a4a207aa-IMG_6576.jpeg", 17:"a5e54915-IMG_6577.jpeg", 18:"28a39e69-IMG_6578.jpeg",
}.items()}

# ---------------------------------------------------------------- audio trim
SIL = [(2.135261,2.859977),(4.077166,5.042698),(6.259093,7.040295),(8.317120,8.599932),
       (9.369683,9.998662),(10.829070,11.256463),(12.366984,13.632948),(15.114127,16.085669),
       (16.328594,16.811066),(18.416757,19.498821),(20.816508,21.503719),(23.122834,23.795102),
       (24.681066,25.244671),(26.363628,26.874649),(27.843084,28.874898),(30.224989,31.429048),
       (33.465782,34.523878),(35.221882,35.483696),(36.348345,37.706259),(39.679478,41.096349),
       (43.700680,44.492925),(45.238912,46.357755),(48.015714,48.359161),(48.996349,49.728639),
       (50.620227,51.840181),(53.750658,55.074989),(56.858798,58.062086),(59.047619,59.803107),
       (60.954354,62.247007),(63.634853,65.274785),(65.957392,66.495669),(67.981610,69.014535),
       (69.450454,70.239705)]
DUR = 70.27
PROTECT = {1: 0.966, 29: 1.000}          # index into SIL: hook pause, "Be worthless" pause
CAP = 0.5

def build_keep():
    keep, cur = [], 0.0
    for i, (s, e) in enumerate(SIL):
        if s > cur: keep.append((cur, s))
        tgt = PROTECT.get(i, CAP)
        keep.append((s, min(e, s + tgt)))
        cur = e
    if cur < DUR: keep.append((cur, DUR))
    return [(a, b) for a, b in keep if b > a + 1e-6]

KEEP = build_keep()
NEWDUR = sum(b - a for a, b in KEEP)

def remap(t):
    """old timeline -> trimmed timeline"""
    acc = 0.0
    for a, b in KEEP:
        if t < a:  return acc
        if t <= b: return acc + (t - a)
        acc += b - a
    return acc

# ---------------------------------------------------------------- text utils
_fc = {}
def font(path, size):
    k = (path, size)
    if k not in _fc: _fc[k] = ImageFont.truetype(path, size)
    return _fc[k]

def cond_text(img, text, size, color, cx, top, bold=True, squeeze=SQUEEZE, alpha=255):
    """Render text, squeeze horizontally, paste centred on cx."""
    f = font(F_BOLD if bold else F_REG, size)
    tmp = Image.new("RGBA", (W * 2, int(size * 1.6)), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    d.text((10, 0), text, font=f, fill=color + (alpha,))
    bb = tmp.getbbox()
    if not bb: return 0
    tmp = tmp.crop(bb)
    nw = max(1, int(tmp.width * squeeze))
    tmp = tmp.resize((nw, tmp.height), Image.LANCZOS)
    img.alpha_composite(tmp, (int(cx - nw / 2), int(top)))
    return tmp.height

def cap1(img, lines, top=270, color=CHARCOAL, size=96, cx=W//2, accent=None):
    y = top
    for ln in lines:
        col = BRICK if (accent and ln in accent) else color
        h = cond_text(img, ln, size, col, cx, y)
        y += int(size * 0.98)

def cap2(img, text, top=400, color=CHARCOAL, size=46, cx=W//2, alpha=204):
    cond_text(img, text, size, color, cx, top, bold=False, squeeze=0.94, alpha=alpha)

# ---------------------------------------------------------------- cards
def card_a(img, label, value, cx, cy, w=560, h=170):
    x0, y0 = int(cx - w/2), int(cy - h/2)
    d = ImageDraw.Draw(img)
    d.rectangle([x0, y0, x0+w, y0+h], fill=CREAM + (255,), outline=CHARCOAL + (255,), width=3)
    f = font(F_REG, 30)
    d.text((x0+26, y0+30), " ".join(label), font=f, fill=CHARCOAL + (255,))
    tmp = Image.new("RGBA", (w, 110), (0,0,0,0))
    cond_text(tmp, value, 66, CHARCOAL, w//2, 0)
    img.alpha_composite(tmp, (x0, y0+78))
    d.line([x0+26, y0+h-22, x0+w-26, y0+h-22], fill=CHARCOAL + (255,), width=2)

def card_b(img, l_lab, l_val, r_lab, r_val, cx=W//2, cy=430, w=900, h=290):
    x0, y0 = int(cx - w/2), int(cy - h/2)
    d = ImageDraw.Draw(img)
    d.rectangle([x0, y0, x0+w, y0+h], fill=CREAM + (255,), outline=CHARCOAL + (255,), width=3)
    split = x0 + int(w * 0.38)
    d.line([split, y0+16, split, y0+h-16], fill=CHARCOAL + (255,), width=2)
    f = font(F_REG, 28)
    d.text((x0+30, y0+26), " ".join(l_lab), font=f, fill=CHARCOAL + (255,))
    d.text((split+34, y0+26), " ".join(r_lab), font=f, fill=CHARCOAL + (255,))
    t1 = Image.new("RGBA", (split-x0, 110), (0,0,0,0))
    cond_text(t1, l_val, 62, CHARCOAL, (split-x0)//2, 0)
    img.alpha_composite(t1, (x0, y0+120))
    t2 = Image.new("RGBA", (x0+w-split, 210), (0,0,0,0))
    cond_text(t2, r_val, 150, BRICK, (x0+w-split)//2, 0)
    img.alpha_composite(t2, (split, y0+86))

def card_c(img, text, cy, size=78, cx=W//2, rule=0.60):
    h = cond_text(img, text, size, CHARCOAL, cx, cy)
    d = ImageDraw.Draw(img)
    rw = int(W * rule)
    yy = cy + h + 22
    d.line([cx-rw//2, yy, cx+rw//2, yy], fill=CHARCOAL + (255,), width=9)

# ---------------------------------------------------------------- cut map
# (cut, gen, t_in, t_out, base_scale, base_dy, z0, z1, dx0, dx1, dy0, dy1)
CUTS = [
 (1, 1, 0.00, 4.50, 1.00,   0, 1.00, 1.06,  0,0,  0,0),
 (2, 2, 4.50, 6.55, 1.00,   0, 1.00, 1.07,  0,0,  0,0),
 (3, 3, 6.55, 9.65, 1.25, 430, 1.00, 1.00,  0,0,  0,0),
 (4, 4, 9.65,12.65, 1.00,   0, 1.07, 1.00,  0,0,  0,0),
 (5, 5,12.65,15.60, 1.00,   0, 1.00, 1.05,  0,0,  0,0),
 (6, 6,15.60,19.00, 1.00,   0, 1.00, 1.09,  0,0,  0,0),
 (7, 7,19.00,23.40, 1.00,   0, 1.00, 1.06,  0,0,  0,20),
 (8, 8,23.40,27.90, 1.00,   0, 1.00, 1.00,  0,0,  0,0),
 (9, 9,27.90,31.00, 1.00,   0, 1.00, 1.00,  0,0,  0,0),
 (10,10,31.00,34.40, 1.00,  0, 1.00, 1.11,  0,0,  0,0),
 (11,11,34.40,37.00, 1.00,  0, 1.00, 1.08,  0,0,  0,0),
 (12,12,37.00,40.50, 1.00,  0, 1.00, 1.05,  0,0,  0,0),
 (13,13,40.50,44.10, 1.22, 210, 1.00, 1.04,  0,0,  0,0),
 (14,13,44.10,46.00, 1.22, 210, 1.40, 1.40, 130,130, 40,40),
 (15,14,46.00,49.35, 1.00,  0, 1.00, 1.00,  0,30,  0,0),
 (16,15,49.35,51.20, 1.00,  0, 1.00, 1.00,  0,0,  0,0),
 (17,16,51.20,54.40, 1.00,  0, 1.00, 1.05,  0,0,  0,0),
 (18,16,54.40,57.40, 1.00,  0, 1.25, 1.25,  0,0,  60,60),
 (19,17,57.40,61.50, 1.00,  0, 1.00, 1.04,  0,0,  0,0),
 (20,17,61.50,64.20, 1.00,  0, 1.20, 1.20,  0,0, -90,-90),
 (21,18,64.20,68.40, 1.00,  0, 1.00, 1.04,  0,0,  0,0),
 (22,18,68.40,70.27, 1.00,  0, 1.30, 1.30, 120,120,-150,-150),
]

# ---------------------------------------------------------------- cue sheet
CUES = [
 (0.40, 2.86, "cap1",  dict(lines=["THE CARD INDUSTRY","CALLS YOU"], top=126, size=84)),
 (1.90, 2.86, "acc",   dict(text="A DEADBEAT", top=316, size=122)),
 (2.86, 4.30, "cap1",  dict(lines=["FOR PAYING IN FULL"], top=270)),
 (4.60, 6.35, "onc",   dict(text="DEADBEAT", top=790)),
 (5.00, 6.35, "cap1",  dict(lines=["THEIR WORD.","NOT MINE."], top=150, color=CREAM)),
 (6.95, 9.45, "cap1",  dict(lines=["NOT AN INSULT"], top=250)),
 (7.90, 9.45, "cap2",  dict(text="a category", top=380)),
 (10.00,12.45,"cap1",  dict(lines=["YOU EARNED","THEM NOTHING"], top=250)),
 (11.00,12.45,"cA",    dict(label="INTEREST EARNED", value="£0.00", cx=540, cy=1520, w=520, anchor=True)),
 (13.25,15.40,"cap1",  dict(lines=["YOU WERE NEVER","THE CUSTOMER"], top=250)),
 (16.35,18.80,"cap1",  dict(lines=["THE CARD ISN'T","THE PRODUCT"], top=110, size=88)),
 (17.40,18.80,"cap2",  dict(text="the balance is", top=300)),
 (19.50,23.20,"cap1",  dict(lines=["THE LIMIT WENT UP","ON ITS OWN"], top=230)),
 (20.30,23.20,"cA",    dict(label="LIMIT", value="£2,000 → £3,500", cx=540, cy=1690, w=660, anchor=True)),
 (21.60,23.20,"cap2",  dict(text="you didn't ask. it arrived.", top=450)),
 (24.20,26.40,"cap1",  dict(lines=["THE CASHBACK","IS BAIT"], top=250)),
 (25.40,27.70,"sml",   dict(text="1% BACK", cx=250, top=1180)),
 (28.60,30.80,"cB",    dict(l_lab="CASHBACK", l_val="1%", r_lab="APR", r_val="24%", cy=470)),
 (31.60,34.20,"cap1",  dict(lines=["ITS OWN","LITTLE BOX"], top=200)),
 (32.30,34.20,"sml",   dict(text="£25", cx=756, top=1442, size=58, anchor=True)),
 (32.30,34.20,"sml",   dict(text="MINIMUM PAYMENT", cx=372, top=1452, size=34, anchor=True)),
 (34.60,36.80,"cap1",  dict(lines=["NONE OF IT","IS AN ACCIDENT"], top=230)),
 (37.90,40.30,"cap1",  dict(lines=["THAT IS","THE DESIGN"], top=230, accent=["THE DESIGN"])),
 (41.10,43.90,"cap1",  dict(lines=["RIBA ISN'T A FEE","YOU TRIGGER"], top=230)),
 (44.60,45.80,"cap1",  dict(lines=["IT'S THE","REVENUE MODEL"], top=230, accent=["REVENUE MODEL"])),
 (46.60,49.15,"cap1",  dict(lines=["A REAL SALE","PROFITS ONCE"], top=230)),
 (47.90,49.15,"cC",    dict(text="PROFIT: FIXED AT THE SALE", cy=1560, size=62)),
 (49.60,51.00,"cap1",  dict(lines=["THEN IT STOPS"], top=270)),
 (51.90,54.20,"cap1",  dict(lines=["RIBA GROWS","WHILE YOU SLEEP"], top=230)),
 (54.80,57.20,"cap1",  dict(lines=["TIME IS THE","INGREDIENT"], top=200)),
 (55.90,57.20,"cC",    dict(text="RIBA: PRICED IN TIME", cy=430, size=62)),
 (58.10,59.40,"cC",    dict(text="BALANCE £0.00", cy=300, size=76)),
 (59.40,61.30,"cap1",  dict(lines=["YOU'RE WORTHLESS","TO THEM"], top=300, size=78)),
 (62.30,64.00,"acc",   dict(text="BE WORTHLESS", top=300)),
 (65.00,68.20,"cap1",  dict(lines=["PART 3","THE CARD THAT PASSES"], top=250, size=84)),
 (69.00,70.10,"cap1",  dict(lines=["FOLLOW"], top=300, size=110, accent=["FOLLOW"])),
]

# ---------------------------------------------------------------- rendering
_src = {}
def load(gen, scale, dy):
    k = (gen, scale, dy)
    if k in _src: return _src[k]
    im = Image.open(GEN[gen]).convert("RGB")
    r = max(W / im.width, H / im.height) * scale
    im = im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)
    canvas = Image.new("RGB", (W, H), CREAM)
    canvas.paste(im, ((W - im.width) // 2, (H - im.height) // 2 + int(dy)))
    _src[k] = canvas
    return canvas

def ease(p):  return 1 - (1 - p) ** 3

def frame_at(t_old):
    cut = None
    for c in CUTS:
        if c[2] <= t_old < c[3]: cut = c; break
    if cut is None: cut = CUTS[-1]
    _, gen, ti, to, bs, bdy, z0, z1, dx0, dx1, dy0, dy1 = cut
    p = ease(min(1.0, max(0.0, (t_old - ti) / max(1e-6, to - ti))))
    z  = z0 + (z1 - z0) * p
    dx = dx0 + (dx1 - dx0) * p
    dy = dy0 + (dy1 - dy0) * p
    base = load(gen, bs, bdy)
    zw, zh = int(W * z), int(H * z)
    im = base.resize((zw, zh), Image.LANCZOS)
    left = (zw - W) // 2 + int(dx)
    top  = (zh - H) // 2 + int(dy)
    left = max(0, min(zw - W, left)); top = max(0, min(zh - H, top))
    im = im.crop((left, top, left + W, top + H)).convert("RGBA")

    for (a, b, kind, kw) in CUES:
        if not (a <= t_old < b): continue
        if kind == "cap1":
            cap1(im, kw["lines"], kw.get("top",270), kw.get("color",CHARCOAL),
                 kw.get("size",96), accent=kw.get("accent"))
        elif kind == "cap2":
            cap2(im, kw["text"], kw.get("top",400), kw.get("color",CHARCOAL))
        elif kind == "acc":
            cond_text(im, kw["text"], 150, BRICK, W//2, kw["top"])
        elif kind == "onc":
            cond_text(im, kw["text"], 112, CHARCOAL, W//2, kw["top"])
        elif kind == "sml":
            cond_text(im, kw["text"], kw.get("size",56), CHARCOAL, kw["cx"], kw["top"])
        elif kind == "cA":
            card_a(im, kw["label"], kw["value"], kw["cx"], kw["cy"], kw.get("w",560))
        elif kind == "cB":
            card_b(im, kw["l_lab"], kw["l_val"], kw["r_lab"], kw["r_val"], cy=kw.get("cy",430))
        elif kind == "cC":
            card_c(im, kw["text"], kw["cy"], kw.get("size",78))
    return im.convert("RGB")

def main():
    out = f"{SCRATCH}/frames"
    shutil.rmtree(out, ignore_errors=True); os.makedirs(out)
    # build old-time samples that map onto the trimmed timeline
    n = int(NEWDUR * FPS)
    inv = []
    acc = 0.0
    for a, b in KEEP:
        inv.append((acc, acc + (b - a), a)); acc += b - a
    def to_old(tn):
        for s, e, a in inv:
            if s <= tn <= e: return a + (tn - s)
        return DUR
    print(f"trimmed duration {NEWDUR:.2f}s  frames {n}")
    for i in range(n):
        tn = i / FPS
        frame_at(to_old(tn)).save(f"{out}/f{i:05d}.jpg", quality=94)
        if i % 200 == 0: print(f"  {i}/{n}", flush=True)
    # trimmed audio
    parts = "+".join([f"between(t,{a},{b})" for a, b in KEEP])
    subprocess.run([FF, "-y", "-i", VO, "-af",
                    f"aselect='{parts}',asetpts=N/SR/TB", "-ac", "1",
                    f"{SCRATCH}/vo-trim.wav"], check=True, capture_output=True)
    subprocess.run([FF, "-y", "-framerate", str(FPS), "-i", f"{out}/f%05d.jpg",
                    "-i", f"{SCRATCH}/vo-trim.wav", "-c:v", "libx264", "-preset", "medium",
                    "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", f"{SCRATCH}/deadbeat-short.mp4"], check=True, capture_output=True)
    print("done")

if __name__ == "__main__":
    main()
