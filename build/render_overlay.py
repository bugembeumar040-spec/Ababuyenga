"""Render the caption/burn-in layer and stream it to ffmpeg as raw RGBA.

Text is baked once into RGBA sprites (outline + soft ink shadow included),
then only transformed per frame, so the whole 1404-frame layer renders in
seconds. Sprites carry their padding inset so layout anchors on the TEXT
box, not on the padded bitmap -- getting that wrong is what made the
two-line CAP1 blocks collide with CAP2.

Writes raw RGBA to stdout, or PNGs to fr/ with --probe.
"""
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from edl import FPS, W, H, TOTAL_F, scenes
from captions import EVENTS, SCRIM, CREAM, INK, ACCENT

ANTON = "fonts/Anton-Regular.ttf"
NARROW = "fonts/ArchivoNarrow-Bold.ttf"

MARGIN = 84
MAXW = W - 2 * MARGIN                      # 912px type column

SLOT_Y = {                                 # (y, anchor) on the TEXT box
    "cap1": (1120, "top"),
    "cap2": (1440, "top"),
    "print": (700, "center"),
}


def font(path, size, weight=None):
    f = ImageFont.truetype(path, size)
    if weight is not None:
        try:
            f.set_variation_by_axes([weight])
        except Exception:
            pass
    return f


def ease_out(t):
    return 1 - (1 - t) ** 3


def split_runs(runs):
    """Split colour runs on newlines -> lines, each a list of runs."""
    lines, cur = [], []
    for text, col in runs:
        for i, p in enumerate(text.split("\n")):
            if i:
                lines.append(cur)
                cur = []
            if p:
                cur.append((p, col))
    lines.append(cur)
    return [l for l in lines if l] or [[("", CREAM)]]


def measure(lines, f, tracking=0):
    return [sum(f.getlength(t) + tracking * len(t) for t, _ in runs) for runs in lines]


def fit(lines, path, start, minsize, tracking=0, weight=None):
    size = start
    while size > minsize:
        f = font(path, size, weight)
        if max(measure(lines, f, tracking)) <= MAXW:
            return f
        size -= 2
    return font(path, minsize, weight)


def draw_block(lines, f, leading, tracking=0, stroke=0):
    """Coloured runs -> tight RGBA sprite. Returns (img, inset)."""
    widths = measure(lines, f, tracking)
    asc, desc = f.getmetrics()
    lh = int((asc + desc) * leading)
    pad = stroke + 8
    img = Image.new("RGBA", (int(max(widths)) + pad * 2, lh * len(lines) + pad * 2),
                    (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i, runs in enumerate(lines):
        x = (img.width - widths[i]) / 2
        y = pad + i * lh
        for text, col in runs:
            fill = col if len(col) == 4 else col + (255,)
            if tracking:
                for ch in text:
                    d.text((x, y), ch, font=f, fill=fill,
                           stroke_width=stroke, stroke_fill=INK + (255,))
                    x += f.getlength(ch) + tracking
            else:
                d.text((x, y), text, font=f, fill=fill,
                       stroke_width=stroke, stroke_fill=INK + (255,))
                x += f.getlength(text)
    return img, pad


def with_shadow(sprite, inset, blur=16, alpha=145, dy=7):
    """Soft ink shadow so cream type survives a cream card or a white page."""
    pad = blur * 3
    out = Image.new("RGBA", (sprite.width + pad * 2, sprite.height + pad * 2), (0, 0, 0, 0))
    sh = Image.new("RGBA", out.size, (0, 0, 0, 0))
    mask = sprite.split()[3].point(lambda a: min(255, int(a * alpha / 255)))
    sh.paste(Image.new("RGBA", sprite.size, INK + (255,)), (pad, pad + dy), mask)
    out = Image.alpha_composite(out, sh.filter(ImageFilter.GaussianBlur(blur)))
    out.paste(sprite, (pad, pad), sprite)
    return out, inset + pad


def stack(top, top_inset, bot, bot_inset, gap):
    """Stack a small label over a big value, keeping a usable inset."""
    w = max(top.width, bot.width)
    img = Image.new("RGBA", (w, top.height + gap + bot.height), (0, 0, 0, 0))
    img.paste(top, ((w - top.width) // 2, 0), top)
    img.paste(bot, ((w - bot.width) // 2, top.height + gap), bot)
    return img, top_inset


def build_sprite(ev):
    kind = ev["kind"]
    lines = split_runs(ev["runs"])

    if kind == "cap1":
        s, ins = draw_block(lines, fit(lines, ANTON, 106, 62), 1.02, stroke=5)
        return with_shadow(s, ins, 18, 150, 8)

    if kind == "cap2":
        s, ins = draw_block(lines, fit(lines, NARROW, 50, 30, weight=620), 1.16, stroke=3)
        return with_shadow(s, ins, 12, 130, 5)

    if kind == "hero":                                    # DEADBEAT
        s, ins = draw_block(lines, fit(lines, ANTON, 210, 120), 1.0, stroke=7)
        return with_shadow(s, ins, 26, 175, 10)

    if kind == "slam":                                    # 24.9% APR
        s, ins = draw_block(lines, fit(lines, ANTON, ev.get("vsize", 150), 90), 1.0, stroke=6)
        return with_shadow(s, ins, 24, 170, 9)

    # num / print: a small tracked label over a big value
    val_f = fit(lines, ANTON, ev.get("vsize", 100), 52)
    val, v_ins = draw_block(lines, val_f, 1.02, stroke=0 if kind == "print" else 5)

    if not ev.get("label"):
        return with_shadow(val, v_ins, 18, 185, 8)

    lab_col = INK + (205,) if kind == "print" else CREAM + (255,)
    lab, l_ins = draw_block([[(ev["label"], lab_col)]], font(NARROW, 38, 700),
                            1.0, tracking=7, stroke=0 if kind == "print" else 5)
    blk, ins = stack(lab, l_ins, val, v_ins, 14)
    if kind == "print":
        return with_shadow(blk, ins, 10, 55, 4)
    return with_shadow(blk, ins, 18, 185, 8)


def anim(ev, t):
    """-> (opacity, scale, dy) at time t, or None when the element is off."""
    tin, tout = ev["tin"], ev["tout"]
    if t < tin or t >= tout:
        return None
    kind, dt = ev["kind"], t - tin
    if kind == "hero":
        ind, s0, s1, over = 7 / FPS, 0.86, 1.0, 1.045
    elif kind == "slam":
        ind, s0, s1, over = 5 / FPS, 1.26, 1.0, 0.985
    else:
        ind, s0, s1, over = 5 / FPS, 0.978, 1.0, 1.0

    if dt < ind:
        p = ease_out(dt / ind)
        if over != 1.0:
            sc = (s0 + (over - s0) * p if p < 0.72
                  else over + (s1 - over) * ((p - 0.72) / 0.28))
        else:
            sc = s0 + (s1 - s0) * p
        dy = int(round(16 * (1 - p))) if kind in ("cap1", "cap2", "num") else 0
        return min(1.0, dt / (2.5 / FPS)), sc, dy

    outd = 4 / FPS
    if t > tout - outd:
        return max(0.0, (tout - t) / outd), s1, 0
    return 1.0, s1, 0


def scrim_mask(peak):
    """Bottom gradient: clear at 44% height, full by 86%."""
    col = Image.new("L", (1, H))
    px = col.load()
    y0, y1 = int(H * 0.44), int(H * 0.86)
    for y in range(H):
        u = 0.0 if y <= y0 else 1.0 if y >= y1 else (y - y0) / (y1 - y0)
        px[0, y] = int(round(255 * (u * u * (3 - 2 * u)) * peak))
    return col.resize((W, H))


def main():
    probe = "--probe" in sys.argv
    want = ({int(a) for a in sys.argv[sys.argv.index("--probe") + 1].split(",")}
            if probe else set())

    built = []
    for ev in EVENTS:
        sprite, inset = build_sprite(ev)
        y, anchor = SLOT_Y.get(ev.get("slot"), (ev.get("y", 1120), ev.get("yanchor", "top")))
        built.append((ev, sprite, inset, y, anchor))

    scene_at = []
    for s in scenes():
        scene_at += [s["name"]] * s["frames"]

    scrims = {}
    for name, peak in SCRIM.items():
        plate = Image.new("RGBA", (W, H), INK + (255,))
        plate.putalpha(scrim_mask(peak))
        scrims[name] = plate

    a07 = next(s for s in scenes() if s["name"] == "A07")
    out = sys.stdout.buffer

    for fi in range(TOTAL_F):
        t = fi / FPS
        frame = scrims[scene_at[fi]].copy()

        for ev, sprite, inset, cy, anchor in built:
            a = anim(ev, t)
            if a is None:
                continue
            op, sc, dy = a
            if ev["kind"] == "print":
                # ride the shot's 10% push so it stays printed on the paper
                sc *= 1.0 + 0.10 * ((t - a07["tin"]) / a07["length"])
            s, ins = sprite, inset
            if abs(sc - 1.0) > 0.002:
                s = sprite.resize((max(1, round(sprite.width * sc)),
                                   max(1, round(sprite.height * sc))), Image.LANCZOS)
                ins = inset * sc
            if op < 0.999:
                s = s.copy()
                s.putalpha(s.split()[3].point(lambda v, o=op: int(v * o)))

            x = round((W - s.width) / 2)
            if anchor == "top":
                y = round(cy - ins) + dy
            elif anchor == "bottom":
                y = round(cy - s.height + ins) + dy
            else:
                y = round(cy - s.height / 2) + dy
            frame.alpha_composite(s, (x, y))

        if probe:
            if fi in want:
                frame.save(f"fr/ov_{fi}.png")
            if fi > max(want):
                break
        else:
            out.write(frame.tobytes())

    if not probe:
        out.flush()


if __name__ == "__main__":
    main()
