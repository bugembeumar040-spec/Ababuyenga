#!/usr/bin/env python3
"""
yt.py - YouTube channel CLI for Finance % Decoded.

Zero dependencies: standard library only. No pip install, no virtualenv.

Three tiers, each needing more setup than the last. Use the lowest one that
answers the question - the cheap tiers cost no API quota at all.

  TIER 0  no credentials      latest  handle
  TIER 1  API key             channel  videos  video  comments  search
  TIER 2  OAuth               analytics  retention  upload  update  thumbnail

Config is read from environment variables first, then ~/.config/ababuyenga/youtube.json:

  YT_API_KEY         Tier 1. Data API key.
  YT_CLIENT_ID       Tier 2. OAuth desktop-app client id.
  YT_CLIENT_SECRET   Tier 2. OAuth desktop-app client secret.
  YT_REFRESH_TOKEN   Tier 2. Printed by `yt.py auth`. Set this in the Claude
                     environment so every session is authenticated on start.
  YT_CHANNEL_ID      Default channel for Tier 0/1 commands.

Every command takes --json to emit the raw API response instead of the compact
human summary. Default output is deliberately terse - it is read by an LLM.
"""

import argparse
import html
import json
import mimetypes
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from datetime import date, timedelta

DATA_API = "https://www.googleapis.com/youtube/v3"
UPLOAD_API = "https://www.googleapis.com/upload/youtube/v3"
ANALYTICS_API = "https://youtubeanalytics.googleapis.com/v2"
TOKEN_URL = "https://oauth2.googleapis.com/token"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"

# Enough for analytics, retention and stats. Cannot upload, edit or delete -
# so a token minted with these is safe to hand to something you don't fully
# trust with the channel.
READ_SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]

# Adds publishing and metadata editing. force-ssl can also DELETE videos.
WRITE_SCOPES = READ_SCOPES + [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]

CONFIG_PATH = os.path.expanduser("~/.config/ababuyenga/youtube.json")
CHUNK = 8 * 1024 * 1024  # 8 MiB upload chunks


# --------------------------------------------------------------------------
# config
# --------------------------------------------------------------------------

def load_config():
    cfg = {}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH) as fh:
                cfg = json.load(fh)
        except (OSError, ValueError) as exc:
            die(f"could not read {CONFIG_PATH}: {exc}")
    for key in ("api_key", "client_id", "client_secret", "refresh_token", "channel_id"):
        env = os.environ.get("YT_" + key.upper())
        if env:
            cfg[key] = env
    return cfg


def save_config(cfg):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as fh:
        json.dump(cfg, fh, indent=2)
    os.chmod(CONFIG_PATH, 0o600)


def need(cfg, *keys):
    missing = [k for k in keys if not cfg.get(k)]
    if missing:
        names = ", ".join("YT_" + m.upper() for m in missing)
        die(f"missing credential(s): {names}\nRun: python3 tools/youtube/yt.py setup")
    return [cfg[k] for k in keys]


def die(msg, code=1):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


# --------------------------------------------------------------------------
# http
# --------------------------------------------------------------------------

def http(url, method="GET", body=None, headers=None, raw_body=None,
         want_headers=False, soft=False):
    """Call the API. Dies on error unless soft=True, which returns None instead."""
    hdrs = dict(headers or {})
    data = raw_body
    if body is not None:
        data = json.dumps(body).encode()
        hdrs.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            payload = resp.read()
            parsed = json.loads(payload) if payload else {}
            return (parsed, dict(resp.headers), resp.status) if want_headers else parsed
    except urllib.error.HTTPError as exc:
        if soft:
            return None
        detail = exc.read().decode(errors="replace")
        try:
            detail = json.loads(detail)["error"]["message"]
        except Exception:
            detail = detail[:500]
        die(f"HTTP {exc.code} from {urllib.parse.urlsplit(url).path}: {detail}")
    except urllib.error.URLError as exc:
        if soft:
            return None
        die(f"network error reaching {urllib.parse.urlsplit(url).netloc}: {exc.reason}")


def get_text(url, attempts=8):
    """Fetch a public page. youtube.com serves these unevenly - one measured
    run of the same feed URL gave 404, 404, 500, 200, 404 - so a single failure
    means nothing. Retry with a capped backoff rather than believing it."""
    delay, last = 1.0, "unknown error"
    for attempt in range(attempts):
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req) as resp:
                return resp.read().decode(errors="replace")
        except urllib.error.HTTPError as exc:
            last = f"HTTP {exc.code}"
            if exc.code in (401, 403):
                break  # a real refusal, not a wobble
        except urllib.error.URLError as exc:
            last = f"network error: {exc.reason}"
        if attempt < attempts - 1:
            time.sleep(delay)
            delay = min(delay * 2, 4.0)  # capped: this is flakiness, not overload
    die(f"{last} fetching {url} (after {attempts} attempts)")


# --------------------------------------------------------------------------
# oauth
# --------------------------------------------------------------------------

def access_token(cfg):
    """Exchange the long-lived refresh token for a short-lived access token."""
    client_id, client_secret, refresh = need(cfg, "client_id", "client_secret", "refresh_token")
    form = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh,
        "grant_type": "refresh_token",
    }).encode()
    res = http(TOKEN_URL, method="POST", raw_body=form,
               headers={"Content-Type": "application/x-www-form-urlencoded"})
    return res["access_token"]


def bearer(cfg):
    return {"Authorization": "Bearer " + access_token(cfg)}


def data_auth(cfg):
    """Authorize a Data API call, preferring the cheap API key.

    An OAuth token authorizes these endpoints just as well, so once Tier 2 is
    set up the API key becomes optional - don't make people create one twice.
    Returns (extra query params, extra headers)."""
    if cfg.get("api_key"):
        return {"key": cfg["api_key"]}, {}
    if cfg.get("client_id") and cfg.get("client_secret") and cfg.get("refresh_token"):
        return {}, bearer(cfg)
    die("need either YT_API_KEY, or OAuth credentials (run: yt.py setup)")


REDIRECT = "http://localhost:8765"


def auth_url(client_id, readonly=False):
    return AUTH_URL + "?" + urllib.parse.urlencode({
        "client_id": client_id,
        "redirect_uri": REDIRECT,
        "response_type": "code",
        "scope": " ".join(READ_SCOPES if readonly else WRITE_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
    })


def extract_code(pasted):
    """Accept either the whole pasted redirect URL or a bare code."""
    pasted = pasted.strip().strip('"').strip("'")
    if not pasted:
        die("nothing supplied")
    if not pasted.startswith("http"):
        return pasted
    query = urllib.parse.parse_qs(urllib.parse.urlsplit(pasted).query)
    if "error" in query:
        die(f"Google returned an error: {query['error'][0]}")
    code = query.get("code", [None])[0]
    if not code:
        die("no ?code= parameter in that URL - paste the whole address bar")
    return code


def cmd_auth(args, cfg):
    client_id, client_secret = need(cfg, "client_id", "client_secret")
    url = auth_url(client_id, readonly=args.readonly)

    # --url and --code split the flow in two so it works with no terminal:
    # something else can show the URL, and the code comes back as an argument.
    if args.url:
        print(url)
        return

    if args.code:
        code = extract_code(args.code)
    else:
        print("1. Open this URL in the browser signed into the channel's Google account:\n")
        print(url + "\n")
        print("2. Approve access. The browser lands on a localhost page that fails")
        print("   to load - that is expected and fine.")
        print("3. Copy the ENTIRE address bar of that failed page and paste it below.\n")
        if not args.no_browser:
            try:
                webbrowser.open(url)
            except Exception:
                pass
        code = extract_code(input("Pasted redirect URL (or bare code): "))

    form = urllib.parse.urlencode({
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": REDIRECT,
        "grant_type": "authorization_code",
    }).encode()
    res = http(TOKEN_URL, method="POST", raw_body=form,
               headers={"Content-Type": "application/x-www-form-urlencoded"})

    refresh = res.get("refresh_token")
    if not refresh:
        die("Google did not return a refresh_token. Revoke the app's access at "
            "https://myaccount.google.com/permissions and run auth again.")

    cfg["refresh_token"] = refresh
    save_config({k: v for k, v in cfg.items() if k in
                 ("api_key", "client_id", "client_secret", "refresh_token", "channel_id")})

    print(f"\nSaved to {CONFIG_PATH}")
    print("\nThis container is ephemeral. To stay authenticated in every future")
    print("Claude session, add this as an environment variable in your Claude")
    print("environment settings:\n")
    print(f"  YT_REFRESH_TOKEN={refresh}\n")
    print("Treat it like a password - it does not expire on its own.")


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def resolve_channel(cfg, ref=None):
    """Return a UC... channel id from a handle, URL, raw id, or config default."""
    ref = ref or cfg.get("channel_id")
    if not ref:
        die("no channel given. Pass --channel @handle, or set YT_CHANNEL_ID.")
    if re.fullmatch(r"UC[\w-]{22}", ref):
        return ref

    handle = ref
    if "youtube.com" in ref:
        m = re.search(r"/(@[\w.-]+)", ref) or re.search(r"/channel/(UC[\w-]{22})", ref)
        if not m:
            die(f"could not read a channel from URL: {ref}")
        handle = m.group(1)
        if handle.startswith("UC"):
            return handle
    if not handle.startswith("@"):
        handle = "@" + handle

    if cfg.get("api_key"):
        res = http(f"{DATA_API}/channels?" + urllib.parse.urlencode(
            {"part": "id", "forHandle": handle, "key": cfg["api_key"]}))
        items = res.get("items") or []
        if items:
            return items[0]["id"]

    # No key, or the handle lookup came back empty: scrape the public page.
    # Only canonical fields - a bare "channelId" in the HTML belongs to whatever
    # video the page happens to be recommending, not to the channel itself.
    html = get_text("https://www.youtube.com/" + handle)
    for pattern in (r'"externalId":"(UC[\w-]{22})"',
                    r'itemprop="identifier" content="(UC[\w-]{22})"',
                    r'youtube\.com/channel/(UC[\w-]{22})'):
        m = re.search(pattern, html)
        if m:
            return m.group(1)
    die(f"could not resolve {handle} to a channel id")


def num(value):
    try:
        n = int(value)
    except (TypeError, ValueError):
        return "-"
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def duration(iso):
    m = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m:
        return "-"
    h, mi, s = (int(x) if x else 0 for x in m.groups())
    total = h * 3600 + mi * 60 + s
    return f"{total // 60}:{total % 60:02d}"


def out(args, payload, lines):
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print("\n".join(lines))


def date_range(days):
    end = date.today() - timedelta(days=1)  # analytics lags ~1 day
    return (end - timedelta(days=days - 1)).isoformat(), end.isoformat()


def paged(url_base, params, limit, headers=None):
    """Walk nextPageToken pagination until `limit` items are collected."""
    items, token = [], None
    while len(items) < limit:
        q = dict(params, maxResults=min(50, limit - len(items)))
        if token:
            q["pageToken"] = token
        res = http(f"{url_base}?" + urllib.parse.urlencode(q), headers=headers)
        batch = res.get("items") or []
        items.extend(batch)
        token = res.get("nextPageToken")
        if not token or not batch:
            break
    return items[:limit]


# --------------------------------------------------------------------------
# tier 0 - no credentials
# --------------------------------------------------------------------------

def cmd_handle(args, cfg):
    cid = resolve_channel(cfg, args.channel)
    out(args, {"channelId": cid}, [cid])


def cmd_latest(args, cfg):
    """Latest uploads via the public RSS feed. No API key, no quota cost."""
    cid = resolve_channel(cfg, args.channel)
    xml = get_text(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}")
    entries = re.findall(r"<entry>(.*?)</entry>", xml, re.S)[: args.n]

    def field(block, tag):
        m = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", block, re.S)
        if not m:
            return ""
        # Titles arrive escaped - &quot;Islamic&quot; must come back as quotes.
        return html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip()

    rows, payload = [], []
    for e in entries:
        vid = field(e, "yt:videoId")
        title = field(e, "title")
        published = field(e, "published")[:10]
        seen = re.search(r'<media:statistics\s+views="(\d+)"', e)  # self-closing tag
        views = seen.group(1) if seen else ""
        payload.append({"id": vid, "title": title, "published": published, "views": views})
        rows.append(f"{published}  {vid}  {num(views) if views else '':>6}  {title}")
    out(args, payload, rows or ["no entries in feed"])


# --------------------------------------------------------------------------
# tier 1 - api key
# --------------------------------------------------------------------------

def cmd_channel(args, cfg):
    auth, hdr = data_auth(cfg)
    cid = resolve_channel(cfg, args.channel)
    res = http(f"{DATA_API}/channels?" + urllib.parse.urlencode(
        dict(auth, part="snippet,statistics,contentDetails", id=cid)), headers=hdr)
    items = res.get("items") or []
    if not items:
        die(f"no channel found for {cid}")
    c = items[0]
    s, st = c["snippet"], c["statistics"]
    out(args, res, [
        f"{s['title']}  ({cid})",
        f"subscribers  {num(st.get('subscriberCount'))}",
        f"total views  {num(st.get('viewCount'))}",
        f"videos       {st.get('videoCount', '-')}",
        f"uploads list {c['contentDetails']['relatedPlaylists']['uploads']}",
    ])


def uploads_playlist(cfg, cid):
    auth, hdr = data_auth(cfg)
    res = http(f"{DATA_API}/channels?" + urllib.parse.urlencode(
        dict(auth, part="contentDetails", id=cid)), headers=hdr)
    items = res.get("items") or []
    if not items:
        die(f"no channel found for {cid}")
    return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]


def cmd_videos(args, cfg):
    auth, hdr = data_auth(cfg)
    cid = resolve_channel(cfg, args.channel)
    playlist = uploads_playlist(cfg, cid)
    entries = paged(f"{DATA_API}/playlistItems",
                    dict(auth, part="contentDetails", playlistId=playlist), args.n, hdr)
    ids = [e["contentDetails"]["videoId"] for e in entries]
    if not ids:
        out(args, [], ["no uploads"])
        return

    payload, rows = [], []
    for i in range(0, len(ids), 50):
        batch = ids[i:i + 50]
        res = http(f"{DATA_API}/videos?" + urllib.parse.urlencode(
            dict(auth, part="snippet,statistics,contentDetails", id=",".join(batch))), headers=hdr)
        for v in res.get("items") or []:
            st = v.get("statistics", {})
            payload.append(v)
            rows.append("  ".join([
                v["snippet"]["publishedAt"][:10],
                v["id"],
                f"{num(st.get('viewCount')):>6}",
                f"{num(st.get('likeCount')):>5}L",
                f"{num(st.get('commentCount')):>4}C",
                f"{duration(v['contentDetails'].get('duration')):>5}",
                v["snippet"]["title"],
            ]))
    out(args, payload, rows)


def cmd_video(args, cfg):
    auth, hdr = data_auth(cfg)
    res = http(f"{DATA_API}/videos?" + urllib.parse.urlencode(
        dict(auth, part="snippet,statistics,contentDetails,status", id=args.video_id)), headers=hdr)
    items = res.get("items") or []
    if not items:
        die(f"no video {args.video_id}")
    v = items[0]
    s, st = v["snippet"], v.get("statistics", {})
    out(args, res, [
        s["title"],
        f"published  {s['publishedAt'][:10]}   length {duration(v['contentDetails'].get('duration'))}",
        f"views {num(st.get('viewCount'))}   likes {num(st.get('likeCount'))}   comments {num(st.get('commentCount'))}",
        f"privacy    {v.get('status', {}).get('privacyStatus', '-')}",
        f"tags       {', '.join(s.get('tags', [])) or '-'}",
        "",
        s.get("description", "")[:1000],
    ])


def cmd_comments(args, cfg):
    auth, hdr = data_auth(cfg)
    params = dict(auth, part="snippet", order=args.order, textFormat="plainText")
    if args.video_id:
        params["videoId"] = args.video_id
    else:
        params["allThreadsRelatedToChannelId"] = resolve_channel(cfg, args.channel)
    items = paged(f"{DATA_API}/commentThreads", params, args.n, hdr)
    rows, payload = [], []
    for t in items:
        c = t["snippet"]["topLevelComment"]["snippet"]
        payload.append(c)
        text = " ".join(c["textDisplay"].split())
        rows.append(f"[{c.get('likeCount', 0):>3} likes] {c['authorDisplayName']}: {text[:300]}")
    out(args, payload, rows or ["no comments"])


def cmd_search(args, cfg):
    """Competitor / topic research. Costs 100 quota units per call - use sparingly."""
    auth, hdr = data_auth(cfg)
    params = dict(auth, part="snippet", q=args.query, type="video",
                  order=args.order, maxResults=min(args.n, 50))
    if args.days:
        after = (date.today() - timedelta(days=args.days)).isoformat() + "T00:00:00Z"
        params["publishedAfter"] = after
    if args.shorts:
        params["videoDuration"] = "short"
    res = http(f"{DATA_API}/search?" + urllib.parse.urlencode(params), headers=hdr)
    hits = res.get("items") or []
    ids = [h["id"]["videoId"] for h in hits]
    stats = {}
    if ids:
        det = http(f"{DATA_API}/videos?" + urllib.parse.urlencode(
            dict(auth, part="statistics", id=",".join(ids))), headers=hdr)
        stats = {v["id"]: v.get("statistics", {}) for v in det.get("items") or []}
    rows = []
    for h in hits:
        vid = h["id"]["videoId"]
        st = stats.get(vid, {})
        rows.append("  ".join([
            h["snippet"]["publishedAt"][:10],
            vid,
            f"{num(st.get('viewCount')):>6}",
            f"{h['snippet']['channelTitle'][:22]:<22}",
            h["snippet"]["title"],
        ]))
    out(args, hits, rows or ["no results"])


# --------------------------------------------------------------------------
# tier 2 - oauth
# --------------------------------------------------------------------------

def cmd_analytics(args, cfg):
    hdr = bearer(cfg)
    start, end = date_range(args.days)
    metrics = ("views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,"
               "subscribersGained,subscribersLost,likes,comments,shares")
    params = {"ids": "channel==MINE", "startDate": start, "endDate": end, "metrics": metrics}
    if args.video:
        params["filters"] = "video==" + args.video
    res = http(f"{ANALYTICS_API}/reports?" + urllib.parse.urlencode(params), headers=hdr)

    cols = [c["name"] for c in res.get("columnHeaders", [])]
    row = (res.get("rows") or [[0] * len(cols)])[0]
    data = dict(zip(cols, row))

    # Impressions and CTR live in a separate report that rejects some filter
    # combinations. If it is unavailable, carry on without it.
    ctr = {}
    c = http(f"{ANALYTICS_API}/reports?" + urllib.parse.urlencode(dict(
        params, metrics="impressions,impressionsClickThroughRate")), headers=hdr, soft=True)
    if c:
        ccols = [x["name"] for x in c.get("columnHeaders", [])]
        ctr = dict(zip(ccols, (c.get("rows") or [[0] * len(ccols)])[0]))

    scope = f"video {args.video}" if args.video else "channel"
    mins = data.get("estimatedMinutesWatched", 0)
    lines = [
        f"{scope}   {start} -> {end}  ({args.days}d)",
        f"views              {num(data.get('views'))}",
        f"watch time         {num(mins)} min  ({mins/60:.1f} h)" if mins else "watch time         -",
        f"avg view duration  {data.get('averageViewDuration', 0)}s"
        f"  ({data.get('averageViewPercentage', 0):.1f}% of video)",
        f"subs               +{data.get('subscribersGained', 0)} / -{data.get('subscribersLost', 0)}"
        f"  (net {data.get('subscribersGained', 0) - data.get('subscribersLost', 0):+d})",
        f"likes {data.get('likes', 0)}   comments {data.get('comments', 0)}   shares {data.get('shares', 0)}",
    ]
    if ctr:
        lines.append(f"impressions        {num(ctr.get('impressions'))}"
                     f"   CTR {ctr.get('impressionsClickThroughRate', 0):.2f}%")
    out(args, {"summary": data, "ctr": ctr}, lines)


def cmd_retention(args, cfg):
    """Audience retention curve - the number that actually decides a Short."""
    hdr = bearer(cfg)
    start, end = date_range(args.days)
    res = http(f"{ANALYTICS_API}/reports?" + urllib.parse.urlencode({
        "ids": "channel==MINE",
        "startDate": start,
        "endDate": end,
        "metrics": "audienceWatchRatio,relativeRetentionPerformance",
        "dimensions": "elapsedVideoTimeRatio",
        "filters": "video==" + args.video,
    }), headers=hdr)

    rows = res.get("rows") or []
    if not rows:
        out(args, res, ["no retention data (video too new, or too few views)"])
        return
    lines = [f"retention  video {args.video}  {start} -> {end}", ""]
    for ratio, watch, _rel in rows:
        if round(ratio * 100) % 5:  # one row per 5% of the video
            continue
        bar = "#" * int(round(watch * 40))
        lines.append(f"{ratio*100:5.0f}%  {watch*100:5.1f}%  {bar}")
    out(args, rows, lines)


def cmd_rank(args, cfg):
    """Every video's analytics side by side, in one call. avgView% is the
    column that matters - it is what the Shorts feed rewards."""
    hdr = bearer(cfg)
    start, end = date_range(args.days)
    res = http(f"{ANALYTICS_API}/reports?" + urllib.parse.urlencode({
        "ids": "channel==MINE", "startDate": start, "endDate": end,
        "metrics": "views,averageViewPercentage,averageViewDuration,subscribersGained",
        "dimensions": "video", "sort": "-views", "maxResults": args.n,
    }), headers=hdr)
    rows = res.get("rows") or []

    titles = {}
    if rows:
        auth, dhdr = data_auth(cfg)
        ids = [r[0] for r in rows]
        for i in range(0, len(ids), 50):
            det = http(f"{DATA_API}/videos?" + urllib.parse.urlencode(
                dict(auth, part="snippet,contentDetails", id=",".join(ids[i:i + 50]))),
                headers=dhdr)
            for v in det.get("items") or []:
                titles[v["id"]] = (v["snippet"]["title"],
                                   duration(v["contentDetails"].get("duration")))

    lines = [f"{start} -> {end}    views  avgView%   avgDur  subs  len  title", ""]
    for vid, views, avg_pct, avg_dur, subs in rows:
        title, length = titles.get(vid, ("?", "?"))
        lines.append(f"{vid}  {num(views):>7}  {avg_pct:6.1f}%  {avg_dur:5.0f}s  {subs:+4d}  "
                     f"{length:>5}  {title[:58]}")
    out(args, rows, lines)


def cmd_sources(args, cfg):
    """Traffic-source breakdown. Answers 'did the Shorts feed stop serving me',
    which view counts alone cannot."""
    hdr = bearer(cfg)
    start, end = date_range(args.days)
    params = {
        "ids": "channel==MINE", "startDate": start, "endDate": end,
        "metrics": "views,estimatedMinutesWatched",
        "dimensions": "insightTrafficSourceType",
        "sort": "-views",
    }
    if args.video:
        params["filters"] = "video==" + args.video
    res = http(f"{ANALYTICS_API}/reports?" + urllib.parse.urlencode(params), headers=hdr)
    rows = res.get("rows") or []
    total = sum(r[1] for r in rows) or 1
    scope = f"video {args.video}" if args.video else "channel"
    lines = [f"{scope}   {start} -> {end}", ""]
    for source, views, mins in rows:
        lines.append(f"{source:<26} {num(views):>7}  {100*views/total:5.1f}%   {num(mins):>6} min")
    out(args, rows, lines or ["no data"])


def cmd_upload(args, cfg):
    if not os.path.isfile(args.file):
        die(f"no such file: {args.file}")
    size = os.path.getsize(args.file)
    mime = mimetypes.guess_type(args.file)[0] or "video/*"

    snippet = {"title": args.title, "description": args.description or ""}
    if args.tags:
        snippet["tags"] = [t.strip() for t in args.tags.split(",") if t.strip()]
    if args.category:
        snippet["categoryId"] = args.category
    status = {"privacyStatus": args.privacy, "selfDeclaredMadeForKids": False}
    if args.publish_at:
        status["privacyStatus"] = "private"  # required for a scheduled release
        status["publishAt"] = args.publish_at

    hdr = bearer(cfg)
    init_url = f"{UPLOAD_API}/videos?" + urllib.parse.urlencode(
        {"uploadType": "resumable", "part": "snippet,status"})
    _, headers, _ = http(init_url, method="POST", body={"snippet": snippet, "status": status},
                         headers=dict(hdr, **{
                             "X-Upload-Content-Length": str(size),
                             "X-Upload-Content-Type": mime,
                         }), want_headers=True)
    session = headers.get("Location")
    if not session:
        die("YouTube did not return a resumable upload session URL")

    sent, video = 0, None
    with open(args.file, "rb") as fh:
        while sent < size:
            chunk = fh.read(CHUNK)
            last = sent + len(chunk)
            req = urllib.request.Request(session, data=chunk, method="PUT", headers={
                "Content-Length": str(len(chunk)),
                "Content-Range": f"bytes {sent}-{last-1}/{size}",
            })
            try:
                with urllib.request.urlopen(req) as resp:
                    body = resp.read()
                    if resp.status in (200, 201):
                        video = json.loads(body)
            except urllib.error.HTTPError as exc:
                if exc.code == 308:  # incomplete - server confirms what it has
                    rng = exc.headers.get("Range")
                    last = int(rng.split("-")[1]) + 1 if rng else last
                else:
                    detail = exc.read().decode(errors="replace")[:400]
                    die(f"upload failed at byte {sent} (HTTP {exc.code}): {detail}")
            sent = last
            pct = 100 * sent / size
            print(f"\ruploading  {pct:5.1f}%  ({sent/1e6:.1f}/{size/1e6:.1f} MB)",
                  end="", file=sys.stderr, flush=True)
    print("", file=sys.stderr)

    if not video:
        die("upload finished but YouTube returned no video resource")
    vid = video["id"]
    if args.thumbnail:
        set_thumbnail(cfg, vid, args.thumbnail)
    out(args, video, [
        f"uploaded  {vid}",
        f"https://youtu.be/{vid}",
        f"privacy   {video.get('status', {}).get('privacyStatus')}"
        + (f"  -> public at {args.publish_at}" if args.publish_at else ""),
    ])


def set_thumbnail(cfg, video_id, path):
    if not os.path.isfile(path):
        die(f"no such thumbnail: {path}")
    with open(path, "rb") as fh:
        blob = fh.read()
    mime = mimetypes.guess_type(path)[0] or "image/jpeg"
    http(f"{UPLOAD_API}/thumbnails/set?videoId={video_id}", method="POST", raw_body=blob,
         headers=dict(bearer(cfg), **{"Content-Type": mime, "Content-Length": str(len(blob))}))
    return True


def cmd_thumbnail(args, cfg):
    set_thumbnail(cfg, args.video_id, args.file)
    print(f"thumbnail set on {args.video_id}")


def cmd_update(args, cfg):
    hdr = bearer(cfg)
    key = cfg.get("api_key")
    # A videos.update replaces the whole snippet, so read the current one first.
    lookup = {"part": "snippet,status", "id": args.video_id}
    if key:
        lookup["key"] = key
    current = http(f"{DATA_API}/videos?" + urllib.parse.urlencode(lookup), headers=hdr)
    items = current.get("items") or []
    if not items:
        die(f"no video {args.video_id}")
    snippet = items[0]["snippet"]
    status = items[0]["status"]

    changed = []
    if args.title:
        snippet["title"] = args.title
        changed.append("title")
    if args.description:
        snippet["description"] = args.description
        changed.append("description")
    if args.tags:
        snippet["tags"] = [t.strip() for t in args.tags.split(",") if t.strip()]
        changed.append("tags")
    if args.privacy:
        status["privacyStatus"] = args.privacy
        changed.append("privacy")
    if args.thumbnail:
        set_thumbnail(cfg, args.video_id, args.thumbnail)
        changed.append("thumbnail")
    if not changed:
        die("nothing to update - pass --title / --description / --tags / --privacy / --thumbnail")

    if changed != ["thumbnail"]:
        snippet.pop("thumbnails", None)
        http(f"{DATA_API}/videos?part=snippet,status", method="PUT", headers=hdr,
             body={"id": args.video_id, "snippet": snippet, "status": status})
    print(f"updated {args.video_id}: {', '.join(changed)}")


# --------------------------------------------------------------------------
# setup
# --------------------------------------------------------------------------

def cmd_setup(args, cfg):
    have = lambda k: "set" if cfg.get(k) else "MISSING"
    print(f"""
YouTube setup - current state
  api_key        {have('api_key')}
  client_id      {have('client_id')}
  client_secret  {have('client_secret')}
  refresh_token  {have('refresh_token')}
  channel_id     {cfg.get('channel_id') or 'MISSING'}

  config file    {CONFIG_PATH}

TIER 1 - read public stats (2 minutes)
  1. https://console.cloud.google.com/projectcreate  -> create a project
  2. APIs & Services > Library > enable "YouTube Data API v3"
  3. APIs & Services > Credentials > Create credentials > API key
  4. export YT_API_KEY=...   and   export YT_CHANNEL_ID=@yourhandle

TIER 2 - analytics + uploading (10 minutes, needs Tier 1's project)
  1. Enable "YouTube Analytics API" in the same project's Library
  2. APIs & Services > OAuth consent screen: External, add your own Google
     account under Test users. Publishing the app is not required.
  3. Credentials > Create credentials > OAuth client ID > Desktop app
  4. export YT_CLIENT_ID=...   export YT_CLIENT_SECRET=...
  5. python3 tools/youtube/yt.py auth

To persist across Claude sessions, put those exports in the Claude
environment's variables rather than this container - the container is wiped
when the session ends.
""".strip())


# --------------------------------------------------------------------------
# cli
# --------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(prog="yt.py", description="YouTube channel CLI (stdlib only)")
    p.add_argument("--json", action="store_true", help="emit raw API JSON")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add(name, fn, help_text):
        sp = sub.add_parser(name, help=help_text)
        sp.set_defaults(fn=fn)
        return sp

    add("setup", cmd_setup, "print credential status and setup steps")

    sp = add("auth", cmd_auth, "run the OAuth flow, print a refresh token")
    sp.add_argument("--url", action="store_true",
                    help="just print the authorization URL and exit")
    sp.add_argument("--code", help="redirect URL or bare code, for a non-interactive exchange")
    sp.add_argument("--readonly", action="store_true",
                    help="mint a token that can read stats but not upload, edit or delete")
    sp.add_argument("--no-browser", action="store_true")

    sp = add("handle", cmd_handle, "resolve a @handle or URL to a UC... id")
    sp.add_argument("--channel")

    sp = add("latest", cmd_latest, "latest uploads via RSS (no credentials, no quota)")
    sp.add_argument("--channel")
    sp.add_argument("-n", type=int, default=15)

    sp = add("channel", cmd_channel, "channel stats")
    sp.add_argument("--channel")

    sp = add("videos", cmd_videos, "list uploads with view/like/comment counts")
    sp.add_argument("--channel")
    sp.add_argument("-n", type=int, default=25)

    sp = add("video", cmd_video, "one video in detail")
    sp.add_argument("video_id")

    sp = add("comments", cmd_comments, "recent comments on a video or the channel")
    sp.add_argument("video_id", nargs="?")
    sp.add_argument("--channel")
    sp.add_argument("-n", type=int, default=25)
    sp.add_argument("--order", default="time", choices=["time", "relevance"])

    sp = add("search", cmd_search, "topic/competitor search (100 quota units)")
    sp.add_argument("query")
    sp.add_argument("-n", type=int, default=20)
    sp.add_argument("--days", type=int, help="only videos from the last N days")
    sp.add_argument("--shorts", action="store_true", help="under 4 minutes only")
    sp.add_argument("--order", default="viewCount",
                    choices=["viewCount", "date", "relevance", "rating"])

    sp = add("analytics", cmd_analytics, "views, watch time, CTR, subs (OAuth)")
    sp.add_argument("--days", type=int, default=28)
    sp.add_argument("--video", help="scope to one video")

    sp = add("retention", cmd_retention, "audience retention curve for a video (OAuth)")
    sp.add_argument("video")
    sp.add_argument("--days", type=int, default=90)

    sp = add("rank", cmd_rank, "all videos ranked, with retention % (OAuth)")
    sp.add_argument("--days", type=int, default=90)
    sp.add_argument("-n", type=int, default=50)

    sp = add("sources", cmd_sources, "traffic-source breakdown (OAuth)")
    sp.add_argument("--days", type=int, default=28)
    sp.add_argument("--video", help="scope to one video")

    sp = add("upload", cmd_upload, "upload a video (OAuth)")
    sp.add_argument("file")
    sp.add_argument("--title", required=True)
    sp.add_argument("--description", "--desc", dest="description")
    sp.add_argument("--tags", help="comma separated")
    sp.add_argument("--category", default="25", help="25 = News & Politics, 22 = People & Blogs")
    sp.add_argument("--privacy", default="private", choices=["private", "unlisted", "public"])
    sp.add_argument("--publish-at", help="RFC3339, e.g. 2026-08-12T17:00:00Z")
    sp.add_argument("--thumbnail")

    sp = add("update", cmd_update, "change title/description/tags/privacy/thumbnail (OAuth)")
    sp.add_argument("video_id")
    sp.add_argument("--title")
    sp.add_argument("--description", "--desc", dest="description")
    sp.add_argument("--tags")
    sp.add_argument("--privacy", choices=["private", "unlisted", "public"])
    sp.add_argument("--thumbnail")

    sp = add("thumbnail", cmd_thumbnail, "set a thumbnail (OAuth)")
    sp.add_argument("video_id")
    sp.add_argument("file")

    args = p.parse_args()
    try:
        args.fn(args, load_config())
    except KeyboardInterrupt:
        sys.exit(130)
    except BrokenPipeError:
        sys.exit(0)


if __name__ == "__main__":
    main()
