# Overlay cards — Ṭumaʾnīnah (Ar-Raʿd 28)

32 motion-graphics cards across the 18:07 cut, plus 10 āyah plates — 42 overlays,
never two at once. Rendered
with Remotion from `../cards-src`.

Cards sit at roughly 30-second intervals but are anchored to the line each one
glosses, not to the clock — on a fixed grid they drifted up to 18s from the words
they name. Each is pre-rolled one second so its animation finishes as the line
lands, clamped so it never fades up over the previous frame.

Each card's content is drawn from what is actually being said at that mark — read
off the transcribed audio, not the written script, so the wording matches the
delivery (the recording says "not forced numbness" where the script said
"not sedation"). `../timing/cards.csv` has the grid and the frame under each card.

Section 9, THE NAME AT THE END, was never recorded, so the Al-Fajr address is
carried by card 36 in the close rather than by a section of its own.

## What is here

| folder | format | use |
|---|---|---|
| `webm/` | VP9, 1920×1080, 30fps, **alpha** | drop straight on the timeline above the art — no blend mode, no keying |
| `mp4/` | H.264, 1920×1080, 30fps, white ground | for editors that will not take alpha WebM — set the clip to **Multiply** |
| `still/` | PNG, frame 90 over white | quick review / contact sheet, not for the cut |
| `plates/` | VP9 alpha + PNG | āyah plates for the empty cartouche frames |

## Fitting

`../timing/fit.py` resolves cards against plates. A card carrying across a picture
cut is ordinary editing and is left alone; a card competing with a full-frame
āyah is not. Five cards were dropped where the plate states the same beat, and
cards whose line lands within 1.5s of a plate's end are held back to start as the
plate clears — their line then arrives a moment before the card, which is the
trade. `../timing/cards_dropped.json` records what went and why.

## Plates

Ten frames in the pack are empty illuminated cartouches and banners. They are
blank on purpose: a generated image cannot be trusted to render Qur'ānic script,
which is what produced the malformed Arabic in the early batches. The interior
was left bare so the text could be set here instead.

Each plate carries the āyah actually being spoken over that frame, centred inside
the cartouche, and holds for the length of the shot. Where a card at the same
moment carried the same āyah, the card's Arabic was dropped — the plate states it
full size and the card glosses it.

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

23 of the 37 cards carry Arabic: Qurʾānic quotations, the root vocabulary the
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
node render.mjs            # all 37
node render.mjs --only 17  # one card, by number
```
