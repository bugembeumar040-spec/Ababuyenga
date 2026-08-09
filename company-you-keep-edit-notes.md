# "You Sink to Your Room" — assembly notes

The sixteen Seedance 2.5 clips generated in the Higgsfield app, cut against the
emotion-tagged voiceover into one master.

**Output:** `media/you-sink-to-your-room_1080x1920.mp4` — 67.29s · 1080×1920 ·
24fps · h264 crf16 · AAC 192k · −14.4 LUFS integrated, −1.5 dBTP

**Thumbnail:** `media/thumbnail_1080x1920.jpg` — the ball stopped on the dirt
past the touchline, from CLIP 05, exactly as the pack specifies. No text.

**Stems:** `media/company-vo.mp3` (voice only) · `media/sfx-bed.mp3` (sound bed
only, pre-duck, pre-gain).

Reproduce with `build/build.py`, then `build/captions.py`, then `build/sfx.py`.

## Which take went in

All sixteen scenes had a completed generation. Four had two takes.

| Scene | Job | Take notes |
|---|---|---|
| 01 | `cf47d957` | |
| 02 | `64cbfe7c` | |
| 03 | `fab77d46` | |
| 04 | `4bd9df48` | **chosen over `7b49dd2c`** — see below |
| 05 | `c835595c` | |
| 06 | `437ae0d9` | |
| 07 | `59d4c361` | second take, cleaner framing than `c402439a` |
| 08 | `d65ca2d3` | |
| 09 | `7f382eab` | |
| 10 | `8395065a` | |
| 11 | `cdad366c` | second take, `ac467b03` also usable |
| 12 | `0320d203` | the "No marks" re-run; pages verified blank |
| 13 | `ac98ff42` | |
| 14 | `4439d19f` | |
| 15 | `513279ef` | |
| 16 | `bde0411b` | |

**Scene 04 — the one real rejection.** Take `7b49dd2c` grew a Nike swoosh on the
player's shirt partway through the clip. That is the exact drift the pack's retry
policy says to check people clips for, and it is disqualifying. Take `4bd9df48`
carries only a small abstract chevron crest — not a real mark — and shows the
speed mismatch against the other players better anyway.

**Scene 12 — the critical check passed.** The pack calls malformed script under
an Ibn al-Qayyim citation the worst failure available to this video. Both takes
came back with genuinely blank pages. Verified frame by frame before use.

Five clips (01, 10, 12, 13, 14) were generated with `generate_audio` left on and
came back carrying model-invented audio. All video was demuxed with `-an`; none
of it reaches the master.

## The cut

The voiceover is the clock. Scene lengths were re-derived from the recorded audio
rather than taken from the pack's estimated map, per the house rule.

| # | Start | Len | Line | Gap | Picture |
|---|---|---|---|---|---|
| 01 | 0.000 | 5.258 | 5.058 | 0.10 | slow 1.040× |
| 02 | 5.258 | 4.018 | 3.898 | 0.12 | trim |
| 03 | 9.276 | 2.830 | 2.480 | 0.35 | trim @1.00s |
| 04 | 12.106 | 5.003 | 4.723 | 0.28 | trim |
| 05 | 17.108 | 2.578 | 1.928 | **0.65** | trim @0.90s |
| 06 | 19.687 | 2.631 | 2.451 | 0.18 | trim @1.20s |
| 07 | 22.318 | 4.870 | 4.720 | 0.15 | trim |
| 08 | 27.188 | 2.440 | 2.120 | 0.32 | speed 2.07× |
| 09 | 29.628 | 4.016 | 3.736 | 0.28 | trim |
| 10 | 33.644 | 4.702 | 4.562 | 0.14 | trim |
| 11 | 38.346 | 3.639 | 3.319 | 0.32 | speed 1.39× |
| 12 | 41.986 | 6.463 | 6.283 | 0.18 | slow 1.278× |
| 13 | 48.448 | 5.450 | 5.200 | 0.25 | slow 1.078× |
| 14 | 53.898 | 4.783 | 4.623 | 0.16 | trim |
| 15 | 58.681 | 3.114 | 2.664 | 0.45 | trim @0.90s |
| 16 | 61.795 | 5.550 | 5.300 | 0.25 | slow 1.101× |

Average cut 4.21s against the pack's 3.75s target — longer because the emotional
read is longer, but the rhythm is unchanged and no clip sits past 5s of *source*.

**The 0.65s gap after scene 05** is the beat the pack insists on around "So he
stops making them." The [emphatic] half-time line does not ride in on top of it.

### Where the picture was retimed, and why

The pack's rule is never stretch a clip, because the slow-down reads instantly.
That rule is about motion. It was held everywhere motion exists and relaxed only
on shots that are close to still, where nothing gives it away:

- **12, slowed 28%** — the book. Prompt is "absolute stillness", a reverent slow
  push-in. The line under it is the 20-word citation, the longest in the script
  at 6.28s, and it cannot fit a 5.04s clip by any other means.
- **13, slowed 8%** — the vase. Already generated as extreme slow motion.
- **01, slowed 4%** and **16, slowed 10%** — a very slow push-in and a slow
  crane-out. 16 is the only retime with a human gait in it and the only one worth
  a second look; at 0.91× the walk still reads normal.

Two clips were sped up instead of trimmed, because trimming would have cut the
shot's payoff:

- **08, 2.07×** — the pitch-to-street match cut only completes at ~3.1s. Cutting
  at 2.44s would have lost the reveal. At double speed it becomes a whip
  transition, which suits "That's not football. That's people."
- **11, 1.39×** — the phone dims to black at the very end of the clip. That is
  the shot's whole point.

**Scene 05 is windowed, not head-trimmed.** The ball comes to rest at ~2.5s, so
the cut takes 0.90–3.48s: the roll in, the stop, and a held beat on the stopped
ball. "HE STOPS" lands on the ball at rest.

## Captions

Six moments, per spec — not sixteen. Cream `#F5EFE2`, navy `#142433` outline,
accent word terracotta `#E8622F`. CAP 1 at 62% height, CAP 2 at 76%. Every
caption clears 200ms before its cut.

| Scene | Caption | In → Out |
|---|---|---|
| 03 | WATCH WHAT HAPPENED | 10.23 → 11.91 |
| 05 | HE STOPS *(alone, no CAP 2)* | 17.61 → 19.49 |
| 09 | YOU **SINK** TO YOUR ROOM | 31.70 → 33.44 |
| 11 | COMFORTABLE IS CONTAGIOUS | 39.99 → 41.79 |
| 12 | Ibn al-Qayyim, al-Fawāʾid *(lower third)* | 42.34 → 48.25 |
| 13 | TIME → HEART → EVERYTHING *(builds)* | 49.35 / 50.70 / 51.90 → 53.70 |
| 15 | WHO DO I BECOME / IN THAT ROOM? | 58.83 / 60.35 → 61.60 |

Caption entries are synced to measured speech, not guessed. Scene 09's caption
fires at 31.70s because silence detection puts the start of "You sink to your
room" at 2.21s into the line. Scene 13's three words build on the line's three
measured pauses, at fixed positions so nothing reflows as it fills in.

The citation lower-third carries no page number, per the pack's accuracy note.

Two deviations from the letter of the caption spec, both for legibility: the
outline is 6px rather than 2px with a soft drop shadow behind it, because these
frames are busier than the finance packs and 2px disappears against the
terracotta; and the condensed face is simulated by squeezing DejaVu Sans Bold to
0.84× width, since no condensed font is installed here. Swap in the house face
before this becomes a habit.

## Sound

Brief was engaging but quiet — peaceful to sit inside. So the bed is ambience
and spot effects only. No music, no melody, nothing with a pitch centre that
would turn into a tune under the voiceover.

Everything is synthesised in `build/sfx.py` rather than sampled. That keeps it
licence-clean, and more usefully it means every sound in the mix is one that was
chosen rather than inherited — nothing arrives with a room, a key or a hiss
floor attached to it.

### Four movements, tracking the picture

| Window | Scenes | Bed |
|---|---|---|
| 0.00 – 27.19 | 01–07 | open air over the pitch, with a little more top end so it reads outdoors; four sparse, distant birdsong motifs |
| 27.19 – 29.63 | 08 | the match cut, and the street on the other side of it |
| 29.00 – 58.68 | 09–14 | interior room tone, darker and narrower; scene 10 adds the low body of a room with people in it |
| 58.68 – 67.35 | 15–16 | rain on glass, then night air over the street |

Scene 10's warmth is deliberately *not* voices. It is band-limited to 190–700 Hz
with a slow wander — the body of a room with people in it, and nothing
intelligible that could compete with the voiceover.

### Spot effects

Only on beats the picture already plays. Nothing was added to a scene just
because it was quiet — scenes 09 and 12 in particular are left almost bare,
because two closed doors and a citation both want stillness.

| Time | Effect |
|---|---|
| 12.45 | one soft pass-by on the sprint |
| 17.15 | the ball rolling, slowing, and a small thud as it settles at 19.17 |
| 26.95 | rising whoosh through the match cut — the one moment allowed to lift |
| 38.45 | the cushion giving way under an unseen weight |
| 49.33 / 50.68 / 51.88 | ceramic, on the three caption beats, plus four micro-shards drifting after |
| 54.35 – 55.71 | three soft steps out of the warm room |
| 58.70 – 62.00 | rain, with four beads running down the pane |
| 62.05 – 66.5 | two people walking in step, receding as the camera cranes out |

### Levels

The bed is keyed off the voice with a gentle sidechain (ratio 4, 25ms attack,
420ms release) so it breathes in the gaps and steps back under speech. It is
never allowed to compete:

- ducked bed sits at −39.6 LUFS against a −14.4 LUFS programme
- spot effects peak −24 to −32 dBFS; voice peaks sit near −1.5 dBFS
- in the silences, where you actually hear it, the bed measures −25 to −33 dB

Before this pass every gap in the cut was digital silence at −91 dB. The 0.65s
beat after "So he stops making them" was dead air; it now has air in it, which
is the point — the pause reads as held rather than as a dropout.

Two things were caught by measurement rather than by ear and are worth
remembering if the bed is ever rebuilt: the interior movement originally came in
6 dB under the outdoor one and would have vanished on a phone, and the rain sat
10 dB hotter than every other movement. Both are levelled now. There was also a
dip at the street→interior crossfade where one bed had faded out before the next
faded in; the interior now starts at 29.00 and comes up under the tail of the
street.

## Known gaps

- **Runtime is 67.29s against the pack's 60.0s slate ceiling.** Deliberate, and
  chosen over compressing the read. Reasoning and the two rejected alternatives
  are at the foot of `company-you-keep-vo-script.txt`.
- **No music.** The pack does not specify any and none was licensed. The sound
  bed is ambience and effects, deliberately with no pitch centre. The cut still
  ends on the last spoken word, as the pack requires — the 0.20s picture fade
  and the bed's 0.45s tail both sit inside the gap after "Follow."
- **The bed is synthetic.** It is good enough to feel like room tone and rain,
  but it is not a recorded library. The birdsong is the most synthetic element
  in it, which is why there are four motifs and not fourteen, all sitting ~30 dB
  under the voice. If this becomes a series, real ambience recordings would be
  the first upgrade worth paying for.
- **Upscaled, not native 1080p.** Seedance 2.5 caps at 720p. The master was
  lanczos-upscaled once, on the assembled cut, never per clip. Running the
  finished file through `upscale_video` would do better if it matters.
