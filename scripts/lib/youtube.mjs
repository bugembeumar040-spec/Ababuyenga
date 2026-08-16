import { createReadStream, statSync } from 'node:fs';
import { basename, extname } from 'node:path';

const API = 'https://www.googleapis.com/youtube/v3';
const UPLOAD = 'https://www.googleapis.com/upload/youtube/v3/videos';

const MIME = {
  '.mp4': 'video/mp4',
  '.mov': 'video/quicktime',
  '.avi': 'video/x-msvideo',
  '.webm': 'video/webm',
  '.mkv': 'video/x-matroska',
};

async function get(token, path, params = {}) {
  const url = new URL(`${API}/${path}`);
  for (const [key, value] of Object.entries(params)) url.searchParams.set(key, value);

  const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    const reason = body?.error?.message || res.statusText;
    throw new Error(`YouTube API ${res.status} on ${path}: ${reason}`);
  }
  return body;
}

export async function myChannel(token) {
  const data = await get(token, 'channels', {
    part: 'snippet,statistics,contentDetails',
    mine: 'true',
  });
  const channel = data.items?.[0];
  if (!channel) {
    throw new Error(
      'That Google account has no YouTube channel, or you approved a different ' +
      'account than the one that owns the channel.'
    );
  }
  return channel;
}

export async function recentVideos(token, limit = 10) {
  const channel = await myChannel(token);
  const uploads = channel.contentDetails?.relatedPlaylists?.uploads;
  if (!uploads) return { channel, videos: [] };

  const playlist = await get(token, 'playlistItems', {
    part: 'contentDetails',
    playlistId: uploads,
    maxResults: String(Math.min(limit, 50)),
  });

  const ids = playlist.items?.map((item) => item.contentDetails.videoId) ?? [];
  if (!ids.length) return { channel, videos: [] };

  // One batched call for all the stats — cheaper against the daily quota than
  // asking per video.
  const details = await get(token, 'videos', {
    part: 'snippet,statistics,contentDetails',
    id: ids.join(','),
  });
  return { channel, videos: details.items ?? [] };
}

export async function uploadVideo(token, options) {
  const {
    file,
    title,
    description = '',
    tags = [],
    categoryId = '22',
    privacy = 'private',
    madeForKids = false,
    synthetic = false,
    onProgress,
  } = options;

  const size = statSync(file).size;
  const mime = MIME[extname(file).toLowerCase()] || 'video/*';

  const metadata = {
    snippet: { title: title || basename(file, extname(file)), description, tags, categoryId },
    status: {
      privacyStatus: privacy,
      // The API rejects an upload that does not state this explicitly.
      selfDeclaredMadeForKids: madeForKids,
      containsSyntheticMedia: synthetic,
    },
  };

  // Step 1: open a resumable session. Google replies with a one-off URL in the
  // Location header that the bytes then go to.
  const init = await fetch(`${UPLOAD}?uploadType=resumable&part=snippet,status`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
      'X-Upload-Content-Length': String(size),
      'X-Upload-Content-Type': mime,
    },
    body: JSON.stringify(metadata),
  });

  if (!init.ok) {
    const body = await init.json().catch(() => ({}));
    throw new Error(
      `Could not start the upload: ${body?.error?.message || init.statusText}`
    );
  }

  const session = init.headers.get('location');
  if (!session) throw new Error('Google did not return an upload URL.');

  onProgress?.(`Uploading ${(size / 1048576).toFixed(1)} MB…`);

  // Step 2: stream the file up. Streaming keeps memory flat regardless of size.
  const res = await fetch(session, {
    method: 'PUT',
    headers: { 'Content-Type': mime, 'Content-Length': String(size) },
    body: createReadStream(file),
    duplex: 'half',
  });

  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(`Upload failed: ${body?.error?.message || res.statusText}`);
  }
  return body;
}
