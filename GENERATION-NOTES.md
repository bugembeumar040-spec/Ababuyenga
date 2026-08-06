# Track A — Higgsfield generation notes

Status: **not generated via API.** Generate in the Higgsfield app instead, where Unlimited
mode works. Zero credits spent.

## The finding

Unlimited mode **is** live on this account for Seedance 2.0 — confirmed by screenshot of the
app's Create Video panel: Seedance 2.0, 5s, 9:16, 1080p, Bitrate High, Unlimited mode toggled
on, and a `Generate Unlimited` button.

It is not reachable through the MCP API. Those are both true at once, and the split is the
whole story:

| Surface | Unlimited on Seedance 2.0 |
|---|---|
| Higgsfield app (web / mobile) | **Works** — `Generate Unlimited` |
| MCP API (`generate_video` / `generate_video_batch`) | **Refused** |

API evidence, four submission attempts:

- `models_explore(seedance_2_0)` → `supports_unlim: true`, account allowance
  `unlim: {available: false, remaining: null}`
- Every `use_unlim: true` submit → `"Unlimited generations aren't supported for seedance_2_0."`
- Retried after `select_workspace` (the sole workspace showed `is_selected: false`, a plausible
  cause) — same refusal, so that was not it
- Retried at the exact app settings including `bitrate_mode: "high"` — same refusal
- `unlim_trial_in_mcp_active: false`

Consistent with the plan config, where every unlimited tooltip reads **"Available on web"** and
Seedance 2.0 is listed as `FULL ACCESS` rather than `UNLIMITED`.

**Correction to an earlier version of this file:** it stated that no plan tier makes Seedance 2.0
unlimited, and recommended a credit top-up. That was wrong. The entitlement exists on this plan;
it is the API surface that lacks it. Do not buy credits for this.

## Do not pay for this

Generating the pack through the API would cost **765 credits** (6x10s @ 90, 5x5s @ 45, 1080p std)
against a balance of 238.05. Irrelevant now — the app path is free. Recorded only so the number
isn't re-derived later.

## Run it in the app

Paste-ready sheet with per-clip settings and tap-to-copy prompts:
`higgsfield-seedance2-batch.json` holds the same 11 prompts as structured data.

App settings — set once:

| Setting | Value |
|---|---|
| Model | Seedance 2.0 |
| Aspect ratio | 9:16 |
| Resolution | 1080p |
| Bitrate | High |
| Unlimited mode | On |
| Audio | **Off** |

Audio defaults to On in the app and must be turned off — these are silent plates, VO and BURN-IN
text are added in the edit per the brief.

Duration changes per clip; use the GEN column, not LEN:

| Clip | GEN | Clip | GEN |
|---|---|---|---|
| A01 | 10s | A07 | 10s |
| A02 | 10s | A08 | 5s |
| A03 | 5s | A09 | 10s |
| A04 | 5s | A10 | 5s |
| A05 | 10s | A11 | 10s |
| A06 | 5s | | |

Order: **A03 first** — it is the clerk reference frame. Regenerate until the head is completely
blank, save that frame, then attach it through **@ Elements** on A03 / A05 / A11 to lock AMIR.

## One thing the pack assumes that Seedance 2.0 does not do

**No negative prompt.** The model exposes no negative parameter on either surface. The pack's
NEGATIVE block is folded into every prompt as a trailing avoid-clause instead. That is weaker
than a true negative, which is why A03 is likely to need several passes before the head reads
genuinely blank.

(An API-only wrinkle, noted in case the API path is ever used: a "3D RENDER" preset recommendation
intercepts the first submit and must be cleared with `declined_preset_id`.)

## Still outstanding from the brief

Record the VO first and re-derive real IN/OUT into `video/src/creditcard/beats.ts`. That file does
not exist in this repo yet, and the pack's timings are ~150wpm estimates, not the cut. GEN is what
the model outputs; trim to LEN at the OUT point in the edit — never stretch a short clip to cover
a long scene.
