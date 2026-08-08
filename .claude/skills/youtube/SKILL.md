---
name: youtube
description: Read or act on the Finance % Decoded YouTube channel - view counts, watch time, CTR, audience retention, comments, competitor/topic research, uploading a Short, or editing a video's title, description, tags or thumbnail. Use whenever the user asks how a video or the channel performed, what to make next based on real numbers, or wants something published or changed on YouTube.
---

# YouTube channel

Everything goes through one zero-dependency CLI:

```bash
python3 tools/youtube/yt.py <command>
```

Run `python3 tools/youtube/yt.py setup` first if you are unsure which
credentials exist — it prints what is set and what is missing, and it costs
nothing. Do not read `yt.py` to work out how to call it; the commands below are
the whole interface.

## Pick the cheapest tier that answers the question

| Need | Command | Cost |
|---|---|---|
| What went up recently, with views | `latest` | free, no credentials |
| Subs, total views, video count | `channel` | 1 unit |
| Uploads with views/likes/comments | `videos -n 25` | ~2 units |
| One video in detail | `video ID` | 1 unit |
| Comments | `comments [ID]` | 1 unit |
| Watch time, retention %, subs | `analytics --days 28` | free (Analytics API) |
| Every video ranked, side by side | `rank --days 90` | free |
| Where traffic actually comes from | `sources --days 28` | free |
| Where viewers drop off within a video | `retention ID` | free |
| What others are doing on a topic | `search "query" --shorts --days 30` | **100 units** |

`latest` needs no API key at all, so reach for it first when the question is
just "what's up and how is it doing". Only use `search` when the question is
genuinely about other channels — the daily quota is 10,000 units, so it is 100
searches and then nothing works until midnight Pacific.

Add `--json` when you need fields the summary omits. Default output is compact
on purpose — prefer it.

## Reading performance

For "how did X do", one `analytics --video ID` beats scraping `videos`, because
it carries watch time, average view percentage and CTR — the numbers that
actually decide whether a Short worked. View count alone is close to noise on
this channel.

Before blaming the content for weak views, run `rank` and `sources`. On a
Shorts channel, views and retention move independently: this channel has
videos at 150-188% average view percentage sitting on 39 views. When retention
is high and views are low the problem is distribution, not the script, and
rewriting hooks will not fix it. `sources` shows whether the SHORTS feed is
still serving the channel at all.

Note that impressions and CTR are not exposed for this channel - the Analytics
API refuses that metric combination, which is usual when traffic is
Shorts-dominated. Do not report CTR figures; they are not available.

For "why did X underperform" *once distribution is confirmed healthy*, use
`retention ID`. It prints the
audience-watch-ratio curve as a bar chart at 5% intervals. On a Short, the drop
between 0% and 15% is the hook; a cliff later is a pacing or payoff problem.
Say which it is rather than quoting the whole curve back.

## Publishing

Default to `--privacy private` and let the user flip it public, unless they
explicitly said publish now. Scheduling:

```bash
python3 tools/youtube/yt.py upload out/creditcard.mp4 \
  --title "They Call You a Deadbeat" \
  --desc "$(cat out/description.txt)" \
  --tags "credit cards,personal finance,debt" \
  --publish-at 2026-08-12T17:00:00Z \
  --thumbnail out/thumb.jpg
```

`--publish-at` needs RFC3339 UTC and forces privacy to private until the
timestamp. Uploads cost 1600 quota units, so a failed upload is expensive —
check the file exists and the title is under 100 characters before running it.

Editing an existing video is `update`; it preserves fields you do not pass:

```bash
python3 tools/youtube/yt.py update VIDEO_ID --title "..." --thumbnail new.jpg
```

## Connecting it to the prompt packs

The repo's prompt packs (`credit-card-prompt-pack.txt` and successors) carry a
CONTINUITY section listing arguments already spent on the channel. When asked
what to make next, check the real numbers before suggesting anything — a topic
that looks fresh may already be live and underperforming. `latest` is enough to
see what has shipped; `analytics --video` tells you whether it worked.

## When credentials are missing

The CLI exits with the exact variable name it needs. Do not try to work around
it or hand-roll API calls — point the user at the matching tier in
`tools/youtube/README.md` and stop. Setup is a few minutes of clicking in Google
Cloud Console that only they can do.

Tokens live in environment variables or `~/.config/ababuyenga/youtube.json`.
Never print a refresh token or client secret into a commit, a PR body, or a
file in the repo.
