# Ṭumaʾnīnah — delivery status

Everything in the pack is delivered. This file used to carry the cut order and a
27:17 card grid; both are now generated from the voiceover instead of being
maintained by hand, so it points at those rather than repeating them.

| deliverable | state | where |
|---|---|---|
| 116 scene frames, 16:9 | complete, on disk | `images/` |
| cut order, in/out per frame | generated from the VO | `timing/SHOTLIST.md`, `timing/shotlist.csv` |
| 43 overlay cards, one per 30 s | rendered | `overlays/`, grid in `timing/cards.csv` |
| card content | editable source | `cards-src/cards.json` |

Runtime is **21:04**. Both the shot list and the card grid regenerate from
`transcript.md` — see `timing/README.md`.

## Six frames with no line in this cut

Scenes 29, 30, 30B, 80, 81 and 81B were written against script lines that did not
survive into the recorded cut. They are parked beside their neighbours and marked
`B-ROLL` in the shot list — usable as cutaways, or droppable without a gap.
