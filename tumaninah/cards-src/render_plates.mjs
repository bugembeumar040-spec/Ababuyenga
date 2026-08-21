import {bundle} from '@remotion/bundler';
import {renderFrames, selectComposition} from '@remotion/renderer';
import {execFileSync} from 'child_process';
import fs from 'fs';
import os from 'os';
import path from 'path';

const CHROME = '/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell';
const FFMPEG = execFileSync('python3', ['-c', 'import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())'])
	.toString().trim();
const OUT = path.resolve('../overlays/plates');
const plates = JSON.parse(fs.readFileSync('plates.json', 'utf8'));
const shots = JSON.parse(fs.readFileSync('../timing/placed.json', 'utf8'));
const ff = (a) => execFileSync(FFMPEG, ['-y', '-loglevel', 'error', ...a]);

fs.mkdirSync(OUT, {recursive: true});
const serveUrl = await bundle({entryPoint: path.resolve('src/index.ts'), onProgress: () => {}});

for (const p of plates) {
	const shot = shots.find((s) => s.scene === p.scene);
	// The plate holds for the shot it sits on, so it never outlives the frame.
	const dur = Math.max(60, Math.round(shot.dur_s * 30));
	const props = {ar: p.ar, gloss: p.gloss, ref: p.ref, bg: 'transparent'};
	const comp = await selectComposition({serveUrl, id: 'Plate', inputProps: props, browserExecutable: CHROME});
	comp.durationInFrames = dur;
	const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'plate-'));
	await renderFrames({
		serveUrl, composition: comp, browserExecutable: CHROME,
		chromiumOptions: {gl: 'swangle'}, concurrency: 4, imageFormat: 'png',
		inputProps: props, outputDir: dir, onStart: () => undefined, onFrameUpdate: () => undefined,
	});
	const files = fs.readdirSync(dir).filter((f) => f.endsWith('.png'))
		.sort((a, b) => Number(a.match(/\d+/)[0]) - Number(b.match(/\d+/)[0]));
	files.forEach((f, i) => fs.renameSync(path.join(dir, f), path.join(dir, `f${String(i).padStart(5, '0')}.png`)));
	const pat = path.join(dir, 'f%05d.png');
	const base = `plate-scene-${p.scene}`;
	ff(['-framerate', '30', '-i', pat, '-c:v', 'libvpx-vp9', '-pix_fmt', 'yuva420p',
		'-crf', '28', '-b:v', '0', '-auto-alt-ref', '0', '-an', path.join(OUT, `${base}.webm`)]);
	ff(['-i', path.join(dir, 'f00045.png'), '-f', 'lavfi', '-i', 'color=c=white:s=1920x1080',
		'-filter_complex', '[1:v][0:v]overlay', '-frames:v', '1', path.join(OUT, `${base}.png`)]);
	fs.rmSync(dir, {recursive: true, force: true});
	console.log(`${base}  ${(dur / 30).toFixed(1)}s`);
}
console.log('done');
