import { execFileSync, spawnSync } from 'node:child_process';
import { FFMPEG, FFPROBE } from './paths.mjs';
import { syllables } from './text.mjs';

/** Exact media duration in seconds. */
export function probeDuration(file) {
  const out = execFileSync(FFPROBE, [
    '-v', 'error',
    '-show_entries', 'format=duration',
    '-of', 'default=nw=1:nk=1',
    file,
  ]).toString().trim();
  const d = Number(out);
  if (!Number.isFinite(d) || d <= 0) throw new Error(`could not read duration of ${file}`);
  return d;
}

/**
 * Speech segments, derived by inverting ffmpeg's silence detection.
 * threshold/minSilence are deliberately conservative: a TTS voiceover has clean
 * digital silence between lines, so we only need to catch real pauses.
 */
export function speechSegments(file, duration, { thresholdDb = -34, minSilence = 0.16 } = {}) {
  // silencedetect reports on stderr, so the run has to be captured, not piped through.
  const proc = spawnSync(FFMPEG, [
    '-hide_banner', '-nostats',
    '-i', file,
    '-af', `silencedetect=noise=${thresholdDb}dB:d=${minSilence}`,
    '-f', 'null', '-',
  ], { encoding: 'utf8', maxBuffer: 32 * 1024 * 1024 });
  if (proc.status !== 0) throw new Error(`silencedetect failed on ${file}:\n${proc.stderr?.slice(-800)}`);
  const res = proc.stderr || '';

  const silences = [];
  let open = null;
  for (const line of res.split('\n')) {
    const s = line.match(/silence_start:\s*(-?[\d.]+)/);
    const e = line.match(/silence_end:\s*(-?[\d.]+)/);
    if (s) open = Math.max(0, Number(s[1]));
    if (e && open !== null) {
      silences.push([open, Math.min(duration, Number(e[1]))]);
      open = null;
    }
  }
  if (open !== null) silences.push([open, duration]);

  const segments = [];
  let cursor = 0;
  for (const [ss, se] of silences) {
    if (ss - cursor > 0.05) segments.push({ start: cursor, end: ss });
    cursor = Math.max(cursor, se);
  }
  if (duration - cursor > 0.05) segments.push({ start: cursor, end: duration });
  return segments.length ? segments : [{ start: 0, end: duration }];
}

/**
 * A monotonic map between "speech time" (silences removed) and wall-clock time.
 * Word timings are laid out in speech time and mapped back, so no caption can
 * ever be scheduled inside a pause.
 */
export function speechClock(segments) {
  let acc = 0;
  const spans = segments.map((s) => {
    const span = { ...s, sStart: acc, sEnd: acc + (s.end - s.start) };
    acc += s.end - s.start;
    return span;
  });
  const total = acc;
  const toWall = (t) => {
    const clamped = Math.min(Math.max(t, 0), total);
    for (const s of spans) {
      if (clamped <= s.sEnd) return s.start + (clamped - s.sStart);
    }
    const last = spans[spans.length - 1];
    return last.end;
  };
  const boundaries = spans.flatMap((s) => [s.start, s.end]);
  return { total, spans, toWall, boundaries };
}

const WORD_COST = 0.34;

function weightOf(token) {
  let w = syllables(token) + WORD_COST;
  if (/[,;:—-]$/.test(token)) w += 0.35;
  if (/[.!?]$/.test(token)) w += 0.6;
  return w;
}

/**
 * Lay the known script over the detected speech.
 *
 * The voiceover text is known exactly (it is the script the VO was read from),
 * so this is a forced alignment, not a transcription: every token gets a share
 * of speech time proportional to its spoken weight, then sentence boundaries
 * snap to real pauses when one is close enough to be the same event.
 */
export function alignScript(scenes, segments, duration, { snapWindow = 0.4 } = {}) {
  const clock = speechClock(segments);

  const sentences = [];
  scenes.forEach((scene, si) => {
    scene.vo.forEach((text, li) => {
      const tokens = text.split(/\s+/).filter(Boolean);
      sentences.push({
        sceneIndex: si,
        sceneId: scene.id,
        lineIndex: li,
        text,
        tokens,
        weight: tokens.reduce((a, t) => a + weightOf(t), 0),
      });
    });
  });

  const totalWeight = sentences.reduce((a, s) => a + s.weight, 0);
  const perUnit = clock.total / totalWeight;

  let cursor = 0;
  for (const s of sentences) {
    s.sStart = cursor;
    s.sEnd = cursor + s.weight * perUnit;
    cursor = s.sEnd;
  }

  for (const s of sentences) {
    s.start = clock.toWall(s.sStart);
    s.end = clock.toWall(s.sEnd);
  }

  // Snap each boundary to a real pause edge when one sits within snapWindow.
  for (let i = 0; i < sentences.length; i++) {
    const s = sentences[i];
    const snapped = nearest(clock.boundaries, s.start, snapWindow);
    if (snapped !== null) {
      const prev = sentences[i - 1];
      const floor = prev ? prev.start + 0.25 : 0;
      if (snapped >= floor && snapped < s.end - 0.2) {
        s.start = snapped;
        if (prev) prev.end = Math.max(prev.start + 0.2, snapped);
      }
    }
  }
  sentences[sentences.length - 1].end = Math.max(
    sentences[sentences.length - 1].start + 0.2,
    Math.min(duration, sentences[sentences.length - 1].end),
  );

  // Words inside a sentence, again in speech time.
  for (const s of sentences) {
    const sSpanStart = invert(clock, s.start);
    const sSpanEnd = invert(clock, s.end);
    const span = Math.max(0.05, sSpanEnd - sSpanStart);
    let acc = 0;
    s.words = s.tokens.map((tok) => {
      const w = weightOf(tok);
      const a = sSpanStart + (acc / s.weight) * span;
      acc += w;
      const b = sSpanStart + (acc / s.weight) * span;
      return { text: tok, start: clock.toWall(a), end: clock.toWall(b) };
    });
  }

  return { sentences, clock };
}

function nearest(values, target, window) {
  let best = null;
  let bestD = Infinity;
  for (const v of values) {
    const d = Math.abs(v - target);
    if (d < bestD) {
      bestD = d;
      best = v;
    }
  }
  return bestD <= window ? best : null;
}

/** Wall-clock -> speech-clock, the inverse of clock.toWall. */
function invert(clock, wall) {
  for (const s of clock.spans) {
    if (wall <= s.end) return s.sStart + Math.max(0, wall - s.start);
  }
  return clock.total;
}

/**
 * Scene cuts from the aligned script.
 * A cut lands `leadIn` before its first word so the image is established before
 * the line arrives, but never inside the previous scene's last word.
 */
export function sceneTimings(scenes, sentences, duration, { leadIn = 0.2, minLen = 1.2 } = {}) {
  const cuts = scenes.map((scene, i) => {
    const first = sentences.find((s) => s.sceneIndex === i);
    if (!first) throw new Error(`scene ${scene.id} has no voiceover lines`);
    return { scene, i, firstWord: first.start };
  });

  const timings = [];
  for (let i = 0; i < cuts.length; i++) {
    const prevSentences = sentences.filter((s) => s.sceneIndex === i - 1);
    const prevEnd = prevSentences.length ? prevSentences[prevSentences.length - 1].end : 0;
    let start = i === 0 ? 0 : Math.max(prevEnd + 0.02, cuts[i].firstWord - leadIn);
    if (i > 0) start = Math.max(start, timings[i - 1].start + minLen);
    timings.push({ id: cuts[i].scene.id, start });
  }
  for (let i = 0; i < timings.length; i++) {
    timings[i].end = i + 1 < timings.length ? timings[i + 1].start : duration;
    timings[i].length = timings[i].end - timings[i].start;
  }
  return timings;
}
