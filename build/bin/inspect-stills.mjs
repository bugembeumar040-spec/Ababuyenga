#!/usr/bin/env node
/**
 * Pre-flight look at the supplied stills.
 *
 * Reports, per image: native size, aspect vs 9:16, the background colour it was
 * generated on, and — the one that decides the edit — where the content starts
 * from the top, i.e. how much clean headroom the caption band actually has.
 * The pack reserves the upper third for captions and says "never over a face";
 * this is how we find out which frames honour that and which do not.
 */
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { FFMPEG, FFPROBE, OUT, ROOT } from '../lib/paths.mjs';

const dir = path.resolve(ROOT, process.argv[2] || 'media/zakat/stills');
const SW = 180;
const SH = 320;
const X0 = Math.round(SW * 0.12);
const X1 = Math.round(SW * 0.88);
const XW = X1 - X0;

function rgb(file) {
  return execFileSync(FFMPEG, [
    '-hide_banner', '-loglevel', 'error', '-i', file,
    '-vf', `scale=${SW}:${SH}:force_original_aspect_ratio=increase,crop=${SW}:${SH}`,
    '-frames:v', '1', '-pix_fmt', 'rgb24', '-f', 'rawvideo', '-',
  ], { maxBuffer: 16 * 1024 * 1024 });
}

function dims(file) {
  const out = execFileSync(FFPROBE, ['-v', 'error', '-select_streams', 'v:0',
    '-show_entries', 'stream=width,height', '-of', 'csv=p=0', file]).toString().trim();
  const [w, h] = out.split(',').map(Number);
  return { w, h };
}

/** Modal colour of the outer border — these are all flat-background plates. */
function background(buf) {
  const bins = new Map();
  const sample = (x, y) => {
    const i = (y * SW + x) * 3;
    const key = `${buf[i] >> 3},${buf[i + 1] >> 3},${buf[i + 2] >> 3}`;
    bins.set(key, (bins.get(key) || 0) + 1);
  };
  for (let x = 0; x < SW; x++) { sample(x, 0); sample(x, 1); sample(x, SH - 1); }
  for (let y = 0; y < SH; y++) { sample(0, y); sample(SW - 1, y); }
  const [key] = [...bins.entries()].sort((a, b) => b[1] - a[1])[0];
  const [r, g, b] = key.split(',').map((v) => (Number(v) << 3) + 4);
  return { r, g, b };
}

/** First row from the top carrying real content, as a fraction of height. */
function contentTop(buf, bg, threshold = 34, minFrac = 0.012) {
  for (let y = 0; y < SH; y++) {
    let hits = 0;
    for (let x = 0; x < SW; x++) {
      const i = (y * SW + x) * 3;
      const d = Math.abs(buf[i] - bg.r) + Math.abs(buf[i + 1] - bg.g) + Math.abs(buf[i + 2] - bg.b);
      if (d > threshold) hits++;
    }
    if (hits / SW >= minFrac) return y / SH;
  }
  return 1;
}

/**
 * Per-row ink coverage, downsampled to BANDS buckets. This is what lets the
 * layout stage place captions and cards in the empty parts of each specific
 * frame instead of trusting one global band for the whole film.
 */
const BANDS = 96;
function occupancy(buf, bg, threshold = 34) {
  const bands = new Array(BANDS).fill(0);
  const rowsPer = SH / BANDS;
  for (let y = 0; y < SH; y++) {
    let hits = 0;
    for (let x = 0; x < SW; x++) {
      const i = (y * SW + x) * 3;
      const d = Math.abs(buf[i] - bg.r) + Math.abs(buf[i + 1] - bg.g) + Math.abs(buf[i + 2] - bg.b);
      if (d > threshold) hits++;
    }
    bands[Math.min(BANDS - 1, Math.floor(y / rowsPer))] += hits / SW;
  }
  return bands.map((v) => Number((v / rowsPer).toFixed(4)));
}

/**
 * Local detail, not ink.
 *
 * What makes text illegible is busy pixels, not coloured ones — a caption sits
 * perfectly happily on a flat olive shirt and not at all on a face. Measuring
 * difference-from-background scores those two the same and pushes text into the
 * wrong half of the frame. This counts edge pixels instead, so flat fills read
 * as available space and detail (faces, hands, printed cards) reads as busy.
 */
function detail(buf, threshold = 26) {
  const bands = new Array(BANDS).fill(0);
  const rowsPer = SH / BANDS;
  const lum = (i) => 0.299 * buf[i] + 0.587 * buf[i + 1] + 0.114 * buf[i + 2];
  for (let y = 0; y < SH; y++) {
    let hits = 0;
    for (let x = X0; x < X1; x++) {
      const i = (y * SW + x) * 3;
      const l = lum(i);
      const dx = x + 1 < SW ? Math.abs(lum(i + 3) - l) : 0;
      const dy = y + 1 < SH ? Math.abs(lum(i + SW * 3) - l) : 0;
      if (Math.max(dx, dy) > threshold) hits++;
    }
    bands[Math.min(BANDS - 1, Math.floor(y / rowsPer))] += hits / XW;
  }
  // Dilate vertically: an edge one band away still crowds a line of type.
  const raw = bands.map((v) => v / rowsPer);
  return raw.map((_, i) => Number(Math.max(
    raw[Math.max(0, i - 1)], raw[i], raw[Math.min(BANDS - 1, i + 1)],
  ).toFixed(4)));
}

/** Mean luminance per band — decides whether dark type needs a plate to read. */
function luma(buf) {
  const bands = new Array(BANDS).fill(0);
  const rowsPer = SH / BANDS;
  for (let y = 0; y < SH; y++) {
    // Darkest run across the text band, not its mean: a narrow dark figure on a
    // wide cream field averages bright while still swallowing dark type.
    let darkest = 255;
    for (let x = X0; x < X1 - 8; x++) {
      let run = 0;
      for (let k = 0; k < 8; k++) {
        const i = (y * SW + x + k) * 3;
        run += 0.299 * buf[i] + 0.587 * buf[i + 1] + 0.114 * buf[i + 2];
      }
      darkest = Math.min(darkest, run / 8);
    }
    bands[Math.min(BANDS - 1, Math.floor(y / rowsPer))] += darkest;
  }
  return bands.map((v) => Number((v / rowsPer).toFixed(1)));
}

const hex = ({ r, g, b }) => `#${[r, g, b].map((v) => v.toString(16).padStart(2, '0')).join('').toUpperCase()}`;

const files = fs.readdirSync(dir).filter((f) => /\.(png|jpe?g|webp)$/i.test(f)).sort();
const rows = [];
for (const f of files) {
  const full = path.join(dir, f);
  const { w, h } = dims(full);
  const buf = rgb(full);
  const bg = background(buf);
  const top = contentTop(buf, bg);
  rows.push({ file: f, w, h, aspect: w / h, bg: hex(bg), contentTop: top, profile: occupancy(buf, bg), detail: detail(buf), luma: luma(buf) });
}

const pad = (s, n) => String(s).padEnd(n);
console.log(`\n${pad('FILE', 44)} ${pad('SIZE', 12)} ${pad('AR', 7)} ${pad('BG', 9)} HEADROOM`);
for (const r of rows) {
  const ar = r.aspect.toFixed(3);
  const arFlag = Math.abs(r.aspect - 9 / 16) / (9 / 16) > 0.02 ? ' *' : '  ';
  const head = `${(r.contentTop * 100).toFixed(0)}%`;
  const headFlag = r.contentTop < 0.30 ? '  <- content enters the caption band' : '';
  console.log(`${pad(r.file.slice(0, 43), 44)} ${pad(`${r.w}x${r.h}`, 12)} ${pad(ar + arFlag, 7)} ${pad(r.bg, 9)} ${pad(head, 6)}${headFlag}`);
}
console.log(`\n* = aspect is not 9:16 and will be cropped to fill.`);
console.log(`HEADROOM = fraction of frame height that is empty background above the subject.\n`);

fs.writeFileSync(path.join(OUT, 'stills-inspect.json'), `${JSON.stringify(rows, null, 2)}\n`);
