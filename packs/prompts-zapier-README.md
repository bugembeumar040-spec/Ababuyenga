# Zapier wiring — `prompts-zapier.csv` / `.json`

48 rows, one per shot. Prompts are **fully expanded** — the style block and the recurring-element anchors (`PLAIN`, `HANDS`, `LEDGER`, `MARKET`) are already substituted into every row, because Zapier won't resolve tokens. Each row's `prompt` is ready to POST as-is.

## Columns

| Column | Use |
|---|---|
| `shot_id` | `01`–`48`, zero-padded so filenames sort correctly |
| `section` | Which script section it belongs to |
| `tc_est` | Estimated timecode. **Estimates** — re-derive from the real VO render |
| `hold_seconds_est` | Weighted screen time, scaled to a 29:30 runtime. Sums to ~30 min |
| `prompt` | Full expanded prompt. Send verbatim |
| `negative_prompt` | Base negative + per-row additions for risky shots |
| `aspect_ratio` | `16:9` throughout |
| `seed_group` | Rows sharing a value **must share a seed** — see below |
| `notes` | Human instruction. Do **not** send to the model |
| `status` / `output_url` | Left empty for Zapier to write back |

## Zap shape

```
Trigger        →  Zapier Tables (import the CSV) or Google Sheets
Loop           →  Looping by Zapier, one iteration per row
Action         →  POST to your image API
                  prompt          = {{prompt}}
                  negative_prompt = {{negative_prompt}}
                  aspect_ratio    = {{aspect_ratio}}
                  seed            = {{seed_group}} → resolved via the lookup below
Action         →  Upload result to Drive, filename {{shot_id}}_{{section}}.png
Action         →  Write URL back to {{output_url}}, set {{status}} = done
```

Add a **Filter** step on `status is empty` so re-runs only fill gaps instead of regenerating the whole sheet. On a 48-row loop that's the difference between one credit and forty-eight.

## Seed groups — the one thing that will break the edit

Five groups. Rows in a group must be generated with the **same seed** or the visual continuity fails on screen:

| Group | Rows | Why |
|---|---|---|
| `plain` | 01, 48 | The callback pair. Same location, midday → dawn. Different seeds and the ending doesn't land |
| `rain` | 07, 08, 29, 30 | 07 and 08 are the same patch of earth before and after rain — the *riba* root made visible. This is the most important pair in the video |
| `coins` | 11, 12, 13, 27, 28, 40, 41 | Same currency throughout, or it reads as different eras |
| `paper` | 15, 16, 17, 20, 22, 25, 26 | Same parchment stock and lighting |
| `papyrus` | 46, 47 | Same fragment seen twice |

Practical approach: run one row per group first, keep the seed that works, then pass it as a constant for the rest of that group.

## Known failure modes

**Rows 46 and 47** are the hardest generations in the sheet. Models will put writing on papyrus almost every time. `blank surface with no script whatsoever` is in the prompt and the negative for both. If it still writes: generate the mount and lighting empty, composite the fragment separately. On this channel a plausible-looking pseudo-Arabic fragment is worse than no shot at all.

**Row 02** drifts modern — "immense crowd on a gravel plain" pulls contemporary Hajj imagery. The row carries extra negatives for ihram towels, tent cities, Jamarat and the clock tower. Push the altitude until no face resolves at 100% zoom; regenerate rather than crop.

**Rows in the `coins` group** — models reflexively stamp portraits or script on currency. Every one of those rows carries `stamped coins, minted design, portrait on coin`. Check each output.

**Row 31** must have exactly **eight** bowls — they're the eight zakat categories, and §22 of the script calls back to them. Count them before accepting.

## Channel rules baked into every row

- No figural depiction of any prophet or companion — no face, no back, no silhouette, no light-blur where a person would be
- No generated Arabic script anywhere. All Arabic burns in during the edit from the verified mushaf
- Human presence limited to hands and distant unresolvable figures
