# FAE Assets Details 2026 — Report Format Specification

Reference workbook: `FAE_Assets_Details_2026.xlsx` (7.3 MB, 4 sheets, 60 embedded photos).
This is the master template. Any consolidated batch must match the structure, styling and
data-placement rules below.

---

## 1. Workbook-level conventions

| Property | Value |
|---|---|
| Font | Calibri throughout (no other typeface anywhere) |
| Header fill | Solid, theme colour 3 = **dk2 `#44546A`** (dark slate blue) |
| Header font | **Bold, white** (theme 0 = `#FFFFFF`), centred horizontally + vertically |
| Data font | Black (theme 1), centred horizontally + vertically |
| Number format | `General` on every cell — plain integer counts, no currency/decimals |
| Borders | `thin` inside a group; **`medium`** on the outer edge of each asset group and around the header band |
| Gridlines | Shown |
| Autofilter / conditional formatting | None |
| Print | Portrait, A4 (paper 9), per-sheet printer settings embedded, aggressive scale-to-fit |
| View | Zoom below 100% on wide sheets (master uses 50 / 55 / 85), gridlines shown |

**Print setup is part of the format, not an afterthought.** Three of the master's four
tabs carry portrait + A4 + an explicit print area; only `Common Area Assets Details`
omits it. Generated sheets set portrait, A4, a print area covering the used range,
`fitToWidth=1` and repeating header rows `1:2`. Fit-to-width replaces the master's
hand-tuned scale values (10% / 12% / 25%), which are per-sheet artefacts that would be
meaningless on a narrow sheet; the intent — get every column onto one page wide — is
the same. Zoom is set from sheet width: >40 columns → 50, >12 → 55, otherwise 85.

**Total row rule:** the last row of each table is labelled `Total` in column A, with the
label cell merged across the identity columns, and `=SUM(<first data row>:<last data row>)`
in every count column.

---

## 2. Header architecture (the defining feature)

Three of the four tabs use a **two-row banded header**:

- **Row 1** — asset group name, horizontally merged across all of its sub-columns.
- **Row 2** — the sub-type breakdown within that group.
- **Identity columns** (Area, Washroom no, Gender, and single-column assets) are
  **vertically merged `X1:X2`** so the one label spans both header rows.
- A single-column asset that still needs a sub-label is written as row 1 = asset,
  row 2 = sub-type, *unmerged* (e.g. `Chair` / `Baby Changing`).

The recurring sub-type vocabulary, in this order:

| Group width | Sub-headers |
|---|---|
| 4-way | `Cubicle` · `vanity` · `Handicap` · `Baby changing` |
| 3-way | `Washroom` · `Handicap` · `Baby changing` |
| 2-way | `Washroom` · `Corridors` (Wall Frames) — or `Sink` · `Water tap` (Janitor/Cleaner room) |
| 5-way | `cubicle soap` · `Lotion vanity` · `vanity soap` · `Handicap soap` · `Baby Room soap/Lotion` |

`Remarks` is always the **last column**, single-cell header, wide (30–42 chars).

---

## 3. Sheet-by-sheet layout

### 3.1 `FAE Washroom Deatils` — A1:BL51, 64 columns
Freeze `A10` · zoom 50% · print scale 10% · print area `$A$1:$BL$51`
Row heights: 1 = 55.4, 2 = 44.15, data = 33.65
Col widths: A 13.45 · B 16.18 · C 46.45 · D–E 15.45 · F–G 16.45 · H–BK 15.45 · BL 42.54
Fonts: header 16 pt bold · data 18 pt · Remarks 14 pt

| Cols | Row 1 (group) | Row 2 (sub-types) |
|---|---|---|
| A–H | Area · Washroom no · Washroom (Gender) · Urinal · Cubicle · Nappy bin · Airfreshner · Sanitizer dispencer | *(vertically merged)* |
| I | Chair | Baby Changing |
| J–M | Box Tissue Dispenser | Cubicle · vanity · Handicap · Baby changing |
| N–Q | Trays Big & Small | Cubicle · vanity · Handicap · Baby changing |
| R–U | Face Towels | Cubicle · vanity · Handicap · Baby changing |
| V–Y | Washbasin | Cubicle · vanity · Handicap · Baby changing |
| Z–AB | Cubicle | Washroom · Handicap · Baby changing |
| AC–AD | Wall Frames | Washroom · Corridors |
| AE–AG | Wall tissue holder | cubicle · Handicap · Baby changing |
| AH–AK | Dust Bins on Vanity | vanity · cubicle · Handicap · Baby changing |
| AL–AP | Lotion & Hand soap dispencer | cubicle soap · Lotion vanity · vanity soap · Handicap soap · Baby Room soap/Lotion |
| AQ–AS | Water Taps | washroom · Handicap · Baby changing |
| AT–AV | Mirror tissue dispencer | vanity · Handicap · Baby changing |
| AW–AY | Toilet roll dispencer | Washroom · Handicap · Baby changing |
| AZ–BB | Shattaf pipe | Cubicle · Handicap · Baby changing |
| BC–BE | Peddle Bin | cubicle · Handicap · Baby changing |
| BF–BG | Janitor Room | Sink · Water tap |
| BH–BK | Mirror | Cubicle · vanity · Handicap · Baby changing |
| BL | Remarks | — |

Data rows 3–24: rows 3–14 male washrooms (BLVD, GF, BASEMENT, VIP Lounge, 1F, 2F, 3F, 4F),
rows 15–24 female washrooms (FF, SF, MLB, 3rd, 4th, VIP Lounge).
Row 51 `A51:C51` = `Total`.

### 3.2 `Staff Washroom Deatils` — A1:AS19, 45 columns
Freeze `A9` · zoom 55% · print scale 12%
Row heights: 1 = 55.4, 2 = 58.4, data = 32.15 · Col widths: A 16.45 · B 50.54 · C–AR 16.45 · AS 36.45

Identity A–F merged vertically: Area · Washroom (Gender) · Urinal · Sanitary bin · Airfreshner ·
Sanitizer dispencer. G = Chair / Baby Changing. Then 3-way groups: Washbasin (H–J), Cubicle (K–M),
Wall Frames (N–O: Washroom/Corridors), Dust Bins on Wall and tissue holder (P–R),
Dust Bins on Vanity (S–U), Hand soap dispencer (V–X), Water Taps (Y–AA),
Mirror tissue dispencer (AB–AD), Toilet roll dispencer (AE–AG), Shattaf pipe (AH–AJ),
Peddle Bin (AK–AM), Cleaner room (AN–AO: Sink/Water tap), Mirror (AP–AR), Remarks (AS).

Data rows 3–18 (Loading Bay 1–8, staff lockers, drivers, valet parking, GSD, security control room).
Row 19 = `Total`, `A19:B19` merged, `=SUM(C3:C18)` across C–AR.

### 3.3 `Prayer Room Details` — A1:W18, 23 columns
Freeze `A3` · zoom 55% · print scale 25%
Row heights: 1 = 55.4, 2 = 57.0, data = 35.9 · Col widths: A 13.45 · B 13.54 · C 42.54 · D–V 15.45 · W 30.0

Identity A–C merged vertically: Area · Prayer Room no · Washroom (Gender).
`D1:M1` merged **ablution group, label left blank** → Tap · Sink · Hand soap · Hand shattaf ·
Shoe cabinet · Wooden Bench · Dust bin / interfold · door mat · Hangers · Seating.
`N1:T1` = `Prayer room` → Air freshner · Chairs · wall clock · Prayer mat holder · Book stand ·
Cloth cabinet · Inam stage. `U2` = Quran, `V2` = Abbay (outside any group label). `W1` = Remarks.

Data rows 3–4 only (MLB · FPYR and MPYR). Row 18 = `Total`, `A18:C18` merged, `=SUM(D3:D17)`.

### 3.4 `Common Area Assets Details` — A1:BK12, 63 columns
Freeze `B3` · zoom 85% · no print area set
Row heights: 1 = 37.4, **2 = 107.5 (photo strip)**, data = 25.0, 11 = 17.5 (spacer), 12 = 32.5
Col widths: A 25.45 · B 28.82 · C 18.18 · D–BJ 18.54 · BK 17.82 · Fonts: header 12 pt bold · data 12 pt (A/B bold)

**Single-row header** — this tab breaks the two-row pattern. `A1:A2` = Level, `B1:B2` = Location,
`BK1:BK2` = Remarks are vertically merged; C1–BJ1 carry the 60 asset names in row 1 only.

**Row 2 is a photo strip.** One embedded PNG per asset column, anchored `<col>2 → <col+1>3`
(one cell wide, one cell tall). 60 images, `image1.png`–`image60.png` in left-to-right column
order matching C1–BJ1. Photos are on-site reference shots, timestamped 5 Jul 2026.

Data rows 3–10: BLVD · LG Lobby · GF · FF · SF · 3rd Floor · 4th Floor · Basement Lift Lobby,
all with Location = `FAE`. Row 11 blank spacer. Row 12 = `Total`, `=SUM(x3:x8)`.

**Blank-vs-zero rule differs here:** the three washroom/prayer tabs write an explicit `0`
for "none present"; this tab leaves the cell **empty**.

---

## 4. Value conventions

- Counts are plain integers.
- **Split counts are text, not numbers:** `5+5`, `11+11`, `6+6`, `1+1` — used where one figure
  covers two sub-locations (e.g. trays cubicle+vanity, baby-room soap+lotion). Preserve as text.
- Remarks are free-text exceptions, e.g. `Staff washroom don't have janitor room`,
  `3r floor no Janitor room`, `viplounge Janitor inside no sink & Tap`,
  `Shower 2 / dress changing 4`, `1 hand drayer`.
- Area codes in use: `BLVD`, `GF`, `LG`, `LB`, `FF`, `SF`, `MLB`, `1F`, `2F`, `3F`, `4F`,
  `3rd`, `4th`, `BASEMENT`, `Vip Lounge`, `Basement Lift Lobby`, `LG Lobby`.
  Note the trailing spaces in the original (`1F `, `3rd  `, `Viploung `).

## 5. Spelling — reproduce verbatim

The register uses consistent non-standard spellings. Keep them so consolidated sheets match:
`Deatils` (tab names), `Airfreshner`, `dispencer`, `Peddle Bin`, `Shattaf`, `drayer`,
`Abbay`, `Inam stage`, `Viploung`, `valvet`, `Consel Table`, `broun`.

---

## 6. Known defects in the source workbook

> **USER DECISION: leave all as it is.** Do NOT fix any of the items below when
> consolidating. Reproduce the format verbatim — including the missing/short total
> ranges, the duplicate rows, the `o`-for-`0` typo, the mid-table freeze pane, the
> blank-vs-zero inconsistency, and every non-standard spelling in §5. Listed here for
> awareness only.

1. **`FAE Washroom Deatils` row 51 `Total` has no formulas** — the label is there, every
   count column is empty. The only tab without a working total.
2. **Rows 21–24 duplicate rows 17–20** on the same tab (MLB Female / 3rd / 4th / VIP Lounge)
   with *conflicting* values; rows 23–24 are truncated mid-row (stop at column J).
   Row 21 vs 17 and row 22 vs 18 disagree on nearly every count.
3. **`Common Area Assets Details` row 12 totals only `3:8`** — excludes row 9 (4th Floor)
   and row 10 (Basement Lift Lobby). Should be `3:10`.
4. `Staff Washroom Deatils` cell `O4` contains the letter `o` instead of `0`.
5. `FAE Washroom Deatils` freeze pane is `A10` — mid-table, so the header scrolls away.
6. Column D (Urinal) is left blank on female washroom rows 15–24 rather than `0`,
   inconsistent with the explicit-zero rule used elsewhere on that tab.
7. `Prayer Room Details` group `D1:M1` has no label; `U`/`V` (Quran, Abbay) sit outside
   any group merge.
8. Tab-name typo `Deatils` on two of four tabs.

---

## 6a. Batch 1 output (one workbook per source file)

| Source file | Output in `reports/` | Tabs |
|---|---|---|
| `Common_area__Bin.xlsx` | `TDM_Common_Area_Bins_Details_2026.xlsx` | 1 |
| `Steel_Bins.xlsx` | `TDM_Steel_Bins_Details_2026.xlsx` | 1 |
| `Mall_Washroom.xlsx` | `TDM_Mall_Washroom_Details_2026.xlsx` | 5 |
| `Planters_in_Malls.xlsx` | `Planters_in_Malls_Details_2026.xlsx` | 4 |
| `Washroom_Summery.xlsx` | `Washroom_Summary_Details_2026.xlsx` | 15 |

Build tooling lives in `tools/` (`fmt.py` carries the master styling; one builder
per source file; `verify.py` checks the result). Re-runnable for later batches.

Mapping rules applied to every source table:

- Source `Floor` -> **Area**; source `Location` (Male WR / Female WR) -> **Washroom (Gender)**;
  a **Washroom no** column is inserted between them to match the master's A/B/C layout.
  It is a per-Area sequence, except where the source already carried its own number
  (External Staff Washroom's `No` column), which is used verbatim.
- Source title banners are dropped (the master has none) and their wording moved into the tab name.
- Every table gains a `Remarks` column last, even where the source had none.
- **Total formulas are translated, never redesigned** — each reference is remapped to the new
  layout so the totals keep exactly the rows the source included or omitted.
- Blocks stacked or placed side-by-side in one source sheet are split onto their own tabs
  (Zabeel, China Town, Fountain Views), except baby rooms, which are stacked under a
  `Property` column.

## 6b. Batch 2 output

Seven files were sent, but two pairs were byte-identical duplicates
(`LG_FC` = `LG_FC_2`, `Bin_Stations_in_Food_Courts` = `..._2`), so five were built.

| Source file | Output in `reports/` | Tabs |
|---|---|---|
| `LG_FC.xlsx` | `LG_FC_Furniture_Details_2026.xlsx` | 2 |
| `Bin_Stations_in_Food_Courts.xlsx` | `Bin_Stations_in_Food_Courts_Details_2026.xlsx` | 4 |
| `New_External_dining_furniture_details.xlsx` | `New_External_Dining_Furniture_Details_2026.xlsx` | 2 |
| `SF_FC_ASSETS_INSPECTION_TRACKER2026.xlsx` | `SF_FC_Assets_Inspection_Tracker_2026.xlsx` | 1 |
| `SF_FC.xlsx` | `SF_FC_Furniture_Details_2026.xlsx` | 5 |

New handling introduced in this batch:

- **Per-row reference photos.** Unlike the master's row-2 photo strip, these sources
  keep an `IMAGE` / `Asset photo` column with one photo per data row. That column is
  retained and the photos are re-anchored row by row, with source row heights kept.
  Where the source stacked two photos in one cell, both are placed side by side.
- **Full contiguous row spans are preserved** (first data row through the last total
  row, blank rows included) so every remapped formula reference stays valid. Compacting
  the blanks away would have pointed totals at themselves.
- **Repeating label-row / value-row layouts are normalised** into one row per record with
  assets as columns (`SF FC External`). Where the same asset was spelled two ways across
  blocks, the first spelling becomes the column and the variant is recorded in Remarks.
- Emaar logos in title rows are dropped, as in batch 1.
- No total row is added where the source has none (the inspection tracker has none).

## 6c. Per-entity registers

Split out of the combined workbook so every property has its own register, matching
how FAE already sits in `FAE_Assets_Details_2026.xlsx`. One sheet per asset type.

| Entity | Workbook | Tabs |
|---|---|---|
| The Dubai Mall | `TDM_Assets_Details_2026.xlsx` | 30 |
| Fountain Views | `FV_Assets_Details_2026.xlsx` | 5 |
| Zabeel | `Zabeel_Assets_Details_2026.xlsx` | 4 |
| China Town | `China_Town_Assets_Details_2026.xlsx` | 4 |
| Fashion Parking | `FP_Assets_Details_2026.xlsx` | 4 |
| Fashion Avenue Ext. | *(already exists — the master)* | 4 |

Where a source tab held several properties (`Baby Room Details`,
`Washroom Assets Summery`, `Store Inventory`), only that entity's rows are carried
across and the block's own total formulas are remapped to their new row positions.
The cross-property `Sub Total` row is **not** carried into an entity register — it
covered every property and is meaningless for one.

Two rows appear in two registers on purpose, because they belong to a TDM table but
describe a Fashion Parking location: the `Fashion Lobby` bin row (qty 24) and the
`L3 FP Valet office` washroom row. TDM keeps its source tables whole; FP surfaces
them as its own data.

## 6d. Mall side register, and removal of FAE from grouped output

`Mall_side__Assets_Details_2026.xlsx` arrived already built on this master's own
template — same 64-column washroom layout, same prayer-room columns, same
photo-strip idea. It became `Mall_Side_Assets_Details_2026.xlsx` (3 tabs) and was
merged into the TDM register and the grouped workbook. All of its locations are
mall floors (LG / GF / FF / SF), so none of it belongs to Zabeel, FV, CT or FP.

- The washroom and prayer-room tabs are direct re-renders; column B holds the
  location *name* here rather than a number, which is how the source uses it.
- The source's **common-area sheet stacks four per-floor blocks** (LG / GF / FF / SF),
  each with its own header, photo strip and total. These were merged into one
  master-shape table: `Level | Location | 37 union asset columns | Remarks`, with a
  single photo strip and each block's own total row preserved and remapped. Where a
  block repeated a header (`Sofa` six times in GF), later occurrences are numbered
  `Sofa (2)`…`Sofa (6)` so nothing collapses.
- Four Remarks-column `SUM()` formulas from the source were dropped: the master puts
  no total in its Remarks column, and all four evaluated to 0 over text cells.
- `Prayer Room` keeps its cross-sheet total `='Mall Side Washroom Deatils'!D69`,
  retargeted to the new tab name.

**FAE is excluded from the grouped output**, per instruction. The combined workbook is
now `Malls_Assets_Details_2026_Combined.xlsx` (the old name carried "FAE"). Removed:
the three FAE tabs; the FAE baby-room block; the `FAE`, `FAE Staff + Driver` and
`FAE Handicap` summary lines; the FAE pedal-bin line; and the
`Malls,FAE,ZB.FV & CT baby room` line, which mixed FAE into one figure that could not
be split. Totals whose ranges spanned a removed row were rewritten over the retained
range — a necessary consequence of the removal, not a silent correction.
The ten per-source batch workbooks still contain FAE: they are faithful reformats of
their sources and serve as the audit trail.

## 7. Consolidation checklist

- [ ] Same four-tab structure, same tab names and order.
- [ ] Two-row banded header on washroom/prayer tabs; single-row + photo strip on common-area tab.
- [ ] Calibri, `#44546A` header fill, white bold header text, centred everything.
- [ ] Identity columns vertically merged across rows 1–2.
- [ ] Medium borders at group boundaries, thin inside.
- [ ] Row heights and column widths per §3.
- [ ] `Remarks` last column on every tab.
- [ ] Total rows replicated exactly as the master has them (per §6 — no corrections).
- [ ] Explicit `0` on washroom/prayer tabs; blank on common-area tab.
- [ ] Split counts (`5+5`) preserved as text.
- [ ] Photos re-anchored one-per-column in row 2 of the common-area tab if supplied.
- [ ] Freeze panes above the first data row.
