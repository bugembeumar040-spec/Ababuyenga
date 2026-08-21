# Thumbnail

`PROMPTS.md` holds five Google Flow prompts for the background image, and the
text to set over it.

`layout-reference.png` shows that text layout, composited over a frame from the
pack (scene 72, the settled glass). It is a reference for where the type sits —
not the thumbnail to upload.

## Setting the text over a Flow image

The Remotion `Thumb` composition does the overlay. Flow cannot be trusted with
the Arabic — it renders script-like shapes rather than words — so the āyah and
the headline are typed here in Amiri and Inter instead.

```
cp <your-flow-image>.jpg cards-src/public/thumb/bg.jpg
cd cards-src
node render_thumb.mjs '{"src":"thumb/bg.jpg","ar":"طُمَأْنِينَة","line1":"IT DOES NOT","line2":"MEAN “PEACE”","ref":"AR-RAʿD 28"}' ../thumbnail/thumbnail.png
```

The composition currently renders at 1280×720 and places the text over the left
45%, assuming the subject sits right of centre — which is what the prompts ask
for. Raise the `Thumb` composition in `cards-src/src/Root.tsx` to 1920×1080 and
scale the font sizes with it if you want the larger upload.
