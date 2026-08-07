# Render pipeline — "They Call You a Deadbeat"

Builds the finished Short from the 18 generated stills + the recorded VO.
No editor required; everything in the pack's cut map and cue sheet is code here.

## Files

    render_1080.py   1080x1920 @ 30fps. Holds the source of truth for the
                     cut map (CUTS), the caption cue sheet (CUES), and the
                     silence-trim maths (SIL / PROTECT / build_keep).
    render_4k.py     2160x3840 master. Imports CUTS/CUES/KEEP from
                     render_1080 and re-renders with true condensed
                     outlines, real per-glyph tracking, and crops that
                     always downsample. Use this one for upload.

## Dependencies

    pip install Pillow fonttools imageio-ffmpeg faster-whisper

## Fonts

The pack specs Anton + Inter. Both are blocked by proxy policy in the build
environment, so `render_4k.py` reads two fonts generated at build time:

    fonts/CondBold.ttf   DejaVu Sans Bold, outlines scaled x0.76
    fonts/CondReg.ttf    DejaVu Sans,      outlines scaled x0.90

Regenerate with fontTools by transforming glyf outlines and hmtx advances
(see the commit that added this directory). Condensing at the OUTLINE level
matters — raster-squeezing the rendered text is what made the first pass
look cheap. If you have Anton and Inter available, point F_BOLD / F_REG at
them instead and drop the transform.

## Audio trim

`build_keep()` caps every silence at 0.5s except two protected beats: the
pause after "for paying in full" and the pause after "Be worthless".
70.27s -> 57.87s. The remap is piecewise-linear, so every cut and cue stays
locked to its word.

## Run

    python render_4k.py        # writes deadbeat-short-4k.mp4

Paths at the top of render_1080.py point at the upload directory the stills
and VO arrived in. Repoint GEN{} and VO before running elsewhere.

## collide.py — caption clearance sweep

    python collide.py

Renders each cue's layer alone to get its exact bbox, then samples the
caption-free frame underneath at BOTH ends of the cue and reports how much
of that box is non-background.

Checking both ends matters: every push moves the subject during the hold, so
a caption that clears at the IN point can be buried by the OUT point. That is
how "A DEADBEAT" ended up on KAREEM's hairline and "the balance is" ended up
printed on the blank card.

Its background test picks one dominant colour per frame, so it over-reports
on frames with several flat regions (a caption on the cream wall above a sand
desk reads as "not background"). Treat the output as a shortlist to look at,
not a verdict — confirm by eye before moving anything.

## Anchored burn-ins

Cues marked `anchor=True` are tied to a feature IN the picture rather than to
the frame — £25 inside its printed box, a card resting on a table. They are
transformed by the live zoom each frame:

    screen = (design - centre) * z + centre - offset

Without this they drift off their mark as the push runs; the 11% push on cut
10 moved the box about 56px down over its hold while the number stayed put.
Captions that belong to the frame (every CAP1/CAP2) must NOT anchor.
