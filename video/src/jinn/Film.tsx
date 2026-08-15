import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile } from "remotion";
import { SHOTS, type Shot as ShotType } from "./beats";
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

  return (
    <AbsoluteFill style={{ backgroundColor: PALETTE.night }}>
      <Audio
        src={staticFile("jinn-vo.mp3")}
        startFrom={offset}
        volume={1}
      />
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
  );
};
