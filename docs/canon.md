# Canon — Finance % Decoded

Everything reusable across videos. Extracted from the Klarna and credit-card packs so
a new script never has to load an old pack to recover them. If a rule here conflicts
with a per-video pack, the pack wins for that video only — then update this file.

---

## Format

9:16 vertical · 1080x1920 (stills may render 2048x3640 and downscale, to leave
headroom for the push) · 30–60s total · subject in the lower two-thirds, clean
headroom above for captions.

---

## House style

Stylised low-poly 3D. Matte clay shading, soft subsurface material on characters.
Near-photorealistic surface texture on everything physical — card stock fibre, paper
grain and deckled edges, brass patina and specular hits, wool, walnut grain. Real
cast contact shadows anchoring every object.

Lighting is always the same instrument: **one hard key**, usually camera-left and
raking, throwing a single long defined shadow the other way; deep near-black
surround; **one warm amber accent** — a rim, a glint, a practical off-frame. Cool
neutral grade otherwise. Shallow cinematic depth of field throughout.

Camera is slow and deliberate or locked off. Pushes are 4–13% total travel, eased
out, never linear. Orbits and arcs 12–15 degrees. **There is no fast camera move
anywhere in this house style.** Where a clip names a move, set it with the
platform's motion control preset rather than trusting prompt text — presets hold,
described motion drifts.

Stills are framed 10–15% wider than the equivalent video prompt, because each one
gets a push in the edit and the push crops in.

---

## Palette

| Role | Hex |
|---|---|
| Terracotta (accent, AMIR's shirt, caption accent word) | `#E85F42` |
| Deep navy (institution — clerk, sleeves) | `#1E3A5F` |
| Cream (cards, paper, trousers, beanies) | `#E8DCC8` |
| Caption fill | `#F5F0E6` |
| Caption outline / near-black ground | `#0A0C10` |

Terracotta is the person. Navy is the institution. Cream is the paper the argument
is written on. Do not add a fourth colour.

---

## Characters

Both have a **COMPLETELY BLANK featureless head — no eyes, no nose, no mouth, a
smooth matte tan block.** Simplified geometric anatomy. This is non-negotiable and
the negative prompt enforces it; a face appearing is a regenerate, not a fix.

**AMIR** — terracotta `#E85F42` t-shirt, cream `#E8DCC8` trousers, white sneakers,
cream beanie.

**THE CLERK / SHOPKEEPER** — deep navy `#1E3A5F` apron over a cream shirt, navy
bucket hat.

**Reference frames are locked assets.** Reuse the approved AMIR and clerk frames
across videos; do not regenerate them from scratch. If they are lost: generate the
cleanest full view of the character first, regenerate until the head is completely
blank, save that frame, and feed it as the reference image on every other clip that
character appears in. Character drift between clips is what kills this format.

---

## Negative prompt

Paste once per shoot, applies to every generation.

```
facial features, eyes, mouth, nose, lips, eyebrows, face, portrait, text,
lettering, numbers, logos, brand names, watermark, signature, cartoon outlines,
cel shading, flat vector, anime, 2D illustration, distorted hands, extra fingers,
extra limbs, morphing objects, warping architecture, camera shake, whip pans,
blurry, low resolution, oversaturated, plastic sheen, uncanny, stock-photo smiles
```

For stills, drop the motion terms — `morphing objects, warping architecture, camera
shake, whip pans` — and add the frame ones: `HDR glow, oversaturation, blown
highlights, tilted horizon, clutter, busy background, composite look`. Everything
else carries over; the blank-head and no-text terms are the load-bearing half and
never change.

---

## The burn-in-the-numbers rule

**Never generate text, numbers, or logos inside an image or clip.** Every prompt
asks for blank cards, blank screens, blank statements, empty ruled boxes on purpose.
All figures are typographic, burned in during the edit.

Give each video one **two-numbers-in-collision** beat — the device that carried
"£1,461 a month. Only £420 buys your house." and "1% BACK vs 24.9% APR". Set the
small number small and the large number large, and give that beat the most
typographic weight in the film.

---

## Caption spec

Heavy condensed sans. **CAP 1** uppercase at 62% height; **CAP 2** sentence case at
76%. Fill `#F5F0E6` with a 2px `#0A0C10` outline, accent word in `#E85F42`.

CAP 1 lands on the first stressed syllable of the line, CAP 2 one beat later, both
clearing 200ms before the cut.

Where CAP 1 is a single word doing the whole hook, give it the full box — hold it
with no CAP 2 until the beat has landed.

---

## Voiceover

ElevenLabs v3 · stability 45–55 · similarity 75 · speed 1.0.

Tags sparse — `[serious]`, `[whispers]`, `[emphatic]`, `[calm]`, `[warmly]`. Full
stops between numbers do the pacing, not tags. Estimate at ~150wpm when drafting,
but **the recorded VO is the only real timing** — re-derive IN/OUT points from it
before generating anything.

If v3 rushes the one line the video rests on, generate that scene as its own pass
with the line isolated and cut it in.

---

## Packaging

- **Title: declarative, not interrogative.** "Is Klarna Halal?" was retitled to
  "You've Already Paid Klarna." at publish and the declarative won. The "Is X Halal?"
  pattern stays available as an alt, but ship the statement.
- **Never put "riba" in a title.** English SERP is polluted by the Royal Institute of
  British Architects. Description and spoken script only.
- **Length** 30–60s (slate rule).
- **Description** 600+ characters. Do not ship the 197-char boilerplate.
- **Tags** total under 500 characters — hard YouTube limit, silently rejects above it.
- **Thumbnail** one isolated object, one word beside it in terracotta, nothing else.
- **Series framing** in the closing caption ("Part 3: …") is the cheapest retention
  available and is currently unused across 21 uploads.

---

## Accuracy posture

Three habits that keep the comment section survivable:

1. **Attribute jargon precisely.** "The card industry has a word" is accurate for US
   card-industry slang like *deadbeat* / *revolver*; claiming it as a UK term is not.
   The FCA's own vocabulary for the same split is *transactors* vs *revolvers* — worth
   citing in the description as corroboration.
2. **Present figures as illustration, never as one product.** Representative ranges,
   no named issuer on screen.
3. **Never issue a fiqh verdict in your own voice.** Make claims about a product's
   economics and let the contrast carry it — the way murabaha carried the Klarna pack.
   The fiqh on cards where interest is never actually incurred is genuinely differed,
   and a verdict in the VO invites the one argument that cannot be won in a reply.
