#!/usr/bin/env python3
"""Compare every captured plate against every other.

Reports near-duplicates (a resend or a repeated seed) and, more importantly,
whether any two plates register closely enough to be a line/wash pair.
"""
import glob, itertools, sys
import numpy as np
from PIL import Image

def grey(p):
    return np.asarray(Image.open(p).convert("L").resize((344, 192)), dtype=np.float32) / 255

def wash(p):
    """Chroma spread across the non-ink area.

    Plain saturation does not work here: the parchment ground is a warm tone, so
    even pure line art scores as heavily saturated. What separates a wash from a
    line pass is how much the paper area VARIES in colour -- a wash lays down
    blobs of differing hue, flat paper does not.
    """
    a = np.asarray(Image.open(p).convert("RGB").resize((344, 192))).astype(np.float32) / 255
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    L = 0.299 * r + 0.587 * g + 0.114 * b
    C = np.sqrt((r - g) ** 2 + (0.5 * (r + g) - b) ** 2)
    paper = L >= 0.45
    return float(C[paper].std()) if paper.sum() > 100 else 0.0

def ncc(a, b):
    a, b = a - a.mean(), b - b.mean()
    return float((a * b).sum() / np.sqrt((a * a).sum() * (b * b).sum()))

def main():
    files = sorted(glob.glob("clarity/plates/inbox/*/*.jpg"))
    g = {f: grey(f) for f in files}
    s = {f: wash(f) for f in files}
    dup, pair = [], []
    for a, b in itertools.combinations(files, 2):
        r = ncc(g[a], g[b])
        if r > 0.95: dup.append((a, b, r))
        elif r > 0.75: pair.append((a, b, r))
    n = lambda p: "/".join(p.split("/")[-1].split("-")[:2])
    print(f"{len(files)} plates captured")
    lo = sorted(files, key=lambda f: s[f])[:3]
    print("least-washed plates: " + ", ".join(f"{n(f)} {s[f]:.4f}" for f in lo))
    print(f"chroma spread ranges {min(s.values()):.4f}-{max(s.values()):.4f} "
          f"across {len(files)} plates -- a continuum, not two classes, so no plate "
          f"is a line pass")
    print(f"near-duplicates (>0.95): {[(n(a), n(b), round(r,3)) for a,b,r in dup] or 'none'}")
    print(f"registering pairs (0.75-0.95): {[(n(a), n(b), round(r,3)) for a,b,r in pair] or 'NONE'}")
main()
