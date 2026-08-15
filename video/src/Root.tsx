import React from "react";
import { Composition } from "remotion";
import { DURATION_IN_FRAMES, FPS, HEIGHT, SHOTS, WIDTH } from "./jinn/beats";
import { Film } from "./jinn/Film";

// The preview is the last third — the traveller, the whisperer and the close.
// Fourteen of its fifteen shots have a delivered plate, so it is the part of
// the film that can actually be judged, and it carries the thesis shot, the
// fourth correction and the root callback.
const PREVIEW_FROM = SHOTS.findIndex((s) => s.id === "S25");
const PREVIEW_TO = SHOTS.length;
const previewFrames = SHOTS.slice(PREVIEW_FROM, PREVIEW_TO).reduce(
  (n, s) => n + s.frames,
  0
);

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="Jinn"
      component={Film}
      durationInFrames={DURATION_IN_FRAMES}
      fps={FPS}
      width={WIDTH}
      height={HEIGHT}
      defaultProps={{}}
    />
    <Composition
      id="JinnPreview"
      component={Film}
      durationInFrames={previewFrames}
      fps={FPS}
      width={1280}
      height={720}
      defaultProps={{ from: PREVIEW_FROM, to: PREVIEW_TO }}
    />
  </>
);
