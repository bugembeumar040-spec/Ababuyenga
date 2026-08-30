#!/usr/bin/env python3
"""ONE-TIME. Run locally. Produces the refresh token for GitHub Secrets.

    python3 youtube/auth.py <CLIENT_ID> <CLIENT_SECRET>

Opens Google's consent screen, catches the redirect on localhost, and
prints a refresh token that does not expire. Nothing is written to disk.
"""
import sys, json, urllib.parse, urllib.request, webbrowser, http.server, threading
from yt import SCOPE

PORT = 8731
REDIRECT = f"http://localhost:{PORT}"
code = {}


class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        code.update({k: v[0] for k, v in q.items()})
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        ok = "code" in q
        self.wfile.write(b"<h2>Done - return to your terminal.</h2>" if ok
                         else b"<h2>Denied. Re-run auth.py.</h2>")

    def log_message(self, *a):
        pass


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    cid, secret = sys.argv[1], sys.argv[2]
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
        "client_id": cid, "redirect_uri": REDIRECT, "response_type": "code",
        "scope": SCOPE, "access_type": "offline", "prompt": "consent"})

    srv = http.server.HTTPServer(("localhost", PORT), H)
    threading.Thread(target=srv.handle_request, daemon=True).start()
    print(f"\nSign in as the OWNER of the channel:\n\n{url}\n")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    while "code" not in code and "error" not in code:
        pass
    srv.server_close()
    if "error" in code:
        raise SystemExit(f"Consent denied: {code['error']}")

    data = urllib.parse.urlencode({
        "code": code["code"], "client_id": cid, "client_secret": secret,
        "redirect_uri": REDIRECT, "grant_type": "authorization_code"}).encode()
    with urllib.request.urlopen(
            urllib.request.Request("https://oauth2.googleapis.com/token", data)) as r:
        tok = json.load(r)

    rt = tok.get("refresh_token")
    if not rt:
        raise SystemExit("No refresh_token returned. Revoke prior access and retry.")
    print("=" * 62)
    print("Add these three as GitHub repo secrets:\n")
    print(f"  YT_CLIENT_ID      {cid}")
    print(f"  YT_CLIENT_SECRET  {secret}")
    print(f"  YT_REFRESH_TOKEN  {rt}")
    print("=" * 62)


if __name__ == "__main__":
    main()
