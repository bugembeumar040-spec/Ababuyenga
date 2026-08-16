import { readFileSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

export const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..', '..');

// Minimal .env reader so the repo stays dependency-free. Real environment
// variables always win, which is what makes the GitHub Actions secrets work
// without any extra wiring.
function loadDotEnv() {
  const path = join(ROOT, '.env');
  if (!existsSync(path)) return;
  for (const line of readFileSync(path, 'utf8').split('\n')) {
    const match = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*)$/i);
    if (!match) continue;
    const key = match[1];
    if (process.env[key]) continue;
    process.env[key] = match[2].trim().replace(/^["']|["']$/g, '');
  }
}

loadDotEnv();

export function credentials({ needRefreshToken = true } = {}) {
  const clientId = process.env.YT_CLIENT_ID;
  const clientSecret = process.env.YT_CLIENT_SECRET;
  const refreshToken = process.env.YT_REFRESH_TOKEN;

  if (!clientId || !clientSecret) {
    fail(
      'Missing YT_CLIENT_ID / YT_CLIENT_SECRET.',
      'Follow docs/YOUTUBE-SETUP.md steps 1-4, then put them in .env or in the',
      'GitHub repository secrets.'
    );
  }
  if (needRefreshToken && !refreshToken) {
    fail(
      'Missing YT_REFRESH_TOKEN — this channel is not connected yet.',
      'Run:  node scripts/yt.mjs connect'
    );
  }

  return { clientId, clientSecret, refreshToken };
}

export function fail(...lines) {
  console.error('\n' + lines.join('\n') + '\n');
  process.exit(1);
}
