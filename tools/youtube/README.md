# YouTube channel integration

`yt.py` is a standard-library-only CLI that connects this repo to the channel.
No `pip install`, no virtualenv, no MCP server — one file, Python 3.7+.

Claude drives it through `.claude/skills/youtube/`, so in a session you can just
say *"how did the Klarna short do?"* rather than spelling out commands.

## Why a CLI and not a connector

There is no first-party YouTube connector for Claude. The options are a
third-party MCP server (another dependency, another OAuth grant, another thing
that breaks) or a small script. The script is cheaper to run and cheaper in
tokens: output is deliberately terse, so a request like "last 10 videos with
views" costs one command and a handful of lines back, not a page of JSON.

## Three tiers

Use the lowest tier that answers the question — the cheap ones cost no API
quota at all.

| Tier | Setup | Commands |
|---|---|---|
| 0 | none | `latest`, `handle` |
| 1 | API key, ~2 min | `channel`, `videos`, `video`, `comments`, `search` |
| 2 | OAuth, ~10 min | `analytics`, `rank`, `sources`, `retention`, `upload`, `update`, `thumbnail` |

Tier 2 credentials also authorize every Tier 1 command, so once OAuth is set up
the API key is optional.

Tier 0 works right now, with no account setup:

```bash
python3 tools/youtube/yt.py latest
```

The channel — `@financeundoubtlydecoded` / `UCVOoFJkRiOdJsWnewt8HJkw` — is set as
`YT_CHANNEL_ID` in `.claude/settings.json`, so commands default to it. Pass
`--channel @someoneelse` to look at another channel.

## Tier 1 — public stats

1. Create a project: <https://console.cloud.google.com/projectcreate>
2. **APIs & Services → Library** → enable **YouTube Data API v3**
3. **Credentials → Create credentials → API key**
4. Export it:

```bash
export YT_API_KEY=AIza...
```

An API key is read-only and public-data-only. It cannot touch your account.

## Tier 2 — analytics and uploading

Needs the Tier 1 project.

1. **Library** → enable **YouTube Analytics API**
2. **OAuth consent screen** → External. Add your own Google account under
   **Test users**. You do *not* need to publish or verify the app.
3. **Credentials → Create credentials → OAuth client ID → Desktop app**
4. Export the pair and run the flow:

```bash
export YT_CLIENT_ID=....apps.googleusercontent.com
export YT_CLIENT_SECRET=GOCSPX-...
python3 tools/youtube/yt.py auth            # add --readonly for a stats-only token
```

`auth` prints a URL. Approve it in the browser signed into the channel's
account. The browser then lands on a `localhost` page that **fails to load —
that is expected**. Copy that failed page's full address bar and paste it back.
You get a refresh token.

### Scope choice

`--readonly` mints a token that can read stats, analytics and retention but
**cannot upload, edit or delete**. Without it you also get upload and
`force-ssl`, and `force-ssl` can delete videos. If a token is going anywhere
you would not trust with the channel — including into a chat transcript — mint
it `--readonly` and re-run without the flag later if you want publishing.

### No terminal? Split the flow

`auth --url` prints the authorization URL and exits. `auth --code "<pasted
redirect URL>"` does the exchange non-interactively. That lets the browser half
happen anywhere, with no interactive prompt:

```bash
python3 tools/youtube/yt.py auth --url --readonly
# ...approve in a browser, copy the failed localhost address bar...
python3 tools/youtube/yt.py auth --readonly --code "http://localhost:8765/?code=4/0A..."
```

### Make it survive the session

Claude's container is wiped when a session ends. Anything you `export` in a
session dies with it. Put these four in your **Claude environment variables**
instead, and every future session starts already connected:

```
YT_API_KEY
YT_CLIENT_ID
YT_CLIENT_SECRET
YT_REFRESH_TOKEN
```

(`YT_CHANNEL_ID` is already committed in `.claude/settings.json` — it is not a
secret. These four are.)

The refresh token does not expire on its own. Treat it like a password — it can
upload to and edit your channel. Revoke at
<https://myaccount.google.com/permissions>.

## Commands

```bash
yt.py setup                                  # credential status + these steps
yt.py latest [--channel @h] [-n 15]          # newest uploads, no credentials
yt.py channel                                # subs, total views, video count
yt.py videos -n 25                           # uploads with views/likes/comments
yt.py video VIDEO_ID                         # one video, full detail
yt.py comments [VIDEO_ID] -n 25              # recent comments
yt.py search "credit card debt" --shorts --days 30
yt.py analytics --days 28 [--video ID]       # watch time, subs, retention %
yt.py rank --days 90                         # every video ranked, with avgView%
yt.py sources --days 28 [--video ID]         # traffic-source breakdown
yt.py retention VIDEO_ID                     # the drop-off curve, as a bar chart
yt.py upload clip.mp4 --title "..." --desc "..." --tags "a,b" \
      --privacy private --publish-at 2026-08-12T17:00:00Z --thumbnail thumb.jpg
yt.py update VIDEO_ID --title "..." --thumbnail new.jpg
```

Add `--json` to any command for the raw API response.

## Quota

The Data API gives you 10,000 units/day by default. Most calls cost 1 unit.
Two exceptions worth knowing:

- `search` — **100 units**. That is 100 searches a day, total. Use `videos`
  when you only want your own channel.
- `upload` — **1600 units**.

Tier 0 (`latest`, `handle`) uses no quota, which is why the skill prefers it.

## Notes

- `--publish-at` forces privacy to `private`; YouTube requires that for a
  scheduled release, then flips it public at the timestamp.
- `update` reads the current snippet before writing, because the API replaces
  the whole snippet on update — otherwise you would blank the description.
- Analytics lag about a day, so date ranges end yesterday.
- Retention data only appears once a video has enough views.
- Credentials are read from environment variables first, then
  `~/.config/ababuyenga/youtube.json` (mode 600, never in the repo).
