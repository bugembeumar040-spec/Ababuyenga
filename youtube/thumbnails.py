#!/usr/bin/env python3
"""Upload youtube/thumbs/<videoId>.jpg for any video that has one.

    python3 youtube/thumbnails.py            # list what is ready
    python3 youtube/thumbnails.py --apply    # upload

Skips videos with no image file, so it is safe to run before the
artwork exists. YouTube caps thumbnails at 2 MB.
"""
import json
import sys
import pathlib
from yt import api

HERE = pathlib.Path(__file__).parent
THUMBS = HERE / "thumbs"
APPLY = "--apply" in sys.argv
LIMIT = 2 * 1024 * 1024


def main():
    meta = json.loads((HERE / "clarity-metadata.json").read_text())
    found = 0
    for v in meta["videos"]:
        vid = v["videoId"]
        img = THUMBS / f"{vid}.jpg"
        if not img.exists():
            print(f"  skip    {vid}  (no thumbs/{vid}.jpg)")
            continue
        size = img.stat().st_size
        if size > LIMIT:
            print(f"  TOO BIG {vid}  ({size / 1e6:.1f} MB > 2 MB)")
            continue
        found += 1
        print(f"  ready   {vid}  ({size / 1024:.0f} KB)  {v.get('thumbnailText', '')}")
        if APPLY:
            api("thumbnails/set", "POST", params={"videoId": vid},
                raw=img.read_bytes(), ctype="image/jpeg", upload=True)
            print("    uploaded")

    if not found:
        print("\nNo images in youtube/thumbs/. Add <videoId>.jpg files.")
    elif not APPLY:
        print(f"\n{found} ready. Re-run with --apply to upload.")


if __name__ == "__main__":
    main()
