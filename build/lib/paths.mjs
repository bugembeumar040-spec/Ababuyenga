import { fileURLToPath } from 'node:url';
import path from 'node:path';
import fs from 'node:fs';
import ffmpegStatic from 'ffmpeg-static';
import ffprobeStatic from 'ffprobe-static';

export const BUILD = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const ROOT = path.resolve(BUILD, '..');
export const OUT = path.join(ROOT, 'out');
export const MEDIA = path.join(ROOT, 'media');

export const FFMPEG = ffmpegStatic;
export const FFPROBE = ffprobeStatic.path;

export function readJson(p) {
  return JSON.parse(fs.readFileSync(p, 'utf8'));
}

/** --vo <path> and --stills <dir> override scenes.json without editing it. */
function argValue(flag) {
  const i = process.argv.indexOf(flag);
  return i !== -1 && process.argv[i + 1] ? process.argv[i + 1] : null;
}

export function loadConfig() {
  const spineFile = argValue('--spine') || 'scenes.json';
  const scenes = readJson(path.join(BUILD, spineFile));
  const style = readJson(path.join(BUILD, argValue('--style') || scenes.project.style || 'style.json'));
  const vo = argValue('--vo');
  const stills = argValue('--stills');
  if (vo) scenes.project.voiceover = vo;
  if (stills) scenes.project.stillsDir = stills;
  if (process.argv.includes('--fixtures')) {
    scenes.project.voiceover = 'media/_fixtures/creditcard-vo-fixture.mp3';
    scenes.project.stillsDir = 'media/_fixtures/stills';
    scenes.project.slug = `${scenes.project.slug}-fixture`;
  }
  return { scenes, style };
}

export function ensureOut() {
  fs.mkdirSync(OUT, { recursive: true });
  return OUT;
}
