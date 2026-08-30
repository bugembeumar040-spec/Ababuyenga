"""Shared YouTube Data API helper. Auth via refresh token in env."""
import json, os, urllib.request, urllib.error, urllib.parse

SCOPE = "https://www.googleapis.com/auth/youtube.force-ssl"
BASE = "https://www.googleapis.com/youtube/v3"
_cache = {}


def _post(url, fields):
    data = urllib.parse.urlencode(fields).encode()
    with urllib.request.urlopen(urllib.request.Request(url, data)) as r:
        return json.load(r)


def access_token():
    """Exchange the long-lived refresh token for a 1-hour access token."""
    if "tok" in _cache:
        return _cache["tok"]
    need = ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN")
    miss = [n for n in need if not os.environ.get(n)]
    if miss:
        raise SystemExit(f"Missing env: {', '.join(miss)}. See youtube/README.md")
    r = _post("https://oauth2.googleapis.com/token", {
        "client_id": os.environ["YT_CLIENT_ID"],
        "client_secret": os.environ["YT_CLIENT_SECRET"],
        "refresh_token": os.environ["YT_REFRESH_TOKEN"],
        "grant_type": "refresh_token"})
    _cache["tok"] = r["access_token"]
    return _cache["tok"]


def api(path, method="GET", params=None, body=None, raw=None, ctype=None):
    url = f"{BASE}/{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"Bearer {access_token()}")
    data = raw
    if body is not None:
        data = json.dumps(body).encode()
        req.add_header("Content-Type", "application/json")
    elif raw is not None:
        req.add_header("Content-Type", ctype or "application/octet-stream")
    try:
        with urllib.request.urlopen(req, data) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"HTTP {e.code} {method} {path}\n{e.read().decode()[:500]}")
