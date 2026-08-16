"""OAuth: turn a client ID + secret into a stored, refreshable credential.

The browser step happens once, on your machine. After that every command
refreshes silently from token.json.
"""

from __future__ import annotations

import json
import os
import stat
import sys
from pathlib import Path

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from . import config


class AuthError(RuntimeError):
    """Raised with a message that tells the user exactly what to do next."""


def _client_config() -> dict:
    """Build an installed-app client config from env vars, if both are set."""
    client_id = os.environ.get("YTAUTO_CLIENT_ID")
    client_secret = os.environ.get("YTAUTO_CLIENT_SECRET")
    if not (client_id and client_secret):
        return {}
    return {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }


def _write_token(creds: Credentials) -> None:
    path = config.token_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(creds.to_json())
    # Owner read/write only. This file is a bearer credential for your channel.
    path.chmod(stat.S_IRUSR | stat.S_IWUSR)


def login(force: bool = False) -> Credentials:
    """Run the browser consent flow and store the resulting refresh token."""
    token = config.token_path()
    if token.exists() and not force:
        raise AuthError(
            f"Already logged in ({token}). Re-run with --force to replace it."
        )

    inline = _client_config()
    secrets = config.client_secrets_path()
    if inline:
        flow = InstalledAppFlow.from_client_config(inline, config.SCOPES)
    elif secrets.exists():
        flow = InstalledAppFlow.from_client_secrets_file(str(secrets), config.SCOPES)
    else:
        raise AuthError(
            "No OAuth client found. Either:\n"
            f"  - save the JSON you downloaded from Google Cloud to {secrets}, or\n"
            "  - export YTAUTO_CLIENT_ID and YTAUTO_CLIENT_SECRET\n"
            "The OAuth client must be of type 'Desktop app'."
        )

    # access_type=offline + prompt=consent is what actually returns a refresh
    # token. Without prompt=consent Google omits it on re-authorisation.
    creds = flow.run_local_server(
        port=0,
        access_type="offline",
        prompt="consent",
        authorization_prompt_message="Opening your browser to authorise. If it "
        "does not open, visit:\n{url}",
        success_message="Authorised. You can close this tab and return to the terminal.",
    )
    _write_token(creds)
    return creds


def load() -> Credentials:
    """Load stored credentials, refreshing the access token when stale."""
    token = config.token_path()
    if not token.exists():
        raise AuthError(f"Not logged in. Run:  python -m ytauto login")

    try:
        creds = Credentials.from_authorized_user_file(str(token), config.SCOPES)
    except ValueError as exc:
        raise AuthError(f"{token} is not readable as a credential: {exc}") from exc

    if creds.valid:
        return creds

    if not creds.refresh_token:
        raise AuthError(
            "Stored credential has no refresh token. Run:  python -m ytauto login --force"
        )

    try:
        creds.refresh(Request())
    except RefreshError as exc:
        raise AuthError(
            f"Refresh failed ({exc}).\n\n"
            "The usual cause: your OAuth consent screen is still in 'Testing', "
            "which expires refresh tokens after 7 days.\n"
            "Fix it once in Google Cloud Console > APIs & Services > OAuth "
            "consent screen > Publish app, then run:\n"
            "  python -m ytauto login --force"
        ) from exc

    _write_token(creds)
    return creds


def scopes_missing(creds: Credentials) -> list[str]:
    """Scopes the stored token lacks — a stale token predating a scope change."""
    granted = set(creds.scopes or [])
    return [s for s in config.SCOPES if s not in granted]
