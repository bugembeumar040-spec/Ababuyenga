import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from "remotion";
import type { Shot } from "./beats";
import { FPS } from "./beats";
import { CAPTIONS, ROOT_LETTERS, type Caption as Cap } from "./captions";
import { EMPHASIS, PALETTE, SAFE, SERIF, TYPE } from "./theme";

const LEAD_IN = Math.round(FPS * 0.55); // plate lands first, then the type
const TAIL = Math.round(FPS * 0.45); // and clears before the cut

const norm = (w: string) => w.toLowerCase().replace(/[^a-z0-9'’·-]/g, "");

/** Split a line into tokens, flagging the ones inside an emphasis phrase. */
function tokenize(text: string, em: string[] = []) {
  const words = text.split(/\s+/).filter(Boolean);
  const flags = new Array(words.length).fill(false);
  for (const phrase of em) {
    const target = phrase.split(/\s+/).map(norm);
    for (let i = 0; i + target.length <= words.length; i++) {
      if (target.every((t, k) => norm(words[i + k]) === t)) {
        for (let k = 0; k < target.length; k++) flags[i + k] = true;
      }
    }
  }
  return words.map((word, i) => ({ word, em: flags[i] }));
}

/** A pen-drawn rule that fills the run it sits under. */
const RuleUnder: React.FC<{ progress: number; strike?: boolean }> = ({
  progress,
  strike = false,
}) => (
  <svg
    viewBox="0 0 100 8"
    preserveAspectRatio="none"
    style={{
      position: "absolute",
      left: "-2%",
      width: "104%",
      height: strike ? "0.16em" : "0.14em",
      bottom: strike ? "0.34em" : "-0.06em",
      overflow: "visible",
    }}
  >
    <path
      d="M0 5 Q 28 2.4 55 4.8 T 100 3.6"
      stroke={strike ? PALETTE.ink : EMPHASIS}
      strokeWidth={strike ? 4.5 : 3.4}
      strokeLinecap="round"
      fill="none"
      strokeDasharray={130}
      strokeDashoffset={130 * (1 - progress)}
      opacity={0.92}
    />
  </svg>
);

const Word: React.FC<{
  word: string;
  em: boolean;
  t: number;
  still: boolean;
  size: number;
}> = ({ word, em, t, still, size }) => {
  const o = interpolate(t, [0, 1], [0, 1], { extrapolateRight: "clamp" });
  // Ink taking: it arrives out of focus and sharpens as the fibre pulls it in.
  const blur = interpolate(t, [0, 1], [10, 0], { extrapolateRight: "clamp" });
  const y = still ? 0 : interpolate(t, [0, 1], [16, 0], { extrapolateRight: "clamp" });
  const track = interpolate(t, [0, 1], [0.12, still ? 0.06 : 0.015], {
    extrapolateRight: "clamp",
  });
  return (
    <span
      style={{
        position: "relative",
        display: "inline-block",
        marginRight: size * 0.26,
        opacity: o,
        filter: `blur(${blur}px)`,
        transform: `translateY(${y}px)`,
        letterSpacing: `${track}em`,
        color: em ? EMPHASIS : PALETTE.rawPaper,
      }}
    >
      {word}
      {em ? <RuleUnder progress={interpolate(t, [0.45, 1], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })} /> : null}
    </span>
  );
};

const Line: React.FC<{
  text: string;
  em?: string[];
  p: number;
  size: number;
  mode: string;
  weight?: number;
  delay?: number;
}> = ({ text, em, p, size, mode, weight = 600, delay = 0 }) => {
  const tokens = tokenize(text, em);
  const still = mode === "hold";
  const hard = mode === "hard";
  // A hard line lands whole. Everything else staggers, and a held line
  // staggers slowest — the stillness is the point.
  const span = hard ? 0 : still ? 0.55 : 0.42;
  return (
    <div
      style={{
        fontFamily: SERIF,
        fontSize: size,
        fontWeight: weight,
        lineHeight: 1.24,
        textShadow: `0 3px 26px rgba(20,16,12,0.72), 0 1px 3px rgba(20,16,12,0.9)`,
      }}
    >
      {tokens.map((tk, i) => {
        const start = delay + (tokens.length > 1 ? (i / tokens.length) * span : 0);
        const t = interpolate(p, [start, start + 0.3], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
          easing: Easing.out(Easing.quad),
        });
        return <Word key={i} word={tk.word} em={tk.em} t={t} still={still} size={size} />;
      })}
    </div>
  );
};

/** The J-N-N device: the root letters carry ember inside every cognate. */
const RootWord: React.FC<{ word: string; p: number }> = ({ word, p }) => {
  let used = 0;
  const letters = word.split("").map((ch, i) => {
    let isRoot = false;
    if (used < ROOT_LETTERS.length && ch.toUpperCase() === ROOT_LETTERS[used]) {
      isRoot = true;
      used += 1;
    }
    const t = interpolate(p, [i * 0.035, i * 0.035 + 0.34], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.out(Easing.cubic),
    });
    return (
      <span
        key={i}
        style={{
          display: "inline-block",
          opacity: t,
          filter: `blur(${(1 - t) * 12}px)`,
          transform: `translateY(${(1 - t) * 10}px)`,
          color: isRoot ? EMPHASIS : PALETTE.rawPaper,
        }}
      >
        {ch === " " ? " " : ch}
      </span>
    );
  });
  return (
    <div
      style={{
        fontFamily: SERIF,
        fontSize: TYPE.root,
        fontWeight: 700,
        letterSpacing: "0.06em",
        lineHeight: 1.05,
        textShadow: "0 4px 40px rgba(20,16,12,0.8)",
      }}
    >
      {letters}
    </div>
  );
};

/** A citation slug, ruled like a margin note. */
const Cite: React.FC<{ text: string; p: number }> = ({ text, p }) => {
  const o = interpolate(p, [0, 0.18], [0, 1], { extrapolateRight: "clamp" });
  return (
    <div
      style={{
        position: "absolute",
        left: SAFE.left,
        top: SAFE.citeTop,
        opacity: o,
        fontFamily: SERIF,
        fontSize: TYPE.cite,
        letterSpacing: "0.34em",
        color: PALETTE.gold,
        textTransform: "uppercase",
        textShadow: "0 2px 18px rgba(20,16,12,0.85)",
      }}
    >
      <div style={{ position: "relative", paddingBottom: 16 }}>
        {text}
        <svg
          viewBox="0 0 100 3"
          preserveAspectRatio="none"
          style={{ position: "absolute", left: 0, bottom: 0, width: "100%", height: 4 }}
        >
          <path
            d="M0 1.6 Q 40 0.6 70 1.9 T 100 1.2"
            stroke={PALETTE.gold}
            strokeWidth={1.6}
            fill="none"
            strokeDasharray={110}
            strokeDashoffset={110 * (1 - interpolate(p, [0.05, 0.45], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }))}
          />
        </svg>
      </div>
    </div>
  );
};

/** Running counter for the four corrections. Cheapest retention in the film. */
const Chip: React.FC<{ text: string; p: number }> = ({ text, p }) => {
  const o = interpolate(p, [0.08, 0.26], [0, 1], { extrapolateRight: "clamp" });
  return (
    <div
      style={{
        position: "absolute",
        right: SAFE.right,
        top: SAFE.citeTop,
        opacity: o,
        fontFamily: SERIF,
        fontSize: TYPE.kicker,
        letterSpacing: "0.4em",
        color: EMPHASIS,
        border: `2px solid ${EMPHASIS}`,
        padding: "14px 26px 14px 32px",
        textTransform: "uppercase",
      }}
    >
      {text}
    </div>
  );
};

export const CaptionLayer: React.FC<{ shot: Shot }> = ({ shot }) => {
  const frame = useCurrentFrame();
  const cap: Cap | undefined = CAPTIONS[shot.id];
  if (!cap) return null;

  const window = Math.max(shot.frames - LEAD_IN - TAIL, FPS);
  const p = interpolate(frame, [LEAD_IN, LEAD_IN + window], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  // Ink does not vanish; it lifts off the sheet at the very end of the hold.
  const out = interpolate(frame, [shot.frames - TAIL, shot.frames], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const mode = cap.mode ?? "bleed";
  const centred = mode === "hold" || mode === "root" || mode === "strike";

  return (
    <AbsoluteFill style={{ opacity: out }}>
      {cap.cite ? <Cite text={cap.cite} p={p} /> : null}
      {cap.chip ? <Chip text={cap.chip} p={p} /> : null}

      <div
        style={{
          position: "absolute",
          left: SAFE.left,
          right: SAFE.right,
          bottom: 1440 - SAFE.captionBaseline,
          textAlign: centred ? "center" : "left",
        }}
      >
        {mode === "root" && cap.root ? (
          <>
            <RootWord word={cap.root} p={p} />
            {cap.gloss ? (
              <div
                style={{
                  marginTop: 34,
                  fontFamily: SERIF,
                  fontSize: TYPE.gloss,
                  fontStyle: "italic",
                  letterSpacing: "0.06em",
                  color: PALETTE.parchment,
                  opacity: interpolate(p, [0.34, 0.6], [0, 0.94], {
                    extrapolateLeft: "clamp",
                    extrapolateRight: "clamp",
                  }),
                  textShadow: "0 2px 22px rgba(20,16,12,0.85)",
                }}
              >
                {cap.gloss}
              </div>
            ) : null}
          </>
        ) : null}

        {mode === "strike" && cap.strike ? (
          <div
            style={{
              position: "relative",
              display: "inline-block",
              marginBottom: 40,
              fontFamily: SERIF,
              fontSize: TYPE.captionLead,
              fontWeight: 700,
              letterSpacing: "0.05em",
              color: PALETTE.parchment,
              opacity: interpolate(p, [0, 0.12, 0.78, 1], [0, 1, 1, 0.42], {
                extrapolateRight: "clamp",
              }),
              textShadow: "0 3px 26px rgba(20,16,12,0.8)",
            }}
          >
            {cap.strike}
            <RuleUnder
              strike
              progress={interpolate(p, [0.3, 0.56], [0, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              })}
            />
          </div>
        ) : null}

        {cap.text ? (
          <Line
            text={cap.text}
            em={cap.em}
            p={p}
            mode={mode}
            size={cap.sub ? TYPE.captionLead : TYPE.caption}
            weight={mode === "hold" ? 700 : 600}
            delay={mode === "strike" ? 0.6 : 0}
          />
        ) : null}

        {cap.sub ? (
          <div style={{ marginTop: 22, opacity: 0.94 }}>
            <Line
              text={cap.sub}
              em={cap.em}
              p={p}
              mode={mode}
              size={TYPE.caption * 0.72}
              weight={400}
              delay={mode === "hard" ? 0.14 : 0.3}
            />
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};
