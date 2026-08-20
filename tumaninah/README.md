# Ṭumaʾnīnah — Ar-Raʿd 28

Image pack for the study. 16:9, 95 scenes plus 21 B-splits = 116 frames, cut to
a 21:04 voiceover.

## What is here

| path | what it is |
|---|---|
| `build_pack.py` | source of truth — holds the shared style prefix, the pack's negative prompt and the in-prompt guard once, and composes every prompt from its subject sentence |
| `tumaninah-prompt-pack.txt` | the 116 prompts expanded, chaptered, in scene order |
| `manifest.json` | per image: scene id, chapter, IN/OUT, VO line, filename, and both `prompt` and `el_prompt` |
| `CHECKLIST.md` | delivery status, and where the generated lists live |
| `transcript.md` | the assembled voiceover transcript — the timing source of truth |
| `timing/` | shot list and overlay grid, generated from the transcript |
| `cards-src/` | Remotion project for the overlay cards |
| `overlays/` | the 43 rendered cards — alpha WebM, MP4 on white, stills |
| `done.txt` | scenes already covered, so a batch is never paid for twice |
| `next.py` | prints the next pending scenes and what they would cost |
| `images/` | all 116 frames, 1376x768, named by cut position |

Regenerate the pack and manifest with `python3 tumaninah/build_pack.py`.

## Timing

Frames are placed against the recorded voiceover, not the pack's original
chapter estimates — the script was resequenced and the runtime came in at 21:04
rather than 27:17. `timing/README.md` explains the method and why the
transcript's own AUDIO boundaries could not be used directly.

## Why the prompts carry their own negation

The image tool used here takes no negative-prompt field, so anything left only
in the pack's NEGATIVE block never reaches the model. That is what let rendered
text and sigil imagery into an earlier run: scenes whose subject gave text
nowhere to land came back clean, and the moment a writing surface entered the
frame, script appeared and compounded.

`build_pack.py` therefore appends a compact guard to every prompt — text,
script, occult symbolry, and the CGI/glow look — and emits it as `el_prompt`.
Every paper-bearing scene in this run came back genuinely unmarked: the
cartouches, the banners, the open manuscripts, the torn sheet, the envelopes.

## Generation settings

`gemini-3.1-flash-lite-image` via the ElevenLabs creative flow, one generation
per scene. 206 credits (~$0.037) an image against 251 for the 2.5-flash
default; the tool's default `generations_count` of 4 would have quadrupled the
bill, so it is pinned to 1. Total across all 116: ~$4.35.

Each call is a fresh text-to-image node with nothing wired into `connect_from`.
That matters — feeding a previous output back in as a reference is what starts
the drift.

## Known deviation

Scene 25 asks for one illuminated border running unbroken across the gutter,
mirroring the āyah continuing without a new sentence. The render draws a
separate border per page, so the device does not read. Left as-is rather than
spending on a retry; worth regenerating if the edit needs it.
