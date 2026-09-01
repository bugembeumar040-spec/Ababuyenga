# Pure Profit — Zapier run sheet

Two pastes and the Zap builds 33 frames.

`pure-profit-frames.tsv` is tab-separated, so it pastes straight into
Zapier Tables or Google Sheets — one cell per column, no import dialog,
no quote mangling. (CSV would need quoting on every row because the
prompts are full of commas; one bad paste and the whole sheet shifts.)

## Columns

| Column | Use |
|---|---|
| `frame` | 01–33, matches the beat numbers in `pure-profit-VO.txt` |
| `tc_in`, `dur_s` | where it sits in the 5:00 edit |
| `act` | 1–6, matches the VO acts |
| `label` | human name for the beat |
| `seed_group` | **which frames must share a seed — see below** |
| `burn_in` | text to add in the edit, never in the prompt |
| `move` | the Ken Burns move; this is the entire animation |
| `prompt` | the only field the Zap sends |

## PASTE 1 — the table

New Zapier Table → paste the TSV including the header row.

## PASTE 2 — the prompt wrapper

Do **not** put style or negative-prompt text in the table. It's identical
on all 33 rows, and repeating it means editing 33 cells when you want to
change the look. Put it in the Zap action as static text around the
dynamic field:

**Prompt field:**

```
{{prompt}}. Photographic, cinematic still, 9:16 vertical, shallow depth of field, desaturated greys and greens, overcast natural light, one warm practical source, film grain, no text anywhere in frame.
```

**Negative prompt field:**

```
facial features, eyes, mouth, nose, lips, face, portrait, club badge, crest, emblem, sponsor logo, kit manufacturer logo, competition logo, nameset, shirt number, recognisable footballer, celebrity likeness, identifiable stadium, broadcast overlay, scoreboard graphics, text, lettering, numbers, logos, brand names, watermark, signature, cartoon outlines, cel shading, flat vector, anime, 2D illustration, distorted hands, extra fingers, extra limbs, camera shake, blurry, low resolution, oversaturated, plastic sheen, uncanny, stock-photo smiles, crowd celebration, confetti
```

If your model takes no negative-prompt parameter, append it to the prompt
as `--no <list>` or the equivalent for that model.

## The Zap

1. **Trigger** — Zapier Tables, *New Record*. Pasting 33 rows fires 33
   runs. Nothing else needed; no Looping step.
2. **Action** — your image model. Zapier's built-in image apps come and
   go, so the reliable route is **Webhooks by Zapier → POST** to the API
   you're actually on, with `{{prompt}}` wrapped as above.
3. **Delay by Zapier — 5 seconds.** Add this before the generate step.
   33 records fire near-simultaneously and most image APIs will rate-limit
   the burst. This step is the difference between 33 images and 11 images
   and 22 errors.
4. **Upload** — Google Drive, into one folder.
5. **Update Record** — write the file URL back to a `url` column so you
   can see at a glance which frames failed and re-run only those.

**Task cost:** 33 records × 4 steps ≈ 132 tasks per full run. Test with
two or three rows before you paste all 33.

## Seed groups — the one thing to get right

Frames in the same `seed_group` share a room, a floor or a wall and
**must be generated from the same seed**, or the cuts between them read as
different locations and the argument falls apart.

Generate the four **ANCHOR** rows first, save each seed, then run the rest
of that group with the seed locked:

| Group | Anchor | Then |
|---|---|---|
| `GROUND` | **16** | 03, 32, 33 |
| `ROOM` | **08** | 10, 11, 12, 13 |
| `DESK` | **14** | 15, 20, 24, 30 |
| `LEDGER` | **05** | 06 |
| `RAIL` | **21** | 22 |

Rows with an empty `seed_group` are standalone and can run in any order.

`ROOM` matters most: 08 → 10 → 11 → 12 is the same floor with the light
changing, and that sequence is where the film does its arithmetic. `RAIL`
(21 → 22) is a two-frame cut on the identical wall — different seeds there
is the most visible failure in the set.

So: run the anchors as a five-row table first, lock the seeds into the
group rows, then paste the remaining 28.
