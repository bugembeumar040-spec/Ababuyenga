#!/usr/bin/env node
/**
 * Stand-in assets, for exercising the pipeline before the real ones exist.
 *
 * The stills are flat placeholder plates framed to the pack's Track B rule
 * (subject in the lower two-thirds, top two-fifths empty). The "voiceover" is a
 * tone track whose bursts and pauses follow the real script's word weights, so
 * bin/align.mjs gets something structurally honest to align against.
 *
 * Writes to media/_fixtures/ — never to media/stills or media/vo.
 */
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { loadConfig, ROOT, MEDIA, FFMPEG } from '../lib/paths.mjs';
import { syllables } from '../lib/text.mjs';

const { scenes: spine } = loadConfig();
const { width: W, height: H } = spine.project;
const dir = path.join(MEDIA, '_fixtures');
const stills = path.join(dir, 'stills');
fs.mkdirSync(stills, { recursive: true });

const plates = [
  ['0x11151C', '0x2A1F16'], ['0x0E1219', '0x241C2A'], ['0x141A22', '0x33261C'],
  ['0x0C1016', '0x2E2118'], ['0x101720', '0x1E2A3A'], ['0x12161D', '0x3A2A1C'],
  ['0x0F1319', '0x2B2119'], ['0x11151B', '0x352618'], ['0x0D1117', '0x2C2820'],
  ['0x141821', '0x3A2C1E'], ['0x101821', '0x40301C'],
];

spine.scenes.forEach((scene, i) => {
  const [c0, c1] = plates[i % plates.length];
  const out = path.join(stills, `${scene.still}-${scene.name.replace(/\s+/g, '-')}.png`);
  // Subject block low in frame, deliberately varied per scene so cuts are visible.
  const bw = 420 + (i % 4) * 90;
  const bh = 300 + (i % 3) * 120;
  const bx = Math.round(W / 2 - bw / 2 + (i % 3 - 1) * 70);
  const by = Math.round(H * 0.70 - bh / 2);
  execFileSync(FFMPEG, [
    '-y', '-hide_banner', '-loglevel', 'error',
    '-f', 'lavfi', '-i', `gradients=s=${W}x${H}:c0=${c0}:c1=${c1}:x0=120:y0=${H}:x1=${W}:y1=${Math.round(H * 0.45)}:nb_colors=2:d=1`,
    '-vf', [
      `drawbox=x=${bx}:y=${by}:w=${bw}:h=${bh}:color=0xE8DCC8@0.82:t=fill`,
      `drawbox=x=${bx}:y=${by}:w=${bw}:h=${bh}:color=0xE85F42@0.9:t=6`,
      `drawbox=x=${bx + 40}:y=${by + bh - 40}:w=${bw - 80}:h=14:color=0x1E3A5F@0.9:t=fill`,
      `drawbox=x=0:y=0:w=${W}:h=${Math.round(H * 0.40)}:color=0x000000@0.28:t=fill`,
      'noise=alls=6:allf=t+u',
    ].join(','),
    '-frames:v', '1', out,
  ], { stdio: 'ignore' });
  console.log(`still  ${path.relative(ROOT, out)}`);
});

// Tone "voiceover": one burst per sentence, pause length keyed to the punctuation.
const sentences = spine.scenes.flatMap((s) => s.vo);
const parts = [];
const labels = [];
let n = 0;
sentences.forEach((text, i) => {
  const tokens = text.split(/\s+/).filter(Boolean);
  const weight = tokens.reduce((a, t) => a + syllables(t) + 0.34, 0);
  const dur = Number((weight * 0.155).toFixed(3));
  const freq = 150 + (i % 5) * 22;
  parts.push(`sine=f=${freq}:d=${dur}:r=48000,tremolo=f=7:d=0.7,volume=0.35[a${n}]`);
  labels.push(`[a${n}]`);
  n++;
  const gap = i === 0 ? 0.62 : /[.!?]$/.test(text) ? 0.44 : 0.26;
  parts.push(`anullsrc=r=48000:cl=mono:d=${gap}[a${n}]`);
  labels.push(`[a${n}]`);
  n++;
});

const voOut = path.join(dir, 'creditcard-vo-fixture.mp3');
execFileSync(FFMPEG, [
  '-y', '-hide_banner', '-loglevel', 'error',
  '-filter_complex', `${parts.join(';')};${labels.join('')}concat=n=${labels.length}:v=0:a=1,aformat=channel_layouts=mono[out]`,
  '-map', '[out]', '-c:a', 'libmp3lame', '-b:a', '192k', voOut,
], { stdio: 'ignore' });
console.log(`\nvo     ${path.relative(ROOT, voOut)}`);
console.log(`\nTo dry-run the pipeline against these:
  node bin/align.mjs   --vo media/_fixtures/creditcard-vo-fixture.mp3
or point scenes.json project.voiceover / project.stillsDir at media/_fixtures.\n`);
