#!/usr/bin/env node
import { credentials, fail } from './lib/config.mjs';
import { requestDeviceCode, pollForToken, accessToken } from './lib/oauth.mjs';
import { myChannel, recentVideos, uploadVideo } from './lib/youtube.mjs';

const number = (value) => Number(value ?? 0).toLocaleString('en-US');

function parseFlags(argv) {
  const flags = {};
  const positional = [];
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg.startsWith('--')) {
      const key = arg.slice(2);
      const next = argv[i + 1];
      if (next && !next.startsWith('--')) {
        flags[key] = next;
        i += 1;
      } else {
        flags[key] = true;
      }
    } else {
      positional.push(arg);
    }
  }
  return { flags, positional };
}

async function connect() {
  const { clientId, clientSecret } = credentials({ needRefreshToken: false });
  const device = await requestDeviceCode(clientId);

  console.log('\n──────────────────────────────────────────────');
  console.log('  Open this page:  ' + (device.verification_url || 'https://www.google.com/device'));
  console.log('  Enter this code: ' + device.user_code);
  console.log('──────────────────────────────────────────────');
  console.log('\nSign in with the Google account that owns the channel.');
  console.log('Waiting for you to approve');

  const token = await pollForToken({
    clientId,
    clientSecret,
    deviceCode: device.device_code,
    interval: device.interval,
    expiresIn: device.expires_in,
    onWait: () => process.stdout.write('.'),
  });

  const channel = await myChannel(token.access_token);

  console.log('\n\nConnected to: ' + channel.snippet.title);
  console.log('\nAdd this as the repository secret YT_REFRESH_TOKEN:\n');
  console.log('  ' + token.refresh_token + '\n');
  console.log('Treat it like a password — it grants access to the channel.');
  console.log('You can revoke it any time at https://myaccount.google.com/permissions\n');
}

async function stats() {
  const token = await accessToken(credentials());
  const channel = await myChannel(token);
  const s = channel.statistics;

  console.log('\n' + channel.snippet.title);
  console.log('─'.repeat(channel.snippet.title.length));
  console.log('Subscribers : ' + (s.hiddenSubscriberCount ? 'hidden' : number(s.subscriberCount)));
  console.log('Total views : ' + number(s.viewCount));
  console.log('Videos      : ' + number(s.videoCount));
  console.log('Channel ID  : ' + channel.id + '\n');
}

async function videos(argv) {
  const { positional } = parseFlags(argv);
  const limit = Number(positional[0]) || 10;
  const token = await accessToken(credentials());
  const { channel, videos: items } = await recentVideos(token, limit);

  console.log('\nLatest uploads — ' + channel.snippet.title + '\n');
  if (!items.length) {
    console.log('No videos published yet.\n');
    return;
  }
  for (const video of items) {
    const views = number(video.statistics?.viewCount);
    const date = video.snippet.publishedAt.slice(0, 10);
    console.log(`  ${date}  ${views.padStart(9)} views  ${video.snippet.title}`);
    console.log(`              https://youtu.be/${video.id}`);
  }
  console.log();
}

async function upload(argv) {
  const { flags, positional } = parseFlags(argv);
  const file = positional[0];
  if (!file) fail('Usage: node scripts/yt.mjs upload <file.mp4> --title "..." [--privacy private]');

  const token = await accessToken(credentials());
  const video = await uploadVideo(token, {
    file,
    title: flags.title,
    description: flags.description || '',
    tags: flags.tags ? String(flags.tags).split(',').map((t) => t.trim()) : [],
    privacy: flags.privacy || 'private',
    madeForKids: Boolean(flags['made-for-kids']),
    synthetic: Boolean(flags.synthetic),
    onProgress: (message) => console.log(message),
  });

  console.log('\nPublished as "' + video.snippet.title + '"');
  console.log('Visibility: ' + video.status.privacyStatus);
  console.log('https://youtu.be/' + video.id + '\n');
}

const COMMANDS = { connect, stats, videos, upload };

const [command, ...rest] = process.argv.slice(2);

if (!command || command === 'help' || !COMMANDS[command]) {
  console.log(`
YouTube channel commands

  node scripts/yt.mjs connect            Link the channel (one time)
  node scripts/yt.mjs stats              Subscribers, views, video count
  node scripts/yt.mjs videos [n]         Latest uploads with view counts
  node scripts/yt.mjs upload <file>      Upload a video

Upload options
  --title "..."        Video title        --privacy private|unlisted|public
  --description "..."  Description        --tags "a,b,c"
  --synthetic          Declare AI-generated content
`);
  process.exit(command && command !== 'help' ? 1 : 0);
}

try {
  await COMMANDS[command](rest);
} catch (error) {
  fail(error.message);
}
