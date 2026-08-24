# Plate tracking

180 plates are required: a `-line` and a `-wash` pass per scene, generated on
the same seed group so the two register when composited. Received so far: 15
images across 3 batches, stored under `inbox/`.

## Scenes covered so far

| scene | cue | what arrived | complete? |
|---|---|---|---|
| S018 | 3:26 | two wash takes (b02-1, b02-2) | no — no line pass; b02-2 rejected |
| S021 | 4:22 | two wash takes on different seeds (b01-1, b01-2) | no — no line pass |
| S099 | 29:58 | two wash takes (b01-4, b02-4) | no — no line pass |
| S013 | 2:08 | three wash takes (b03-2, b03-3, b03-5) | no — no line pass |
| S014 | 2:27 | two wash takes on different seeds (b03-1, b03-4) | no — no line pass |
| unidentified | — | b01-3, b01-5 (hands over a block of leaves — S020 or S095) | cannot assign |
| unidentified | — | b02-3, b02-5 (open book) | cannot assign |

**0 of 90 scenes are complete.**

## Hard reject

**b02-img2 (S018, second take)** carries generated writing: twelve-plus rows of
pseudo-script across the vellum scrap, plus a wax seal. This breaks the pack's
hard rule — *"No generated text inside a generated image; every glyph is typeset
in the edit"* — and its own negative prompt, which lists *no text, no letters,
no writing, no calligraphy*.

It matters beyond tidiness. Batch 28 of the voiceover says *"The Arabic on
screen in this video is set from a verified mushaf."* Invented script on screen
contradicts that line directly, on a channel the pack says must stay trustworthy
enough to carry a public "AI BE AWARE" comment.

## Faults running across every plate received

| | pack asks | received |
|---|---|---|
| passes | `-line` (line art, no colour, no wash) + `-wash` | **wash only, 15 of 15** |
| seed | shared across a pass pair | **no two images correlate above 0.37** |
| format | PNG | **JPEG** |
| size | 1920x1080 | **1376x768** |
| ratio | 16:9 (1.778) | **1.792** |

Saturation across batch 1 ran 93–99% of pixels above 0.15; batch 2 ran 48–98%.
A line pass would sit near zero.

## Identification

Four images cannot be matched to a scene by sight, because several prompts
describe the same objects and differ only in what is happening in them — three
prompts show two hands cropped at the wrist over parchment, and five show an
open book. Sending plates under their `SAVE AS` names makes this mechanical.

## Prompt misses

- **S099** (both takes) has the arrows but not the subject. The prompt asks for
  *a bare hillcrest with a low stone position on it*, and says *"The empty
  position is the subject."* Neither take has a hillcrest or a stone position.

## The cause, and the fix

The `-line` and `-wash` blocks for a scene are byte-identical apart from one
sentence. Diffed for S014:

    Line art only, no colour, no wash.

That sentence is the entire `-line` block. Everything received so far reads as
the `-wash` block, which strongly suggests only the wash prompt is being pasted,
twice, on two different seeds — which also explains why no pair registers.

`S013-line-PROMPT.txt` and `S014-line-PROMPT.txt` hold the exact line prompts
for the two scenes in batch 3, to generate against and compare.
