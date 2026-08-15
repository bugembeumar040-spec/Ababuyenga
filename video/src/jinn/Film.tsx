import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile, useVideoConfig } from "remotion";
import { HEIGHT, SHOTS, WIDTH, type Shot as ShotType } from "./beats";
import { Shot } from "./Shot";
import { PaperGrain, Vignette } from "./effects";
import { PALETTE } from "./theme";

/**
 * The film.
 *
 * Shots are placed by absolute frame from beats.ts rather than chained in a
 * Series, so a shot whose length changes when the VO is recut cannot push
 * every shot after it off its own line.
 */
export const Film: React.FC<{ from?: number; to?: number }> = ({
  from = 0,
  to,
}) => {
  const end = to ?? SHOTS.length;
  const slice = SHOTS.slice(from, end);
  const offset = slice.length ? slice[0].frameIn : 0;

  // Everything downstream is laid out in 2560x1440 pixels. Scale the whole
  // stage to whatever the composition asks for so a 720p proof is the same
  // frame as the master, not a different type size.
  const config = useVideoConfig();
  const scale = config.width / WIDTH;

  return (
    <AbsoluteFill style={{ backgroundColor: PALETTE.night, overflow: "hidden" }}>
      <Audio src={staticFile("jinn-vo.mp3")} startFrom={offset} volume={1} />
      <AbsoluteFill
        style={{
          width: WIDTH,
          height: HEIGHT,
          transform: `scale(${scale})`,
          transformOrigin: "top left",
        }}
      >
        {slice.map((shot: ShotType) => (
          <Sequence
            key={shot.id}
            from={shot.frameIn - offset}
            durationInFrames={shot.frames}
            name={`${shot.id} · ${shot.beat}`}
          >
            <Shot shot={shot} />
          </Sequence>
        ))}
        {/* One sheet, laid over everything and never cut. */}
        <PaperGrain />
        <Vignette />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
