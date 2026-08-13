# Voiceover audit — `ElevenLabs_20260812T17_35_47__s50_v3.mp3`

No ElevenLabs MCP server is connected to this session, so this is a signal
analysis of the render they produced rather than a console-side check. It still
answers the question that matters, and conclusively.

## The file

| | |
|---|---|
| Format | MP3, 256 kbps CBR, 44.1 kHz, mono |
| Duration | 108.748 s |
| Integrated loudness | −15.9 LUFS |
| Loudness range | 4.7 LU |
| True peak | **−0.5 dBFS**, 1 sample at absolute full scale |
| DC offset | −0.0008 (negligible) |
| Noise floor | −82.5 dB |
| Flat factor | 0.000 (no clipped plateaus) |
| HF energy | −44 dB above 16 kHz, −51 dB above 18 kHz |

**The render is clean.** No artefacts, no flatlining, no DC offset, digital
silence in the gaps. The v3 model and the stability-50 setting are not the
problem here, and nothing about the delivery needs redoing.

## The finding: every pause is punctuation

The film came in 20.7 s over the pack's 88 s target. That is not the read — the
speech itself is 71.4 s for 217 words, about **182 wpm**, *faster* than the
163 wpm the pack measured from your Pension VO. The overrun is entirely silence:
**37.3 s of it, against a budgeted 8.1 s.**

Where that silence sits is the whole answer:

```
43 pauses detected (≥0.25 s, −40 dB)
37 sentence-final stops + 6 em dashes = 43
```

**Exactly one to one.** ElevenLabs inserted a pause at every terminal
punctuation mark in the script and nowhere else. Mean gap 0.87 s. Not one gap
exceeds 1.30 s, so there is no dead air to trim and no single bad beat — the
pacing is uniform and entirely mechanical.

The cause is the script, not the settings. The pack wrote it in fragments on
purpose — *"Full stops where you want a beat — this script is written in
fragments on purpose"* — which lands at **5.9 words per full stop**. At ~0.87 s
per stop, 37 stops is 32 s of silence before you have said anything.

## What to change next time

**To hit a length target, cut terminal punctuation, not words.** Every full stop
you convert to a comma is worth about 0.87 s. Reaching 88 s from here needs
roughly 15 fewer stops — or accept the length, which for this upload you did,
and which your own channel data supports anyway.

**Export WAV, not MP3.** The 16 kHz rolloff is normal for 256 kbps MP3 and
inaudible, but it means the audio is lossy-encoded once in ElevenLabs and again
to AAC on render. PCM out of ElevenLabs removes a generation for free.

**Watch the output ceiling.** −0.5 dBTP with a sample at full scale is hot for a
master. It caused no problem here — the render normalises to −14.2 LUFS /
−4.1 dBTP — but if you reuse this MP3 anywhere that re-encodes without
normalising, that is one lossy pass from inter-sample clipping.

**Leave stability at 50.** LRA of 4.7 LU is tight and consistent, which is what
you want for spoken word heard on a phone speaker. Nothing to gain by moving it.

## Delivered file

The audio in `out/zakat.mp4` is loudness-normalised to −14.2 LUFS with a true
peak of −4.1 dBTP, using a measured two-pass linear `loudnorm` so sample timing
is untouched — which matters, because every caption is aligned to positions in
this exact file.
