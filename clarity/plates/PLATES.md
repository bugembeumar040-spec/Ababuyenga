# Plate tracking

180 plates are required: a `-line` and a `-wash` pass per scene, generated on
the same seed group so the two register when composited. Received so far: 41
images across 9 batches, stored under `inbox/`.

## Scenes covered so far

| scene | cue | what arrived | complete? |
|---|---|---|---|
| S018 | 3:26 | two wash takes (b02-1, b02-2) | no — no line pass; b02-2 rejected |
| S021 | 4:22 | two wash takes on different seeds (b01-1, b01-2) | no — no line pass |
| S099 | 29:58 | two wash takes (b01-4, b02-4) | no — no line pass |
| S013 | 2:08 | three wash takes (b03-2, b03-3, b03-5) | no — no line pass |
| S014 | 2:27 | two wash takes on different seeds (b03-1, b03-4) | no — no line pass |
| S002 *or* S034 | 0:02 / 9:15 | two wash takes on different seeds (b07-2, b08-1) | no — and which scene is unresolved |
| S003 | 0:11 | one wash take (b07-5) | no — no line pass |
| S023 | 5:05 | two wash takes (b09-3, b09-5), correlating 0.552 | no — closest pair yet, still short |
| S025 | 5:44 | two near-identical wash takes (b09-1, b09-2) | no — and see the photoreal question |
| **S027** | 6:34 | **the line pass** (b09-4) | **no — needs its wash on the same seed** |
| S004 | 0:19 | two wash takes (b07-3, b07-4) | no — no line pass |
| S010 | 1:24 | five wash takes (b04-5, b05-3, b05-5, b06-4, b06-5) | no — no line pass |
| S011 | 1:36 | four wash takes (b04-1, b04-2, b05-1, b05-4) | no — no line pass |
| S012 *or* S118 | 1:50 / 36:56 | three wash takes (b04-3, b04-4, b05-2) | no — and which scene is unresolved |
| unidentified | — | b01-3, b01-5 (hands over a block of leaves — S020 or S095) | cannot assign |
| unidentified | — | b02-3, b02-5 (open book) | cannot assign |

**0 of 90 scenes are complete.**

## One judgement call for the user

b09-img1 and b09-img2 (S025) read as photoreal — real paper fibre, shallow depth
of field, a photographic book gutter — against the pack's hard rule, *"No
photoreal anything — ink and watercolour only."* Not rejected here, because
unlike the batch-2 case this is a question of render style rather than a clear
breach.

Note that the abstract ink marks in b09-img1, img2 and img4 are **compliant**.
S025 asks for *"annotation reduced to abstract"* and S027 for *"columned pages
of abstract ink marks"*. That is not the batch-2 violation, where a vellum
scrap carried script no prompt had asked for.

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
| passes | `-line` + `-wash` | **1 line pass, 40 wash, 41 total** |
| seed | shared across a pass pair | **no two images correlate above 0.37** |
| format | PNG | **JPEG** |
| size | 1920x1080 | **1376x768** — except b04-1, which came back 2752x1536 |
| ratio | 16:9 (1.778) | **1.792** |

Measuring this needed a correction. Plain saturation does not separate the two
passes, because the parchment ground is a warm tone and scores as saturated even
under pure line art. What does separate them is **chroma spread across the
non-ink area** — a wash lays down blobs of differing hue, flat paper does not.

Batch 9 settled it. **b09-img4 is a genuine line pass: 0.0023**, against
0.0367–0.0996 for all forty wash plates. That is an order of magnitude apart —
a separate class, not a lighter wash. Every earlier candidate, including
b06-img4 at 0.0367, was a wash after all.

It is `S027-line`, and it reads the prompt exactly, down to *"the columns
visibly not aligning with each other."*

**This proves the two-pass design works.** The generator produces line art when
given the `-line` block. What is still missing is a pair: S027-line has no wash
counterpart on its seed, so it composites with nothing.

## Identification

Four images cannot be matched to a scene by sight, because several prompts
describe the same objects and differ only in what is happening in them — three
prompts show two hands cropped at the wrist over parchment, and five show an
open book. Sending plates under their `SAVE AS` names makes this mechanical.

## Prompt misses

- **b04-5 (S010)** adds a bound volume with a gold clasp to the table. The
  prompt asks only for loose leaves sorted into descending stacks. The stacks
  themselves are right, and blank, as required.
- **S012 / S118 cannot be told apart by design.** The pack defines S118 as
  *"Return to S012's aerial"* — deliberately the same composition 35 minutes
  later. Only the `SAVE AS` name can separate these two.
- **S099** (both takes) has the arrows but not the subject.
- **S002 / S034 cannot be told apart by design**, for the same reason as
  S012 / S118: the pack defines S034 as *"Return to S002's composition, closer
  now."* Only the `SAVE AS` name separates them.

Batch 7 is the strongest yet on fidelity. b07-5 reads S003 exactly, down to the
cloak *"still holding the shape of a body that has gone"*, and both S004 takes
keep the centre of the frame empty as the prompt asks. The art direction is
landing; only the two-pass structure is missing. The prompt asks for
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

One plate in batch 4 arrived at 2752x1536 rather than 1376x768, so output size
is settable — it is just not set to what the pack asks for.

## The seed is now demonstrably under control

b05-img1 and b05-img4 correlate at **0.999** — different files, same image. That
is the first proof in 25 plates that a seed can be held fixed across two runs.

It isolates what is left. The pipeline can already hold a seed; it is simply
running the same `-wash` prompt on it twice. Holding that seed and swapping in
the `-line` block is the whole remaining step.

`platecheck.py` compares every captured plate against every other and reports
line passes, near-duplicates, and registering pairs.
