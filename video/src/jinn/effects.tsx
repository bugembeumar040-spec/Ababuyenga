import React from "react";
import {
  AbsoluteFill,
  Img,
  interpolate,
  random,
  staticFile,
  useCurrentFrame,
} from "remotion";
import { PALETTE } from "./theme";

/**
 * One sheet of paper for the whole film.
 *
 * The plates cut beneath it but this layer never does, so the tooth, the
 * deckle and the cockle stay put across every cut. It is the single cheapest
 * thing that stops 64 generated images reading as 64 separate images.
 *
 * Because it never changes, it is baked. The SVG below is the source of truth
 * and lives in its own `GrainPlate` composition; the film loads the rendered
 * PNG. Evaluating two full-canvas feTurbulence filters 18,417 times to get the
 * same pixels every time was over half the render.
 */
export const PaperGrain: React.FC<{ opacity?: number }> = ({
  opacity = 0.38,
}) => (
  <AbsoluteFill style={{ pointerEvents: "none", mixBlendMode: "multiply", opacity }}>
    <Img
      src={staticFile("paper-grain.png")}
      style={{ width: "100%", height: "100%" }}
    />
  </AbsoluteFill>
);

/** The grain, drawn live. Rendered once to public/paper-grain.png — see Root. */
export const GrainPlate: React.FC = () => (
  <AbsoluteFill style={{ pointerEvents: "none" }}>
    <svg width="100%" height="100%" viewBox="0 0 2560 1440" preserveAspectRatio="none">
      <filter id="tooth" x="0" y="0" width="100%" height="100%">
        <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves={4} seed={7} />
        <feColorMatrix type="saturate" values="0" />
        <feComponentTransfer>
          <feFuncA type="linear" slope="0.55" intercept="0" />
        </feComponentTransfer>
      </filter>
      <rect width="2560" height="1440" filter="url(#tooth)" />
      {/* cockle — the long soft ripple a wet sheet keeps after it dries */}
      <filter id="cockle">
        <feTurbulence type="fractalNoise" baseFrequency="0.004 0.011" numOctaves={2} seed={3} />
        <feColorMatrix type="saturate" values="0" />
        <feComponentTransfer>
          <feFuncA type="linear" slope="0.16" />
        </feComponentTransfer>
      </filter>
      <rect width="2560" height="1440" filter="url(#cockle)" />
    </svg>
  </AbsoluteFill>
);

/**
 * Parchment falloff at the edges. No black — the sheet just runs out of light.
 *
 * Deliberately NOT baked like the grain. Baking it measured a max channel
 * difference of 2/255 — an 8-bit rounding artefact of round-tripping a smooth
 * gradient through PNG — and bought almost no time, because rasterising one
 * radial gradient is cheap. The grain was worth baking because feTurbulence is
 * not. Don't "optimise" this one.
 */
export const Vignette: React.FC = () => (
  <AbsoluteFill style={{ pointerEvents: "none" }}>
    <svg width="100%" height="100%" viewBox="0 0 2560 1440" preserveAspectRatio="none">
      <radialGradient id="vig" cx="50%" cy="46%" r="72%">
        <stop offset="55%" stopColor={PALETTE.night} stopOpacity="0" />
        <stop offset="100%" stopColor={PALETTE.night} stopOpacity="0.34" />
      </radialGradient>
      <rect width="2560" height="1440" fill="url(#vig)" />
    </svg>
  </AbsoluteFill>
);

/**
 * WASH BLOOM. Pigment dropped into a wet field: it pushes out fast, then keeps
 * creeping, and dries with a hard edge where it stops. Called for by name on
 * S06b, S13c and S29b.
 */
export const WashBloom: React.FC<{
  progress: number;
  x?: number;
  y?: number;
  color?: string;
}> = ({ progress, x = 50, y = 55, color = PALETTE.gold }) => {
  // Fast out, long creep — a wash never eases in.
  const r = interpolate(progress, [0, 0.35, 1], [0, 46, 68], {
    extrapolateRight: "clamp",
  });
  const alpha = interpolate(progress, [0, 0.12, 0.7, 1], [0, 0.5, 0.42, 0.34], {
    extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill style={{ pointerEvents: "none", mixBlendMode: "multiply" }}>
      <svg width="100%" height="100%" viewBox="0 0 2560 1440" preserveAspectRatio="none">
        <filter id="wet">
          <feTurbulence type="fractalNoise" baseFrequency="0.013" numOctaves={3} seed={11} />
          <feDisplacementMap in="SourceGraphic" scale={90} />
        </filter>
        <radialGradient id="bloom">
          <stop offset="0%" stopColor={color} stopOpacity={alpha * 0.55} />
          <stop offset="72%" stopColor={color} stopOpacity={alpha * 0.75} />
          {/* the dried edge — pigment stacks up where the water stopped */}
          <stop offset="93%" stopColor={color} stopOpacity={alpha} />
          <stop offset="100%" stopColor={color} stopOpacity={0} />
        </radialGradient>
        <ellipse
          cx={`${x}%`}
          cy={`${y}%`}
          rx={`${r}%`}
          ry={`${r * 0.82}%`}
          fill="url(#bloom)"
          filter="url(#wet)"
        />
      </svg>
    </AbsoluteFill>
  );
};

/**
 * A drawn rule, laid down the way a pen lays one: it starts, it travels, and
 * the pressure is uneven. Used under emphasis words and for the cognate stems.
 */
export const InkRule: React.FC<{
  progress: number;
  width: number;
  color?: string;
  weight?: number;
}> = ({ progress, width, color = PALETTE.ember, weight = 6 }) => {
  const len = Math.max(width, 1);
  return (
    <svg width={len} height={weight * 4} viewBox={`0 0 ${len} ${weight * 4}`}>
      <path
        d={`M0 ${weight * 2} Q ${len * 0.3} ${weight * 1.2} ${len * 0.55} ${
          weight * 2.1
        } T ${len} ${weight * 1.7}`}
        stroke={color}
        strokeWidth={weight}
        strokeLinecap="round"
        fill="none"
        strokeDasharray={len * 1.3}
        strokeDashoffset={len * 1.3 * (1 - progress)}
        opacity={0.9}
      />
    </svg>
  );
};

/**
 * Dust in a light shaft. Flecks of raw paper, drifting — the one moving thing
 * allowed in a locked-off frame, and it keeps a held plate from reading frozen.
 */
export const Motes: React.FC<{ seed: string; count?: number }> = ({
  seed,
  count = 26,
}) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <svg width="100%" height="100%" viewBox="0 0 2560 1440">
        {new Array(count).fill(0).map((_, i) => {
          const x = random(`${seed}x${i}`) * 2560;
          const y0 = random(`${seed}y${i}`) * 1440;
          const speed = 0.18 + random(`${seed}s${i}`) * 0.42;
          const y = (y0 - frame * speed + 1440) % 1440;
          const drift = Math.sin((frame + i * 40) / 90) * 14;
          return (
            <circle
              key={i}
              cx={x + drift}
              cy={y}
              r={0.8 + random(`${seed}r${i}`) * 2.1}
              fill={PALETTE.rawPaper}
              opacity={0.14 + random(`${seed}o${i}`) * 0.2}
            />
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};
