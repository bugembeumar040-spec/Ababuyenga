# Connecting the YouTube channel

This repo talks to the **YouTube Data API v3** using Google's device flow — the
same flow a smart TV uses. You approve it by typing a short code on your phone
or laptop. There is no web server, no redirect URL, and nothing to install.

One credential covers everything. The device flow does not accept the
`youtube.upload` scope, but it does accept the broader `youtube` scope, and that
scope authorises uploads as well as reads.

## What you do once

1. Create an OAuth client of type **TVs and Limited Input devices** at
   <https://console.cloud.google.com/auth/clients>.
   The type matters — a Web or Desktop client returns `Invalid client type`.
2. Make sure the **YouTube Data API v3** is enabled at
   <https://console.cloud.google.com/apis/library/youtube.googleapis.com>.
3. Set the app to **In production** at
   <https://console.cloud.google.com/auth/audience>.
   Left on *Testing*, Google kills the refresh token after **7 days** and every
   command starts failing with `invalid_grant`.
4. Put the client ID and secret somewhere the code can read them — either a
   local `.env` (see `.env.example`) or the repository secrets at
   <https://github.com/bugembeumar040-spec/Ababuyenga/settings/secrets/actions>.
5. Run `node scripts/yt.mjs connect` and follow the prompt. It prints a refresh
   token; save that as the `YT_REFRESH_TOKEN` secret.

## Commands

```
node scripts/yt.mjs connect         Link the channel (one time)
node scripts/yt.mjs stats           Subscribers, views, video count
node scripts/yt.mjs videos [n]      Latest uploads with view counts
node scripts/yt.mjs upload <file>   Upload a video
```

Upload defaults to **private**, so nothing goes live by accident. Make it
visible deliberately:

```
node scripts/yt.mjs upload out/short.mp4 \
  --title "They call you a deadbeat" \
  --description "..." \
  --tags "finance,credit" \
  --synthetic \
  --privacy public
```

`--synthetic` sets YouTube's altered-or-synthetic-content disclosure. For a
channel whose footage is model-generated, that flag belongs on every upload.

## Quotas

A project gets 10,000 units/day. Reads are cheap — `stats` costs 1 unit, and
`videos` costs about 3. Uploads bill to a separate daily bucket of roughly 100
videos (down from 1,600 units each before December 2025, which had capped
uploads at about 6/day).

## Troubleshooting

| Message | Cause |
| --- | --- |
| `Invalid client type` | The OAuth client is not "TVs and Limited Input devices". Create one that is. |
| `invalid_grant` | Refresh token expired or revoked. Publish the app (step 3), then re-run `connect`. |
| `invalid_client` | Client ID/secret wrong or from a different project. |
| `no YouTube channel` | You approved a Google account that does not own the channel. |

Revoke this repo's access at any time:
<https://myaccount.google.com/permissions>
