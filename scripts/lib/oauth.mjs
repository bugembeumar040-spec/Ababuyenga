const DEVICE_CODE_URL = 'https://oauth2.googleapis.com/device/code';
const TOKEN_URL = 'https://oauth2.googleapis.com/token';

// The limited-input device flow accepts only a short list of scopes, and
// `youtube.upload` is NOT one of them. The broader `youtube` scope is, and it
// authorises videos.insert as well as reads — so this single scope covers the
// whole CLI. Do not "tighten" this to youtube.upload; the device flow rejects it.
export const SCOPE = 'https://www.googleapis.com/auth/youtube';

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function postForm(url, params) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams(params),
  });
  const body = await res.json().catch(() => ({}));
  return { status: res.status, body };
}

function describe(body) {
  const code = body.error || 'unknown_error';
  const detail = body.error_description ? ` — ${body.error_description}` : '';
  return `${code}${detail}`;
}

export async function requestDeviceCode(clientId) {
  const { status, body } = await postForm(DEVICE_CODE_URL, { client_id: clientId, scope: SCOPE });
  if (status !== 200) {
    throw new Error(
      `Could not start sign-in: ${describe(body)}\n` +
      'The usual cause is an OAuth client that is not of type ' +
      '"TVs and Limited Input devices".'
    );
  }
  return body;
}

export async function pollForToken({ clientId, clientSecret, deviceCode, interval, expiresIn, onWait }) {
  let waitMs = (interval || 5) * 1000;
  const deadline = Date.now() + (expiresIn || 1800) * 1000;

  while (Date.now() < deadline) {
    await sleep(waitMs);
    const { status, body } = await postForm(TOKEN_URL, {
      client_id: clientId,
      client_secret: clientSecret,
      device_code: deviceCode,
      grant_type: 'urn:ietf:params:oauth:grant-type:device_code',
    });

    if (status === 200) return body;

    switch (body.error) {
      case 'authorization_pending':
        onWait?.();
        break;
      case 'slow_down':
        waitMs += 5000;
        break;
      case 'access_denied':
        throw new Error('You declined the permission request on the Google page.');
      case 'expired_token':
        throw new Error('The code expired before it was entered. Run connect again.');
      default:
        throw new Error(describe(body));
    }
  }
  throw new Error('Timed out waiting for you to approve on google.com/device.');
}

// Access tokens last about an hour; the refresh token is the durable credential,
// so every command mints a fresh access token rather than caching one.
export async function accessToken({ clientId, clientSecret, refreshToken }) {
  const { status, body } = await postForm(TOKEN_URL, {
    client_id: clientId,
    client_secret: clientSecret,
    refresh_token: refreshToken,
    grant_type: 'refresh_token',
  });
  if (status !== 200) {
    throw new Error(
      `Could not refresh access: ${describe(body)}\n` +
      'If this says invalid_grant, the refresh token was revoked or expired ' +
      '(apps left in "Testing" expire them after 7 days). Run connect again.'
    );
  }
  return body.access_token;
}
