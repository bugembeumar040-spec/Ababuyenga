#!/usr/bin/env python3
"""
Import the delivered illustrations into public/plates/ under their shot ids.

The plates arrive with generator filenames (IMG_7284.png, Clay_oil_lamps_...jpeg)
that carry no shot information, so tools/plate-map.json holds the pairing and
this script applies it. Every plate is fitted to the 2560x1440 canvas: the
delivered art is 16:9 already, so this is a resample rather than a crop, and
anything off-ratio is centre-cropped to 16:9 first so the film never letterboxes
mid-cut.

Variants of the same composition go to public/plates/alt/ under
<shot-id>--<n>.png. Swapping which take is used is then a rename, not a
regeneration.

Usage:  python3 tools/import-plates.py [source-dir]
"""
import json
import shutil
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
    "/root/.claude/uploads/50184755-fdb6-5352-9ece-6ef7e8acb8f2"
)
DEST = ROOT / "public" / "plates"
ALT = DEST / "alt"
W, H = 2560, 1440


def find(name: str) -> Path | None:
    """Sources land with a hash prefix; match on the trailing filename."""
    for p in SRC.iterdir():
        if p.name == name or p.name.endswith("-" + name):
            return p
    return None


def fit(src: Path, dest: Path) -> str:
    im = Image.open(src).convert("RGB")
    ratio = im.width / im.height
    target = W / H
    note = ""
    if abs(ratio - target) > 0.01:
        # Centre-crop to 16:9 rather than squash — the compositions are all
        # centred and the pack frames them wide on purpose.
        if ratio > target:
            new_w = round(im.height * target)
            im = im.crop(((im.width - new_w) // 2, 0, (im.width + new_w) // 2, im.height))
        else:
            new_h = round(im.width / target)
            im = im.crop((0, (im.height - new_h) // 2, im.width, (im.height + new_h) // 2))
        note = " (cropped to 16:9)"
    if (im.width, im.height) != (W, H):
        note += f" [{im.width}x{im.height} -> {W}x{H}]"
        im = im.resize((W, H), Image.LANCZOS)
    dest.parent.mkdir(parents=True, exist_ok=True)
    im.save(dest, "PNG")
    return note


def main() -> None:
    spec = json.loads((ROOT / "tools" / "plate-map.json").read_text())
    if DEST.exists():
        shutil.rmtree(DEST)
    DEST.mkdir(parents=True)
    (DEST / ".gitkeep").touch()

    missing_src = []
    for shot, name in sorted(spec["map"].items()):
        src = find(name)
        if src is None:
            missing_src.append((shot, name))
            continue
        note = fit(src, DEST / f"{shot}.png")
        print(f"  {shot:6} <- {name}{note}")

    for shot, names in sorted(spec["alt"].items()):
        for i, name in enumerate(names, start=1):
            src = find(name)
            if src is not None:
                fit(src, ALT / f"{shot}--{i}.png")

    print(f"\n{len(spec['map']) - len(missing_src)} plates imported")
    print(f"{sum(len(v) for v in spec['alt'].values())} variants in plates/alt/")
    print("run tools/scan-plates.py for what is still pending — it derives that")
    print("from the cut rather than from any list kept in this file")
    for shot, name in missing_src:
        print(f"  !! {shot}: source not found — {name}")


if __name__ == "__main__":
    main()
