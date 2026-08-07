#!/usr/bin/env python3
"""Find captions that overlap subject matter instead of sitting on clean background.

For every cue: render the caption layer alone to get its exact bbox, then look at
the caption-free frame underneath at both ends of the cue (pushes move the subject
during a shot, so a caption clear at the IN point can be buried by the OUT point).
Report the fraction of that bbox that is NOT background.
"""
from PIL import Image
from collections import Counter
import render as R
import render2 as R2

W, H, S = R2.W, R2.H, R2.S

def draw_cue(img, kind, kw):
    if kind == "cap1":
        R2.cap1(img, kw["lines"], kw.get("top",270), kw.get("color",R2.CHARCOAL),
                kw.get("size",96), kw.get("accent"))
    elif kind == "cap2":
        R2.cap2(img, kw["text"], kw.get("top",400), kw.get("color",R2.CHARCOAL))
    elif kind == "acc":
        R2.put(img, kw["text"], R2.F_BOLD, 150*S, R2.BRICK, W//2, kw["top"]*S, track=-0.02*150*S)
    elif kind == "onc":
        R2.put(img, kw["text"], R2.F_BOLD, 112*S, R2.CHARCOAL, W//2, kw["top"]*S, track=-0.015*112*S)
    elif kind == "sml":
        sz = kw.get("size",56)
        R2.put(img, kw["text"], R2.F_BOLD, sz*S, R2.CHARCOAL, kw["cx"]*S, kw["top"]*S, track=0.02*sz*S)
    elif kind == "cA":
        R2.card_a(img, kw["label"], kw["value"], kw["cx"], kw["cy"], kw.get("w",560))
    elif kind == "cB":
        R2.card_b(img, kw["l_lab"], kw["l_val"], kw["r_lab"], kw["r_val"], kw.get("cy",470))
    elif kind == "cC":
        R2.card_c(img, kw["text"], kw["cy"], kw.get("size",78))

def cue_bbox(kind, kw):
    layer = Image.new("RGBA", (W, H), (0,0,0,0))
    draw_cue(layer, kind, kw)
    return layer.getbbox()

_clean = {}
def clean_frame(t):
    k = round(t, 3)
    if k in _clean: return _clean[k]
    cut = next((c for c in R.CUTS if c[2] <= t < c[3]), R.CUTS[-1])
    _, gen, ti, to, bs, bdy, z0, z1, dx0, dx1, dy0, dy1 = cut
    p = R2.ease(min(1.0, max(0.0, (t-ti)/max(1e-6, to-ti))))
    z = z0 + (z1-z0)*p
    dx = (dx0 + (dx1-dx0)*p) * S
    dy = (dy0 + (dy1-dy0)*p) * S
    B = R2.base(gen, bs, bdy)
    cw, ch = W*R2.M/z, H*R2.M/z
    cx = max(0, min(B.width-cw,  (B.width-cw)/2  + dx*R2.M/z))
    cy = max(0, min(B.height-ch, (B.height-ch)/2 + dy*R2.M/z))
    im = B.crop((int(cx),int(cy),int(cx+cw),int(cy+ch))).resize((W,H), Image.LANCZOS)
    _clean[k] = im
    return im

def bg_of(im):
    small = im.resize((160, 284), Image.NEAREST).quantize(colors=8).convert("RGB")
    return Counter(small.getdata()).most_common(1)[0][0]

def busy(im, box, bg, tol=34):
    reg = im.crop(box)
    if reg.width == 0 or reg.height == 0: return 0.0
    px = reg.resize((max(1,reg.width//4), max(1,reg.height//4)), Image.NEAREST).getdata()
    n = sum(1 for r,g,b in px if abs(r-bg[0])+abs(g-bg[1])+abs(b-bg[2]) > tol)
    return n / len(px)

print(f"{'cue':>28} {'t_in':>6} {'t_out':>6} {'in%':>6} {'out%':>6}  verdict")
print("-"*78)
bad = []
for (a, b, kind, kw) in R.CUES:
    box = cue_bbox(kind, kw)
    if box is None: continue
    # pad the box a little - type needs breathing room, not just non-overlap
    pad = 14 * S
    box = (max(0,box[0]-pad), max(0,box[1]-pad), min(W,box[2]+pad), min(H,box[3]+pad))
    scores = []
    for t in (a + 0.05, b - 0.05):
        im = clean_frame(t)
        scores.append(busy(im, box, bg_of(im)))
    label = kw.get("text") or " / ".join(kw.get("lines", [])) or kw.get("value","") or kw.get("r_val","")
    v = "OK"
    if max(scores) > 0.28: v = "*** OBSTRUCTS"; bad.append((a,b,kind,kw,label,max(scores)))
    elif max(scores) > 0.12: v = "  tight"
    print(f"{label[:28]:>28} {a:6.2f} {b:6.2f} {scores[0]*100:5.1f}% {scores[1]*100:5.1f}%  {v}")

print("\n" + "="*78)
print(f"{len(bad)} cue(s) obstruct the subject:")
for a,b,kind,kw,label,s in bad:
    print(f"  {a:6.2f}-{b:6.2f}  {kind:5}  {label[:40]:40} {s*100:.0f}% covered")
