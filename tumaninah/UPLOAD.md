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

**Publish 21:00 tonight, Tuesday 1 September — UAE time.**
In the scheduler field that is `2026-09-01T17:00:00Z` UTC.

The 21 August slot lapsed while the session was idle, so this is re-set for
today. A Tuesday is a slightly weaker slot than the Friday it was written for —
midweek evening rather than the start of the UAE weekend — but 21:00 still sits
in the Gulf evening window and travels the same way: 18:00 London, 13:00 New
York, 22:00 Karachi.

If you would rather have the stronger slot, **Friday 4 September at 21:00**
(`2026-09-04T17:00:00Z`) opens the UAE weekend and is worth the three-day wait
for a piece with no news hook.

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

If you cannot get it uploaded and processed by 20:30, take **22:30 UAE**
(`2026-09-01T18:30:00Z`) rather than rushing. Do not schedule a slot the upload
cannot make — a missed schedule publishes late and unannounced.

## The file

`tumaninah-1080p.mp4` — 1920×1080, 18:07, H.264, AAC 48 kHz, −16.4 LUFS, 89 MB.

It is **not** in the repo: the remote's pre-receive hook refuses a file that
size, and it exceeds the 30 MB I can hand over directly. It was sent to you in
four parts instead. Put them in one folder and rejoin:

```
cat tumaninah-1080p.mp4.0*.part > tumaninah-1080p.mp4
```

Windows PowerShell:

```
cmd /c copy /b tumaninah-1080p.mp4.00.part+tumaninah-1080p.mp4.01.part+tumaninah-1080p.mp4.02.part+tumaninah-1080p.mp4.03.part tumaninah-1080p.mp4
```

Then check it rejoined intact — this must match:

```
72081ec95e7d5a44a5af81210c43b389
```

It is a 776 kb/s encode of a 1233 kb/s master. The master itself is 164 MB, which
is over both the 30 MB I can send you directly and GitHub's 100 MB file limit, so
it stays in the container and dies with it. The difference is invisible on this
material — the picture is watercolour stills with no motion, so the bitrate is
doing almost nothing. If you ever want the higher-rate version, `timing/master.py`
rebuilds it in about fifteen minutes.

If the checksum matches, the file is byte-identical to what I rendered and
verified. If it does not, one part did not download fully — re-download that
part rather than re-joining the same files.

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
