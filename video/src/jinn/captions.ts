// The type layer.
//
// Not a transcript. The VO already says every word; burning it all in doubles
// the reading load and flattens the emphasis. What is typeset here is the
// fragment worth stopping on, the four corrections, and the verse citations —
// the three things a viewer screenshots or scrubs back to.
//
// Kinetic devices, in order of how hard they hit:
//   root    — the J-N-N cognate device. The three root letters carry ember
//             inside each word, so the family is visible before it is argued.
//   strike  — the wrong claim, struck through in ink, replaced. One per
//             correction; the pack marks four.
//   hard    — no stagger, full line on one frame. Saved for the two hardest
//             turns in the film (S20b, S22).
//   hold    — dead still, wide tracking, slow. Every SILENCE shot.
//   bleed   — the default. Words settle in one at a time like ink taking.

export type CapMode = "bleed" | "hold" | "hard" | "root" | "strike";

export type Caption = {
  /** Lower-third line. Fragment, not sentence — it is read, not narrated. */
  text?: string;
  /** Second line, smaller, one beat later. */
  sub?: string;
  /** Words drawn in ember. Matched case-insensitively, punctuation ignored. */
  em?: string[];
  mode?: CapMode;
  /** Cognate word for mode "root" — root letters marked inside it. */
  root?: string;
  /** Gloss beneath a root word. */
  gloss?: string;
  /** The wrong claim, for mode "strike". */
  strike?: string;
  /** Citation slug, top left. Latin only — Arabic is burned in from a mushaf. */
  cite?: string;
  /** Running index chip, top right. */
  chip?: string;
  /** Wash bloom centre, as [x%, y%]. */
  bloomAt?: [number, number];
};

// Caption wording follows the RECORDING, not the pack. The VO was read from a
// softened script in places — "a lifeless man" not "a dead man", "a fallen
// king" not "a corpse", "your future" not "your marriage", "owned" not
// "heavier". A viewer hearing one word and reading another on the same frame
// is the most damaging thing this film can do to its own credibility.
//
// Entries for S07, S07b, S07c, S14, S14b, S15, S15b and S16 are kept even
// though the recorded VO does not contain those lines. beats.ts drops the
// shots, so these never render — and they come straight back if a fuller VO is
// recorded, without anyone having to rewrite the type edit.
export const CAPTIONS: Record<string, Caption> = {
  S01: { text: "somebody watching this has paid", sub: "to have a jinn removed", em: ["paid"] },
  S02: { text: "he said he could see", sub: "what you couldn't", em: ["see"], mode: "hold" },
  S02b: { text: "then named a price", em: ["price"], mode: "hard" },
  S03: { text: "the Quran shuts that door", sub: "not with a warning — with a story" },
  S03b: { root: "JINN", gloss: "a word you have said a thousand times", mode: "root" },

  S04: { text: "J · N · N", sub: "to conceal. to cover so it can't be seen.", em: ["conceal"], mode: "hold" },
  S05: { root: "JANNA", gloss: "the garden — growth so thick the ground disappears", mode: "root" },
  S05b: { root: "JANEEN", gloss: "the unborn child, hidden in the womb", mode: "root" },
  S05c: { root: "MAJNOON", gloss: "not mad — a mind covered over", mode: "root" },
  S06: { root: "JUNNA", gloss: "a shield. what you get behind.", mode: "root" },
  S06b: {
    text: "same three letters, every time",
    sub: "not evil. concealed.",
    em: ["concealed"],
    mode: "hold",
    bloomAt: [50, 52],
  },

  S07: { root: "MARIJ MIN NAR", gloss: "the clear moving part of a flame", mode: "root" },
  S07b: { text: "and man, from clay", cite: "Ar-Rahman · 55:15", em: ["clay"] },
  S07c: { text: "they were here before", sub: "one word everyone reads past", em: ["before"], cite: "Al-Hijr · 15:27" },

  S08: { text: "the angels bow", sub: "one doesn't" },
  S08b: {
    strike: "A FALLEN ANGEL",
    text: "he was never one",
    chip: "CORRECTION 1 OF 4",
    mode: "strike",
  },
  S09: {
    text: "KANA MIN AL-JINN",
    sub: "he was of the jinn",
    cite: "Al-Kahf · 18:50",
    mode: "hold",
    em: ["AL-JINN"],
  },
  S10: { text: "I believed the fallen angel version", sub: "most of my life" },
  S10b: { text: "nobody corrected me", sub: "it's in the paintings" },
  S11: { text: "he had the one thing angels don't", sub: "a choice", em: ["choice"] },
  S11b: {
    text: "not a perfect thing that broke",
    sub: "a thing that decided",
    em: ["decided"],
    mode: "hard",
  },

  S12: {
    text: "among us are the righteous",
    sub: "and among us are others below that",
    cite: "Al-Jinn · 72:11",
    chip: "CORRECTION 2 OF 4",
  },
  S12b: { text: "we follow different paths", em: ["different"] },
  S13: { text: "believers. disbelievers.", sub: "the ones who get it right, and the ones who don't" },
  S13b: { text: "exactly like the street you live on", em: ["street"] },
  S13c: {
    text: "when we heard the guidance",
    sub: "we believed in it",
    cite: "Al-Jinn · 72:13",
    bloomAt: [46, 58],
  },

  S14: { text: "an ordinary night", mode: "hold" },
  S14b: { text: "he didn't know they were there", cite: "Al-Ahqaf · 46:29", em: ["didn't know"] },
  S15: { text: "nobody summoned them", sub: "no ritual. no circle on the ground.", em: ["no ritual"] },
  S15b: { text: "they walked past. they heard it.", sub: "and it moved them" },

  S16: { text: "both of us, inside one sentence", cite: "Adh-Dhariyat · 51:56" },
  S16b: { text: "a book that was never addressed to you alone", em: ["alone"] },

  S17: { text: "soldiers of the jinn, and men, and birds", cite: "An-Naml · 27:17" },
  S17b: { text: "before you rise from your place", cite: "An-Naml · 27:39" },
  S18: { text: "every builder and diver", cite: "Sad · 38:37", mode: "hold" },
  S18b: { text: "chambers. basins. cauldrons.", sub: "real, physical power", cite: "Saba · 34:13" },
  S19: {
    text: "under a prophet. by permission.",
    sub: "never for sale. never for you.",
    em: ["never for sale"],
    mode: "hold",
  },

  S20: { text: "he died standing up", sub: "leaning on his staff", mode: "hold" },
  S20b: { text: "and nobody noticed", mode: "hard" },
  S21: { text: "the jinn kept working", sub: "cutting. lifting. carrying." },
  S21b: { text: "for a man who was already dead", em: ["already dead"] },
  S22: { text: "a small creature of the earth", sub: "ate through the wood of the staff", mode: "hard", em: ["small creature"] },
  S22b: { text: "and he fell", cite: "Saba · 34:14", mode: "hard" },
  S23: {
    text: "THEY COULD NOT SEE A LIFELESS MAN",
    sub: "standing in front of them",
    chip: "CORRECTION 3 OF 4",
    mode: "hold",
    em: ["COULD NOT SEE"],
  },
  S23b: { text: "a room full of them, working for a fallen king", em: ["fallen king"] },

  S24: { text: "if they can't see a dead king in the room", sub: "they cannot see your future" },
  S24b: { text: "he was selling you something", sub: "the Quran took apart fourteen centuries ago", mode: "hard", em: ["selling"] },
  S24c: { text: "send this to someone who needs it", mode: "hold" },

  S25: { text: "night comes down in a valley you don't know", cite: "Al-Jinn · 72:6" },
  S25b: { text: "you're sleeping out in the open" },
  S25c: { text: "I seek refuge with the master of this valley", mode: "hold" },
  S26: {
    text: "RAHAQA",
    sub: "they asked for protection. what they got was weight.",
    em: ["weight"],
    mode: "hold",
    cite: "Al-Jinn · 72:6",
  },
  S26b: {
    text: "safety from something hidden",
    sub: "doesn't make you safe. it makes you owned.",
    em: ["owned"],
    chip: "CORRECTION 4 OF 4",
  },

  S27: { text: "shayateen of mankind and jinn", cite: "Al-An'am · 6:112" },
  S27b: { text: "devils from among the jinn", sub: "and devils from among people", em: ["people"], mode: "hold" },
  S28: {
    text: "some of it is sitting across the table from you",
    sub: "asking for cash",
    cite: "An-Nas · 114:6",
    mode: "hold",
    em: ["cash"],
  },
  S28b: { text: "you spent your life afraid of the hidden one", em: ["hidden"] },
  S28c: { text: "the Book closes by pointing at the visible one", em: ["visible"], mode: "hard" },

  S29: { root: "JUNNA", gloss: "it never hands you a technique. it hands you a shield.", mode: "root" },
  S29b: { text: "jinn — the concealed", sub: "janna. janeen. majnoon. junna.", bloomAt: [54, 50] },
  S29c: { text: "al-Fatiha. Ayat al-Kursi.", sub: "the last two surahs. the words in the morning." },
  // The recording ends on "only One sees both", after the fire/clay line —
  // the reverse of the pack's order. These two captions follow the recording,
  // so the film's last words are also its last caption.
  S30: {
    text: "protection that never asks you to negotiate",
    sub: "with anything hidden",
    em: ["negotiate"],
    mode: "hold",
  },
  S30b: {
    text: "made from fire. made from clay.",
    sub: "only One sees both",
    em: ["One"],
    mode: "hold",
  },
};

/** Root letters marked inside a cognate. Latin transliteration only. */
export const ROOT_LETTERS = ["J", "N", "N"];
