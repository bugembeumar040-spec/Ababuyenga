"""Shared YouTube Data API helper. Auth via refresh token in env."""
import json, os, urllib.request, urllib.error, urllib.parse

SCOPE = "https://www.googleapis.com/auth/youtube.force-ssl"
BASE = "https://www.googleapis.com/youtube/v3"
UPLOAD = "https://www.googleapis.com/upload/youtube/v3"
_cache = {}


def _post(url, fields):
    data = urllib.parse.urlencode(fields).encode()
    with urllib.request.urlopen(urllib.request.Request(url, data)) as r:
        return json.load(r)


def access_token():
    """Exchange the long-lived refresh token for a 1-hour access token.

    YT_ACCESS_TOKEN short-circuits this, for a one-off run with a token
    pasted straight from the OAuth Playground.
    """
    if "tok" in _cache:
        return _cache["tok"]
    direct = os.environ.get("YT_ACCESS_TOKEN", "").strip()
    if direct:
        _cache["tok"] = direct
        return direct
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


def api(path, method="GET", params=None, body=None, raw=None, ctype=None,
        upload=False):
    # Media goes to the /upload/ host path; the plain endpoint
    # rejects it with mediaBodyRequired.
    url = f"{UPLOAD if upload else BASE}/{path}"
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
        raise ApiError(e.code, method, path, e.read().decode())


class ApiError(Exception):
    def __init__(self, code, method, path, body):
        self.code, self.body = code, body
        try:
            errs = json.loads(body)["error"].get("errors", [])
            self.reason = errs[0].get("reason", "") if errs else ""
        except Exception:
            self.reason = ""
        super().__init__(f"HTTP {code} {method} {path}\n{body[:500]}")
