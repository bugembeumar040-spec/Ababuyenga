#!/usr/bin/env node
/**
 * Assemble the short: stills + moves + burnt captions/cards + voiceover -> MP4.
 *
 * Usage:
 *   node bin/render.mjs                 full quality
 *   node bin/render.mjs --preview       fast, for checking timing
 */
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync, spawnSync } from 'node:child_process';
import { loadConfig, ensureOut, ROOT, OUT, BUILD, FFMPEG } from '../lib/paths.mjs';
import { resolveStills, writeStillsMap, probeImage, rel } from '../lib/stills.mjs';

const preview = process.argv.includes('--preview');
const { scenes: spine, style } = loadConfig();
const { width: W, height: H, fps } = spine.project;

const timelinePath = path.join(OUT, 'timeline.json');
const assPath = path.join(OUT, 'captions.ass');
for (const [p, cmd] of [[timelinePath, 'bin/align.mjs'], [assPath, 'bin/captions.mjs']]) {
  if (!fs.existsSync(p)) {
    console.error(`\n${rel(p)} missing — run: node ${cmd}\n`);
    process.exit(2);
  }
}
const timeline = JSON.parse(fs.readFileSync(timelinePath, 'utf8'));
const voPath = path.join(ROOT, spine.project.voiceover);
const stillsDir = path.join(ROOT, spine.project.stillsDir);

/**
 * Consecutive scenes are one shot when a scene declares continuesFrom — the
 * artwork holds across the beat instead of cutting. Scene 07 uses this: the
 * pack calls it sacrificial, so its line rides on 06's frame.
 */
const shots = [];
for (const scene of timeline.scenes) {
  if (scene.continuesFrom && shots.length) {
    const last = shots[shots.length - 1];
    last.frames += scene.frames;
    last.scenes.push(scene.id);
  } else {
    shots.push({ id: scene.id, still: scene.still, frames: scene.frames, move: scene.move, scenes: [scene.id] });
  }
}

const { assignments, files } = resolveStills(shots, stillsDir, spine.project.slug);
const missing = assignments.filter((a) => !a.file);
if (missing.length) {
  console.error(`\nNo image for scene(s) ${missing.map((m) => m.id).join(', ')}.`);
  console.error(`Put images in ${rel(stillsDir)}/ — ${files.length} found.\n`);
  process.exit(2);
}
writeStillsMap(assignments, stillsDir, spine.project.slug);

console.log(`\nSHOTS  ${shots.length} shots across ${timeline.scenes.length} scenes`);
for (const [i, a] of assignments.entries()) {
  const dims = probeImage(a.file);
  const shot = shots[i];
  const span = shot.scenes.length > 1 ? ` (holds ${shot.scenes.join('+')})` : '';
  console.log(`  ${a.id}${span.padEnd(16)} ${path.basename(a.file).slice(0, 40).padEnd(41)} ${dims.width}x${dims.height}  ${(shot.frames / fps).toFixed(2)}s  [${a.how}]`);
}

const S = preview ? 1 : style.render.supersample;
const IW = W * S;
const IH = H * S;

/** Ease-out cubic on the output frame counter, as an ffmpeg expression. */
const ease = (frames) => (frames > 1 ? `(1-pow(1-on/${frames - 1},3))` : '1');

function sceneChain(scene, inputIndex) {
  const n = scene.frames;
  const e = ease(n);
  const push = scene.move?.push ?? 0;
  const dxFrac = (scene.move?.driftX ?? 0) / W;
  const dyFrac = (scene.move?.driftY ?? 0) / H;

  let z;
  if (push > 0) z = `1+${push.toFixed(4)}*${e}`;
  else if (push < 0) z = `${(1 - push).toFixed(4)}-${(-push).toFixed(4)}*${e}`;
  else z = '1';

  const zx = `min(max(${z},1),4)`;
  const x = `iw/2-(iw/zoom/2)${dxFrac ? `+${dxFrac.toFixed(5)}*(iw/zoom)*${e}` : ''}`;
  const y = `ih/2-(ih/zoom/2)${dyFrac ? `+${dyFrac.toFixed(5)}*(ih/zoom)*${e}` : ''}`;

  return [
    `[${inputIndex}:v]`,
    `scale=${IW}:${IH}:force_original_aspect_ratio=increase:flags=lanczos,`,
    `crop=${IW}:${IH},setsar=1,format=rgb24,`,
    `zoompan=z='${zx}':x='${x}':y='${y}':d=${n}:s=${W}x${H}:fps=${fps},`,
    `format=yuv420p,setsar=1[v${scene.id}]`,
  ].join('');
}

/**
 * Two-pass loudnorm: measure first, then apply in linear mode. Linear mode is
 * the only one that leaves the VO's timing untouched, which matters because the
 * captions are aligned to sample positions in this exact file.
 */
function measureLoudness(file, target) {
  const res = spawnSync(FFMPEG, [
    '-hide_banner', '-nostats', '-i', file,
    '-af', `loudnorm=I=${target}:TP=${style.render.truePeak}:LRA=11:print_format=json`,
    '-f', 'null', '-',
  ], { encoding: 'utf8' });
  const text = `${res.stderr || ''}`;
  const start = text.lastIndexOf('{');
  const end = text.lastIndexOf('}');
  if (start === -1 || end === -1) return null;
  try { return JSON.parse(text.slice(start, end + 1)); } catch { return null; }
}

const target = style.render.loudnessTarget;
const measured = measureLoudness(voPath, target);
if (measured) {
  console.log(`\nLOUDNESS  measured ${measured.input_i} LUFS, peak ${measured.input_tp} dBTP  ->  target ${target} LUFS`);
} else {
  console.log('\nLOUDNESS  measurement failed — falling back to single-pass loudnorm');
}

const audioFilter = measured
  ? `loudnorm=I=${target}:TP=${style.render.truePeak}:LRA=11:measured_I=${measured.input_i}:measured_TP=${measured.input_tp}:measured_LRA=${measured.input_lra}:measured_thresh=${measured.input_thresh}:offset=${measured.target_offset}:linear=true,aresample=48000:first_pts=0`
  : `loudnorm=I=${target}:TP=${style.render.truePeak}:LRA=11,aresample=48000:first_pts=0`;

const fontsDir = path.join(BUILD, style.font.dir);
const escapeFilterPath = (p) => p.replace(/\\/g, '/').replace(/:/g, '\\\\:').replace(/'/g, "\\\\'");

const audioIndex = shots.length;
const chains = shots.map((s, i) => sceneChain(s, i));
const concatIn = shots.map((s) => `[v${s.id}]`).join('');
const graph = [
  ...chains,
  `${concatIn}concat=n=${shots.length}:v=1:a=0[vcat]`,
  `[vcat]ass=filename='${escapeFilterPath(assPath)}':fontsdir='${escapeFilterPath(fontsDir)}'[vout]`,
  `[${audioIndex}:a]${audioFilter}[aout]`,
].join(';\n');

ensureOut();
const graphPath = path.join(OUT, 'filtergraph.txt');
fs.writeFileSync(graphPath, `${graph}\n`);

const outFile = path.join(OUT, preview ? `${spine.project.slug}-preview.mp4` : `${spine.project.slug}.mp4`);
const args = [
  '-y', '-hide_banner',
  ...assignments.flatMap((a) => ['-i', a.file]),
  '-i', voPath,
  '-filter_complex_script', graphPath,
  '-map', '[vout]', '-map', '[aout]',
  '-c:v', 'libx264',
  '-preset', preview ? 'veryfast' : style.render.preset,
  '-crf', String(preview ? 28 : style.render.crf),
  '-profile:v', 'high', '-level', '4.1',
  '-pix_fmt', 'yuv420p',
  '-r', String(fps),
  '-g', String(fps * 2),
  '-c:a', 'aac', '-b:a', style.render.audioBitrate, '-ar', '48000', '-ac', '2',
  '-movflags', '+faststart',
  '-t', timeline.source.duration.toFixed(3),
  outFile,
];

console.log(`\nRENDER  ${shots.length} shots, ${timeline.source.totalFrames} frames @ ${fps}fps, supersample ${S}x  ->  ${rel(outFile)}`);
const t0 = Date.now();
const run = spawnSync(FFMPEG, args, { stdio: ['ignore', 'ignore', 'pipe'], encoding: 'utf8' });
if (run.status !== 0) {
  console.error(run.stderr.split('\n').slice(-40).join('\n'));
  process.exit(1);
}
console.log(`done in ${((Date.now() - t0) / 1000).toFixed(1)}s\n`);

execFileSync(FFMPEG, ['-hide_banner', '-y', '-i', outFile, '-vf', `select='not(mod(n\\,${Math.max(1, Math.floor(timeline.source.totalFrames / 12))}))',scale=270:480,tile=4x3`, '-frames:v', '1', path.join(OUT, 'contact-sheet.png')], { stdio: 'ignore' });
console.log(`contact sheet -> ${rel(path.join(OUT, 'contact-sheet.png'))}\n`);
