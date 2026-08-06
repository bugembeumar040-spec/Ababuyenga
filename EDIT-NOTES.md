# "They Call You a Deadbeat" — Track A cut

Assembled from the last 11 Higgsfield clips (all `seedance_2_0`, 9:16), aligned
to `media/creditcard-vo.mp3` and the Track A scene pack.

**Output:** `out/deadbeat_short.mp4` — 1080×1920, 24fps, 1404 frames, **58.500s**,
H.264 high/CRF 17, AAC 192k, −14.3 LUFS, −3.3 dBFS peak.
`out/deadbeat_short_vo-only.mp4` is the same picture with no sound design.

Rebuild: `build/build_base.py` → `build/build_audio.sh` → `build/render_final.sh`.

---

## The timing had to be re-derived

The pack says timings are ~150wpm estimates and to re-derive them from the
recorded VO before generating. The recording is **57.81s**, and the read is
tighter than the script — two scripted lines never made it in:

- "If you never carry a balance, you were never the customer." — dropped
- "[emphatic] None of that is an accident. That's the design." — reduced to
  "That's the design."

So the pack's scene map does not survive contact with the VO and was not used.
The VO was transcribed with word-level timestamps (faster-whisper), and cuts
were placed in the gaps **between** utterances so picture leads sound by ~0.25s
and each shot is established before its line arrives. Every cut is quantised to
a whole frame at 24fps; nothing drifts.

| #   | scene         | in     | out    | len   | frames | src in | VO line it carries |
|-----|---------------|--------|--------|-------|--------|--------|--------------------|
| A01 | the hook      | 0.000  | 3.917  | 3.917 | 94     | 3.30   | "…a word for people who pay in full" |
| A02 | the term      | 3.917  | 9.542  | 5.625 | 135    | 1.20   | "Deadbeats." / "That's the actual term…" |
| A03 | the revolver  | 9.542  | 14.292 | 4.750 | 114    | 0.20   | "The profitable one is a revolver…" |
| A04 | the product   | 14.292 | 18.083 | 3.792 | 91     | 1.15   | "So the card isn't the product…" |
| A05 | the limit     | 18.083 | 22.417 | 4.333 | 104    | 0.00   | "Why the limit goes up? You didn't ask…" |
| A06 | the rewards   | 22.417 | 28.375 | 5.958 | 143    | 0.00   | "1% back, 24.9% owed." |
| A07 | the box       | 28.375 | 33.000 | 4.625 | 111    | 2.20   | "…gets its own box. That's the design." |
| A08 | the rule      | 33.000 | 37.667 | 4.667 | 112    | 0.10   | "Riba isn't a fee you might trigger…" |
| A09 | the real sale | 37.667 | 44.000 | 6.333 | 152    | 0.40   | "A real sale takes its profit once…" |
| A10 | time          | 44.000 | 48.583 | 4.583 | 110    | 0.20   | "Riba grows while you sleep…" |
| A11 | the close     | 48.583 | 58.500 | 9.917 | 238    | 0.08   | "Pay it to zero… Follow, the fix is next." |

## Source in-points are not 0

Each clip is cut to where its action actually is, which is rarely the head:

- **A01** — the hand only enters at 3.4s. Starting at 0 would have opened the
  film on four seconds of a motionless card. In-point 3.30 puts the hand
  entering ~0.1s after the cut.
- **A05** — AMIR's beanie and head drift progressively **white** from ~4.5s.
  The scene ends at 4.33s of source for that reason, before the drift shows.
- **A07** — the fingertip taps the box at 3–6s; in-point 2.20 centres that.
- **A03 / A04 / A08 / A10** — trimmed off the head to land the action mid-shot.

## One clip needed extending

Only **A06** came up short: the scene needs 143 frames and the 5s generation
gives 121. Rather than stretch it — the pack is right that a slow-down reads
immediately — the final settled frame is **frozen for 22 frames (0.94s)**. The
scale has stopped moving by then, and the "24.9% APR" slam plus CAP2 animate
over the hold, so it is not visible.

A10 originally needed more than it had too. Instead of freezing sand mid-fall,
which would have been obvious, the A10→A11 cut was moved earlier into the
1.78s VO gap. A11 now carries 9.917s and AMIR is on screen and settled for
1.3s before "Pay it to zero" arrives, which reads as a resolve rather than a
compromise.

## Conform

Six clips generated at 720×1280 (A01, A02, A05, A07, A09, A11) and five at
1080×1920. The 720p sources are lanczos-upscaled and lightly sharpened, and
light temporal grain is applied to **everything** — that is what stops the
upscaled shots reading softer than the natives when they sit next to each other.

## Type

Anton for CAP1 and burn-ins, Archivo Narrow for CAP2. Cream `#F5F0E6`, ink
`#0A0C10` outline, terracotta `#E85F42` on the word that costs you something.
Every caption lands on a real word onset from the transcript and clears its cut
by ≥0.19s, per the pack's spec.

Two deliberate departures from the pack:

1. **Outline weight.** The spec says 2px; at 1080 wide with 100px+ type that
   disappears. CAP1 uses a 5px stroke plus a soft ink shadow. Same intent,
   scaled to the actual raster.
2. **Text budget — at most two objects on screen.** The pack lists a CAP1/CAP2
   pair *and* a burn-in number for several scenes. Rendering all three collides
   and reads as clutter, so the burn-in takes the CAP1 slot: it **replaces**
   CAP1 on 05 and 06, and **hands off** to it on 10 and 11 (verified no
   overlap at either handoff). A07 keeps all three because its number is set in
   ink on the white page — different colour, different zone, no competition.
   Scene 09's "PROFIT: FIXED AT THE SALE" is dropped outright: CAP1 and CAP2
   already say it word for word.

`£25.00` on A07 is set in ink and **scales with the shot's 10% push**, so it
reads as printed on the statement rather than captioned over it.

Legibility is handled with a per-scene scrim (0.40 on near-black A01 up to 0.82
on the blown-out A07 page). A single global value either did nothing or crushed
A11's golden hour.

## Sound

VO high-passed at 75Hz, gently compressed, two-pass loudnorm to −14 LUFS.

Three low impacts on the beats the film turns on — DEADBEAT (4.12), the APR
slam (25.64), £0.00 (50.32) — mixed well under the voice (+1.35 / +0.63 /
+0.23 dB RMS in their windows, and measurably **zero** everywhere else). No
music: this house style has none, and a synthesised bed would sit under the VO
doing no work on the phone speakers these get watched on. If the impacts aren't
wanted, `out/deadbeat_short_vo-only.mp4` is the same picture without them.

## Continuity

Both burned arguments stay burned — no merchant-fee pass-through, and the
minimum payment appears once (A07) as evidence, never explained. The back third
is the fix, paying off Klarna's "the fix is next", and nothing was cut from
09–11.

---

## Packaging

**Title:** They Call You a Deadbeat for Paying in Full
(follows the Klarna retitle — declarative, not "Is X Halal?")

**Thumbnail:** `out/thumb_deadbeat.jpg` (the word on the two-card frame) or
`out/thumb_card.jpg` (the isolated backlit card, for setting DEADBEAT beside it).

**Description** (630 chars, no "riba" in the title per the RIBA/architects SERP
rule):

> The card industry really does have a word for customers who pay in full every
> month: deadbeats. It's not an insult, it's a category — and it tells you who
> the product is actually built for.
>
> The profitable customer is a "revolver": someone who never quite clears the
> balance. UK regulators use the same split — the FCA's credit card market work
> calls them transactors and revolvers. Once you see that, the rest of the
> design stops looking accidental: the limit that rises on its own, the cashback
> that costs a fraction of the interest it earns, the minimum payment in its own
> box.
>
> Figures are illustrative of mainstream UK cards, not one product.
>
> Part 3: the halal card that actually exists.

**Tags** (198 chars): `credit card, credit card debt, deadbeat, revolver,
transactor, minimum payment, apr, cashback, halal finance, islamic finance,
riba, personal finance uk, money tips, debt free`
