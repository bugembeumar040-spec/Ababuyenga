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

## Source audit vs the Track A run sheet

The run sheet specifies Seedance 2.0 / 9:16 / **1080p** / High bitrate / audio
off, with the A03 clerk frame attached via `@ Elements` on A03, A05 and A11.
Checked against the generation params of all eleven:

| clip | gen | delivered | `@ Elements` | verdict |
|------|-----|-----------|--------------|---------|
| A01  | 10s | **720p**  | —            | under spec |
| A02  | 10s | **720p**  | —            | under spec |
| A03  | 5s  | 1080p     | is the ref   | to spec |
| A04  | 5s  | 1080p     | —            | to spec |
| A05  | 10s | **720p**  | A03 ✓        | under spec |
| A06  | 5s  | 1080p     | A03 (stray)  | too short for its scene |
| A07  | 10s | **720p**  | —            | under spec |
| A08  | 5s  | 1080p     | —            | to spec |
| A09  | 10s | **720p**  | —            | under spec |
| A10  | 5s  | 1080p     | —            | to spec |
| A11  | 10s | **720p**  | **none**     | under spec |

Model, ratio, bitrate and `generate_audio: false` are correct on all eleven —
the run sheet's audio warning landed.

**Every 10s clip came out 720p and every 5s clip came out 1080p**, with no
exceptions. The split falls exactly along duration, which reads as the
resolution resetting when duration changed rather than eleven separate slips.
It is **not** a model limit: `seedance_2_0` accepts 4–15s, and 1080p requires
only `mode=std`, which all eleven already used. The long clips are re-generable
at 1080p as they stand.

**A11 was generated with no reference**, against the spec. Comparing AMIR in
A05 (which does carry the A03 reference) against A11 frame to frame, the build
holds — same blank tan head, same beanie, no meaningful drift — so this did not
need a reshoot. Worth attaching on any regeneration anyway.

Regeneration priority, if you go back: the six 10s clips at 1080p (removes the
upscale from six of eleven shots, including both AMIR scenes and the close);
then A06 at 10s (removes the freeze below); then A11 with the reference.
A05 will still cap around 4.5s whatever you do — the head drift is inherent.

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

## Packaging — CONFIRMED

**Title:** They Call You a Deadbeat for Paying in Full  (43 chars)

Chosen over four alternates. Declarative, per the Klarna retitle at publish;
leads with the jargon; carries "paying in full", which is the behaviour the
target viewer recognises in themselves. An "Is Your Credit Card Halal?" title
was rejected on purpose — it promises a ruling the script deliberately never
issues in your own voice.

**Thumbnail:** `out/thumb_deadbeat.jpg` (the word on the two-card frame) or
`out/thumb_card.jpg` (the isolated backlit card, for setting DEADBEAT beside it).

**Description** (839 chars — clears the 600 floor, nothing like the 197-char
boilerplate. No "riba" above the fold, per the RIBA/architects SERP rule):

> The card industry really does have a word for customers who pay in full every
> month: deadbeats. It isn't an insult — it's a category, and it tells you who
> the product is actually built for.
>
> The profitable customer is a "revolver": someone who never quite clears the
> balance. UK regulators use the same split — the FCA's credit card market study
> calls them transactors and revolvers. Once you can see that line, the rest of
> the design stops looking accidental: the limit that rises without being asked
> for, the cashback that costs a fraction of the interest it earns, the minimum
> payment sitting in its own box.
>
> A real sale takes its profit once, at the moment of sale. It never grows
> again. The difference is time.
>
> Figures shown are illustrative of mainstream UK cards, not any one product.
>
> Part 3: the halal card that actually exists.

VERIFY BEFORE PUBLISH: the FCA transactors/revolvers attribution. It is the
line doing the corroboration work in the comments, and it names a regulator.

**Tags** (17 tags, 231 chars — hard limit is 500, which YouTube rejects
silently):

```
credit card, credit card debt, deadbeat, revolver, transactor, minimum payment,
apr, cashback, credit limit, halal finance, islamic finance, riba, personal
finance uk, money tips, debt free, credit card interest, financial literacy
```

**Hashtags** (12 — YouTube ignores *every* hashtag on a video that carries
more than 15, so this stays well under. Paste as the last line of the
description):

```
#creditcard #debtfree #islamicfinance #halalmoney #creditcarddebt #personalfinanceuk #minimumpayment #apr #cashback #moneytips #financialliteracy #ukfinance
```

Order matters: only the **first three** render above the title, so
`#creditcard #debtfree #islamicfinance` are deliberately first — reach, the
video's own resolution (BALANCE £0.00), and the channel's niche.

`#shorts` is left out on purpose: YouTube classifies vertical short-form
automatically, so it spends a slot and buys nothing.

`#riba` is also left out. It is fine in the tags and description prose, but a
hashtag is a shared public feed, and that one is contested with the Royal
Institute of British Architects — the same reason it is kept out of the title.
`#islamicfinance` and `#halalmoney` reach the same audience unambiguously.

TikTok variant, if cross-posting:

```
#creditcard #debtfree #islamicfinance #halalmoney #moneytok #personalfinance #ukmoney #financialliteracy #debtfreejourney #fyp
```

**Pinned comment** (post at publish; it pre-empts the one argument you can't
win in a reply):

> "Deadbeat" is US card-industry slang — the UK regulator's word for the same
> customer is "transactor". Either way you're the one they don't make money on.
> This video is about how the product earns, not a ruling on whether any
> specific card is permissible. Part 3 is the fix.

**Publishing note.** No YouTube connector is attached to this session — the
upload is manual. The relevant clock for this video is not time of day but how
much momentum the Klarna upload still has, since this is what pays off its
"the fix is next" promise.

---

## Virality predictor — opening 14.3s

Run on `out/deadbeat_hook16.mp4` (frames 0–342, the first three complete
scenes). The tool caps at **16 seconds**, so the 58.5s cut cannot be analysed
whole; the opening was chosen because it is what decides a Short.

Model is Higgsfield `brain_activity` — predicted cortical activation mapped to
fsaverage, carrying its own disclaimer: *"Predictive proxy metrics, not
guaranteed performance or clinical measures."* It is not a view forecast.

| metric | value |
|---|---|
| overall | 49 |
| viral potential | 50 |
| brain engagement | 40 |
| **hook (0–3s window)** | **33** |
| sustain | 100 |

`sustain: 100` and `peak_second: 14` are artefacts of the 14.3s window — the
curve is still rising when the clip is cut off. Treat them as "did not decay
inside the window", not as a finding about the film.

Global activation by second — starts high, troughs at 5s, recovers:

```
 0s 0.442  1s 0.424  2s 0.400  3s 0.365  4s 0.344  <- DEADBEAT lands 4.12
 5s 0.335 (trough)   6s 0.357  7s 0.377  8s 0.404  9s 0.418
10s 0.421 11s 0.437 12s 0.423 13s 0.417 14s 0.445
```

Regions: Visual peaks 9s (0.447). Auditory/temporal and language both climb
steadily and peak at 11s (0.608 / 0.548) — the VO and captions carrying load.
Default Mode is the highest-mean region (0.673) and peaks at 5s, exactly on
the global trough.

**The finding that matters:** the hook window scores lowest, and the trough
sits on the DEADBEAT beat. A01 is a dark, near-static macro and A02 is two
motionless cards — deliberate, on-style, and the least visually arresting
three seconds available. The model cannot tell absorption from disengagement
at the trough, so read it as a flag, not a verdict.

The cheapest lever is the 1.26s of silence between "…pay in full" (ends 2.86)
and "Deadbeats" (4.12). Tightening it to ~0.7s pulls the hero word to ~3.5s
and shortens the quiet opening. **This is in direct tension with the pack's
pacing note** — "give it a full beat of silence either side, do not let the
next line ride in on it" — so it is not changed unilaterally.
