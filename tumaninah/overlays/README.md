# Overlay cards — Ṭumaʾnīnah (Ar-Raʿd 28)

55 motion-graphics cards, one every 30 seconds across the 27:17 cut
(0:00, 0:30, 1:00 … 27:00). Rendered with Remotion from `../cards-src`.

## What is here

| folder | format | use |
|---|---|---|
| `webm/` | VP9, 1920×1080, 30fps, **alpha** | drop straight on the timeline above the art — no blend mode, no keying |
| `mp4/` | H.264, 1920×1080, 30fps, white ground | for editors that will not take alpha WebM — set the clip to **Multiply** |
| `still/` | PNG, frame 90 over white | quick review / contact sheet, not for the cut |

Filenames are `card-NN_MMSS_<headline-slug>` so they sort in cut order and
the in-point is readable without opening anything.

## Timing

Each card is 6 seconds: elements rise in over the first ~1s, hold, then the
whole card fades out over the last 14 frames. The exit is baked in, so a card
can be cut to its in-point and left alone.

## Design

Lower-third, left-anchored, clear of the centre of frame where the
watercolour art carries its subject.

- ochre rule `#C89A4A` — grows in from the bottom
- chapter pill `#E8C98A` ground, indigo text
- Qurʾānic text — Amiri, right-to-left, indigo `#2E3A56`
- headline — Inter 700; sienna `#A65A3A` when it sits under Arabic (it reads
  as the gloss), indigo and much larger when it is the hero
- sub — Inter 400, slate `#6B7280`

## Arabic

30 of the 55 cards carry Arabic. It is restricted to Qurʾānic vocabulary and
Qurʾānic quotations — the ḥadīth material in chapters 4 and 11 is left in
English rather than set in Arabic. Text is fully vowelled and rendered in
Amiri, which shapes and stacks the ḥarakāt correctly; the sūrah and āyah are
named in the sub line under every quotation.

The card content lives in `../cards-src/cards.json` — edit there and re-render
rather than editing any file in this folder.

## Re-rendering

```
cd ../cards-src
npm install
node render.mjs            # all 55
node render.mjs --only 17  # one card, by number
```
