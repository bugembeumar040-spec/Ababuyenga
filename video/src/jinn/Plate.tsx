import React from "react";
import {
  AbsoluteFill,
  Easing,
  Img,
  interpolate,
  random,
  staticFile,
  useCurrentFrame,
} from "remotion";
import type { Shot } from "./beats";
import { PALETTE } from "./theme";
import { Motes } from "./effects";

/**
 * The plate layer: one generated illustration, moved.
 *
 * Every move is total travel across the shot and eased out, never linear —
 * a camera on a geared head arrives, it does not stop dead. Shots the pack
 * marks "hold dead still" get exactly zero transform; that stillness is doing
 * work in the edit and a breathing scale would undo it.
 */
export const Plate: React.FC<{ shot: Shot; available: boolean }> = ({
  shot,
  available,
}) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [0, shot.frames], [0, 1], {
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  const { zoom, dx, dy } = shot.camera;
  // Overscan so a pull-back never runs off the edge of the plate.
  const base = 1.14;
  const scale = shot.locked ? base : base * (1 + zoom * p);
  const tx = shot.locked ? 0 : dx * p;
  const ty = shot.locked ? 0 : dy * p;

  return (
    <AbsoluteFill style={{ overflow: "hidden", backgroundColor: PALETTE.parchment }}>
      <AbsoluteFill
        style={{
          transform: `scale(${scale}) translate(${tx}px, ${ty}px)`,
          transformOrigin: "50% 50%",
        }}
      >
        {available ? (
          <Img
            src={staticFile(shot.plate)}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        ) : (
          <ProceduralPlate shot={shot} />
        )}
      </AbsoluteFill>
      {/* Dust only where the pack put a light shaft in the room. */}
      {shot.locked ? <Motes seed={shot.id} count={18} /> : null}
    </AbsoluteFill>
  );
};

/**
 * Stand-in plate, drawn in the house palette from the shot id.
 *
 * The film cuts and renders end to end before a single illustration exists, so
 * timing, type and camera can be judged now. Drop the real file at
 * public/plates/<id>.png and this disappears — nothing else changes.
 */
const ProceduralPlate: React.FC<{ shot: Shot }> = ({ shot }) => {
  const s = shot.id;
  const washX = 22 + random(`${s}wx`) * 56;
  const washY = 30 + random(`${s}wy`) * 44;
  const wedgeSkew = -22 + random(`${s}sk`) * 44;
  const night = random(`${s}n`) > 0.62;
  const ground = night ? PALETTE.night : PALETTE.parchment;

  return (
    <AbsoluteFill>
      <svg width="100%" height="100%" viewBox="0 0 2560 1440" preserveAspectRatio="xMidYMid slice">
        <rect width="2560" height="1440" fill={PALETTE.parchment} />
        <rect width="2560" height="1440" fill={ground} opacity={night ? 0.72 : 0.2} />

        {/* the hard-edged wedge of raw paper the style calls light */}
        <polygon
          points={`${400 + wedgeSkew},0 ${980 + wedgeSkew},0 ${1520},1440 ${840},1440`}
          fill={PALETTE.rawPaper}
          opacity={0.5}
        />
        {/* one flat translucent shadow wash, clean edge, thrown right */}
        <polygon
          points={`${1520},1440 ${840},1440 ${1180},900 ${2100},1010`}
          fill={PALETTE.shadow}
          opacity={0.28}
        />

        {/* a wash pooling and granulating where the brush sat longest */}
        <filter id={`g-${s}`}>
          <feTurbulence type="fractalNoise" baseFrequency="0.02" numOctaves={3} seed={s.length * 5} />
          <feDisplacementMap in="SourceGraphic" scale={70} />
        </filter>
        <radialGradient id={`w-${s}`}>
          <stop offset="0%" stopColor={PALETTE.ink} stopOpacity="0.34" />
          <stop offset="88%" stopColor={PALETTE.ink} stopOpacity="0.22" />
          <stop offset="100%" stopColor={PALETTE.ink} stopOpacity="0" />
        </radialGradient>
        <ellipse
          cx={`${washX}%`}
          cy={`${washY}%`}
          rx="30%"
          ry="26%"
          fill={`url(#w-${s})`}
          filter={`url(#g-${s})`}
        />

        {/* loose contour — the subject, unresolved */}
        <rect
          x={780}
          y={300}
          width={1000}
          height={330}
          rx={18}
          fill="none"
          stroke={PALETTE.ink}
          strokeWidth={5}
          strokeOpacity={0.5}
          strokeDasharray="180 26 90 18"
        />

        {/* Slate sits high in the frame, clear of the caption band. */}
        <text
          x={1280}
          y={430}
          textAnchor="middle"
          fill={PALETTE.ink}
          fillOpacity={0.5}
          fontSize={118}
          fontFamily="serif"
          letterSpacing={20}
        >
          {s}
        </text>
        <text
          x={1280}
          y={500}
          textAnchor="middle"
          fill={PALETTE.ink}
          fillOpacity={0.34}
          fontSize={34}
          fontFamily="serif"
          letterSpacing={6}
        >
          PLATE PENDING · public/plates/{s}.png
        </text>
        <text
          x={1280}
          y={556}
          textAnchor="middle"
          fill={PALETTE.ink}
          fillOpacity={0.3}
          fontSize={29}
          fontFamily="serif"
        >
          {shot.move}
        </text>
      </svg>
    </AbsoluteFill>
  );
};
