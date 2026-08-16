# YouTube Automation for @clarityinthequran

> **Start here instead:** `youtube_easy_mode.ipynb` is form-driven — you
> fill in boxes and tap Run, never touching code. This document is the
> engineer's version, kept for reference and troubleshooting.

Upload, read comments, reply, and back up a YouTube channel — entirely
from an iPhone, using Google Colab + Google Drive. No terminal, no local
Python, no local OAuth web server.

**Open the notebook in Colab:**
`colab.research.google.com/github/bugembeumar040-spec/ababuyenga/blob/claude/youtube-colab-automation-7bka5n/youtube-automation/youtube_colab_automation.ipynb`

Workflow: CapCut → export to Drive → run the Colab cells.

---

## Read this first: three real constraints

These are properties of Google's platform, not of this code. Plan around
them rather than being surprised by them later.

**1. Colab's native auth cannot do YouTube.**
`google.colab.auth.authenticate_user()` signs the VM into your account for
Drive and Cloud APIs, but it cannot request the `youtube.upload` scope. The
notebook still calls it (it makes Drive work smoothly), but YouTube access
comes from a separate paste-the-link OAuth flow in Cell 1D. Google shut off
the old copy/paste "oob" flow in January 2023, so the flow redirects to
`http://localhost:8080/`. **Safari will fail to load that page — that is
correct.** The authorization code is in the failed page's URL; you copy the
whole URL from the address bar and paste it into Colab. You do this once;
the token is then saved to Drive and refreshed silently.

**2. API uploads are locked to private until your project is audited.**
Any video uploaded via `videos.insert` from an API project that has not
passed YouTube's compliance audit is restricted to private. This has applied
to all projects created since 28 July 2020. So the practical loop is: upload
via Colab → open the YouTube Studio app on your phone → set it public. To
remove the restriction, request an audit at
`support.google.com/youtube/contact/yt_api_form`.

**3. Tokens die every 7 days while your app is in "Testing".**
An External OAuth app left in Testing status has its refresh tokens revoked
after 7 days, meaning you redo the paste flow weekly. Publishing the app to
Production stops this. See step 6 below.

---

## 1. Google Cloud setup on your phone

Do this once, in Safari, signed into **the Google account that owns the
channel**. Before anything else: tap **`aA`** in the address bar →
**Request Desktop Website**. The Cloud Console's mobile layout hides the
menus you need.

### Step 1 — Create the project
1. Go to `console.cloud.google.com`.
2. Tap the project dropdown in the top blue bar.
3. Tap **New Project**.
4. Name it `Clarity Automation` → **Create**.
5. Reopen the dropdown and select it. No billing card is required.

### Step 2 — Enable the YouTube Data API v3
1. Go straight to
   `console.cloud.google.com/apis/library/youtube.googleapis.com`.
2. Confirm your project name is in the top bar.
3. Tap the blue **Enable** button.

### Step 3 — Configure the OAuth consent screen
Google moved this to "Google Auth Platform" — older tutorials point at the
wrong menu.
1. Go to `console.cloud.google.com/auth/overview`.
2. Tap **Get started**.
3. **App name:** `Clarity Automation`.
   **User support email:** your own address.
4. **Audience:** choose **External** → Next.
5. **Contact information:** your email again → Next.
6. Tick the Google API Services User Data Policy box → **Create**.

### Step 4 — Add the YouTube scopes
1. Left menu → **Data Access**.
2. Tap **Add or remove scopes**.
3. In the filter box, type `youtube`.
4. Tick both of these:
   - `.../auth/youtube.upload` — post videos
   - `.../auth/youtube.force-ssl` — read comments, post replies
5. Tap **Update**, then **Save**.

### Step 5 — Create the credentials
1. Left menu → **Clients** → **Create client**.
2. **Application type: Desktop app.** (This matters — desktop clients
   accept the `localhost` redirect the notebook uses. A "Web application"
   client would require you to pre-register the redirect URI.)
3. Name it `Colab Client` → **Create**.
4. Tap **Download JSON**. It saves to your Files app.
5. In Files, rename it to exactly **`client_secret.json`**.
6. Move it into your private Drive secrets folder (see below).

### Step 6 — Publish the app (stops the weekly re-auth)
1. Left menu → **Audience**.
2. Under Publishing status, tap **Publish app** → confirm.

Your app stays unverified, so you will always tap through a
"Google hasn't verified this app" warning → **Advanced** → **Go to
Clarity Automation (unsafe)**. That is expected for a personal tool and is
safe here — it is your own app, on your own account.

If you would rather stay in Testing: go to **Audience** → **Test users** →
**Add users** → your own email, and accept re-authorising every 7 days.

---

## 2. Drive folders

Create three folders in **My Drive** from the Google Drive app, then put
their names into Cell 1A of the notebook:

| Placeholder | Holds |
|---|---|
| `YOUR_UPLOAD_FOLDER` | CapCut exports waiting to be uploaded |
| `YOUR_BACKUP_FOLDER` | Downloaded channel backups |
| `YOUR_SECRETS_FOLDER` | `client_secret.json` and `token.json` |

**Keep the secrets folder private.** `token.json` grants full write access
to your channel — anyone holding it can upload and delete videos. Never
share that folder, and never commit either file to git.

---

## 3. Running it

| Cell | Purpose | When |
|---|---|---|
| 1 | Install, mount Drive, authenticate | Every session |
| 2 | Upload / read comments / reply | After Cell 1 |
| 3 | Back up the channel with `yt-dlp` | After Cell 1 |

Cells 2 and 3 only *define* functions — running them posts nothing. Usage
examples sit commented out at the bottom of each; delete the `#` to run one.

### Daily quota
You get 10,000 units per day, and it resets at midnight Pacific.

| Call | Cost | Practical limit |
|---|---|---|
| `upload_video` | 1,600 | ~6 uploads/day |
| `reply_to_comment` | 50 | ~200 replies/day |
| `read_latest_comments` | 1 per page of 100 | effectively unlimited |

---

## 4. Backups

The Data API has no download endpoint, so Cell 3 uses `yt-dlp` against your
**uploads playlist**, which includes Shorts — the `/videos` tab does not.

Each finished video id is appended to `_backup_archive.txt` in your backup
folder, so re-running only fetches what is new. Delete that file to force a
full re-download. Each video is saved with its `.info.json` (title,
description, tags, stats), thumbnail, and captions.

Videos download to the VM's local disk first and move to Drive only after
success — writing straight to the Drive mount corrupts `yt-dlp`'s merge step
on large files.

**If you hit "Sign in to confirm you're not a bot":** Colab runs on
datacenter IPs that YouTube rate-limits, and this got much more common
through 2025. In order of effort: re-run later; uncomment the
`player_client` line in `build_download_options()`; or drop a
Netscape-format `cookies.txt` into your secrets folder (also required for
**private** videos, which yt-dlp cannot see otherwise). Since exporting
cookies from an iPhone is awkward, the fallback for a guaranteed complete
archive is Google Takeout (`takeout.google.com`, select YouTube) — slower,
but official and immune to bot checks.

---

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `client_secret.json missing` | File is not in `SECRETS_FOLDER_PATH`, or is still named `client_secret_1234....json`. Rename it exactly. |
| `Safari cannot connect to the server` | **Expected.** Copy the whole URL from the address bar and paste it into Colab. |
| `No ?code= found` | You pasted the consent-screen URL instead of the *failed localhost* URL. Redo it and copy the URL from the page that failed. |
| `access_denied` | Your account is not a test user, or the app is unpublished. See step 6. |
| `invalid_grant` after ~a week | The 7-day Testing expiry. Publish the app, delete `token.json`, re-run Cell 1. |
| `quotaExceeded` | 10,000 units spent. Resets midnight Pacific. |
| Video uploaded but stuck private | The compliance-audit restriction. Flip it in the Studio app, or request an audit. |
| `redirect_uri_mismatch` | Your client is a "Web application". Delete it, create a **Desktop app** client. |
