# Regenerate B06 and B10

Two supplied stills do not match `zakat-prompt-pack.txt`. Everything else in the
set does. The build is held until these land.

Drop the replacements into `media/zakat/stills/` using the **same filenames** as
the frames they replace (`06-Figure_holding_blank_card_2K_202608122015.jpeg` and
`09-Man_standing_with_resolved_expre__202608122023.jpeg`) and the pipeline picks
them up with no edit — the scene mapping is pinned in `out/zakat-stills-map.json`.

Two changes apply to **both** prompts, because they are set-wide faults:

- **No printing on any card, paper or screen.** Eight of the supplied frames
  carry generated text (`ATM CARD`, `GLOBAL BANK`, `CITY BANK`, card numbers,
  `J. DOE`) and real VISA / Mastercard trade dress. The pack: *"Always
  unprinted; numbers are burned in at the edit"* and *"Generated text is where
  this style falls apart."* The burned-in numbers now collide with the printed
  ones, and the card-scheme marks are an avoidable monetisation flag.
- **Generate at 2K or larger.** Nine supplied frames are 768×1376, below the
  1080×1920 canvas, so they are upscaled ~1.4×.

---

## B06 · ZAKAT · replaces the collision beat's second half

**What is wrong.** The supplied frame casts **Bilal** — sand button-up shirt —
where the pack requires **Sami** in teal. Your own 16A confirms the reading:
Bilal is the tan one, Sami the blue one. It is also not a mirror of B05: the
figure sits centre rather than right, at a noticeably larger scale, so the cut
between 05 and 06 reads as a scene change instead of a one-word swap. The pack
is explicit — *"If you only art-direct one moment in this film, direct this
one"* — and *"The ONLY difference is that this figure has a face."*

```
Flat 2D vector still, plain warm cream background, composed as an exact mirror
of the INTEREST frame. SAMI stands on the right of frame in three-quarter view
with a warm open expression, one hand extended forward at waist height, palm up.

SAMI — Adult man, medium-brown skin, short black hair, dark stubble beard, thick
dark-brown outline. Teal / deep petrol-blue short-sleeved t-shirt, slate-grey
trousers, dark brown shoes.

A single COMPLETELY BLANK cream rounded card sits in mid-air to the left, angled
as though travelling toward his open palm. No printing, no lettering, no numbers,
no logos, no card-scheme marks anywhere on the card. Soft grey ellipse shadow
beneath him.

Flat 2D vector cartoon illustration, thick uniform dark-brown outlines, simple
round dot eyes, minimal facial detail, soft flat colour fills with very subtle
shading and no gradients, rounded friendly geometry, plain warm cream background,
soft grey ellipse contact shadow beneath each figure, clean children's-picture-book
clarity, generous negative space. 9:16 vertical, subject in the lower two-thirds,
clean headroom above for captions.

Match the INTEREST frame's composition exactly — same figure position, same card
position, same scale.
```

**Match to:** `05-Featureless_figure_viewing_float__2K_202608122011.jpeg`. Put the
figure at the same size and the same distance from the right edge as the grey
clerk, and the card at the same height and offset. The two frames should
differ only in who is standing there.

---

## B10 · THE REFRAME · replaces the open-hands beat

**What is wrong.** The supplied frame has Adam with **closed fists held forward**.
The line it plays under is *"It never asks you to give wealth away."* Open, empty
palms are the argument; closed fists say the opposite. The pose also duplicates
the gesture language of 14, which is a different beat.

```
ADAM stands in front view with a RESOLVED expression — level brows, mouth firm,
chin slightly lifted, both hands open and empty at his sides with palms turned
forward, fingers relaxed and clearly visible. Nothing held in either hand.

ADAM — Adult man, fair skin, short dark-brown hair, clean-shaven, soft rounded
jaw, thick dark-brown outline. Rust / terracotta short-sleeved t-shirt, ochre-tan
trousers, dark brown shoes.

A single COMPLETELY BLANK cream rounded card sits alone on a simple flat surface
beside him — no printing, no lettering, no numbers, no logos, no card-scheme
marks. Plain warm cream background, soft grey ellipse shadow beneath him.

Flat 2D vector cartoon illustration, thick uniform dark-brown outlines, simple
round dot eyes, minimal facial detail, soft flat colour fills with very subtle
shading and no gradients, rounded friendly geometry, plain warm cream background,
soft grey ellipse contact shadow beneath each figure, clean children's-picture-book
clarity, generous negative space. 9:16 vertical, subject in the lower two-thirds,
generous headroom above for captions.
```

**Headroom note.** The supplied frame has 6% clean space above the subject — the
tightest in the set — which forced this scene's caption down onto his chest. If
the replacement leaves the pack's *"generous headroom above"*, the caption
returns to the upper third with no override needed.

---

## Optional, same pass

Not blocking, but if you are regenerating anyway these are the frames whose
printed cards are most visible on screen behind burned-in type:

| Scene | File | What is printed |
|---|---|---|
| 03 | `03-Blank_card_floating_above_stack_…` | `ATM CARD`, `1234 5678 9012 4334`, bank logo |
| 08 | `07-Stack_of_blank_cards_2K_…` | `GLOBAL BANK`, card numbers, `J. DOE` |
| 12 | `11-Four_objects_sit_on_surface_…` | `CITY BANK` on the card stack |
| 16A | `17-Split_composition_of_teller_and_…` | bank cards on the counter |

After the files land:

```
cd build
node bin/inspect-stills.mjs media/zakat/stills
node bin/align.mjs   --spine scenes-zakat.json
node bin/captions.mjs --spine scenes-zakat.json
node bin/render.mjs  --spine scenes-zakat.json
node bin/audit.mjs   --spine scenes-zakat.json
```
