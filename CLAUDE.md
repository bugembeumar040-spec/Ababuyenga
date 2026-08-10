# Finance % Decoded — production repo

Prompt packs and scripts for a vertical short-form YouTube channel. Faith-and-money
explainers, ~30–60s, 9:16. No application code — the deliverables are text files
that get pasted into image/video/voice tools by hand.

## Files

| File | What it is |
|---|---|
| `credit-card-prompt-pack.txt` | "They Call You a Deadbeat" — 11 scenes, Track A (video) + Track B (stills), captions, VO, packaging |
| `docs/canon.md` | House style, characters, palette, caption spec, VO settings, packaging rules. **Stable across every video.** |
| `docs/continuity.md` | What has already shipped and may not be reused. Read before writing any new script. |
| `docs/token-playbook.md` | Where this account's tokens actually go, and what to do about it |

## Reading rule

`docs/canon.md` carries everything reusable. **Do not open a previous video's prompt
pack to learn the house style** — that costs ~9.5k tokens to recover facts that live
in canon.md for under 2k. Open a pack only when the work is about that specific video.

Same for the pack itself: it is sectioned by `====` rules. Grep for the section you
need and read that slice, rather than reading 578 lines to check one caption.

## Working rules

- **One deliverable per session.** Cost is driven by conversation length, not output
  length — every turn re-bills the entire transcript. See `docs/token-playbook.md`.
- **Never generate text, numbers or logos inside an image or clip.** Prompts ask for
  blank cards, blank screens, blank statements on purpose. Numbers are burned in
  during the edit. Every model drifts on typography; none drift on a blank card.
- **Blank heads, always.** Characters have no facial features. This is the format's
  signature and the negative prompt enforces it.
- **Timings in a pack are estimates until the VO is recorded.** Record first, derive
  real IN/OUT points second, generate third. Generating to estimated timings means
  trimming good clips.
- **No fiqh verdict in the author's own voice.** Present the economics; let contrast
  carry the argument. See the accuracy posture in `docs/canon.md`.

## Conventions for new packs

Mirror `credit-card-prompt-pack.txt`: a continuity note, a scene map table
(`# | IN | OUT | LEN | SCENE | VO LINE`), a burn-in-the-numbers list, Track A and
Track B as separate complete shoots that are never mixed, a caption table, the VO
script, packaging, then an accuracy section. Fixed-width, 80 columns, `====` rules
between sections.
