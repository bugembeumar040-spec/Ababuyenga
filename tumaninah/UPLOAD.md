# Upload pack — Ṭumaʾnīnah (Ar-Raʿd 28)

## What I cannot do, and why

**There is no upload tool in this session.** The vidIQ connector has
`vidiq_update_video`, which edits title, description, tags, privacy and schedule
on a video **already on your channel** — it cannot upload a file, and it cannot
set a thumbnail (vidIQ's own note: "Thumbnail updates use a separate endpoint and
are not supported by this tool").

`vidiq_authorize_with_youtube` needs you to complete an authorisation widget, and
this session is non-interactive, so that handoff cannot happen here either.

So the upload itself is yours. Everything below is ready to paste.

## Schedule

**Publish 22:00 today, Friday 21 August — UAE time.**
In the scheduler field that is `2026-08-21T18:00:00Z` UTC.

The 21:00 slot is gone — rendering the master and fixing a card that landed on
the wrong frame took the time. 22:00 is still well inside the Gulf evening
window and leaves headroom for YouTube to process an eighteen-minute 1080p file
before it goes live.

Why that slot:

- Friday evening opens the UAE weekend (Sat–Sun), so the audience is free rather
  than winding down for a work night.
- Gulf YouTube viewing peaks 20:00–23:00 local. Publishing at 21:00 puts the
  video into the front of that window with room to gather early signal, rather
  than arriving after it.
- It is after ʿIshāʾ, which suits an eighteen-minute reflective study far better
  than a commute slot.
- It travels well: 18:00 London, 13:00 New York, 22:00 Karachi, 20:00 Cairo and
  Istanbul. Gulf evening, UK early evening, US East midday.

If you cannot get it uploaded and processed by 21:30, take **23:00 UAE**
(`2026-08-21T19:00:00Z`) rather than rushing. Do not schedule a slot the upload
cannot make — a missed schedule publishes late and unannounced.

## The file

`master/tumaninah-1080p.mp4` — 1920×1080, 18:07, H.264, AAC 48 kHz, −16.4 LUFS,
89 MB. Committed to the repo so you can pull it.

It is a 776 kb/s encode of a 1233 kb/s master. The master itself is 164 MB, which
is over both the 30 MB I can send you directly and GitHub's 100 MB file limit, so
it stays in the container and dies with it. The difference is invisible on this
material — the picture is watercolour stills with no motion, so the bitrate is
doing almost nothing. If you ever want the higher-rate version, `timing/master.py`
rebuilds it in about fifteen minutes.

Delete the mp4 from the repo once you have downloaded it; a 89 MB binary in git
history is a cost you do not need to carry.

## Steps

1. Upload `master/tumaninah-1080p.mp4` (89 MB, in the repo).
2. Paste the title and description below.
3. Set the thumbnail to `thumbnail/thumb-flow-a.png` (the glass). Thumbnail must
   be set manually — no tool here can do it.
4. Paste the tag list into the tags field. Tags are a separate field from the
   hashtags, which are already in the description text.
5. Set **Private with a scheduled publish time** of 21:00 UAE.
6. Add the chapters — they are already in the description and will be picked up
   automatically, since the first is at 0:00.
7. Language: English. Category: Education. Not made for kids.

## Title

```
You've Read This Āyah 100 Times. You've Never Seen Half Of It.
```

## Description

In `METADATA.md`, under "Description" — paste from the line beginning
"The āyah people put on their wall" through the hashtag block.

## Tags

```
tumaninah, ar-rad 28, quran tafsir, quranic arabic, arabic word study,
hearts find rest, dhikr, sakinah, surah ar-rad, quran reflection,
islamic reminder, quran study, arabic root letters, al-fajr 27, sujud
```

## One thing to decide before you publish

Three stretches of your script were never recorded — about 3:50 — and one of them
is the whole of section 9, THE NAME AT THE END, which your own script marks
"★★ THE INVERSION — the whole video is built for this".

The Al-Fajr payoff does survive: it lands in the close at 17:40, where the
narrator says the root comes back as something other than a verb, with
`يَا أَيَّتُهَا النَّفْسُ الْمُطْمَئِنَّةُ` on screen. So the video does resolve.
It resolves in about forty seconds rather than the ninety the script gives it.

That is a judgement call and it is yours. Publishing today is entirely defensible
— the cut is coherent and the argument completes. Recording that section is
roughly twenty minutes of work and one pipeline run if you would rather it
landed at full weight.

Also absent for the same reason, and already left out of the description's
reference list: Al-Baqarah 260, Al-Anfāl 10, An-Nisāʾ 103, Ṭā Hā 124.
