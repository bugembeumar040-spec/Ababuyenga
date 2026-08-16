# ytauto — YouTube upload automation

A local CLI for the Finance % Decoded channel. Validates a video's metadata
against YouTube's real limits, uploads it resumably, attaches the thumbnail,
files it into a playlist, and pulls the numbers back afterwards.

Nothing runs in CI and no credential is ever committed — **this repository is
public**, and `.gitignore` blocks `client_secrets.json`, `token.json` and `.env`.

---

## Read this before your first upload

Two Google policies shape how this tool has to be used. Neither is a bug in the
code, and both bite silently.

### 1. Uploads from an unaudited API project are locked private

Videos uploaded through `videos.insert` from an API project that has not passed
a YouTube compliance audit are **restricted to private, and the lock cannot be
lifted** — YouTube's own help page says you cannot appeal it and must re-upload
through an audited client or the YouTube app.

What this means in practice:

- Upload with `privacy: private`, then **flip the video to public in YouTube
  Studio by hand.** Studio is a first-party client, so it is not affected.
- `publish_at` scheduling will not work until your project is audited. The
  validator warns you if you set it.
- **Your first run must be a throwaway video** — a few seconds of black — so you
  find out how your project behaves before you spend a real render on it.

If you later want true hands-off scheduled publishing, apply through the
[YouTube API Services audit and quota extension form](https://developers.google.com/youtube/v3/guides/quota_and_compliance_audits).

### 2. A "Testing" consent screen expires your login every 7 days

Google issues refresh tokens that **expire after 7 days** when the OAuth consent
screen's publishing status is *Testing*, unless the only scopes are basic
profile ones. YouTube's scopes are not, so a testing-mode setup means re-running
`login` every week. Publishing the app (step 3 below) removes the expiry.

---

## Setup

You already have the client ID and secret, so start at step 2.

### 1. Enable the APIs

Google Cloud Console → **APIs & Services → Library**, enable both:

- **YouTube Data API v3** — upload, thumbnail, playlist
- **YouTube Analytics API** — the `stats` command

### 2. Point the tool at your credentials

The OAuth client must be of type **Desktop app** — the login flow uses a
loopback redirect, which the Web application type rejects.

Either save the downloaded JSON:

```bash
mkdir -p ~/.config/ytauto
cp ~/Downloads/client_secret_*.json ~/.config/ytauto/client_secrets.json
chmod 600 ~/.config/ytauto/client_secrets.json
```

…or, if you only have the two strings, export them:

```bash
export YTAUTO_CLIENT_ID='...apps.googleusercontent.com'
export YTAUTO_CLIENT_SECRET='...'
```

(Set `YTAUTO_HOME` to keep credentials somewhere else.)

### 3. Publish the consent screen

**APIs & Services → OAuth consent screen → Publish app.** This is what avoids
the weekly re-login in §2 above. You will see an "unverified app" interstitial
when you authorise — expected for a personal project; click *Advanced →
Go to (app)*.

If you would rather stay in Testing, add your own Google account under **Test
users** or consent will be refused outright.

### 4. Install and authorise

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m ytauto login
```

A browser window opens once. Authorise with the account that owns the channel —
**if the channel is a Brand Account, select the channel, not your personal
account**, or every upload lands on the wrong one. The token is written to
`~/.config/ytauto/token.json` with `0600` permissions.

Confirm you landed on the right channel:

```bash
.venv/bin/python -m ytauto whoami
```

### 5. Do a throwaway upload first

```bash
ffmpeg -f lavfi -i color=black:s=1080x1920:d=3 -c:v libx264 /tmp/test.mp4
cp videos/_template.yml videos/test.yml     # point video_file at /tmp/test.mp4, give it a title
.venv/bin/python -m ytauto upload videos/test.yml
```

Then open it in Studio and try to make it public. Whether that works tells you
exactly which of the two paths above you are on — before a real video is at
stake. Delete it afterwards.

---

## Everyday use

```bash
python -m ytauto validate videos/creditcard.yml     # limits check, no network
python -m ytauto upload   videos/creditcard.yml     # asks before uploading
python -m ytauto upload   videos/creditcard.yml -y  # no prompt
python -m ytauto publish  VIDEO_ID --privacy public # only on an audited project
python -m ytauto stats --limit 15 --days 28
```

`upload` runs validation first and refuses on any error, because a rejected
upload still costs quota.

### The sidecar file

One YAML file per video, next to the others in `videos/`. Copy
`videos/_template.yml`. `videos/creditcard.yml` is filled in from the packaging
block of `credit-card-prompt-pack.txt` and is ready apart from the two render
paths.

Validation enforces what YouTube enforces:

| Field | Rule |
|---|---|
| `title` | ≤ 100 chars, no `<` or `>` |
| `description` | ≤ 5000 chars; warns under 600 (the channel slate) |
| `tags` | ≤ 500 chars total — **over the limit YouTube drops every tag without an error** |
| `publish_at` | RFC3339, in the future, requires `privacy: private` |
| `made_for_kids` | explicit; YouTube requires a declaration |
| `thumbnail` | ≤ 2 MB, `.jpg`/`.png`, needs a phone-verified account |

### Quota

`videos.insert` costs **1,600 units** of a default **10,000/day** — about six
uploads a day, resetting at midnight Pacific. `stats` costs a handful. The CLI
translates a `quotaExceeded` error into that explanation rather than a stack
trace.

---

## Tests

```bash
.venv/bin/python -m pytest tests/ -q
```

22 tests cover the validation rules and the resumable-upload retry loop
(5xx and socket errors retried with backoff, 4xx surfaced immediately).

## Layout

```
ytauto/auth.py       one-time browser consent, token refresh
ytauto/metadata.py   sidecar parsing and limit validation
ytauto/upload.py     resumable upload, thumbnail, playlist
ytauto/analytics.py  recent uploads, retention
ytauto/cli.py        commands and error translation
videos/              one sidecar per video
```
