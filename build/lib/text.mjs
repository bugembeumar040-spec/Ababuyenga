import fs from 'node:fs';
import path from 'node:path';
import opentype from 'opentype.js';
import { BUILD } from './paths.mjs';

const cache = new Map();

/** Load a font once and expose real glyph-advance measurement. */
export function loadFont(style, which = 'display') {
  const file = which === 'display' ? style.font.displayFile : style.font.bodyFile;
  const full = path.join(BUILD, style.font.dir, file);
  if (!cache.has(full)) {
    if (!fs.existsSync(full)) throw new Error(`font missing: ${full} (run: node bin/fetch-fonts.mjs)`);
    const buf = fs.readFileSync(full);
    const font = opentype.parse(buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength));
    cache.set(full, font);
  }
  return cache.get(full);
}

/**
 * libass does not size a font by its em square — it fits the font's full glyph
 * bounding box into the requested size. For a display face like Anton, whose
 * bbox overflows the em by ~73%, ignoring this makes every measurement 1.7x too
 * large and the auto-fit picks sizes that visibly under-fill the frame.
 *
 * Verified empirically against rendered frames: predicted vs measured ink width
 * is 431.6 vs 432px (Anton) and 759.4 vs 764px (Inter) at the same nominal size.
 */
export function renderScale(font) {
  const { yMax, yMin } = font.tables.head;
  return font.unitsPerEm / (yMax - yMin);
}

/** Width of `text` at nominal `size`, in rendered px. */
export function measure(font, text, size) {
  const scale = (size / font.unitsPerEm) * renderScale(font);
  let w = 0;
  let prev = null;
  for (const ch of text) {
    const glyph = font.charToGlyph(ch);
    if (prev) w += font.getKerningValue(prev, glyph);
    w += glyph.advanceWidth ?? 0;
    prev = glyph;
  }
  return w * scale;
}

/** Cap height in rendered px — what the eye reads as the height of a caps line. */
export function capHeight(font, size) {
  const os2 = font.tables.os2;
  const units = os2?.sCapHeight || font.tables.head.yMax * 0.72;
  return (units / font.unitsPerEm) * size * renderScale(font);
}

/**
 * Greedy wrap into at most `maxLines`, preferring balanced line lengths.
 * Returns null when the text cannot fit the constraints at this size.
 */
export function wrap(font, text, size, maxWidth, maxLines) {
  const words = text.split(/\s+/).filter(Boolean);
  const lines = [];
  let cur = '';
  for (const w of words) {
    const candidate = cur ? `${cur} ${w}` : w;
    if (measure(font, candidate, size) <= maxWidth || !cur) {
      cur = candidate;
    } else {
      lines.push(cur);
      cur = w;
    }
  }
  if (cur) lines.push(cur);
  if (lines.length > maxLines) return null;
  if (lines.some((l) => measure(font, l, size) > maxWidth)) return null;
  return balance(font, lines, size, maxWidth);
}

/** Even out a two-line break so the second line is never a runt. */
function balance(font, lines, size, maxWidth) {
  if (lines.length !== 2) return lines;
  const words = `${lines[0]} ${lines[1]}`.split(' ');
  let best = lines;
  let bestScore = Infinity;
  for (let split = 1; split < words.length; split++) {
    const a = words.slice(0, split).join(' ');
    const b = words.slice(split).join(' ');
    const wa = measure(font, a, size);
    const wb = measure(font, b, size);
    if (wa > maxWidth || wb > maxWidth) continue;
    const score = Math.abs(wa - wb);
    if (score < bestScore) {
      bestScore = score;
      best = [a, b];
    }
  }
  return best;
}

/**
 * Largest size in [min,max] at which `text` wraps within the box.
 * Sizes are searched on a 2px grid — sub-2px differences are invisible at 1080p
 * and a coarse grid keeps repeated renders byte-identical.
 */
export function fit(font, text, { maxWidth, minSize, maxSize, maxLines, targetWidth }) {
  let chosen = null;
  for (let size = maxSize; size >= minSize; size -= 2) {
    const lines = wrap(font, text, size, maxWidth, maxLines);
    if (!lines) continue;
    const widest = Math.max(...lines.map((l) => measure(font, l, size)));
    chosen = { size, lines, width: widest };
    if (!targetWidth || widest <= targetWidth || size === minSize) break;
  }
  if (!chosen) {
    // Nothing fits even at minSize: fall back to minSize and let the audit flag it.
    const lines = wrap(font, text, minSize, maxWidth, maxLines + 2) || [text];
    chosen = { size: minSize, lines, width: Math.max(...lines.map((l) => measure(font, l, minSize))) };
  }
  return chosen;
}

/** Rough syllable count — drives how long a word holds the screen. */
export function syllables(word) {
  const w = word.toLowerCase().replace(/[^a-z£0-9%.]/g, '');
  if (!w) return 1;
  const digits = w.match(/\d/g);
  if (digits) return Math.max(1, digits.length);
  const groups = w.replace(/e\b/, '').match(/[aeiouy]+/g);
  return Math.max(1, groups ? groups.length : 1);
}
