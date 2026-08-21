# Thumbnail — Ṭumaʾnīnah (Ar-Raʿd 28)

Flow prompts for the background image, plus the layout that goes over it.

## What vidIQ's thumbnails actually do

Pulled their six best-performing uploads and looked at them. The grammar is
consistent and it is simple:

| | |
|---|---|
| **Two elements, never three** | one face or one hero object, plus two to four huge words |
| **Type owns half the frame** | one block, usually the right half or the top corners |
| **Two-colour hierarchy** | white for the setup, yellow for the payoff — the payoff word is the biggest thing in frame |
| **Dark saturated ground** | deep blue or near-black, heavy vignette, so both type and subject pop |
| **A verdict marker** | red ✗, green ↑, a line going up — the judgement lands before you read a word |
| **A number** | 184.8K, 999%, 2026 — one concrete figure |
| **Fragments, never sentences** | |

## What transfers here, and what does not

**Transfers:** two elements only; type in one zone at roughly half the frame; a
two-colour hierarchy with the payoff largest; a dark ground under pale artwork.
That last one is the real fix — this pack's watercolour is deliberately pale,
which is right for eighteen minutes of viewing and is exactly what kills it at
210px wide in a sidebar.

**Transfers, and happens to be true:** the strike-through. vidIQ strikes through
bad advice. The entire argument of this video is that "peace" is the wrong word
for ṭumaʾnīnah — so struck `"PEACE"` above `TO SETTLE` is not a borrowed gimmick,
it is the thesis, readable in one glance.

**Does not transfer:** the neon-purple-and-highlighter register, and the face.
On a Qurʾānic word study the first reads as clickbait and misrepresents the film;
the second the pack does not have, and an AI-generated face is a liability.

**The number** becomes the āyah: **28**, set large in ochre beside a smaller
`AR-RAʿD`.

---

## Two rules baked into every prompt below

Both learned the hard way on this pack.

1. **No text in the image.** Every prompt guards against it. Image models render
   Arabic as script-shaped marks rather than words — that is what produced the
   malformed āyāt in the early scene batches. The Arabic is typed afterwards.
2. **Far more contrast than the video art.** Each prompt now asks for a deep
   near-black indigo ground with a single lit subject, not the pale even wash the
   scene pack uses.

Each composition leaves the **left half clear** for the type.

## 1 — The glass (recommended)

The video's central metaphor, one object, odd enough to earn a click.

> Hand-painted watercolour and fine ink illustration on cold-press paper, visible paper tooth. A single plain drinking glass of river water standing on a bare wooden table, positioned in the right third of the frame. The bottom quarter of the water is dark settled silt — a distinct heavy band of burnt sienna and deep slate that has sunk and come to rest; the water above it is completely clear. Hard directional light from the upper right rims the glass brightly and throws a long shadow to the left. The background is a very dark, near-black bruised indigo, several values darker than the glass, so the lit glass is the only bright object in the frame. The left half of the frame is deep unbroken shadow with nothing in it. Strong dramatic tonal contrast, chiaroscuro. Absolutely no text, lettering, calligraphy, Arabic script, numerals, logos or watermarks anywhere in the frame. Not 3D, not CGI, not a photograph.

## 2 — Sujūd

The most emotionally direct image in the pack. Face never visible, which avoids the uncanny-face problem entirely.

> Hand-painted watercolour and fine ink illustration on cold-press paper. A person in a soft charcoal garment in sujūd — forehead and both palms resting on a plain woven reed prayer mat — seen from a low side angle in the right half of the frame, head and shoulders only, face not visible. A single warm ochre shaft of light falls across the shoulder and the mat from the upper right; everything else drops into deep near-black indigo shadow. The left half of the frame is unbroken darkness with nothing in it. Strong dramatic contrast, chiaroscuro, one lit subject against a very dark ground. Absolutely no text, lettering, calligraphy, Arabic script, numerals, logos or watermarks anywhere in the frame. Not 3D, not CGI, not a photograph.

## 3 — Hand on the window

The relatable one — the "worst week of your life" framing.

> Hand-painted watercolour and fine ink illustration on cold-press paper. A close view of one open hand pressed flat against a rain-streaked window pane from the inside, in the right third of the frame. Beyond the glass, a dark storm breaking over rooftops in heavy bruised indigo, with one thin bright band of ochre light on the horizon. Rain runs down the pane in loose ink strokes. The interior is almost black; the hand is lit only by the storm light and is the brightest thing in the frame. The left half is unbroken dark interior with nothing in it. Strong dramatic contrast. Absolutely no text, lettering, calligraphy, Arabic script, numerals, logos or watermarks anywhere in the frame. Not 3D, not CGI, not a photograph.

## 4 — The thunder

Literal to the sūrah's name. Most dramatic, least specific.

> Hand-painted watercolour and fine ink illustration on cold-press paper. A vast bank of storm cloud stacked over a dark flat plain at dusk, seen from far below. One single fork of lightning in the right third of the frame, painted as one confident brilliant ink stroke with a soft ochre bloom around it, by far the brightest element. The underside of the cloud is heavy near-black indigo. No people, no buildings. The left half of the frame is unbroken dark cloud with nothing in it. Extreme contrast between the lightning and the black sky. Absolutely no text, lettering, calligraphy, Arabic script, numerals, logos or watermarks anywhere in the frame. Not 3D, not CGI, not a photograph.

## 5 — Stones

Quiet and abstract. Weakest click, strongest as a series look.

> Hand-painted watercolour and fine ink illustration on cold-press paper. Four smooth river stones settled into wet sand in the right third of the frame, each one half-sunk and at rest, shallow water drawn back around them. Low raking ochre light from the right catches the tops of the stones and throws long shadows left; the rest of the frame falls into deep near-black slate. The left half is empty dark wet sand. Strong dramatic contrast, one lit cluster against a very dark ground. Absolutely no text, lettering, calligraphy, Arabic script, numerals, logos or watermarks anywhere in the frame. Not 3D, not CGI, not a photograph.

---

## The layout over it

`thumbnail-v2.png` is this, rendered. Set in the left half:

| element | text | style |
|---|---|---|
| 1 | `طُمَأْنِينَة` | Amiri Bold 96, cream `#F2EDE2` |
| 2 | IT IS NOT "PEACE" | Inter Bold 76, slate `#8A8F9A`, struck through in sienna `#C4633B` at −2.5° |
| 3 | **TO SETTLE** | Inter Bold 122, ochre `#E0A94F` — the largest thing in frame |
| 4 | AR-RAʿD **28** | Inter Bold, cream at 72% + ochre 54 |

Ground is `#141A2A`, with the image darkened 14% overall and blacked out under
the type. Cream and ochre on near-black, rather than the indigo-on-cream the
video uses — a thumbnail has to survive sitting next to brighter competitors.

Alternate pairs, all true to what the video argues:

- struck `"REST"` / **IT MEANS TO SINK**
- struck `HALF THE ĀYAH` / **IS MISSING**
- struck `A FEELING` / **IT'S A POSITION**

## Rendering it over a Flow image

```
cp <your-flow-image>.jpg cards-src/public/thumb/bg.jpg
cd cards-src
node render_thumb.mjs '{"src":"thumb/bg.jpg","ar":"طُمَأْنِينَة","struck":"IT IS NOT “PEACE”","payoff":"TO SETTLE","ref":"AR-RAʿD","refBig":"28"}' ../thumbnail/thumbnail.png
```

## Before you upload

- Shrink to 210px wide. If `TO SETTLE` is not instantly readable, cut a word.
- The Arabic must be `طُمَأْنِينَة` exactly — check the tooth of the ط and that
  the hamza sits on the alif. Any Flow-generated script is wrong by definition.
- Nothing important in the outer 5% — the sidebar crops it.
