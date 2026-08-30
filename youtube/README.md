# Clarity in the Quran — channel automation

Automates metadata, thumbnails, and growth tracking for
[@ClarityInTheQuran](https://www.youtube.com/@ClarityInTheQuran)
(`UC0eBu0ZXcF20pTAG3lUnPXA`) through the YouTube Data API.

Everything runs in GitHub Actions. After the one-time setup below, you
never touch a terminal again — you click a button, or it runs itself.

---

## Setup — once, about five minutes

Google requires a human to grant access to a channel. No script can do
this part; it is the one unavoidable step.

### 1. Create an OAuth client (~3 min)

1. Go to [console.cloud.google.com](https://console.cloud.google.com/) →
   create a project (any name).
2. **APIs & Services → Library** → search *YouTube Data API v3* → **Enable**.
3. **APIs & Services → OAuth consent screen** → External → fill in the
   app name and your email → **Add yourself as a Test user**.
   Leave it in Testing mode; publishing is not needed.
4. **Credentials → Create credentials → OAuth client ID** →
   type **Desktop app** → Create.
5. Copy the **Client ID** and **Client secret**.

### 2. Grant access (~1 min)

On your own machine:

```bash
git clone https://github.com/bugembeumar040-spec/Ababuyenga
cd Ababuyenga/youtube
python3 auth.py <CLIENT_ID> <CLIENT_SECRET>
```

A browser opens. **Sign in as the account that owns the channel** and
accept. The script prints three values. Nothing is saved to disk.

### 3. Store the three secrets (~1 min)

Repo → **Settings → Secrets and variables → Actions → New repository
secret**. Add each one exactly as printed:

| Secret | Value |
|---|---|
| `YT_CLIENT_ID` | from step 1 |
| `YT_CLIENT_SECRET` | from step 1 |
| `YT_REFRESH_TOKEN` | from step 2 |

The refresh token does not expire. Setup is done.

---

## Running it

Repo → **Actions → YouTube channel automation → Run workflow**, pick a
task, click the green button:

| Task | What it does |
|---|---|
| `report` | Growth snapshot → commits to `GROWTH.md` |
| `sync-preview` | Shows every metadata change. **Writes nothing.** |
| `sync-apply` | Applies titles, descriptions, tags to YouTube |
| `thumbnails-apply` | Uploads any image in `thumbs/` |

**Run `sync-preview` first.** It prints the exact before/after for all
8 videos without touching the channel.

Every Monday at 09:00 UTC the growth snapshot runs on its own and
commits the result. Nothing else runs unattended — no automated job
ever writes to your channel without you clicking it.

---

## Files

| File | Role |
|---|---|
| `clarity-metadata.json` | The source of truth. Edit this, not YouTube. |
| `sync.py` | Pushes metadata. Idempotent — skips unchanged videos. |
| `thumbnails.py` | Uploads `thumbs/<videoId>.jpg`. Skips missing files. |
| `report.py` | Appends to `GROWTH.md`. |
| `auth.py` | One-time consent. Run locally only. |
| `yt.py` | Shared auth + API helper. |

### Changing metadata later

Edit `clarity-metadata.json`, commit, then run `sync-preview` →
`sync-apply`. `sync.py` compares against what is live and only writes
what actually differs, so re-running it is always safe.

### Adding thumbnails

Drop `thumbs/<videoId>.jpg` (1280×720, under 2 MB) and run
`thumbnails-apply`. The `thumbnailText` field in the JSON records the
intended text for each one.

---

## Security

- The three secrets live only in GitHub Actions secrets — never in git.
- `.gitignore` blocks `*token*.json`, `client_secret*.json`, `.env`.
- Scope is `youtube.force-ssl`, limited to your own channel's content.
- Revoke any time at
  [myaccount.google.com/permissions](https://myaccount.google.com/permissions).

## Quotas

The Data API allows 10,000 units/day. A full `sync-apply` of 8 videos
costs ~400. A `report` run costs ~10. Not a constraint at this volume.
