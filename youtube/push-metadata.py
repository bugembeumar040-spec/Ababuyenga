#!/usr/bin/env python3
"""Push clarity-metadata.json to YouTube via the Data API.

Needs an OAuth 2.0 access token with the youtube.force-ssl scope
(an API key will NOT work - videos.update is a write call).

    export YT_TOKEN="ya29...."
    python3 push-metadata.py            # dry run, shows the diff
    python3 push-metadata.py --apply    # actually writes

videos.update REPLACES the whole snippet part, so this fetches each
video's current snippet first and merges, to avoid clearing categoryId
or defaultLanguage.
"""
import json, os, sys, urllib.request, urllib.error, pathlib

API = "https://www.googleapis.com/youtube/v3/videos"
TOKEN = os.environ.get("YT_TOKEN", "").strip()
APPLY = "--apply" in sys.argv
HERE = pathlib.Path(__file__).parent


def call(url, method="GET", body=None):
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, data) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        detail = e.read().decode()[:400]
        raise SystemExit(f"\n  HTTP {e.code} on {method} {url.split('?')[0]}\n  {detail}\n")


def main():
    if not TOKEN:
        raise SystemExit("Set YT_TOKEN to an OAuth access token (youtube.force-ssl scope).")

    meta = json.loads((HERE / "clarity-metadata.json").read_text())
    vids = meta["videos"]
    ids = ",".join(v["videoId"] for v in vids)

    current = {i["id"]: i["snippet"] for i in
               call(f"{API}?part=snippet&id={ids}")["items"]}

    missing = [v["videoId"] for v in vids if v["videoId"] not in current]
    if missing:
        raise SystemExit(f"Not visible to this token: {missing}")

    for v in vids:
        vid = v["videoId"]
        snip = dict(current[vid])
        old = snip["title"]
        snip["title"] = v["title"]
        snip["description"] = v["description"]
        snip["tags"] = v["tags"]

        print(f"\n{vid}")
        print(f"  - {old}")
        print(f"  + {v['title']}")
        print(f"    tags {len(current[vid].get('tags', []))} -> {len(v['tags'])}")

        if APPLY:
            call(f"{API}?part=snippet", "PUT", {"id": vid, "snippet": snip})
            print("    WRITTEN")

    print("\nDry run - rerun with --apply to write." if not APPLY
          else f"\nDone. {len(vids)} videos updated.")


if __name__ == "__main__":
    main()
