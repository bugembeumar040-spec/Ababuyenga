#!/usr/bin/env python3
"""Render the re-derived cue sheet as a readable document.

Placement confidence is token recall in context -- what share of an anchor's
distinctive words actually appear around the matched time. Sequence ratio alone
punishes short anchors ("Open a mushaf") that are correctly placed, so recall is
what decides whether a scene is placeable.
"""
import json

def mmss(x): return f"{int(x//60)}:{x%60:05.2f}"
def ms(x):   return f"{x//60}:{x%60:02d}"

rows = json.load(open("clarity/master/cuesheet.json"))
edl  = json.load(open("clarity/master/edl.json"))
span = {b["batch"]: (b["start"], b["end"]) for b in edl["batches"]}

def batch_of(t):
    for n, (a, b) in span.items():
        if a <= t <= b: return n

REWORDED = (11, 15)
UNPLACEABLE = 0.20
unplaced = [r for r in rows if r["recall"] < UNPLACEABLE]

# ordering faults, ignoring scenes that could not be placed at all
prev, oo = None, []
for r in rows:
    if r in unplaced: continue
    if prev is not None and r["real_cue"] < prev["real_cue"]:
        oo.append((r, prev))
    prev = r

inrew = [r for r in rows if batch_of(r["real_cue"]) in REWORDED and r not in unplaced]
worst = min(rows, key=lambda r: r["drift"])

L = ["# CLARITY IN THE QURAN — SCENE CUE SHEET\n",
     f"90 scenes · 180 plates · re-derived against the assembled master "
     f"({mmss(edl['total'])}).\n",
     "## Every cue in the pack is early — use the `real cue` column\n",
     "The pack's cue times were written against the script's ~150wpm estimate of "
     "43:18. The recorded master runs 82s shorter and the gap widens as it goes, so "
     f"drift grows from under 10s at the open to **{abs(worst['drift']):.0f}s by "
     f"{worst['scene']}**. Cutting to the pack's times would put late images more than "
     "a minute ahead of the words they illustrate.\n",
     "Each `real cue` was measured by locating the scene's VO anchor line in the "
     "word-level transcript of the assembled master.\n"]

if unplaced:
    L += ["## Scene that cannot be placed\n"]
    for r in unplaced:
        L.append(f"- **{r['scene']}** — anchor *\"{r['vo']}\"*. **None** of this line's "
                 "distinctive words appear anywhere in the recording. Batch 15 was "
                 "reworded during generation and this sentence became *\"turned away by "
                 "the locals and departs in sheer exhaustion\"*, so the image has nothing "
                 "left to cut to. The time given below is **interpolated** from its "
                 "neighbours so the plate still has somewhere to sit, but it is not a "
                 "measured match — re-record b15 to script, or re-anchor this scene to a "
                 "line that survives.")
    L.append("")

if oo:
    L += ["## Scenes cued in the wrong order\n",
          "The pack cues these after a scene they actually precede in the audio. The "
          "gaps are small, but the plates will land on the wrong sentence:\n"]
    for r, p in oo:
        L.append(f"- **{r['scene']}** *\"{r['vo'][:46]}\"* sits at {mmss(r['real_cue'])}, "
                 f"before **{p['scene']}** at {mmss(p['real_cue'])} — the pack has them "
                 f"at {ms(p['pack_cue'])} and {ms(r['pack_cue'])} respectively.")
    L.append("")

if inrew:
    L += ["## Scenes anchored to reworded audio\n",
          f"{len(inrew)} scenes sit inside batches 11 and 15. These are placeable, but "
          "the anchor wording no longer matches what is spoken, so check each against "
          "the audio before locking its plate:\n",
          "| scene | real cue | recall | anchor | what is actually said |",
          "|---|---|---|---|---|"]
    SAID = {"S074": "\"a slow distancing\"", "S076": "\"he loses …\" (not \"dies\")",
            "S075": "\"facing profound scarcity\"", "S054": "\"the prophet had lost his sons\""}
    for r in sorted(inrew, key=lambda x: x["real_cue"]):
        L.append(f"| {r['scene']} | {mmss(r['real_cue'])} | {r['recall']:.2f} | "
                 f"{r['vo'][:44]} | {SAID.get(r['scene'], '—')} |")
    L.append("")

L += ["## Full cue sheet\n",
      "`recall` is the share of the anchor's distinctive words found in the audio at "
      "that point. Values of 0.50 on short anchors are normal — they reflect the "
      "transcriber's spelling of transliterated Arabic (mushaf/musaf, Aqaba/Akaba, "
      "Hijra/hidra), not a misplacement.\n",
      "| scene | plates | pack cue | real cue | drift | recall |",
      "|---|---|---|---|---|---|"]
for r in rows:
    p = " · ".join(sorted(r["plates"].values()))
    flag = (" ⚠interp" if r.get("interpolated") else
            " ⚠" if any(r is x for x, _ in oo) else "")
    L.append(f"| {r['scene']}{flag} | {p} | {ms(r['pack_cue'])} | {mmss(r['real_cue'])} | "
             f"{r['drift']:+.1f}s | {r['recall']:.2f} |")
open("clarity/CUESHEET.md", "w").write("\n".join(L) + "\n")
print(f"{len(rows)} scenes · {len(unplaced)} unplaceable · {len(oo)} out of order · "
      f"{len(inrew)} in reworded batches")
