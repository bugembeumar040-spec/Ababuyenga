# Overlay cards — Ṭumaʾnīnah (Ar-Raʿd 28)

43 motion-graphics cards, one every 30 seconds across the 21:04 cut
(0:00, 0:30, 1:00 … 21:00). Rendered with Remotion from `../cards-src`.

Each card's content is drawn from what is actually being said at that mark —
see `../timing/cards.csv`, which also names the frame each card lands on top of.

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

The art behind these cards runs from bare paper to near-black storm, so indigo
type on its own is not readable everywhere. A feathered cream wash rises off the
bottom edge — 0.80 at the very bottom, gone by 430px — which lifts the type
without reading as a box. It is part of the alpha, so the WebM stays legible
over any frame.

- cream scrim `#F2EDE2` — feathered, fades in over the first 18 frames
- ochre rule `#C89A4A` — grows in from the bottom
- chapter pill `#E8C98A` ground, indigo text
- Qurʾānic text — Amiri, right-to-left, indigo `#2E3A56`
- headline — Inter 700; sienna `#A65A3A` when it sits under Arabic (it reads
  as the gloss), indigo and much larger when it is the hero
- sub — Inter 400, slate `#6B7280`

## Arabic

29 of the 43 cards carry Arabic: Qurʾānic quotations, the root vocabulary the
study turns on (`طُمَأْنِينَة`, `السَّكِينَة`, `ذِكْر`, `سُجُود`), and one ḥadīth phrase —
`حَتَّىٰ تَطْمَئِنَّ رَاكِعًا` on card 06, which is the evidence the whole word study rests
on and would be odd to leave in transliteration.

Text is fully vowelled and set in Amiri, which shapes and stacks the ḥarakāt
correctly. The sūrah and āyah are named in the sub line under every quotation,
and each fragment is held on a single line — a wrapped RTL line breaks to the
left and reads as a separate phrase.

The card content lives in `../cards-src/cards.json` — edit there and re-render
rather than editing any file in this folder.

## Re-rendering

```
cd ../cards-src
npm install
node render.mjs            # all 43
node render.mjs --only 17  # one card, by number
```
