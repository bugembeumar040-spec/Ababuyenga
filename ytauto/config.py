"""Paths, scopes and shared constants.

Credentials live outside the repo by default because this repository is public.
Override the location with YTAUTO_HOME if you keep them elsewhere.
"""

from __future__ import annotations

import os
from pathlib import Path

# Scopes:
#   youtube.upload           videos.insert
#   youtube                  thumbnails.set, playlistItems.insert, videos.update
#   yt-analytics.readonly    reports.query (retention / watch time)
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]

# YouTube-enforced limits. Exceeding these is rejected server-side, and the tags
# limit in particular fails *silently* (tags are dropped, upload succeeds).
MAX_TITLE = 100
MAX_DESCRIPTION = 5000
MAX_TAGS_TOTAL = 500
MAX_THUMBNAIL_BYTES = 2 * 1024 * 1024

# videos.insert costs 1600 quota units against a default 10,000/day allowance.
UPLOAD_QUOTA_COST = 1600
DEFAULT_DAILY_QUOTA = 10000


def home() -> Path:
    """Directory holding client_secrets.json and token.json."""
    env = os.environ.get("YTAUTO_HOME")
    if env:
        return Path(env).expanduser()
    return Path.home() / ".config" / "ytauto"


def client_secrets_path() -> Path:
    return home() / "client_secrets.json"


def token_path() -> Path:
    return home() / "token.json"
