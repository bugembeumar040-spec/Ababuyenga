import {bundle} from '@remotion/bundler';
import {renderFrames, selectComposition} from '@remotion/renderer';
import {execFileSync} from 'child_process';
import {createRequire} from 'module';
import fs from 'fs';
import os from 'os';
import path from 'path';

const require = createRequire(import.meta.url);
const CHROME = '/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell';
const FFMPEG = execFileSync('python3', [
	'-c',
	'import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())',
])
	.toString()
	.trim();

const OUT = path.resolve('../overlays');
const cards = JSON.parse(fs.readFileSync('cards.json', 'utf8'));

const only = process.argv.includes('--only')
	? process.argv[process.argv.indexOf('--only') + 1].split(',')
	: null;

const slug = (s) =>
	s
		.normalize('NFKD')
		.replace(/[̀-ͯ]/g, '')
		.replace(/[^a-zA-Z0-9]+/g, '-')
		.toLowerCase()
		.replace(/^-|-$/g, '');

const mmss = (t) => {
	const [m, s] = t.split(':');
	return String(m).padStart(2, '0') + s;
};

const ff = (args) => execFileSync(FFMPEG, ['-y', '-loglevel', 'error', ...args]);

console.log('bundling…');
const serveUrl = await bundle({entryPoint: path.resolve('src/index.ts'), onProgress: () => {}});
console.log('bundled');

for (const dir of ['webm', 'mp4', 'still']) {
	fs.mkdirSync(path.join(OUT, dir), {recursive: true});
}

const list = only ? cards.filter((c) => only.includes(c.n)) : cards;
let i = 0;
const t0 = Date.now();

for (const c of list) {
	i++;
	const base = `card-${c.n}_${mmss(c.t)}_${slug(c.head)}`;
	const props = {ch: c.ch, ar: c.ar, head: c.head, sub: c.sub, bg: 'transparent'};
	const frames = fs.mkdtempSync(path.join(os.tmpdir(), 'card-'));

	// One browser pass per card: a transparent PNG sequence. Both deliverables are
	// encoded from it, so the alpha is decided here rather than by the encoder.
	const comp = await selectComposition({
		serveUrl,
		id: 'Card',
		inputProps: props,
		browserExecutable: CHROME,
	});
	// Cards are trimmed where a plate is about to take the frame, so the length
	// comes from the fit pass rather than being fixed at six seconds.
	if (c.dur_s) {
		comp.durationInFrames = Math.round(c.dur_s * 30);
	}
	await renderFrames({
		serveUrl,
		composition: comp,
		browserExecutable: CHROME,
		chromiumOptions: {gl: 'swangle'},
		concurrency: 4,
		imageFormat: 'png',
		inputProps: props,
		outputDir: frames,
		onStart: () => undefined,
		onFrameUpdate: () => undefined,
	});

	// Remotion names them element-N.png with no zero padding; ffmpeg wants a
	// fixed-width pattern, so renumber before encoding.
	const files = fs
		.readdirSync(frames)
		.filter((f) => f.endsWith('.png'))
		.sort((a, b) => Number(a.match(/\d+/)[0]) - Number(b.match(/\d+/)[0]));
	files.forEach((f, idx) => {
		fs.renameSync(
			path.join(frames, f),
			path.join(frames, `f${String(idx).padStart(5, '0')}.png`),
		);
	});
	const pattern = path.join(frames, 'f%05d.png');

	// Alpha WebM — drops straight onto a timeline, no blend mode.
	ff([
		'-framerate', '30', '-i', pattern,
		'-c:v', 'libvpx-vp9', '-pix_fmt', 'yuva420p', '-crf', '28', '-b:v', '0',
		'-auto-alt-ref', '0', '-an',
		path.join(OUT, 'webm', `${base}.webm`),
	]);

	// H.264 over white for editors that will not take alpha WebM: composite Multiply.
	ff([
		'-framerate', '30', '-i', pattern,
		'-f', 'lavfi', '-i', 'color=c=white:s=1920x1080:r=30',
		'-filter_complex', '[1:v][0:v]overlay=shortest=1,format=yuv420p',
		'-c:v', 'libx264', '-crf', '18', '-preset', 'veryfast', '-an',
		path.join(OUT, 'mp4', `${base}.mp4`),
	]);

	// A flattened still for quick review / contact sheet.
	ff([
		'-i', path.join(frames, 'f00090.png'),
		'-f', 'lavfi', '-i', 'color=c=white:s=1920x1080',
		'-filter_complex', '[1:v][0:v]overlay',
		'-frames:v', '1',
		path.join(OUT, 'still', `${base}.png`),
	]);

	fs.rmSync(frames, {recursive: true, force: true});
	const el = ((Date.now() - t0) / 1000 / i).toFixed(0);
	console.log(`[${i}/${list.length}] ${base}  (~${el}s/card)`);
}
console.log('done');
