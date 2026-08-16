# JINN — motion build

Remotion project for the 64-shot jinn film. 2560×1440, 30fps, cut against the
recorded voiceover rather than the shot pack's word-count estimates.

## Why Remotion and not Hyperframes

Hyperframes is the better tool for a single designed composition you iterate on
by hand. This is not that. It is 64 shots over ten minutes, every cut owed to a
specific pause in a specific audio file, with the shot pack explicitly warning
that the printed timings are estimates to be re-derived once the VO exists.

That makes the spine a data problem, not a layout problem:

- the cut is generated from the VO's silence map, so a recut VO is a re-run of
  one script, not 64 hand nudges;
- every camera move is parsed out of the pack's own `MOVE:` line, so the file
  on disk stays the source of truth;
- the whole thing is text in git and renders headless in CI.

Hyperframes would have meant re-typing all of that by hand and re-typing it
again the next time the voiceover changes.

## Pipeline

```
public/jinn-vo.mp3 ─> tools/align-vo.py ─> media/vo-align.json
                     (word-level ASR,              │
                      matched to the script)       │
jinn-shot-pack-final.txt ──────────────────────────┤
                     (MOVE specs, flags)           v
                                    tools/build-beats.py ─> src/jinn/beats.ts
                                                            (the cut + DROPPED)

delivered art ─┐
               ├─> tools/import-plates.py ─> public/plates/<shot-id>.png
plate-map.json ┘                                   │
                                                   v
                                 tools/scan-plates.py ─> src/jinn/plates.ts
                                                        (presence + tone)
```

### The voiceover

The six recorded groups were loudness-matched to −16 LUFS, joined in order with
a 0.45s beat between groups, and written to `public/jinn-vo.mp3` — that file is
the master and it is what the film plays.

| group | duration |
|---|---|
| 1 | 1:47.00 |
| 2 | 1:26.44 |
| 3 | 1:03.71 |
| 4 | 2:33.97 |
| 5 | 2:25.55 |
| 6 | 0:54.99 |
| **merged** | **10:13.91** |

The pack targeted 11:11. The recording came in 57s shorter, which is why the
printed timings could not be used as-is.

### The cut — force-aligned to the words

`tools/align-vo.py` transcribes the VO with word timestamps and matches that
transcript against the shot pack's own VO lines, so every shot is placed under
the line it is captioned with. `tools/build-beats.py` then turns that into
`beats.ts`, cutting 40% into the gap between one line ending and the next
starting.

```bash
python3 tools/align-vo.py        # --asr to re-transcribe after a VO change
python3 tools/build-beats.py 613.91
```

`build-beats.py` asserts that every shot fully contains its own spoken line and
prints the count. It is currently **56/56**.

**This replaced a worse method, and the difference matters.** The first cut
scaled the pack's planned timings onto the real duration by a single ratio and
snapped each boundary to the nearest pause. That produced captions that drifted
off the voiceover, because it was wrong in three independent ways:

1. **The recording did not compress evenly.** Group 1 came in at 107.00s
   against a planned 107s — a ratio of 1.0 — while the film overall came in 9%
   short. Every shot in that stretch was pulled early against audio that had not
   compressed at all.
2. **Eight shots are not in the recording at all.** The VO was read from a
   shorter script — the pack's own CUT 1 and CUT 2, applied at record time, with
   S16b kept. Placing shots for lines that are never spoken displaces every shot
   after them.
3. **S29 and S29b are spoken in the opposite order to the pack**, as are the two
   closing lines.

A silence map cannot see any of that. A pause tells you someone stopped talking,
not which line they stopped in the middle of. The words can, so the words are
what the cut is built from now, and the cut order is the recording's order.

### Shots not in the voiceover

> S07 · S07b · S07c · S14 · S14b · S15 · S15b · S16

`beats.ts` exports these as `DROPPED` and the film does not place them. Their
plates stay in `public/plates/` and their entries stay in `captions.ts`, so if a
fuller VO is ever recorded they return by re-running the two tools — no art and
no type edit is lost.

### The plates

All 64 illustrations have landed. They arrived with generator filenames
(`IMG_7284.png`, `Clay_oil_lamps_...jpeg`) carrying no shot information, so
`tools/plate-map.json` holds the pairing — each one matched by subject against
that shot's `PROMPT` block — and `tools/import-plates.py` applies it:

```bash
python3 tools/import-plates.py [source-dir]
python3 tools/scan-plates.py
```

Sources are 1365×768 and are centre-fitted and resampled to 2560×1440. That is
a 1.9× upscale, which is why the camera overscans only as far as each shot's
own move needs instead of a flat 14% on every shot.

24 variants were delivered for compositions that need one frame. Those go to
`public/plates/alt/<shot-id>--<n>.png` rather than being thrown away, so
changing which take is used is a rename.

All 64 shots have art. The procedural stand-in stays in the codebase because it
is what lets the film cut and render before the illustrations exist, and it
comes back automatically for any shot whose plate is removed.

That count is derived, not tracked. `scan-plates.py` reads every shot id out of
the generated cut, compares it to what is actually in `public/plates/`, and
writes the answer to `src/jinn/plates.ts` as `PENDING` — so "what is still
missing" is always computed from the two things that can't lie, and it warns
about any plate whose filename matches no shot in the cut. It prints on every
run:

```
64/64 plates: 52 light, 12 dark
pending (0): none
```

Two picks in `plate-map.json` depart from the letter of the prompt and are
recorded under `_calls` there:

- **S24b** wants a close-crop of the bare tabletop where the notes were. The
  delivered frame is the same table from the payer's seat, now bare, with the
  empty chair opposite — the same beat, played wider.
- **S25b** wants the traveller *standing* at the valley mouth. The pick is a
  seated figure instead: the VO line is "you're sleeping out in the open", and
  S25 already carries the standing-in-the-valley frame, so the faithful version
  would have repeated the shot before it. It is in `alt/` if you disagree.

### Plate tone

`scan-plates.py` also measures the mean luminance of the band each caption
occupies. The delivered art runs from bare parchment (52 plates) to a full
indigo night wash (12), and cream type dies on the first while ink type dies on
the second. Rather than hand-tag 64 shots, the type layer reads that number and
picks ink-on-paper or cream-on-night per shot — which is also the only way to
keep the black scrim out of a film whose style sheet forbids black paint.

## The motion layer

Nothing in here fights the house style. No glow, no fast camera, no bounce.

**One sheet.** `PaperGrain` and `Vignette` sit above every shot and never cut.
The tooth and the cockle stay registered across all 64 joins, which is the
single cheapest thing stopping 64 generated images from reading as 64
unrelated images.

**Camera.** Each `MOVE:` line is parsed to a zoom and a drift, applied as total
travel across the shot and eased out. Shots the pack marks *hold dead still*
get exactly zero transform — that stillness is load-bearing in the edit. They
get drifting paper motes instead, so a locked frame reads held rather than
frozen.

**Cuts.** Four-frame dissolve everywhere, except the peak (S22) and the hard
turns (S20b, S22b, S28c, S11b, S24b, S02b), which cut on the frame.

### Kinetic typography

`src/jinn/captions.ts` is the type edit. It is deliberately not a transcript —
the VO says every word already, and burning it all in doubles the reading load
and flattens the emphasis. Typeset are the fragments worth stopping on, the
four corrections, and the citations.

Five modes, in order of how hard they hit:

- **root** — the J‑N‑N device. The three root letters carry ember *inside* each
  cognate: JINN → JANNA → JANEEN → MAJNOON → JUNNA. The family is visible
  before it is argued, which is the strongest kinetic idea the script contains
  and the one the pack already asks for at S06b.
- **strike** — the wrong claim set, struck through with a drawn ink rule, then
  replaced. One per correction; a numbered chip counts 1–4 in the corner.
- **hard** — no stagger, whole line on one frame. S20b "and nobody noticed",
  S22 the peak.
- **hold** — dead still, wide tracking, slowest reveal. Every SILENCE shot.
- **bleed** — the default. Words arrive out of focus and sharpen as the fibre
  pulls them in, staggered, with a drawn rule under the emphasis run.

Arabic is never typeset here. The pack's rule is that all of it is burned in
from a verified mushaf, so citations run as Latin transliteration slugs
(`AL-KAHF · 18:50`) and any Arabic plate goes in `public/plates/` like the
illustrations.

## Commands

```bash
npm install
npm run beats      # re-derive the cut from the VO
npm run studio     # scrub it
npm run preview    # 1280x720 proof of the last third
npm run render     # full 2560x1440
```
