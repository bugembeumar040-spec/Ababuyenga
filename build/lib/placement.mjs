/**
 * Where text can go on a given frame.
 *
 * The pack asks for captions in the upper third and "never over a face". Half
 * the supplied stills put the subject there, so instead of one global band the
 * layout is solved per frame against that frame's own ink coverage: slide a
 * window of the required height and take the emptiest position, with a pull
 * toward the band the pack prefers so a clear frame still reads as specified.
 */

/** Mean ink coverage over [a,b] of a 0..1-indexed occupancy profile. */
function coverage(profile, a, b) {
  const n = profile.length;
  const i0 = Math.max(0, Math.floor(a * n));
  const i1 = Math.min(n, Math.ceil(b * n));
  if (i1 <= i0) return 1;
  let sum = 0;
  for (let i = i0; i < i1; i++) sum += profile[i];
  return sum / (i1 - i0);
}

/**
 * Centre Y (as a fraction of height) for a block of `height` fraction.
 * `blocked` is a list of [top,bottom] fractions already claimed by other text.
 */
/**
 * Cleanliness comes first, position second.
 *
 * A weighted score lets a strong positional preference drag text onto a face,
 * which is the one thing the pack forbids. So this walks widening ink budgets
 * and, at the first budget with any candidate, takes the candidate nearest the
 * preferred band. Only if nothing anywhere is clean does it fall back to the
 * emptiest position in the frame.
 */
const INK_BUDGETS = [0.005, 0.02, 0.05, 0.09, 0.15];

export function bestBand(profile, {
  height,
  preferY = 0.16,
  minY = 0.06,
  maxY = 0.94,
  blocked = [],
  step = 0.01,
} = {}) {
  if (!profile) return { y: preferY, ink: null };
  const half = height / 2;
  const lo = Math.max(minY + half, half);
  const hi = Math.min(maxY - half, 1 - half);

  const candidates = [];
  for (let y = lo; y <= hi + 1e-9; y += step) {
    const top = y - half;
    const bottom = y + half;
    if (blocked.some(([bt, bb]) => bottom > bt && top < bb)) continue;
    candidates.push({ y, ink: coverage(profile, top, bottom) });
  }
  if (!candidates.length) return { y: preferY, ink: coverage(profile, preferY - half, preferY + half) };

  for (const budget of INK_BUDGETS) {
    const clean = candidates.filter((c) => c.ink <= budget);
    if (!clean.length) continue;
    clean.sort((a, b) => Math.abs(a.y - preferY) - Math.abs(b.y - preferY));
    return { y: Number(clean[0].y.toFixed(4)), ink: Number(clean[0].ink.toFixed(4)) };
  }
  const emptiest = candidates.reduce((a, b) => (b.ink < a.ink ? b : a));
  return { y: Number(emptiest.y.toFixed(4)), ink: Number(emptiest.ink.toFixed(4)) };
}

/**
 * The band the topmost subject's head occupies.
 *
 * There is no face detector here, but every one of these frames is a single
 * subject on a flat ground, so the first ink from the top is the head whenever
 * the frame holds a character. Blocking it enforces the pack's "never over a
 * face" without needing to know whose face it is.
 */
export function faceGuards(detailProfile, contentTop, { depth = 0.17, busy = 0.12 } = {}) {
  const guards = [];
  if (detailProfile) {
    const n = detailProfile.length;

    // The first genuinely busy band is the top of the head whenever the
    // character is the topmost thing in frame — which is 15 of these 18 stills.
    // Guarding the profile's peak instead was tried and rejected: on the frames
    // with detailed props above the character (a shelf, a stall awning) the peak
    // is the prop, and guarding it pushes captions down onto the face it was
    // supposed to protect. Those three frames carry an explicit captionY.
    const first = detailProfile.findIndex((v) => v >= busy);
    if (first !== -1) {
      const y = first / n;
      if (y <= 0.75) guards.push([Math.max(0, y - 0.01), Math.min(1, y + depth)]);
    }
  }
  if (!guards.length && contentTop != null && contentTop <= 0.75) {
    guards.push([Math.max(0, contentTop), Math.min(1, contentTop + depth)]);
  }
  return guards;
}

/** Mean luminance under a band, for deciding contrast. */
export function bandLuma(lumaProfile, y, height) {
  if (!lumaProfile) return null;
  const n = lumaProfile.length;
  const i0 = Math.max(0, Math.floor((y - height / 2) * n));
  const i1 = Math.min(n, Math.ceil((y + height / 2) * n));
  if (i1 <= i0) return null;
  let sum = 0;
  for (let i = i0; i < i1; i++) sum += lumaProfile[i];
  return sum / (i1 - i0);
}

/** Rough block height, as a fraction of frame height, per card kind. */
export const CARD_HEIGHT = {
  word: 0.17,
  line: 0.15,
  arrow: 0.11,
  quote: 0.09,
  pill: 0.15,
  collision: 0.25,
  list: 0.30,
};

export function cardHeight(card) {
  if (card.kind === 'list') return 0.13 + 0.055 * card.items.length;
  return CARD_HEIGHT[card.kind] ?? 0.15;
}
