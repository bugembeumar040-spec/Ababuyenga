#!/usr/bin/env node
/**
 * Pre-delivery audit. Everything that can be checked mechanically, is.
 *
 * Exits non-zero on any FAIL so the build can never be pushed silently broken.
 * WARNs are judgement calls that a human should look at but that do not block.
 */
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync, spawnSync } from 'node:child_process';
import { loadConfig, ROOT, OUT, BUILD, FFMPEG, FFPROBE } from '../lib/paths.mjs';
import { loadFont, measure } from '../lib/text.mjs';
import { probeImage, listStills, rel } from '../lib/stills.mjs';

const { scenes: spine, style } = loadConfig();
const { width: W, height: H, fps } = spine.project;

const results = [];
const check = (section, name, ok, detail = '') => {
  results.push({ section, name, status: ok === true ? 'PASS' : ok === 'warn' ? 'WARN' : 'FAIL', detail });
};

const exists = (p) => fs.existsSync(p);
const readJson = (p) => JSON.parse(fs.readFileSync(p, 'utf8'));

// ---------------------------------------------------------------- 1. sources
const voPath = path.join(ROOT, spine.project.voiceover);
const stillsDir = path.join(ROOT, spine.project.stillsDir);
let voInfo = null;

if (!exists(voPath)) {
  check('sources', 'voiceover present', false, `missing ${rel(voPath)}`);
} else {
  const probe = JSON.parse(execFileSync(FFPROBE, [
    '-v', 'error', '-show_streams', '-show_format', '-select_streams', 'a:0', '-of', 'json', voPath,
  ]).toString());
  const a = probe.streams[0];
  voInfo = {
    duration: Number(probe.format.duration),
    sampleRate: Number(a.sample_rate),
    channels: a.channels,
    codec: a.codec_name,
  };
  check('sources', 'voiceover present', true, `${rel(voPath)} — ${voInfo.duration.toFixed(2)}s ${voInfo.codec} ${voInfo.sampleRate}Hz ${voInfo.channels}ch`);
  check('sources', 'voiceover length in slate range (30–60s)',
    voInfo.duration >= 30 && voInfo.duration <= 60 ? true : 'warn',
    `${voInfo.duration.toFixed(2)}s (pack slate rule: 30–60s)`);
  check('sources', 'voiceover sample rate ≥ 44.1kHz', voInfo.sampleRate >= 44100 ? true : 'warn', `${voInfo.sampleRate}Hz`);

  const vd = spawnSync(FFMPEG, ['-hide_banner', '-nostats', '-i', voPath, '-af', 'volumedetect', '-f', 'null', '-'], { encoding: 'utf8' }).stderr;
  const peak = Number(/max_volume:\s*(-?[\d.]+)/.exec(vd)?.[1] ?? NaN);
  check('sources', 'voiceover not clipping', Number.isFinite(peak) && peak <= -0.1 ? true : 'warn', `peak ${peak} dBFS`);
}

const stillFiles = listStills(stillsDir);
check('sources', 'stills present', stillFiles.length > 0, `${stillFiles.length} image(s) in ${rel(stillsDir)}/`);
check('sources', 'one still per scene', stillFiles.length >= spine.scenes.length ? true : 'warn',
  `${stillFiles.length} images for ${spine.scenes.length} scenes${stillFiles.length < spine.scenes.length ? ' — some scenes reuse an image' : ''}`);

for (const f of stillFiles) {
  const p = path.join(stillsDir, f);
  const { width, height } = probeImage(p);
  const ar = width / height;
  const target = W / H;
  const okRes = width >= W && height >= H;
  check('sources', `still ${f} resolution`, okRes ? true : 'warn', `${width}x${height}${okRes ? '' : ` — below ${W}x${H}, will be upscaled`}`);
  const cropLoss = Math.abs(ar - target) / target;
  check('sources', `still ${f} aspect`, cropLoss < 0.02 ? true : 'warn',
    `${ar.toFixed(3)} vs 9:16 ${target.toFixed(3)}${cropLoss >= 0.02 ? ` — ${(cropLoss * 100).toFixed(0)}% will be cropped to fill` : ''}`);
}

// -------------------------------------------------- 2. spine vs the prompt pack
const packPath = path.join(ROOT, spine.project.pack);
if (!exists(packPath)) {
  check('spine', 'prompt pack present', false, `missing ${rel(packPath)}`);
} else {
  const pack = fs.readFileSync(packPath, 'utf8');

  const mapRows = [...pack.matchAll(/^\s*(\d{2}[A-C]?)\s*\|\s*(\d):(\d{2}\.\d)\s*\|\s*(\d):(\d{2}\.\d)\s*\|\s*([\d.]+)s\s*\|\s*([^|]+?)\s*\|/gm)]
    .map((m) => ({
      id: m[1],
      inSec: Number(m[2]) * 60 + Number(m[3]),
      outSec: Number(m[4]) * 60 + Number(m[5]),
      len: Number(m[6]),
      name: m[7].trim(),
    }));
  check('spine', 'scene map parsed from pack', mapRows.length === spine.scenes.length,
    `${mapRows.length} rows in pack, ${spine.scenes.length} scenes in scenes.json`);

  for (const row of mapRows) {
    const scene = spine.scenes.find((s) => s.id === row.id);
    if (!scene) { check('spine', `scene ${row.id} exists`, false, 'in pack but not in scenes.json'); continue; }
    const same = scene.name === row.name && Math.abs(scene.targetIn - row.inSec) < 0.051 && Math.abs(scene.targetOut - row.outSec) < 0.051;
    check('spine', `scene ${row.id} matches pack`, same,
      same ? `${row.name} ${row.inSec}–${row.outSec}` : `pack: "${row.name}" ${row.inSec}–${row.outSec} / spine: "${scene.name}" ${scene.targetIn}–${scene.targetOut}`);
  }

  // The pack's voiceover block is the script of record. Two formats are in use
  // across the packs: a bare block after a VOICEOVER heading, and a VO SCRIPT
  // section whose lines are tagged [01]..[16B] per scene.
  const tagged = [...pack.matchAll(/^\s*\[(\d{2}[A-C]?)\]\s*([\s\S]*?)(?=^\s*\[\d{2}[A-C]?\]|^WORD COUNT|^PACING NOTE)/gm)];
  const normalise = (t) => t.replace(/\s+/g, ' ').replace(/[""]/g, '"').trim();

  if (tagged.length) {
    check('spine', 'voiceover script found in pack', true, `${tagged.length} tagged blocks`);
    let mismatched = [];
    for (const [, id, text] of tagged) {
      const scene = spine.scenes.find((sc) => sc.id === id);
      if (!scene) { mismatched.push(`${id} missing from spine`); continue; }
      if (normalise(text) !== normalise(scene.vo.join(' '))) mismatched.push(id);
    }
    check('spine', 'voiceover script identical to pack', mismatched.length === 0,
      mismatched.length ? `scenes drifted: ${mismatched.join(', ')}`
        : `${tagged.length} scenes, ${spine.scenes.flatMap((sc) => sc.vo).join(' ').split(/\s+/).length} words`);
  } else {
    const voBlock = /VOICEOVER[\s\S]*?={10,}\n([\s\S]*?)\nPACING NOTE/.exec(pack);
    if (!voBlock) {
      check('spine', 'voiceover script found in pack', 'warn', 'could not locate the voiceover block');
    } else {
      const rawLines = voBlock[1].split('\n').map((l) => l.trim()).filter(Boolean);
      const scriptStart = rawLines.findIndex((l) => /^\[[a-z]+\]/.test(l));
      const packLines = (scriptStart === -1 ? rawLines : rawLines.slice(scriptStart))
        .map((l) => l.replace(/\[[a-z]+\]/g, '').trim())
        .filter(Boolean);
      const packJoined = normalise(packLines.join(' '));
      const spineJoined = normalise(spine.scenes.flatMap((sc) => sc.vo).join(' '));
      check('spine', 'voiceover script identical to pack', packJoined === spineJoined,
        packJoined === spineJoined ? `${packLines.length} lines` : 'scenes.json vo[] has drifted from the pack');
    }
  }

  // Continuity rules the pack declares as hard constraints.
  const spokenText = spine.scenes.flatMap((sc) => sc.vo).join(' ').toLowerCase();

  if (/BURNED #1/.test(pack)) {
    const burnedFee = /(interchange|merchant fee|charges the shop|pass(ed|es)? (it )?on to the price|price tag)/.test(spokenText);
    check('spine', 'BURNED #1 merchant-fee argument absent', !burnedFee,
      burnedFee ? 'voiceover reuses the Klarna pass-through spine' : 'no interchange / merchant-fee argument in the VO');
    const minPayMentions = (spokenText.match(/minimum payment/g) || []).length;
    const explains = /(compound|snowball|how long it takes to pay|interest accrues|only covers the interest)/.test(spokenText);
    check('spine', 'BURNED #2 minimum-payment mechanism not re-explained', minPayMentions <= 1 && !explains,
      `"minimum payment" spoken ${minPayMentions}x (pack allows exactly 1, unexplained)`);
  }

  if (/BURNED TERRITORY/.test(pack)) {
    // The pack lists every subject already spent across the channel.
    const burned = ['banks earn the spread', 'money from thin air', 'sound money', 'savings account',
      'credit card', 'minimum payment', 'mortgage', 'bond', 'murabaha', 'musharaka', 'sukuk',
      'ijara', 'takaful', 'gharar', 'paper gold', 'bank run', 'born into debt', 'klarna', 'pension'];
    const hits = burned.filter((t) => spokenText.includes(t));
    check('spine', 'no burned subject carries the script', hits.length === 0,
      hits.length ? `spoken: ${hits.join(', ')}` : `checked ${burned.length} spent subjects, none present`);
  }

  check('spine', 'no ruling issued in the VO', !/\b(haram|halal|forbidden|permissible|impermissible)\b/.test(spokenText),
    'pack: no ruling is issued in your own voice anywhere');

  const ceiling = 90;
  if (voInfo) {
    check('spine', `runtime within the pack's ${ceiling}s ceiling`, voInfo.duration <= ceiling ? true : 'warn',
      voInfo.duration <= ceiling ? `${voInfo.duration.toFixed(1)}s`
        : `${voInfo.duration.toFixed(1)}s — over by ${(voInfo.duration - ceiling).toFixed(1)}s; shipping long was an explicit call`);
  }
}

// -------------------------------------------------------------- 3. timeline
const timelinePath = path.join(OUT, 'timeline.json');
let timeline = null;
if (!exists(timelinePath)) {
  check('timeline', 'timeline built', false, 'run: node bin/align.mjs');
} else {
  timeline = readJson(timelinePath);
  const scenes = timeline.scenes;

  check('timeline', 'starts at zero', Math.abs(scenes[0].start) < 1e-6, `${scenes[0].start}`);
  const last = scenes[scenes.length - 1];
  check('timeline', 'ends with the voiceover', Math.abs(last.end - timeline.source.duration) < 1 / fps + 1e-6,
    `timeline ends ${last.end.toFixed(3)}s, VO ends ${timeline.source.duration.toFixed(3)}s`);

  let contiguous = true;
  for (let i = 1; i < scenes.length; i++) {
    if (Math.abs(scenes[i].start - scenes[i - 1].end) > 1e-6) contiguous = false;
  }
  check('timeline', 'no gaps or overlaps between scenes', contiguous);
  check('timeline', 'frame counts sum to the whole', scenes.reduce((a, s) => a + s.frames, 0) === timeline.source.totalFrames,
    `${scenes.reduce((a, s) => a + s.frames, 0)} / ${timeline.source.totalFrames} frames`);

  const short = scenes.filter((s) => s.length < 1.6);
  check('timeline', 'no scene shorter than 1.6s', short.length === 0,
    short.length ? short.map((s) => `${s.id} ${s.length.toFixed(2)}s`).join(', ') : 'shortest ' + Math.min(...scenes.map((s) => s.length)).toFixed(2) + 's');

  const bigDrift = scenes.filter((s) => Math.abs(s.drift) > 2.0);
  check('timeline', 'scene lengths within 2s of the pack estimate', bigDrift.length === 0 ? true : 'warn',
    bigDrift.length ? bigDrift.map((s) => `${s.id} ${s.drift > 0 ? '+' : ''}${s.drift.toFixed(1)}s`).join(', ') : 'all within 2s');

  const protectedIds = ['15A', '15B', '15C', '16B', '01', '02', '05', '06'];
  const present = protectedIds.filter((id) => scenes.some((s) => s.id === id));
  check('timeline', 'every protected scene survives the cut', present.length === protectedIds.length,
    `${present.length}/${protectedIds.length} present (pack: never cut 01-02, 05-06, 15A-15C, 16B)`);
  const fix = scenes.filter((s) => String(s.id).startsWith('15')).reduce((a, s) => a + s.length, 0);
  check('timeline', 'the three-step fix has room to land', fix >= 12 ? true : 'warn',
    `${fix.toFixed(1)}s across 15A-15C`);

  for (const s of scenes) {
    for (const card of s.cards || []) {
      const inside = card.start >= s.start - 1e-6 && card.end <= s.end + 1e-6;
      check('timeline', `scene ${s.id} ${card.kind} card sits inside its scene`, inside,
        `${card.start.toFixed(2)}-${card.end.toFixed(2)} within ${s.start.toFixed(2)}-${s.end.toFixed(2)}`);
      const held = card.end - card.start;
      check('timeline', `scene ${s.id} ${card.kind} card holds long enough to read`, held >= 1.2 ? true : 'warn',
        `${held.toFixed(2)}s${card.clamped ? ' (clamped by the cut)' : ''}`);
    }
  }

  // Every spoken word must reach the screen.
  const lost = [];
  for (const s of scenes) {
    const spoken = s.sentences.flatMap((x) => x.words.map((w) => w.text.toUpperCase().replace(/[^A-Z0-9%'.-]/g, '')));
    const shown = s.bursts.map((b) => b.text).join(' ').replace(/[^A-Z0-9%'. -]/g, '').split(/\s+/);
    const takeover = (s.cards || []).flatMap((c) => c.replacedBursts || []).join(' ').split(/\s+/);
    for (const w of spoken) {
      if (w && !shown.includes(w) && !takeover.includes(w)) lost.push(`${s.id}:${w}`);
    }
  }
  check('timeline', 'every spoken word appears in a caption', lost.length === 0,
    lost.length ? `missing: ${lost.slice(0, 8).join(', ')}` : 'full coverage');
}

// ------------------------------------------------------------ 4. typography
const layoutPath = path.join(OUT, 'layout.json');
const assPath = path.join(OUT, 'captions.ass');
if (!exists(layoutPath) || !exists(assPath)) {
  check('captions', 'caption track built', false, 'run: node bin/captions.mjs');
} else {
  const { boxes } = readJson(layoutPath);
  const captions = boxes.filter((b) => b.kind === 'caption');
  const cards = boxes.filter((b) => b.kind.startsWith('card'));
  check('captions', 'caption track built', true, `${captions.length} caption lines, ${cards.length} cards`);

  const margin = style.caption.safeMarginX;
  const overWide = boxes.filter((b) => b.width > W - 2 * margin + 1);
  check('captions', 'everything inside the horizontal safe area', overWide.length === 0,
    overWide.length ? overWide.map((b) => `${b.scene} "${b.text}" ${Math.round(b.width)}px > ${W - 2 * margin}px`).join('; ') : `all ≤ ${W - 2 * margin}px`);

  const offScreen = boxes.filter((b) => b.top < 40 || b.bottom > H - 40);
  check('captions', 'everything inside the vertical safe area', offScreen.length === 0,
    offScreen.length ? offScreen.map((b) => `${b.scene} "${b.text}" ${Math.round(b.top)}–${Math.round(b.bottom)}`).join('; ') : 'all within 40px of the edges');

  // A caption and a card must never share screen space at the same instant.
  const collisions = [];
  for (const c of captions) {
    for (const k of cards) {
      const overlapTime = Math.min(c.end, k.end) - Math.max(c.start, k.start);
      const overlapY = Math.min(c.bottom, k.bottom) - Math.max(c.top, k.top);
      if (overlapTime > 0.04 && overlapY > 0) collisions.push(`${c.scene}: "${c.text}" over "${k.text}"`);
    }
  }
  check('captions', 'no caption/card collision', collisions.length === 0, collisions.join('; ') || 'clear');

  const longLines = captions.filter((b) => b.text.length > style.caption.maxCharsPerLine);
  check('captions', `≤ ${style.caption.maxCharsPerLine} characters per caption line`, longLines.length === 0 ? true : 'warn',
    longLines.length ? longLines.map((b) => `"${b.text}" (${b.text.length})`).join('; ') : `longest ${Math.max(...captions.map((b) => b.text.length))}`);

  const flashes = captions.filter((b) => b.end - b.start < style.caption.minBurst - 0.02);
  check('captions', 'no caption flashes below the readable floor', flashes.length === 0 ? true : 'warn',
    flashes.length ? flashes.map((b) => `"${b.text}" ${(b.end - b.start).toFixed(2)}s`).join('; ') : `floor ${style.caption.minBurst}s`);

  const overlong = captions.filter((b) => b.end - b.start > style.caption.maxBurst + 0.05);
  check('captions', 'no caption overstays the burst ceiling', overlong.length === 0 ? true : 'warn',
    overlong.length ? overlong.map((b) => `"${b.text}" ${(b.end - b.start).toFixed(2)}s`).join('; ') : `ceiling ${style.caption.maxBurst}s`);

  if (timeline) {
    const outside = boxes.filter((b) => {
      const scene = timeline.scenes.find((s) => s.id === b.scene);
      return scene && (b.start < scene.start - 1e-3 || b.end > scene.end + 1e-3);
    });
    check('captions', 'no text crosses a cut', outside.length === 0,
      outside.length ? outside.map((b) => `${b.scene} "${b.text}"`).join('; ') : 'every line clears its own cut');
  }

  // Glyph coverage — a missing glyph renders as a blank box and is easy to miss.
  const display = loadFont(style, 'display');
  const body = loadFont(style, 'body');
  const missing = new Set();
  for (const b of boxes) {
    const font = b.kind === 'card:pill' ? body : display;
    for (const ch of b.text) {
      if (ch === ' ') continue;
      if (font.charToGlyph(ch).index === 0) missing.add(`${ch} (${b.kind})`);
      if (display.charToGlyph(ch).index === 0) missing.add(`${ch} (display font)`);
    }
  }
  check('captions', 'every character has a glyph', missing.size === 0,
    missing.size ? [...missing].join(', ') : 'full coverage in Anton + Inter');

  const assText = fs.readFileSync(assPath, 'utf8');
  check('captions', 'ASS parses as a single well-formed script',
    assText.includes('[Events]') && assText.includes('PlayResX: ' + W) && !/\n\n\n/.test(assText),
    `${assText.split('\n').filter((l) => l.startsWith('Dialogue:')).length} dialogue events`);
}

// -------------------------------------------------------------- 5. the file
const outFile = path.join(OUT, `${spine.project.slug}.mp4`);
if (!exists(outFile)) {
  check('output', 'rendered file present', 'warn', `${rel(outFile)} not built yet — run: node bin/render.mjs`);
} else {
  const probe = JSON.parse(execFileSync(FFPROBE, ['-v', 'error', '-show_streams', '-show_format', '-of', 'json', outFile]).toString());
  const v = probe.streams.find((s) => s.codec_type === 'video');
  const a = probe.streams.find((s) => s.codec_type === 'audio');
  const dur = Number(probe.format.duration);

  check('output', 'resolution is 1080x1920', v.width === W && v.height === H, `${v.width}x${v.height}`);
  check('output', 'frame rate', eval(v.r_frame_rate) === fps, v.r_frame_rate);
  check('output', 'pixel format is yuv420p', v.pix_fmt === 'yuv420p', v.pix_fmt);
  check('output', 'has an audio track', !!a, a ? `${a.codec_name} ${a.sample_rate}Hz ${a.channels}ch` : 'none');
  check('output', 'video length matches the voiceover', voInfo ? Math.abs(dur - voInfo.duration) < 0.12 : false,
    voInfo ? `video ${dur.toFixed(2)}s vs VO ${voInfo.duration.toFixed(2)}s` : 'no VO to compare');
  // faststart means the moov atom precedes mdat; ffprobe cannot report this, so
  // read the atom order off the front of the file directly.
  const head = Buffer.alloc(Math.min(4 * 1024 * 1024, fs.statSync(outFile).size));
  const fd = fs.openSync(outFile, 'r');
  fs.readSync(fd, head, 0, head.length, 0);
  fs.closeSync(fd);
  const moov = head.indexOf('moov');
  const mdat = head.indexOf('mdat');
  check('output', 'faststart enabled for web playback',
    moov !== -1 && (mdat === -1 || moov < mdat) ? true : 'warn',
    moov === -1 ? 'moov atom not in the first 4MB' : `moov at ${moov}, mdat at ${mdat}`);

  const eb = spawnSync(FFMPEG, ['-hide_banner', '-nostats', '-i', outFile, '-af', 'ebur128=framelog=quiet:peak=true', '-f', 'null', '-'], { encoding: 'utf8' }).stderr;
  const I = Number(/I:\s*(-?[\d.]+)\s*LUFS/.exec(eb)?.[1] ?? NaN);
  const TP = Number(/Peak:\s*(-?[\d.]+)\s*dBFS/.exec(eb)?.[1] ?? NaN);
  check('output', 'integrated loudness near -14 LUFS', Number.isFinite(I) && Math.abs(I - style.render.loudnessTarget) <= 1.5,
    `${I} LUFS (target ${style.render.loudnessTarget})`);
  check('output', 'true peak below -1.0 dBTP', Number.isFinite(TP) && TP <= -1.0, `${TP} dBFS`);

  // No scene may render as a black or frozen-black frame.
  const bd = spawnSync(FFMPEG, ['-hide_banner', '-nostats', '-i', outFile, '-vf', 'blackdetect=d=0.3:pic_th=0.98', '-f', 'null', '-'], { encoding: 'utf8' }).stderr;
  const blacks = [...bd.matchAll(/black_start:([\d.]+) black_end:([\d.]+)/g)];
  check('output', 'no black holes in the cut', blacks.length === 0,
    blacks.length ? blacks.map((m) => `${m[1]}–${m[2]}s`).join(', ') : 'none');

  const size = fs.statSync(outFile).size;
  check('output', 'file size sane for a Short', size > 2e6 && size < 1.2e8, `${(size / 1e6).toFixed(1)} MB`);
}

// ---------------------------------------------------------------- 6. report
const order = ['sources', 'spine', 'timeline', 'captions', 'output'];
const counts = { PASS: 0, WARN: 0, FAIL: 0 };
console.log('');
for (const section of order) {
  const rows = results.filter((r) => r.section === section);
  if (!rows.length) continue;
  console.log(`── ${section.toUpperCase()} ${'─'.repeat(Math.max(0, 62 - section.length))}`);
  for (const r of rows) {
    counts[r.status]++;
    const mark = r.status === 'PASS' ? '  ok ' : r.status === 'WARN' ? ' warn' : ' FAIL';
    console.log(`${mark}  ${r.name}${r.detail ? `\n        ${r.detail}` : ''}`);
  }
  console.log('');
}
console.log(`${counts.PASS} passed · ${counts.WARN} warnings · ${counts.FAIL} failures\n`);

fs.mkdirSync(OUT, { recursive: true });
fs.writeFileSync(path.join(OUT, 'audit.json'), `${JSON.stringify({ generatedAt: new Date().toISOString(), counts, results }, null, 2)}\n`);

process.exit(counts.FAIL > 0 ? 1 : 0);
