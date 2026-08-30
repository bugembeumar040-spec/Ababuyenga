#!/usr/bin/env python3
"""Append a weekly growth snapshot to youtube/GROWTH.md."""
import json
import pathlib
import datetime
from yt import api

HERE = pathlib.Path(__file__).parent
OUT = HERE / "GROWTH.md"
HDR = "# Growth log\n\nAppended weekly by .github/workflows/youtube.yml\n"


def main():
    meta = json.loads((HERE / "clarity-metadata.json").read_text())
    cid = meta["channelId"]

    ch = api("channels", params={"part": "statistics,contentDetails", "id": cid})["items"][0]
    stats = ch["statistics"]
    uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]

    ids, page = [], None
    while True:
        params = {"part": "contentDetails", "playlistId": uploads, "maxResults": 50}
        if page:
            params["pageToken"] = page
        r = api("playlistItems", params=params)
        ids += [i["contentDetails"]["videoId"] for i in r["items"]]
        page = r.get("nextPageToken")
        if not page:
            break

    rows = []
    for n in range(0, len(ids), 50):
        for v in api("videos", params={"part": "snippet,statistics",
                                       "id": ",".join(ids[n:n + 50])})["items"]:
            rows.append((int(v["statistics"].get("viewCount", 0)),
                         v["snippet"]["publishedAt"][:10],
                         v["snippet"]["title"]))
    rows.sort(reverse=True)

    today = datetime.date.today().isoformat()
    subs = stats.get("subscriberCount", "?")
    views = stats.get("viewCount", "?")
    count = stats.get("videoCount", "?")
    med = rows[len(rows) // 2][0] if rows else 0

    lines = [f"\n## {today}\n",
             f"**{subs} subscribers · {views} total views · {count} videos · "
             f"median {med} views/video**\n",
             "| Views | Published | Title |", "|---:|---|---|"]
    lines += [f"| {v} | {d} | {t[:70]} |" for v, d, t in rows[:10]]

    prev = OUT.read_text() if OUT.exists() else HDR
    OUT.write_text(prev + "\n".join(lines) + "\n")
    print(f"{today}: {subs} subs, {views} views, median {med}")


if __name__ == "__main__":
    main()
