#!/usr/bin/env node
/**
 * Re-derive the cut from the recorded voiceover.
 *
 * The prompt pack's IN/OUT points are ~150wpm estimates written before the VO
 * existed. This reads the actual audio, forced-aligns the known script to it,
 * and writes out/timeline.json — the only timing source the renderer trusts.
 */
import fs from 'node:fs';
import path from 'node:path';
import { loadConfig, ensureOut, ROOT, OUT } from '../lib/paths.mjs';
import { probeDuration, speechSegments, alignScript, sceneTimings } from '../lib/align.mjs';
import { splitBursts, holdBursts, applyTakeover } from '../lib/bursts.mjs';

const { scenes: spine, style } = loadConfig();
const project = spine.project;
const voPath = path.join(ROOT, project.voiceover);

if (!fs.existsSync(voPath)) {
  console.error(`\nVoiceover not found: ${voPath}`);
  console.error('Drop the recorded VO there (or point project.voiceover at it) and re-run.\n');
  process.exit(2);
}

const duration = probeDuration(voPath);
const segments = speechSegments(voPath, duration);
const { sentences } = alignScript(spine.scenes, segments, duration);
const timings = sceneTimings(spine.scenes, sentences, duration);

// Whole frames, and the last scene absorbs the rounding so video length == audio length.
const fps = project.fps;
const totalFrames = Math.round(duration * fps);
let acc = 0;
timings.forEach((t, i) => {
  t.startFrame = Math.round(t.start * fps);
  if (i > 0) timings[i - 1].frames = t.startFrame - timings[i - 1].startFrame;
});
timings[timings.length - 1].frames = totalFrames - timings[timings.length - 1].startFrame;
timings.forEach((t) => {
  t.start = t.startFrame / fps;
  t.length = t.frames / fps;
  t.end = t.start + t.length;
  acc += t.frames;
});

function resolveCardTime(card, scene, sceneIndex, timing) {
  let start;
  if (typeof card.at === 'number') {
    start = timing.start + card.at;
  } else {
    const m = /^vo:(\d+):(\d+)$/.exec(String(card.at));
    if (!m) throw new Error(`scene ${scene.id}: bad card.at "${card.at}"`);
    const [, li, wi] = m.map(Number);
    const sentence = sentences.filter((s) => s.sceneIndex === sceneIndex)[li];
    if (!sentence) throw new Error(`scene ${scene.id}: card.at references missing VO line ${li}`);
    const word = sentence.words[wi];
    if (!word) throw new Error(`scene ${scene.id}: card.at references missing word ${wi} in "${sentence.text}"`);
    start = word.start;
  }
  start = Math.max(timing.start + 0.05, start);
  const end = Math.min(timing.end - 0.08, start + card.hold);
  return { start, end, clamped: end < start + card.hold - 0.01 };
}

const out = {
  generatedAt: new Date().toISOString(),
  source: { voiceover: project.voiceover, duration, fps, totalFrames },
  speech: {
    segments: segments.length,
    speechDuration: Number(segments.reduce((a, s) => a + (s.end - s.start), 0).toFixed(3)),
    silenceDuration: Number((duration - segments.reduce((a, s) => a + (s.end - s.start), 0)).toFixed(3)),
  },
  scenes: spine.scenes.map((scene, i) => {
    const t = timings[i];
    const mine = sentences.filter((s) => s.sceneIndex === i);
    const declared = scene.cards || (scene.card ? [scene.card] : []);
    const cards = declared.map((c) => ({ ...c, ...resolveCardTime(c, scene, i, t) }));

    let bursts = holdBursts(mine.flatMap((s) => splitBursts(s, style.caption)), t, style.caption);
    for (const card of cards) {
      if (!card.takeover) continue;
      const applied = applyTakeover(bursts, card);
      bursts = applied.bursts;
      Object.assign(card, applied.card);
    }

    return {
      id: scene.id,
      name: scene.name,
      still: scene.still,
      start: Number(t.start.toFixed(4)),
      end: Number(t.end.toFixed(4)),
      length: Number(t.length.toFixed(4)),
      frames: t.frames,
      startFrame: t.startFrame,
      targetLength: Number((scene.targetOut - scene.targetIn).toFixed(2)),
      drift: Number((t.length - (scene.targetOut - scene.targetIn)).toFixed(3)),
      move: scene.move,
      captionY: scene.captionY,
      continuesFrom: scene.continuesFrom || null,
      accentWords: scene.accentWords || [],
      cards,
      bursts: bursts.map((b) => ({
        text: b.text,
        start: Number(b.start.toFixed(3)),
        end: Number(b.end.toFixed(3)),
      })),
      sentences: mine.map((s) => ({
        text: s.text,
        start: Number(s.start.toFixed(3)),
        end: Number(s.end.toFixed(3)),
        words: s.words.map((w) => ({ text: w.text, start: Number(w.start.toFixed(3)), end: Number(w.end.toFixed(3)) })),
      })),
    };
  }),
};

ensureOut();
fs.writeFileSync(path.join(OUT, 'timeline.json'), `${JSON.stringify(out, null, 2)}\n`);

const pad = (s, n) => String(s).padEnd(n);
console.log(`\nVO ${project.voiceover}  ${duration.toFixed(2)}s  (${out.speech.segments} speech segments, ${out.speech.silenceDuration.toFixed(2)}s silence)`);
console.log(`Pack target ${project.targetDuration}s  ->  actual ${duration.toFixed(2)}s  (${(duration - project.targetDuration >= 0 ? '+' : '')}${(duration - project.targetDuration).toFixed(2)}s)\n`);
console.log(` #  ${pad('SCENE', 15)} ${pad('IN', 8)} ${pad('OUT', 8)} ${pad('LEN', 7)} ${pad('TARGET', 7)} DRIFT`);
for (const s of out.scenes) {
  const d = s.drift;
  console.log(` ${s.id} ${pad(s.name, 15)} ${pad(s.start.toFixed(2), 8)} ${pad(s.end.toFixed(2), 8)} ${pad(s.length.toFixed(2), 7)} ${pad(s.targetLength.toFixed(2), 7)} ${d >= 0 ? '+' : ''}${d.toFixed(2)}`);
}
console.log(`\nframes ${acc} / ${totalFrames}  ->  out/timeline.json\n`);
