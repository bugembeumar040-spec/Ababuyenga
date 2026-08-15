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
jinn-shot-pack-final.txt ─┐
                          ├─> tools/build-beats.py ─> src/jinn/beats.ts
media/sil.txt ────────────┘                           (frame-accurate cut)

public/plates/*.png ──────> tools/scan-plates.py ─> src/jinn/plates.ts
```

### The voiceover

The six recorded groups were loudness-matched to −16 LUFS, joined in order with
a 0.45s beat between groups, and written to `media/vo.mp3` (also
`public/jinn-vo.mp3`, which is what the film plays).

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

### The cut

`build-beats.py` scales the planned spine onto the real 613.91s, then walks
each of the 63 internal boundaries onto the nearest actual pause in the
recording, within ±2.6s. **59 of 63 cuts land on a real pause**; the other four
had no pause in reach and hold at their scaled position. Cuts land 40% into the
gap, so the incoming plate is up before the next line starts.

Re-run after any VO change:

```bash
npm run beats        # pass the new duration as the first arg if it changed
```

To regenerate the silence map after a recut:

```bash
ffmpeg -i media/vo.wav -af "silencedetect=noise=-38dB:d=0.30" -f null - 2>&1 \
  | grep -E "silence_(start|end)" | awk '{print $4,$5,$6,$7,$8}' > media/sil.txt
```

### The plates

None of the 64 illustrations exist yet. Every shot renders a procedural
stand-in in the house palette — right tone, right light angle, right camera
move, labelled with its shot id and its `MOVE:` line — so timing and type can
be judged now.

Drop `public/plates/S01.png` (and so on, one per shot id) and run
`python3 tools/scan-plates.py`. That shot switches to the real illustration and
nothing else changes.

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
npm run preview    # 1280x720 proof of the root-device beats
npm run render     # full 2560x1440
```
