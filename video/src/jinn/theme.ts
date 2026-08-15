// House palette and type scale — carried verbatim from the shot pack's STYLE
// block so the motion layer and the plates share one system.

export const PALETTE = {
  parchment: "#E8DCC8",
  rawPaper: "#F4EBD9",
  ink: "#3A2E24",
  shadow: "#6E7A80",
  night: "#2B3440",
  gold: "#C9A227",
  ember: "#E8873C",
  garden: "#123B36",
} as const;

// Ember and garden are reserved in the plates. On the type layer ember is the
// single emphasis colour and nothing else is allowed to use it.
export const EMPHASIS = PALETTE.ember;

export const SERIF =
  '"Liberation Serif", "DejaVu Serif", "Bitstream Charter", Georgia, serif';
export const SANS = '"Liberation Sans", "DejaVu Sans", Helvetica, sans-serif';

export const TYPE = {
  // 2560x1440 canvas. Caption sits in the lower third, clear of the subject.
  caption: 74,
  captionLead: 92,
  root: 210,
  cognate: 132,
  gloss: 46,
  cite: 34,
  kicker: 30,
} as const;

export const SAFE = {
  left: 200,
  right: 200,
  captionBaseline: 1180, // baseline of the caption block
  citeTop: 120,
} as const;
