#!/usr/bin/env python3
"""Apply clarity-metadata.json to YouTube. Idempotent.

    python3 youtube/sync.py            # dry run, prints the diff
    python3 youtube/sync.py --apply    # writes changed videos only
"""
import json
import sys
import pathlib
from yt import api

HERE = pathlib.Path(__file__).parent
APPLY = "--apply" in sys.argv


def main():
    meta = json.loads((HERE / "clarity-metadata.json").read_text())
    vids = meta["videos"]
    ids = ",".join(v["videoId"] for v in vids)
    live = {i["id"]: i["snippet"] for i in
            api("videos", params={"part": "snippet", "id": ids})["items"]}

    missing = [v["videoId"] for v in vids if v["videoId"] not in live]
    if missing:
        raise SystemExit(f"Not visible to this account: {missing}")

    changed = 0
    for v in vids:
        vid, cur = v["videoId"], live[v["videoId"]]
        want = {"title": v["title"], "description": v["description"],
                "tags": v["tags"]}
        if all(cur.get(k) == want[k] for k in want):
            print(f"  ok      {vid}  (already current)")
            continue

        changed += 1
        print(f"\n  CHANGE  {vid}")
        if cur.get("title") != want["title"]:
            print(f"    - {cur.get('title')}")
            print(f"    + {want['title']}")
        if cur.get("tags") != want["tags"]:
            print(f"    tags {len(cur.get('tags') or [])} -> {len(want['tags'])}")
        if cur.get("description") != want["description"]:
            print(f"    description rewritten ({len(want['description'])} chars)")

        if APPLY:
            # videos.update REPLACES the snippet part - merge into the live one
            # so categoryId / defaultLanguage are not silently cleared.
            snip = dict(cur)
            snip.update(want)
            api("videos", "PUT", params={"part": "snippet"},
                body={"id": vid, "snippet": snip})
            print("    written")

    if not changed:
        print("\nNothing to do - channel already matches the file.")
    elif APPLY:
        print(f"\nDone. {changed} video(s) updated.")
    else:
        print(f"\n{changed} video(s) would change. Re-run with --apply.")


if __name__ == "__main__":
    main()
