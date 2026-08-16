# Quickstart — ~12 minutes, phone only

> **Start here instead:** `youtube_easy_mode.ipynb` is form-driven — you
> fill in boxes and tap Run, never touching code. This document is the
> engineer's version, kept for reference and troubleshooting.

Full detail lives in `README.md`. This is the shortest path to a
working upload.

## A. Cloud Console — 7 minutes

Safari, signed in as the channel owner.
**First: tap `aA` in the address bar → Request Desktop Website.**

Tap these six links in order. They jump straight to the right page,
which skips all the menu hunting.

| # | Link | Do this |
|---|---|---|
| 1 | `console.cloud.google.com` | Project dropdown (top bar) → New Project → `Clarity Automation` → Create → select it |
| 2 | `console.cloud.google.com/apis/library/youtube.googleapis.com` | Tap **Enable** |
| 3 | `console.cloud.google.com/auth/overview` | Get started → app name + your email → Audience **External** → your email → tick box → Create |
| 4 | `console.cloud.google.com/auth/scopes` | Add or remove scopes → filter `youtube` → tick **youtube.upload** and **youtube.force-ssl** → Update → Save |
| 5 | `console.cloud.google.com/auth/clients` | Create client → type **Desktop app** → Create → **Download JSON** |
| 6 | `console.cloud.google.com/auth/audience` | **Publish app** → confirm |

Step 5 must be **Desktop app**. Web application gives
`redirect_uri_mismatch`.
Step 6 is not optional — skip it and your login dies every 7 days.

## B. Drive — 2 minutes

In the Drive app, create three folders in My Drive. Then, in Files,
rename the downloaded JSON to exactly `client_secret.json` and move it
into the third one.

- upload folder — CapCut exports
- backup folder — downloaded videos
- secrets folder — `client_secret.json` (keep unshared)

## C. Colab — 3 minutes

1. Open the notebook.
2. In Cell 1A, replace the three `YOUR_..._FOLDER` names.
3. Run Cell 1. Approve the Drive popup.
4. At the auth prompt: open the link → pick your account →
   **Advanced → Go to Clarity Automation (unsafe)** → approve both.
5. **Safari will fail to load the page. That is correct.** Copy the
   whole URL from the address bar, paste it into Colab, press enter.
6. It prints your channel name. Done — this step never repeats.

## D. First upload

Run Cell 2, then uncomment and edit:

```python
upload_video(
    VIDEO_FILE_NAME="YOUR_VIDEO.mp4",
    VIDEO_TITLE="YOUR TITLE HERE",
    VIDEO_DESCRIPTION="YOUR DESCRIPTION HERE",
    VIDEO_TAGS=["quran", "tafsir"],
    PRIVACY_STATUS="private",
    CATEGORY_ID="27",
)
```

It uploads private — that is forced by Google until your project
passes an API compliance audit, not a setting in this code. Open the
YouTube Studio app and set it public.

## Daily use after setup

Run Cell 1 (about 30s), then whichever you need:

```python
list_drive_uploads()                      # what's queued
read_unanswered_comments(HOW_MANY=50)     # what needs a reply
reply_to_comment("COMMENT_ID", "text")    # reply
backup_channel(HOW_MANY=5)                # backup
```
