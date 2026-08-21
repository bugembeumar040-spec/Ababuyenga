# Timing

Everything here is derived from `../transcript.md` plus one number: the assembled
runtime. Re-run the three scripts and the whole cut re-times.

```
python3 tumaninah/timing/parse.py            # transcript.md -> beats.json
python3 tumaninah/timing/align.py [TOTAL] [CONTENT_END]
python3 tumaninah/timing/export.py           # -> shotlist.csv, SHOTLIST.md
```

Defaults are `TOTAL=1264` (21:04) and `CONTENT_END=1185` (19:45).

## How the cut is built

```
python3 tumaninah/timing/transcribe_all.py   # every upload -> asr_all.json
python3 tumaninah/timing/classify.py         # which script each upload belongs to
python3 tumaninah/timing/coverage.py         # where each take sits, and what is missing
python3 tumaninah/timing/build.py --audio    # timeline + placed.json + voiceover.m4a
python3 tumaninah/timing/export.py           # shotlist.csv, SHOTLIST.md, cards.csv
python3 tumaninah/timing/preview.py          # watchable picture lock
```

## Why none of this is estimated any more

The first pass estimated everything, and two of its assumptions were false.

**The uploads are two different scripts.** Twenty of the 34 files are an earlier
"honour your parents" video; only 14 are this study. Duration-fitting cannot tell
them apart, so the first take selection was mostly the wrong video. `classify.py`
separates them by content — 14 files score 76-97% against this script, 20 score
3% or less, and nothing sits in between. The 14 then lay out in strict script
order with no overlap or repeat, which is what confirms the set.

**The transcript's AUDIO boundaries never described this script.** Taken
literally they imply 452 wpm in one segment and 39 in another. They are ignored.

Every in-point is now a measured word timestamp from `asr_all.json`. 79 of 116
frames resolve that way.

## Frames held out of the cut

Squeezing the unrecorded frames in gave 37 of them a 1.5s flash each, stacked
past the end of the audio — a run of blank cartouches at the tail. They are now
held out: `placed.json` is the 79 frames that have a spoken line, and
`held.json` lists the rest with the line each one was written for.

## Card timing

`align_cards.py` places every card. The headline is matched as an ordered
sequence against the transcript — tolerant of how the recogniser mangles
transliteration, so "Arad" still finds Ar-Raʿd and "Tumanina" finds ṭumaʾnīnah —
and the card rises 0.7s before the phrase's first word and holds 2.2s past its
last. Length therefore comes from how long the phrase takes to say, not from a
fixed six seconds.

That replaces a bag-of-words overlap scored over a sliding window, which returned
where the *window* started rather than where the phrase was spoken. Combined with
a flat duration, it left cards reading early or late all through the cut — the
title card, for instance, ran 0.0-6.0 while "Ar-Raʿd" is spoken at 7.00.

Thirty of thirty-one cards now contain their phrase end to end. A card whose
headline has no literal counterpart in the speech takes an explicit `anchor_s`.

Run it, then `fit.py`, which resolves cards against plates, renumbers in time
order and refreshes each card's frame. It only ever shortens a card — against a
plate, never against a picture cut.

`audit.py` checks the finished cut end to end: every card contains its phrase,
matched confidently, finishes inside the runtime, is long enough to read, never
shares the screen with a plate, is numbered in order, is rendered at the length
it specifies, and leaves no stale files behind. It replaced two earlier audits
that had drifted onto fields nothing writes any more.

## Sound

`sfx.py` synthesises the ambience beds and mixes them under the voice. Nothing is
sampled or sourced — it is all generated from shaped noise with a fixed seed, so
the stem rebuilds identically and `preview/ambience.wav` never needs committing.

No instruments. This is a Qurʾānic study and music is contested for a good part
of the audience, so the palette is weather, stone and water — which is also the
sūrah's own imagery.

| from | bed | why |
|---|---|---|
| 0:00 | rain, low rumble, two thunder hits | the sūrah is named after thunder and the narration is describing the weather |
| 11:41 | quiet room tone | the glass on the table |
| 13:12 | cave tone with sparse drips | Mount Thawr |
| 16:48 | rumble and rain returning, very low | the close names the thunder again |

The voice is high-passed at 70 Hz and levelled to −16 LUFS; beds sit around
−41 dB mean, roughly 25 dB under it. Run `python3 tumaninah/timing/sfx.py` to
rebuild `ambience.wav` and `mix.m4a`.

## Trims

`cuts.json` lists stretches removed from the assembled audio, in timeline
seconds. Words inside a cut are dropped and everything after shifts back, so a
trim re-times the whole cut. One is in place: the slated section heading
"13. On a Tuesday. Real life." at 14:34, read aloud off the script.

## The three unrecorded stretches

About 3:50 of script has no audio, which is why the cut is 18:12 rather than the
21:04 the table suggested:

| script words | section | what is missing |
|---|---|---|
| 103-155 | end of 1 | "the line you have seen a hundred times" |
| 852-1053 | opening of 5 | Ibrāhīm and 2:260 |
| 1626-1989 | **all of 9** | THE NAME AT THE END — the Al-Fajr inversion |

The 37 frames whose lines fall in those gaps are spaced between their neighbours
and marked GAP in the shot list. Record the audio, re-run the pipeline, and they
snap to real timestamps like the rest.

## Old notes

## Why position is not taken from the AUDIO boundaries

The transcript labels 13 audio boundaries. Taken literally they do not survive a
reading-rate check — the section text assigned to each does not fit the duration
given for it:

| audio | words | implied wpm | given |
|--:|--:|--:|--:|
| 3 | 96 | **39** | 2:27 |
| 4 | 256 | **452** | 0:34 |
| 10 | 191 | **498** | 0:23 |
| 13 | 0 | — | 1:19 |

A narrator does not read at 452 wpm and then at 39. The boundaries are real
durations, but the AUDIO labels have drifted against the section text, so they
place images in the wrong place. The totals are fine — 3,234 words over 1,264 s
is 154 wpm, which is normal — so the total is what gets used.

Position therefore comes from the text itself: each scene's VO line is located in
the transcript, and its word offset is scaled across the runtime. 110 of 116
frames matched a line outright; the six that did not are flagged `B-ROLL` in the
shot list.

## Why the image order changed

The script was resequenced between the prompt pack and this cut. Most visibly,
the ḥadīth beat (pack ch.4, "until you are settled") now runs inside section 2,
ahead of "what we are walking toward" (pack ch.3). Frames are matched
independently and then sorted by where they actually land, so the cut order
follows the narration. 13 frames sit more than three slots from their pack
position.

## Audio 13

The final 79 s carries no scripted dialogue, so narration is laid out over the
first 1,185 s and the closing frame holds through the tail. If that recording
does contain speech, add it to `transcript.md` and re-run with
`align.py 1264 1264`.

## Files

| file | what it is |
|---|---|
| `beats.json` | transcript split into ordered spoken beats with word counts |
| `placed.json` | full per-frame record — match score, word offset, in/out |
| `shotlist.csv` | the cut: 116 rows, in/out/duration/section/frame |
| `SHOTLIST.md` | same, grouped by section, for reading |
| `cards.csv` | the 43 overlay marks and the frame each lands on |

## Preview

`preview.py` builds a silent picture lock — the frames cut to the shot list with
the cards composited on top — so the timing can be watched before the audio is
assembled:

```
python3 tumaninah/timing/preview.py                  # picture + cards
python3 tumaninah/timing/preview.py --picture-only   # frames only, much faster
```

Output lands in `tumaninah/preview/` at 1280×720. Note that the card WebMs carry
alpha, and ffmpeg will silently drop it unless the input is decoded with
`-c:v libvpx-vp9` — the script does this, but it is easy to forget when
compositing by hand.
