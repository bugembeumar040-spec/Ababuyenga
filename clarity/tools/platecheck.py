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

def sat(p):
    a = np.asarray(Image.open(p).convert("RGB").resize((344, 192))).astype(np.float32) / 255
    mx, mn = a.max(2), a.min(2)
    return float((np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0) > 0.15).mean())

def ncc(a, b):
    a, b = a - a.mean(), b - b.mean()
    return float((a * b).sum() / np.sqrt((a * a).sum() * (b * b).sum()))

def main():
    files = sorted(glob.glob("clarity/plates/inbox/*/*.jpg"))
    g = {f: grey(f) for f in files}
    s = {f: sat(f) for f in files}
    dup, pair = [], []
    for a, b in itertools.combinations(files, 2):
        r = ncc(g[a], g[b])
        if r > 0.95: dup.append((a, b, r))
        elif r > 0.75: pair.append((a, b, r))
    n = lambda p: "/".join(p.split("/")[-1].split("-")[:2])
    print(f"{len(files)} plates captured")
    print(f"line passes (under 20% of pixels saturated): "
          f"{[n(f) for f in files if s[f] < 0.20] or 'NONE'}")
    print(f"near-duplicates (>0.95): {[(n(a), n(b), round(r,3)) for a,b,r in dup] or 'none'}")
    print(f"registering pairs (0.75-0.95): {[(n(a), n(b), round(r,3)) for a,b,r in pair] or 'NONE'}")
main()
