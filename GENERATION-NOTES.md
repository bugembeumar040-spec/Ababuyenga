# Track A — Higgsfield generation notes

Status: **not generated.** Blocked on the unlimited requirement. Zero credits spent.

## The blocker

The brief was "generate on Seedance 2 unlimited, don't use any credits." That combination
does not exist on Higgsfield.

Checked against the live API, not assumed:

| Check | Result |
|---|---|
| `models_explore(seedance_2_0)` | `supports_unlim: true`, but account allowance `unlim: {available: false, remaining: null}` |
| Submitted A03 with `use_unlim: true` | Rejected: `"Unlimited generations aren't supported for seedance_2_0."` |
| Account | Plus plan, 238.05 credits |
| `unlim_trial_in_mcp_active` | `false` |
| `trial_status.eligible` | `false` |

Plan config shows Seedance 2.0 / Seedance 2.0 Fast as **`FULL ACCESS`** on both Plus and
Ultra — the model is unlocked, not free. The `UNLIMITED` badges apply only to image models
(Nano Banana, Nano Banana 2, Nano Banana Pro, Seedream 4.5, Seedream 5.0 Lite, Flux.2 Pro,
Kling O1 Image, GPT Image) and to **Kling 3.0** video at 720p/5s for 7 days on annual plans.
Every unlimited tooltip reads "Available on web" — those allowances do not apply to MCP
generations regardless.

**Upgrading raises the credit allowance; it does not make Seedance 2.0 free.**

## Cost, if paying in credits

Preflighted with `get_cost` (no charge):

| Config | 10s | 5s | Full pack (6x10s + 5x5s) |
|---|---|---|---|
| Seedance 2.0 · 1080p · std | 90 | 45 | **765** |
| Seedance 2.0 · 720p · fast | 35 | ~18 | ~298 |
| Seedance 2.0 Mini · 720p | 25 | ~13 | ~213 |

Balance is 238.05, so the 1080p pack the brief specifies is short by ~527 credits.

## When you're ready to run

`higgsfield-seedance2-batch.json` holds all 11 requests with locked params, ready to paste
into `generate_video_batch`.

1. Submit **index 3 (A03) alone** first — it is the clerk reference frame. Regenerate until
   the head is completely blank.
2. Save that frame, `media_upload` it, then attach to A03 / A05 / A11 as
   `medias: [{role: "image_references", value: "<media_id>"}]` to lock AMIR.
3. Submit the remaining 10 in one `generate_video_batch` call.
4. `jobs_wait` in groups of <=12, then a single `show_generation_by_ids`.

## Two things the pack assumes that the API does not do

- **No negative prompt.** Seedance 2.0 exposes no negative parameter. The pack's NEGATIVE
  block is folded into every prompt as a trailing avoid-clause instead.
- **A preset interceptor sits in front of submission.** The first A03 submit returned a
  "3D RENDER" preset recommendation rather than a job. Clear it by passing
  `declined_preset_id` on the retry.

`generate_audio` is `false` on all 11 — these are silent plates. VO and BURN-IN text are
added in the edit, never generated, per the brief.

## Still outstanding from the brief

Record the VO first and re-derive real IN/OUT into `video/src/creditcard/beats.ts`. That
file does not exist in this repo yet, and the timings in the pack are ~150wpm estimates,
not the cut. The `duration` values in the JSON are the GEN lengths (what the model outputs);
trim to the LEN column at the OUT point in the edit.
