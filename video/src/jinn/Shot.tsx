import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import type { Shot as ShotType } from "./beats";
import { FPS } from "./beats";
import { CAPTIONS } from "./captions";
import { PLATES } from "./plates";
import { Plate } from "./Plate";
import { CaptionLayer } from "./Caption";
import { WashBloom } from "./effects";
import { PALETTE } from "./theme";

/**
 * One shot: plate, wash, type.
 *
 * Cuts dissolve over four frames — enough that the paper reads continuous
 * across the join, short enough that it still reads as a cut. The two hardest
 * turns in the film and the peak get no dissolve at all; they land on the
 * frame, which is the only reason they land.
 */
export const Shot: React.FC<{ shot: ShotType }> = ({ shot }) => {
  const frame = useCurrentFrame();
  const cap = CAPTIONS[shot.id];
  const hardCut = shot.peak || cap?.mode === "hard";
  const dissolve = hardCut
    ? 1
    : interpolate(frame, [0, 4], [0, 1], { extrapolateRight: "clamp" });

  const bloomAt = cap?.bloomAt;
  const bloomOn = shot.bloom || Boolean(bloomAt);
  const bloomP = interpolate(
    frame,
    [Math.round(FPS * 0.8), shot.frames - Math.round(FPS * 0.6)],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill style={{ opacity: dissolve, backgroundColor: PALETTE.night }}>
      <Plate shot={shot} available={PLATES.includes(shot.id)} />
      {bloomOn ? (
        <WashBloom
          progress={bloomP}
          x={bloomAt?.[0] ?? 50}
          y={bloomAt?.[1] ?? 54}
          color={PALETTE.gold}
        />
      ) : null}
      {/* Type sits over a wash, not over bare plate — it has to stay readable
          against a light-toned parchment as well as a night-washed one. */}
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(to top, rgba(20,18,14,0.66) 0%, rgba(20,18,14,0.34) 26%, rgba(20,18,14,0) 52%)",
          opacity: CAPTIONS[shot.id] ? 1 : 0,
        }}
      />
      <CaptionLayer shot={shot} />
    </AbsoluteFill>
  );
};
