# Timing

Everything here is derived from `../transcript.md` plus one number: the assembled
runtime. Re-run the three scripts and the whole cut re-times.

```
python3 tumaninah/timing/parse.py            # transcript.md -> beats.json
python3 tumaninah/timing/align.py [TOTAL] [CONTENT_END]
python3 tumaninah/timing/export.py           # -> shotlist.csv, SHOTLIST.md
```

Defaults are `TOTAL=1264` (21:04) and `CONTENT_END=1185` (19:45).

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
