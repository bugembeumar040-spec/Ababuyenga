# Finance % Decoded — short assembly

Turns a prompt pack, a set of stills and a recorded voiceover into a captioned
9:16 MP4. Everything is derived: the pack is the source of truth for the script
and the scene map, the VO is the source of truth for timing, and the stills are
the source of truth for where text can go.

## Layout

```
zakat-prompt-pack.txt          the pack — script, scene map, numbers, caption spec
credit-card-prompt-pack.txt    the previous film's pack
regenerate-06-10.md            outstanding art notes
media/<slug>/stills/           supplied stills
media/<slug>/vo/               recorded voiceover
build/
  scenes-zakat.json            machine-readable spine, transcribed from the pack
  style-zakat.json             caption + card look
  bin/                         the five stages
  lib/                         alignment, layout, typography, placement
out/                           generated; not committed
```

## Running it

```
cd build && npm install

node bin/inspect-stills.mjs media/zakat/stills      # measure the artwork
node bin/align.mjs    --spine scenes-zakat.json     # cut from the VO
node bin/captions.mjs --spine scenes-zakat.json     # lay out captions + cards
node bin/render.mjs   --spine scenes-zakat.json     # assemble  (--preview for a fast one)
node bin/audit.mjs    --spine scenes-zakat.json     # check before delivery
```

`--vo`, `--stills` and `--style` override the spine without editing it.

## How the stages work

**inspect-stills** measures each still: size, aspect, background colour, where
content starts, and two per-row profiles — *detail* (edge density) and *luma*.
Detail rather than ink, because a caption sits happily on a flat shirt and not
at all on a face; measuring difference-from-background scores those the same.

**align** forced-aligns the known script to the recorded audio. Speech segments
come from silence detection, each token gets a share of speech time by syllable
weight, and sentence boundaries snap to real pauses. Timings are laid out in
"speech time" with silences removed and mapped back, so no caption is ever
scheduled inside a pause. Scene cuts fall a beat before their first word. The
pack's IN/OUT points are estimates and are never used for the cut — they are
kept only so the audit can report drift.

**captions** solves placement per frame against that still's own profiles, then
emits ASS. Captions are bare on the artwork where the frame has a clean band;
cards get a cream backing plate where the artwork underneath is busy or too dark
for dark type. A face guard keeps text off the subject's head.

**render** groups scenes into shots (`continuesFrom` holds one still across two
beats), applies the pack's per-scene move via `zoompan` at 2× supersample, burns
the ASS, and normalises loudness to −14 LUFS using a measured two-pass linear
`loudnorm` so the audio's timing is untouched.

**audit** re-reads the pack and fails if the spine has drifted from it, then
checks sources, timeline, typography and the rendered file. Non-zero exit on any
failure.

## Notes that cost time to learn

- **libass does not size a font by its em square.** It fits the font's glyph
  bounding box into the requested size. Anton's bbox overflows its em by ~73%,
  so measuring by `unitsPerEm` alone makes every layout calculation 1.7× too
  large. `lib/text.mjs` corrects for it; verified against rendered frames.
- **ffmpeg's `drawtext` is absent from this build.** All text goes through
  libass, which is the better tool here anyway — exact positioning, per-word
  colour, and shapes drawn in the same pass as the type.
- **The image2 demuxer's index probing silently drops leading frames.** Compose
  grids with explicit inputs and `xstack`, not `%04d.png` + `tile`.
