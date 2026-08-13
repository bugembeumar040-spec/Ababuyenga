/**
 * Caption bursts: the short groups of words that cut on and off with the voice.
 *
 * Split rules, in order of authority:
 *   - never straddle a sentence-final full stop
 *   - never exceed the words-per-burst budget
 *   - never exceed what will fit in maxLines × maxCharsPerLine
 */
/** Words that must never be the last thing on screen in a burst. */
const DANGLING = new Set([
  'a', 'an', 'the', 'of', 'to', 'and', 'or', 'in', 'on', 'at', 'for', 'from',
  'is', 'was', 'it', 'its', 'your', 'you', 'my', 'their', 'this', 'that',
  'with', 'by', 'as', 'so', 'but', 'what', 'who', 'not', 'no', 'every',
]);

const clean = (w) => w.toLowerCase().replace(/[^a-z']/g, '');

export function splitBursts(sentence, caption) {
  const budget = caption.maxCharsPerLine * caption.maxLines;
  const groups = [];
  let cur = [];
  const flush = () => { if (cur.length) groups.push(cur); cur = []; };

  for (const word of sentence.words) {
    cur.push(word);
    const chars = cur.map((w) => w.text).join(' ').length;
    if (/[.!?]$/.test(word.text) || cur.length >= caption.wordsPerBurst || chars >= budget) flush();
  }
  flush();

  // A burst must not end on a word the eye expects to be completed. Push a
  // trailing function word forward so it opens the next burst instead.
  for (let i = 0; i < groups.length - 1; i++) {
    while (groups[i].length > 1 && DANGLING.has(clean(groups[i].at(-1).text))) {
      groups[i + 1].unshift(groups[i].pop());
    }
  }

  // A group with no letters or digits left in it — a bare em dash the pass above
  // stripped down — is not a caption. Fold it into whichever neighbour exists.
  for (let i = groups.length - 1; i >= 0; i--) {
    if (groups[i].some((w) => /[a-z0-9]/i.test(w.text))) continue;
    const target = i > 0 ? i - 1 : 1;
    if (groups[target]) {
      if (target < i) groups[target].push(...groups[i]);
      else groups[target].unshift(...groups[i]);
      groups.splice(i, 1);
    }
  }

  // A single trailing word ("TERM.") reads as a stutter. Fold it back into the
  // previous burst whenever the combined line still fits.
  if (groups.length > 1 && groups[0].length === 1
      && [...groups[0], ...groups[1]].map((w) => w.text).join(' ').length <= budget) {
    groups[1] = [...groups[0], ...groups[1]];
    groups.shift();
  }
  for (let i = groups.length - 1; i > 0; i--) {
    if (groups[i].length > 1) continue;
    const merged = [...groups[i - 1], ...groups[i]];
    if (merged.map((w) => w.text).join(' ').length <= budget && merged.length <= caption.wordsPerBurst + 2) {
      groups[i - 1] = merged;
      groups.splice(i, 1);
    }
  }

  // Last resort: a lone function word left standing by the passes above is worse
  // than a slightly over-long burst, so merge it regardless of the word budget.
  for (let i = groups.length - 1; i >= 0; i--) {
    if (groups[i].length !== 1 || !DANGLING.has(clean(groups[i][0].text))) continue;
    const target = i > 0 ? i - 1 : 1;
    if (!groups[target]) continue;
    const merged = i > 0 ? [...groups[target], ...groups[i]] : [...groups[i], ...groups[target]];
    if (merged.map((w) => w.text).join(' ').length > budget) continue;
    groups[target] = merged;
    groups.splice(i, 1);
  }

  return groups.map((words) => ({
    text: words.map((w) => w.text).join(' ').toUpperCase(),
    start: words[0].start,
    end: words[words.length - 1].end,
  }));
}

/**
 * Give every burst its screen time.
 *
 * A burst holds until the next one cuts it off, so the caption line is never
 * absent while the voice is still mid-sentence. On a real pause it clears
 * shortly after its last word instead of hanging there.
 */
export function holdBursts(bursts, scene, caption) {
  const floor = scene.start;
  const ceiling = scene.end - caption.gapBeforeCut;

  bursts.forEach((b, i) => {
    const next = bursts[i + 1];
    b.start = Math.max(b.start, floor);
    const natural = b.end + 0.45;
    b.end = Math.min(next ? Math.min(next.start, natural) : natural, ceiling);
    if (b.end - b.start < caption.minBurst) {
      b.end = Math.min(b.start + caption.minBurst, next ? next.start : ceiling);
    }
  });

  return bursts.filter((b) => b.end - b.start > 0.12);
}

/**
 * A takeover card stands in for the burst it replaces — it must never swallow
 * one. The card holds from its word until the next burst needs the screen, and
 * only the burst it is standing in for is removed.
 */
export function applyTakeover(bursts, card) {
  if (!card?.takeover) return { bursts, card };

  const replaced = bursts.filter((b) => b.start >= card.start - 0.12 && b.start < card.start + 0.45);
  const kept = bursts.filter((b) => !replaced.includes(b));
  const next = kept.find((b) => b.start >= card.start);

  const end = next ? Math.min(card.end, next.start - 0.05) : card.end;
  return {
    bursts: kept,
    card: { ...card, end: Math.max(card.start + 0.6, end), replacedBursts: replaced.map((b) => b.text) },
  };
}
