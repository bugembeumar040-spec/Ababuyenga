#!/usr/bin/env node
/**
 * Builds out/approval-sheet.png — every scene in the pack against the still
 * proposed for it, labelled, so the mapping can be signed off before a frame
 * is rendered. Flags are computed, not asserted: resolution, headroom, and
 * background drift all come from out/stills-inspect.json.
 */
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { loadConfig, ensureOut, ROOT, OUT, BUILD, FFMPEG } from '../lib/paths.mjs';
import { col, ts } from '../lib/ass.mjs';

const { scenes: spine, style } = loadConfig();
const stillsDir = path.resolve(ROOT, spine.project.stillsDir);
const inspect = JSON.parse(fs.readFileSync(path.join(OUT, 'stills-inspect.json'), 'utf8'));
const byFile = new Map(inspect.map((r) => [r.file, r]));

const TW = 300;
const TH = 533;
const LH = 74;
const CH = TH + LH;
const COLS = 5;
const rows = Math.ceil(spine.scenes.length / COLS);
const W = TW * COLS;
const H = CH * rows;

ensureOut();
const tmp = path.join(OUT, '_tiles');
fs.rmSync(tmp, { recursive: true, force: true });
fs.mkdirSync(tmp, { recursive: true });

const cells = [];
spine.scenes.forEach((scene, i) => {
  const out = path.join(tmp, `${String(i + 1).padStart(4, '0')}.png`);
  const file = scene.still ? path.join(stillsDir, scene.still) : null;
  if (file && fs.existsSync(file)) {
    execFileSync(FFMPEG, ['-y', '-hide_banner', '-loglevel', 'error', '-i', file,
      '-vf', `scale=${TW}:${TH}:force_original_aspect_ratio=increase:flags=lanczos,crop=${TW}:${TH},pad=${TW}:${CH}:0:0:color=0x141118`,
      '-frames:v', '1', out], { stdio: 'ignore' });
  } else {
    execFileSync(FFMPEG, ['-y', '-hide_banner', '-loglevel', 'error',
      '-f', 'lavfi', '-i', `color=c=0x2A1F1C:s=${TW}x${TH}`,
      '-vf', `pad=${TW}:${CH}:0:0:color=0x141118`, '-frames:v', '1', out], { stdio: 'ignore' });
  }
  cells.push({ scene, i, out });
});

// xstack with an explicit layout, not the image2 demuxer + tile: the demuxer's
// index probing silently dropped the first frames and shifted every label.
const grid = path.join(OUT, '_grid.png');
const layout = cells.map((_, i) => `${(i % COLS) * TW}_${Math.floor(i / COLS) * CH}`).join('|');
execFileSync(FFMPEG, ['-y', '-hide_banner', '-loglevel', 'error',
  ...cells.flatMap((c) => ['-i', c.out]),
  '-filter_complex', `${cells.map((_, i) => `[${i}:v]`).join('')}xstack=inputs=${cells.length}:layout=${layout}:fill=0x141118[g]`,
  '-map', '[g]', '-frames:v', '1', grid], { stdio: 'ignore' });

const esc = (t) => String(t).replace(/\\/g, '').replace(/[{}]/g, '');
const events = [];
const line = (x, y, size, colour, text, align = 5) =>
  events.push(`Dialogue: 0,0:00:00.00,0:00:10.00,L,,0,0,0,,{\\an${align}\\pos(${Math.round(x)},${Math.round(y)})\\fs${size}\\c${colour}\\bord2}${esc(text)}`);

const cream = col(style.colour.captionFill);
const accent = col('B5543C');
const warn = col('E8B23A');
const dim = col('9A9186');

for (const { scene, i } of cells) {
  const cx = (i % COLS) * TW + TW / 2;
  const top = Math.floor(i / COLS) * CH + TH;
  const info = scene.still ? byFile.get(scene.still) : null;

  line(cx, top + 16, 34, accent, `${scene.id}  ${scene.name.toUpperCase()}`);
  if (!scene.still) {
    line(cx, top + 44, 26, warn, 'NO IMAGE SUPPLIED');
    line(cx, top + 64, 22, dim, 'pack: designated sacrificial scene');
    continue;
  }
  const flags = [];
  if (info && info.w < 1080) flags.push(`${info.w}px src`);
  if (info && info.contentTop < 0.30) flags.push(`headroom ${(info.contentTop * 100).toFixed(0)}%`);
  line(cx, top + 42, 22, cream, scene.still.replace(/^\d+-/, '').replace(/_20\d+\.jpe?g$/, '').replace(/_/g, ' ').slice(0, 34));
  line(cx, top + 64, 22, flags.length ? warn : dim, flags.length ? flags.join(' · ') : 'ok');
}

const ass = [
  '[Script Info]', 'ScriptType: v4.00+', `PlayResX: ${W}`, `PlayResY: ${H}`,
  'WrapStyle: 2', 'ScaledBorderAndShadow: yes', '',
  '[V4+ Styles]',
  'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding',
  `Style: L,${style.font.body},28,${cream},${cream},&H14111 8&,&H0&,0,0,0,0,100,100,0,0,1,2,0,5,0,0,0,1`.replace('&H14111 8&', '&H181114&'),
  '', '[Events]',
  'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text',
  ...events,
].join('\n');

const assPath = path.join(OUT, '_approval.ass');
fs.writeFileSync(assPath, `${ass}\n`);

const sheet = path.join(OUT, 'approval-sheet.png');
execFileSync(FFMPEG, ['-y', '-hide_banner', '-loglevel', 'error', '-i', grid,
  '-vf', `ass=filename='${assPath}':fontsdir='${path.join(BUILD, style.font.dir)}'`,
  '-frames:v', '1', sheet], { stdio: 'ignore' });

fs.rmSync(tmp, { recursive: true, force: true });
fs.rmSync(grid, { force: true });
console.log(`\n${cells.length} scenes -> ${path.relative(ROOT, sheet)} (${W}x${H})\n`);
export { ts };
