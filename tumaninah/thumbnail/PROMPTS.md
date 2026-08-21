# Thumbnail prompts — Ṭumaʾnīnah (Ar-Raʿd 28)

For Google Flow, 16:9. Five options, strongest first.

**Two rules baked into every prompt below, both learned the hard way on this pack:**

1. **No text in the image.** Every prompt ends with a guard against it. Image models
   render Arabic as malformed pseudo-script — that is what produced the mangled
   āyāt in the early batches. The Arabic goes on afterwards, in a real font.
2. **Higher contrast than the video art.** The scene pack is deliberately low
   contrast and pale. That is right for 18 minutes of watching and wrong for a
   thumbnail read at 210px wide in a sidebar. Each prompt asks for a darker
   ground and a lit subject.

Each composition leaves the **left 45% clear** for the overlay text.

---

## 1 — The glass (recommended)

The video's central metaphor, one object, instantly odd enough to earn a click.

> Hand-painted watercolour and fine ink illustration on cold-press paper, visible paper tooth. A single plain drinking glass of river water standing on a bare wooden table, positioned in the right third of the frame. The bottom quarter of the water is dark settled silt — a distinct heavy band of burnt sienna and deep slate that has sunk and come to rest; the water above it is completely clear. Strong side light from the right rims the glass and throws a long shadow left. Background a deep bruised indigo wash, much darker than the glass, so the glass reads as the single bright object. The left 45 percent of the frame is empty dark wash with nothing in it. Muted palette of indigo, burnt sienna, ochre and slate grey, but with strong tonal contrast between the lit glass and the dark ground. Absolutely no text, lettering, calligraphy, Arabic script, numerals, logos or watermarks anywhere in the frame. Not 3D, not CGI, not a photograph.

## 2 — Sujūd

The most emotionally direct image in the pack. Face never visible, which avoids the uncanny-face problem entirely.

> Hand-painted watercolour and fine ink illustration on cold-press paper. A person in a soft charcoal grey garment in sujūd — forehead and both palms resting on a plain woven reed prayer mat — seen from a low side angle in the right half of the frame, head and shoulders only, face not visible. Warm ochre light falls across the shoulder and the mat from the right; everything else falls away into deep indigo shadow. The left 45 percent of the frame is dark empty wash. Muted palette of indigo, burnt sienna, ochre and slate grey with strong contrast between the lit figure and the dark ground. Absolutely no text, lettering, calligraphy, Arabic script, numerals, logos or watermarks anywhere in the frame. Not 3D, not CGI, not a photograph.

## 3 — Hand on the window

The relatable one — "the worst week of your life" framing.

> Hand-painted watercolour and fine ink illustration on cold-press paper. A close view of one open hand pressed flat against a rain-streaked window pane from the inside, in the right third of the frame. Beyond the glass, a dark storm breaking over rooftops in heavy bruised indigo, with one thin band of ochre light on the horizon. Rain runs down the pane in loose ink strokes. The interior is dim, the hand lit by the storm light. The left 45 percent of the frame is dark interior wash with nothing in it. Strong contrast between the lit hand and the dark room. Muted palette of indigo, burnt sienna, ochre and slate grey. Absolutely no text, lettering, calligraphy, Arabic script, numerals, logos or watermarks anywhere in the frame. Not 3D, not CGI, not a photograph.

## 4 — The thunder

Literal to the sūrah's name. Most dramatic, least specific.

> Hand-painted watercolour and fine ink illustration on cold-press paper. A vast bank of storm cloud stacked over a dark flat plain at dusk, seen from far below. One single fork of lightning on the right side of the frame, painted as one confident bright ink stroke with a soft ochre bloom around it. The underside of the cloud heavy and bruised indigo, a thin band of ochre light along the horizon. No people, no buildings. The left 45 percent of the frame is unbroken dark cloud with nothing in it. Strong contrast between the lightning and the dark sky. Muted palette of indigo, burnt sienna, ochre and slate grey. Absolutely no text, lettering, calligraphy, Arabic script, numerals, logos or watermarks anywhere in the frame. Not 3D, not CGI, not a photograph.

## 5 — Stones

Quiet and abstract. Weakest click, strongest for a series thumbnail.

> Hand-painted watercolour and fine ink illustration on cold-press paper. Four smooth river stones settled into wet sand in the right third of the frame, each one half-sunk and at rest, shallow water drawn back around them. Low warm ochre light from the right rakes across the stones and throws long shadows to the left. Background deep slate and indigo wash. The left 45 percent of the frame is empty dark wet sand. Strong contrast between the lit stones and the dark ground. Muted palette of indigo, burnt sienna, ochre and slate grey. Absolutely no text, lettering, calligraphy, Arabic script, numerals, logos or watermarks anywhere in the frame. Not 3D, not CGI, not a photograph.

---

## Text to add over the image afterwards

Set in the left 45 percent. **Do not ask Flow to render this** — it will mangle the Arabic.

| line | text | style |
|---|---|---|
| 1 | `طُمَأْنِينَة` | Amiri Bold, cream `#F2EDE2`, largest element |
| — | rule | ochre `#C89A4A`, ~250px wide, 10px tall |
| 2 | IT DOES NOT | Inter Black, cream `#F2EDE2` |
| 3 | MEAN "PEACE" | Inter Black, ochre `#C89A4A` |
| 4 | AR-RAʿD 28 | Inter Bold, small, letterspaced, ochre |

Cream on dark, rather than the indigo-on-cream the video uses — a thumbnail
needs to survive being 210px wide next to brighter competitors.

Alternate line pairs, all true to what the video argues:

- `IT MEANS` / `TO SETTLE`
- `THE WORD` / `ISN'T "REST"`
- `HALF THIS ĀYAH` / `GETS DELETED`

## Checking it before you upload

- Shrink to 210px wide. If the two headline lines are not readable, cut a word.
- The Arabic must be `طُمَأْنِينَة` exactly — check the tooth of the ط and that
  the hamza sits on the alif. Any Flow-generated script is wrong by definition.
- The subject must survive the sidebar crop: nothing important in the outer 5%.
