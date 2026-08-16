"""Sidecar YAML -> validated upload metadata.

Validation runs before a single byte is uploaded. videos.insert costs 1600 of
your 10,000 daily quota units, so a rejected upload is expensive; and the tags
limit fails silently server-side, which is worse than an error.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from . import config

VALID_PRIVACY = {"private", "unlisted", "public"}


def tags_length(tags: list[str]) -> int:
    """Conservative reproduction of YouTube's 500-character tag budget.

    YouTube counts the serialised list: tags containing a space are wrapped in
    quotes and those quotes count, plus one separator between tags. Being
    conservative here is deliberate — going over silently drops every tag.
    """
    if not tags:
        return 0
    return sum(len(t) + (2 if " " in t else 0) for t in tags) + len(tags) - 1


@dataclass
class VideoMeta:
    video_file: Path
    title: str
    description: str
    tags: list[str] = field(default_factory=list)
    category_id: str = "27"  # 27 = Education
    privacy: str = "private"
    publish_at: str | None = None
    made_for_kids: bool = False
    language: str = "en"
    thumbnail: Path | None = None
    playlist_id: str | None = None
    recording_date: str | None = None

    def to_body(self) -> dict:
        """The videos.insert request body."""
        status: dict = {
            "privacyStatus": self.privacy,
            "selfDeclaredMadeForKids": self.made_for_kids,
        }
        if self.publish_at:
            status["publishAt"] = self.publish_at
        snippet: dict = {
            "title": self.title,
            "description": self.description,
            "tags": self.tags,
            "categoryId": str(self.category_id),
            "defaultLanguage": self.language,
            "defaultAudioLanguage": self.language,
        }
        body: dict = {"snippet": snippet, "status": status}
        if self.recording_date:
            body["recordingDetails"] = {"recordingDate": self.recording_date}
        return body


def load(path: str | Path) -> VideoMeta:
    """Read a sidecar file. Relative paths resolve against the sidecar itself."""
    path = Path(path)
    raw = yaml.safe_load(path.read_text()) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: expected a YAML mapping at the top level")

    base = path.parent

    def resolve(value):
        if value in (None, ""):
            return None
        p = Path(str(value)).expanduser()
        return p if p.is_absolute() else (base / p)

    known = {
        "video_file", "title", "description", "tags", "category_id", "privacy",
        "publish_at", "made_for_kids", "language", "thumbnail", "playlist_id",
        "recording_date",
    }
    unknown = set(raw) - known
    if unknown:
        raise ValueError(f"{path}: unknown key(s): {', '.join(sorted(unknown))}")

    if "video_file" not in raw:
        raise ValueError(f"{path}: 'video_file' is required")

    tags = raw.get("tags") or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]

    return VideoMeta(
        video_file=resolve(raw.get("video_file")),
        title=str(raw.get("title", "")).strip(),
        description=str(raw.get("description", "")),
        tags=[str(t).strip() for t in tags],
        category_id=str(raw.get("category_id", "27")),
        privacy=str(raw.get("privacy", "private")).lower(),
        publish_at=raw.get("publish_at"),
        made_for_kids=bool(raw.get("made_for_kids", False)),
        language=str(raw.get("language", "en")),
        thumbnail=resolve(raw.get("thumbnail")),
        playlist_id=raw.get("playlist_id"),
        recording_date=raw.get("recording_date"),
    )


def _parse_rfc3339(value: str) -> dt.datetime:
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    stamp = dt.datetime.fromisoformat(text)
    if stamp.tzinfo is None:
        raise ValueError("missing timezone offset")
    return stamp


def validate(meta: VideoMeta) -> tuple[list[str], list[str]]:
    """Return (errors, warnings). Errors block the upload; warnings do not."""
    errors: list[str] = []
    warnings: list[str] = []

    # --- video file -------------------------------------------------------
    if not meta.video_file:
        errors.append("video_file is required")
    elif not meta.video_file.exists():
        errors.append(f"video_file not found: {meta.video_file}")
    elif meta.video_file.stat().st_size == 0:
        errors.append(f"video_file is empty: {meta.video_file}")

    # --- title ------------------------------------------------------------
    if not meta.title:
        errors.append("title is required")
    else:
        if len(meta.title) > config.MAX_TITLE:
            errors.append(
                f"title is {len(meta.title)} chars, limit is {config.MAX_TITLE}"
            )
        if "<" in meta.title or ">" in meta.title:
            errors.append("title cannot contain < or > (YouTube rejects them)")

    # --- description ------------------------------------------------------
    if len(meta.description) > config.MAX_DESCRIPTION:
        errors.append(
            f"description is {len(meta.description)} chars, "
            f"limit is {config.MAX_DESCRIPTION}"
        )
    if "<" in meta.description or ">" in meta.description:
        errors.append("description cannot contain < or >")
    if len(meta.description) < 600:
        warnings.append(
            f"description is {len(meta.description)} chars; the channel slate "
            "calls for 600+"
        )

    # --- tags -------------------------------------------------------------
    total = tags_length(meta.tags)
    if total > config.MAX_TAGS_TOTAL:
        errors.append(
            f"tags total {total} chars, limit is {config.MAX_TAGS_TOTAL}. "
            "Over the limit YouTube drops the tags without reporting an error."
        )
    elif total > config.MAX_TAGS_TOTAL - 40:
        warnings.append(f"tags total {total} chars, close to the {config.MAX_TAGS_TOTAL} limit")

    # --- privacy / scheduling --------------------------------------------
    if meta.privacy not in VALID_PRIVACY:
        errors.append(
            f"privacy must be one of {sorted(VALID_PRIVACY)}, got {meta.privacy!r}"
        )

    if meta.publish_at:
        if meta.privacy != "private":
            errors.append("publish_at requires privacy: private")
        try:
            when = _parse_rfc3339(meta.publish_at)
        except ValueError as exc:
            errors.append(
                f"publish_at is not RFC3339 ({exc}). Example: 2026-08-20T18:00:00Z"
            )
        else:
            if when <= dt.datetime.now(dt.timezone.utc):
                errors.append(f"publish_at is in the past: {meta.publish_at}")
        warnings.append(
            "publish_at only takes effect once your API project has passed a "
            "YouTube compliance audit. Until then the upload stays locked private."
        )

    if meta.privacy == "public":
        warnings.append(
            "privacy: public is ignored by an unaudited API project — the video "
            "is locked private on YouTube's side and cannot be unlocked. "
            "Upload private, then publish from YouTube Studio."
        )

    # --- thumbnail --------------------------------------------------------
    if meta.thumbnail:
        if not meta.thumbnail.exists():
            errors.append(f"thumbnail not found: {meta.thumbnail}")
        else:
            size = meta.thumbnail.stat().st_size
            if size > config.MAX_THUMBNAIL_BYTES:
                errors.append(
                    f"thumbnail is {size / 1024 / 1024:.1f} MB, limit is 2 MB"
                )
            if meta.thumbnail.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
                errors.append(f"thumbnail must be .jpg or .png: {meta.thumbnail.name}")

    # --- misc -------------------------------------------------------------
    if not str(meta.category_id).isdigit():
        errors.append(f"category_id must be numeric, got {meta.category_id!r}")

    if meta.recording_date:
        try:
            _parse_rfc3339(meta.recording_date)
        except ValueError as exc:
            errors.append(f"recording_date is not RFC3339 ({exc})")

    if meta.playlist_id and not str(meta.playlist_id).startswith(("PL", "UU", "LL", "FL")):
        warnings.append(
            f"playlist_id {meta.playlist_id!r} does not look like a playlist ID "
            "(these usually start with PL)"
        )

    return errors, warnings
