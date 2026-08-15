import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import type { Shot as ShotType } from "./beats";
import { FPS } from "./beats";
import { CAPTIONS } from "./captions";
import { PLATES, isLight } from "./plates";
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

  const light = isLight(shot.id);
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
          color={light ? PALETTE.gold : PALETTE.rawPaper}
        />
      ) : null}
      {/* The caption band gets a wash to sit on, in the direction the plate
          is already going: paper lifted on a light shot, night deepened on a
          dark one. Never a black scrim — the style sheet has no black paint in
          it, and a scrim heavy enough to carry cream type over parchment would
          be the most obviously digital thing in the film. */}
      <AbsoluteFill
        style={{
          background: light
            ? "linear-gradient(to top, rgba(244,235,217,0.80) 0%, rgba(244,235,217,0.58) 20%, rgba(244,235,217,0) 46%)"
            : "linear-gradient(to top, rgba(24,22,18,0.90) 0%, rgba(24,22,18,0.72) 24%, rgba(30,28,22,0) 56%)",
          opacity: cap ? 1 : 0,
        }}
      />
      {/* and the same, inverted, so the citation slug has a ground too */}
      <AbsoluteFill
        style={{
          background: light
            ? "linear-gradient(to bottom, rgba(244,235,217,0.72) 0%, rgba(244,235,217,0) 20%)"
            : "linear-gradient(to bottom, rgba(24,22,18,0.66) 0%, rgba(24,22,18,0) 20%)",
          opacity: cap?.cite || cap?.chip ? 1 : 0,
        }}
      />
      <CaptionLayer shot={shot} />
    </AbsoluteFill>
  );
};
