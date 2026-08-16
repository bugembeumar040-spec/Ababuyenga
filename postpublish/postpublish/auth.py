"""OAuth token handling for the YouTube Data API.

Credentials come from the environment, never from a file in the repo:

    YT_CLIENT_ID
    YT_CLIENT_SECRET
    YT_REFRESH_TOKEN

The refresh token must have been minted with a scope that permits writes
(https://www.googleapis.com/auth/youtube or .../youtube.force-ssl). A
read-only token will authenticate fine and then fail on the first mutation,
so check_write_scope() is called before any run that intends to write.
"""

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

TOKEN_URL = "https://oauth2.googleapis.com/token"
TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"

WRITE_SCOPES = {
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/youtubepartner",
}

REQUIRED_ENV = ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN")


class AuthError(RuntimeError):
    pass


class Credentials:
    """Caches an access token in memory and refreshes it when it expires."""

    def __init__(self, client_id, client_secret, refresh_token):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self._access_token = None
        self._expires_at = 0.0
        self._scopes = frozenset()

    @classmethod
    def from_env(cls, env=None):
        env = os.environ if env is None else env
        missing = [k for k in REQUIRED_ENV if not env.get(k)]
        if missing:
            raise AuthError(
                "missing credentials in environment: %s" % ", ".join(missing)
            )
        return cls(
            env["YT_CLIENT_ID"], env["YT_CLIENT_SECRET"], env["YT_REFRESH_TOKEN"]
        )

    def _refresh(self):
        body = urllib.parse.urlencode(
            {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
                "grant_type": "refresh_token",
            }
        ).encode()
        req = urllib.request.Request(TOKEN_URL, data=body)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = json.load(resp)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:400]
            raise AuthError("token refresh failed (%s): %s" % (exc.code, detail))
        self._access_token = payload["access_token"]
        # Refresh a minute early so a long call cannot straddle the expiry.
        self._expires_at = time.time() + float(payload.get("expires_in", 3600)) - 60
        self._scopes = frozenset(payload.get("scope", "").split())

    def token(self):
        if self._access_token is None or time.time() >= self._expires_at:
            self._refresh()
        return self._access_token

    def scopes(self):
        self.token()
        return set(self._scopes)

    def check_write_scope(self):
        """Raise unless the token can actually mutate the channel."""
        granted = self.scopes()
        if not (granted & WRITE_SCOPES):
            raise AuthError(
                "refresh token lacks a write scope. Has: %s. Needs one of: %s"
                % (sorted(granted) or ["<none reported>"], sorted(WRITE_SCOPES))
            )
