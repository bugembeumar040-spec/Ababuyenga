import React from "react";
import { Composition } from "remotion";
import { DURATION_IN_FRAMES, FPS, HEIGHT, SHOTS, WIDTH } from "./jinn/beats";
import { Film } from "./jinn/Film";

// The preview cuts the four beats worth judging before a ten-minute render:
// the root device, the first correction, the peak, and the close.
const PREVIEW_FROM = SHOTS.findIndex((s) => s.id === "S03b");
const PREVIEW_TO = SHOTS.findIndex((s) => s.id === "S07") ;
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
