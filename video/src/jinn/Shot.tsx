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
      {/* Type sits over a wash, not over bare plate. Half these plates are
          near-white parchment and half are night-washed, so cream type needs
          its own ground or it disappears on every second shot. Laid as a
          shadow wash rather than a black scrim — it reads as pigment brushed
          over the paper, which is the only version of this the style allows. */}
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(to top, rgba(22,20,16,0.88) 0%, rgba(22,20,16,0.80) 18%, rgba(30,28,22,0.52) 38%, rgba(30,28,22,0) 62%)",
          opacity: cap ? 1 : 0,
        }}
      />
      {/* and a lighter one up top, so the citation slug has a ground too */}
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(to bottom, rgba(22,20,16,0.62) 0%, rgba(22,20,16,0) 22%)",
          opacity: cap?.cite || cap?.chip ? 1 : 0,
        }}
      />
      <CaptionLayer shot={shot} />
    </AbsoluteFill>
  );
};
