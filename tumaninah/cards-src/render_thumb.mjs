import {bundle} from '@remotion/bundler';
import {renderStill, selectComposition} from '@remotion/renderer';
import path from 'path';
const CHROME = '/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell';
const props = JSON.parse(process.argv[2]);
const out = path.resolve(process.argv[3]);
const serveUrl = await bundle({entryPoint: path.resolve('src/index.ts'), onProgress: () => {}});
const comp = await selectComposition({serveUrl, id: 'Thumb', inputProps: props, browserExecutable: CHROME});
await renderStill({serveUrl, composition: comp, output: out, inputProps: props,
	browserExecutable: CHROME, chromiumOptions: {gl: 'swangle'}, imageFormat: 'png'});
console.log('wrote', out);
