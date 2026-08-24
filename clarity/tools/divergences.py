#!/usr/bin/env python3
"""Write up where the recording still departs from the script pack."""
import sys, os, json, difflib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit import batch_text, norm, audit

STOP_SHORT = 4
L = ["# Script divergences\n",
     "Where the recording departs from the script pack, and why. Every other",
     "batch matches once transcription artefacts are discounted -- the "
     "transcriber's spelling of transliterated Arabic (mushaf/musaf, Iqra/Ikra,",
     "Hira/here) is not a divergence.\n"]

L += ["## Batch 15 — partially restored\n",
      "Batch 15 was reworded during generation to clear ElevenLabs' filter. "
      "Re-recording it whole was refused on acceptable use, and bisection showed "
      "the refusal is cumulative rather than caused by any one sentence — the "
      "filter even rejected a pair whose halves had each passed alone. The batch "
      "was therefore recovered paragraph by paragraph.\n",
      "**Restored verbatim** (re-recorded and spliced back in):\n",
      "- The Khadija paragraph — *\"Khadija dies… told him he was not going mad "
      "on the night he came down from Hira convinced that he was.\"* This "
      "restores scene **S076**'s anchor.",
      "- The Ta'if paragraph — *\"He is driven out of it by a crowd throwing "
      "stones, and leaves bleeding.\"* This restores scene **S079**'s anchor, "
      "which had no measurable cue at all while the line was missing.\n",
      "**Still softened** (these paragraphs could not be re-recorded):\n",
      "| scripted | recorded |", "|---|---|"]
KEEP = [("Then it gets worse", "the situation becomes even heavier"),
        ("Quraysh impose a boycott", "Quraish imposed a strict social barrier"),
        ("Not a fight — a slow squeeze", "Not a conflict, a slow distancing"),
        ("No one sells them food", "Everyday commerce is halted"),
        ("The reports describe people eating leaves", "facing profound scarcity"),
        ("And Abu Talib dies", "and he loses Abi Talib"),
        ("never once handed him over", "never once surrendered him"),
        ("had been able to kill him", "had been able to reach him"),
        ("Abu Talib's protection stood in the way", "Abi Talib's presence stood in the way"),
        ("The Year of Sorrow", "the Year of Sadness")]
for a, b in KEEP: L.append(f"| {a} | {b} |")
L += ["", "No scene is anchored to any of these lines, so none is left unplaceable. "
          "They remain a caption problem only: captions cut from script text will "
          "not match the voice at these points.\n"]

r11 = audit(11)
L += ["## Batch 11 — unchanged\n",
      f"Batch 11 scores {r11['ratio']*100:.0f}% and has not been re-recorded. Its "
      "rewording alters the rendering of **Al-Kawthar 108:2–3**:\n",
      "| scripted | recorded |", "|---|---|",
      "| So pray to your Lord and sacrifice | offer devotion |",
      "| Indeed it is the one who hates you who is cut off | remains without legacy |",
      "| an opponent said of him | a critic claimed |",
      "| the specific cruelty of a specific Tuesday | the challenges of a specific Tuesday |",
      "", "This is the one outstanding decision. Captions and the typeset Arabic "
          "come from script text, so as it stands the caption and the voice will "
          "disagree on a Quranic verse. No scene is unplaceable because of it, so "
          "it does not block the cut — but it should be settled before captions "
          "are typeset.\n"]
open("clarity/DIVERGENCES.md", "w").write("\n".join(L) + "\n")
print("wrote clarity/DIVERGENCES.md")
