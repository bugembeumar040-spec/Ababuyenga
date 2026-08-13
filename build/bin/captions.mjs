#!/usr/bin/env node
/**
 * Burn-ready caption + card track (ASS), rendered from out/timeline.json.
 *
 * Format follows the reference Short: uppercase heavy condensed sans, bare on
 * the artwork, hard cut-on and cut-off per spoken burst, one accent colour per
 * line, and held cards at the turns. See the active style file for the full
 * transcription of both that and the pack's own caption spec.
 *
 * All timing decisions live in bin/align.mjs — this file only lays out pixels.
 * Vertical placement is solved per frame against that still's ink coverage, so
 * text lands in the empty part of the artwork rather than on a face.
 */
import fs from 'node:fs';
import path from 'node:path';
import { loadConfig, ensureOut, OUT } from '../lib/paths.mjs';
import { captionEvents, cardEvents, assemble, captionBlockHeight } from '../lib/ass.mjs';
import { bestBand, cardHeight, faceGuards, bandLuma } from '../lib/placement.mjs';

const { scenes: spine, style } = loadConfig();
const { width: W, height: H } = spine.project;

const timelinePath = path.join(OUT, 'timeline.json');
if (!fs.existsSync(timelinePath)) {
  console.error('\nout/timeline.json missing — run: node bin/align.mjs\n');
  process.exit(2);
}
const timeline = JSON.parse(fs.readFileSync(timelinePath, 'utf8'));

const inspectPath = path.join(OUT, 'stills-inspect.json');
const inspected = fs.existsSync(inspectPath)
  ? new Map(JSON.parse(fs.readFileSync(inspectPath, 'utf8')).map((r) => [r.file, r]))
  : new Map();

const events = [];
const boxes = [];
const placements = [];

for (const [index, scene] of timeline.scenes.entries()) {
  // A scene that continues the previous shot shares its artwork.
  let source = scene.still;
  for (let i = index; i >= 0 && !source; i--) source = timeline.scenes[i].still;
  const info = inspected.get(source) || null;
  const profile = info?.detail || info?.profile || null;
  // The pack's hard rule: never over a face.
  const guards = faceGuards(info?.detail, info?.contentTop);

  const captionBlock = Math.max(0.05, captionBlockHeight(scene.bursts, style, W) / H);
  const capBand = scene.captionY != null
    ? { y: scene.captionY, ink: null }
    : bestBand(profile, {
      height: captionBlock, preferY: style.caption.bandY, minY: 0.07, maxY: 0.93, blocked: guards,
    });
  const captionY = capBand.y;

  const cap = captionEvents(scene.bursts, { ...scene, captionY }, style, W, H);
  events.push(...cap.events);
  boxes.push(...cap.boxes);

  const blocked = [[captionY - captionBlock / 2, captionY + captionBlock / 2]];
  const placedCards = [];

  for (const card of scene.cards || []) {
    const h = cardHeight(card);
    const conflicts = placedCards
      .filter((p) => Math.min(p.end, card.end) - Math.max(p.start, card.start) > 0.04)
      .map((p) => [p.y - p.h / 2, p.y + p.h / 2]);
    const band = card.bandY != null
      ? { y: card.bandY, ink: null }
      : bestBand(profile, {
        height: h,
        preferY: style.card.bandY,
        minY: 0.07,
        maxY: 0.93,
        blocked: [...blocked, ...conflicts, ...guards],
      });

    // Bare on the artwork where the frame allows it; plated where it does not.
    // Plate when the artwork is busy under the type, or too dark for dark type.
    const lumaHere = bandLuma(info?.luma, band.y, h);
    const busy = band.ink != null && band.ink > (style.card.plate?.inkThreshold ?? 0.1);
    const lowContrast = lumaHere != null && lumaHere < (style.card.plate?.lumaThreshold ?? 150);
    const needsPlate = card.plate != null ? card.plate : (busy || lowContrast);
    const rendered = cardEvents({ ...card, bandY: band.y, plate: needsPlate }, { start: card.start, end: card.end }, scene, style, W, H);
    events.push(...rendered.events);
    boxes.push(...rendered.boxes);
    placedCards.push({ y: band.y, h, start: card.start, end: card.end });
    placements.push({ scene: scene.id, kind: `card:${card.kind}`, y: band.y, ink: band.ink, luma: lumaHere, plate: needsPlate, source });
  }

  placements.push({ scene: scene.id, kind: 'caption', y: captionY, ink: capBand.ink, source });
}

ensureOut();
fs.writeFileSync(path.join(OUT, 'captions.ass'), assemble(style, W, H, events));
fs.writeFileSync(path.join(OUT, 'layout.json'), `${JSON.stringify({ boxes, placements }, null, 2)}\n`);

const bursts = timeline.scenes.reduce((a, s) => a + s.bursts.length, 0);
const cards = timeline.scenes.reduce((a, s) => a + (s.cards ? s.cards.length : 0), 0);
console.log(`\n${bursts} caption bursts + ${cards} cards -> out/captions.ass`);
console.log(`${events.length} ASS events, ${boxes.length} layout boxes -> out/layout.json\n`);

const pad = (s, n) => String(s).padEnd(n);
console.log(` #    ${pad('ELEMENT', 16)} ${pad('BAND', 8)} INK UNDER TEXT`);
for (const p of placements.sort((a, b) => a.scene.localeCompare(b.scene))) {
  const ink = p.ink == null ? 'set in spine' : `${(p.ink * 100).toFixed(0)}%${p.plate ? '  (plated)' : ''}`;
  console.log(` ${pad(p.scene, 4)} ${pad(p.kind, 16)} ${pad(p.y.toFixed(2), 8)} ${ink}`);
}
console.log('');
