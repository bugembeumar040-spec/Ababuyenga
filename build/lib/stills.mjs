import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { FFPROBE, ROOT, OUT } from './paths.mjs';

const IMAGE_RE = /\.(png|jpe?g|webp|tiff?)$/i;

export function listStills(dir) {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir)
    .filter((f) => IMAGE_RE.test(f))
    .sort((a, b) => a.localeCompare(b, 'en', { numeric: true }));
}

export function probeImage(file) {
  const out = execFileSync(FFPROBE, [
    '-v', 'error',
    '-select_streams', 'v:0',
    '-show_entries', 'stream=width,height',
    '-of', 'csv=p=0',
    file,
  ]).toString().trim();
  const [w, h] = out.split(',').map(Number);
  return { width: w, height: h };
}

/**
 * Decide which image plays under which scene.
 *
 * Precedence:
 *  1. out/stills-map.json — hand-edited, always wins.
 *  2. filename containing the scene's still code (b01, B-01, scene01 ...).
 *  3. sorted order, spread evenly when there are fewer images than scenes.
 */
export function resolveStills(scenes, stillsDir, slug = 'default') {
  const files = listStills(stillsDir);
  const overridePath = path.join(OUT, `${slug}-stills-map.json`);
  const override = fs.existsSync(overridePath)
    ? JSON.parse(fs.readFileSync(overridePath, 'utf8'))
    : null;

  const result = scenes.map((scene, i) => {
    if (override?.[scene.id]) {
      return { id: scene.id, still: scene.still, file: path.resolve(stillsDir, override[scene.id]), how: 'stills-map.json' };
    }
    const code = scene.still.toLowerCase();
    const num = code.replace(/\D/g, '');
    const match = files.find((f) => {
      const b = path.basename(f, path.extname(f)).toLowerCase().replace(/[^a-z0-9]/g, '');
      return b.includes(code) || b.includes(`scene${num}`) || b === num || b.endsWith(num);
    });
    if (match) return { id: scene.id, still: scene.still, file: path.join(stillsDir, match), how: 'filename' };
    return { id: scene.id, still: scene.still, file: null, how: 'unmatched', index: i };
  });

  const unmatched = result.filter((r) => !r.file);
  if (unmatched.length && files.length) {
    const used = new Set(result.filter((r) => r.file).map((r) => path.basename(r.file)));
    const pool = files.filter((f) => !used.has(f));
    if (pool.length) {
      unmatched.forEach((r, k) => {
        // Spread the available images evenly across the scenes that still need one.
        const pick = pool[Math.min(pool.length - 1, Math.floor((k * pool.length) / unmatched.length))];
        r.file = path.join(stillsDir, pick);
        r.how = pool.length >= unmatched.length ? 'sorted order' : 'reused (fewer images than scenes)';
      });
    }
  }

  return { assignments: result, files };
}

export function writeStillsMap(assignments, stillsDir, slug = 'default') {
  const map = {};
  for (const a of assignments) map[a.id] = a.file ? path.relative(stillsDir, a.file) : '';
  fs.mkdirSync(OUT, { recursive: true });
  const out = path.join(OUT, `${slug}-stills-map.json`);
  fs.writeFileSync(out, `${JSON.stringify(map, null, 2)}\n`);
  return out;
}

export const rel = (p) => path.relative(ROOT, p);
