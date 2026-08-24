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

def colour(p):
    """(indigo %, mark saturation) -- evidence, not a verdict.

    Three attempts to classify line vs wash from one statistic have failed.
    Plain saturation counts the warm parchment ground; chroma spread counts its
    foxing; indigo alone passes any wash that happens to use a warm-only
    palette. Only b09/img4, pure ink on white, is unambiguous.

    So this reports the numbers and leaves the call to the eye. What IS reliable
    is correlation: whether two plates register is a direct measurement and
    needs no classification at all. Judge a pair by its correlation, then look
    at these two numbers to see which side is which.
    """
    a = np.asarray(Image.open(p).convert("RGB")).astype(np.float32) / 255
    r, b = a[..., 0], a[..., 2]
    mx, mn = a.max(2), a.min(2)
    S = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    indigo = float(((b > r + 0.04) & (S > 0.15)).mean()) * 100
    L = 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
    ink = L < 0.60
    return indigo, (float(S[ink].mean()) if ink.sum() > 500 else 0.0)


def ncc(a, b):
    a, b = a - a.mean(), b - b.mean()
    return float((a * b).sum() / np.sqrt((a * a).sum() * (b * b).sum()))

def main():
    files = sorted(glob.glob("clarity/plates/inbox/*/*.jpg"))
    g = {f: grey(f) for f in files}
    s = {f: colour(f) for f in files}
    dup, pair = [], []
    for a, b in itertools.combinations(files, 2):
        r = ncc(g[a], g[b])
        if r > 0.95: dup.append((a, b, r))
        elif r > 0.75: pair.append((a, b, r))
    n = lambda p: "/".join(p.split("/")[-1].split("-")[:2])
    print(f"{len(files)} plates captured")
    print(f"near-duplicates (>0.95): {[(n(a), n(b), round(r,3)) for a,b,r in dup] or 'none'}")
    if pair:
        print("registering pairs (0.75-0.95) -- a usable line/wash pair:")
        for a, b, r in pair:
            print(f"  {n(a)} + {n(b)}  corr {r:.3f}")
            for f in (a, b):
                print(f"     {n(f)}: indigo {s[f][0]:.2f}%  mark saturation {s[f][1]:.3f}")
    else:
        print("registering pairs (0.75-0.95): NONE")
main()
