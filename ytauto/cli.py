"""Command line entry point:  python -m ytauto <command>"""

from __future__ import annotations

import argparse
import json
import sys

from googleapiclient.errors import HttpError

from . import analytics as analytics_mod
from . import auth, config, metadata, upload as upload_mod

STUDIO = "https://studio.youtube.com/video/{id}/edit"
WATCH = "https://www.youtube.com/watch?v={id}"


def _err(msg: str) -> None:
    print(msg, file=sys.stderr)


def _http_error_hint(exc: HttpError) -> str:
    """Turn Google's JSON error into something actionable."""
    try:
        detail = json.loads(exc.content.decode())["error"]
        reason = (detail.get("errors") or [{}])[0].get("reason", "")
        message = detail.get("message", "")
    except Exception:
        return str(exc)

    hints = {
        "quotaExceeded": (
            "Daily quota (10,000 units) is spent. An upload costs 1,600, so the "
            "ceiling is ~6 uploads/day. Resets at midnight Pacific."
        ),
        "uploadLimitExceeded": "This channel hit its daily upload cap. Try tomorrow.",
        "forbidden": (
            "The authorised account may not own this channel. If the channel is "
            "a Brand Account, re-run login and pick it on the consent screen."
        ),
        "youtubeSignupRequired": "That Google account has no YouTube channel attached.",
        "invalidCategoryId": "category_id is not valid in this region.",
        "invalidVideoMetadata": "YouTube rejected the metadata — check title and description.",
        "mediaBodyRequired": "No video file was attached to the request.",
        "failedPrecondition": (
            "Thumbnail rejected. Custom thumbnails require a verified (phone-"
            "confirmed) YouTube account."
        ),
    }
    hint = hints.get(reason, "")
    text = f"{reason or 'error'}: {message}" if message else str(exc)
    return f"{text}\n\n{hint}" if hint else text


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------

def cmd_login(args) -> int:
    try:
        creds = auth.login(force=args.force)
    except auth.AuthError as exc:
        _err(str(exc))
        return 1
    print(f"Authorised. Token stored at {config.token_path()}")
    try:
        info = upload_mod.channel_info(upload_mod.youtube(creds))
        print(f"Channel: {info['snippet']['title']}  ({info['id']})")
    except Exception as exc:  # channel lookup is a nicety, not the point
        _err(f"(could not read channel: {exc})")
    return 0


def cmd_whoami(args) -> int:
    creds = auth.load()
    missing = auth.scopes_missing(creds)
    if missing:
        _err("Token is missing scopes: " + ", ".join(missing))
        _err("Run:  python -m ytauto login --force")
        return 1
    info = upload_mod.channel_info(upload_mod.youtube(creds))
    stats = info.get("statistics", {})
    print(f"Channel : {info['snippet']['title']}")
    print(f"ID      : {info['id']}")
    print(f"Videos  : {stats.get('videoCount', '?')}")
    print(f"Subs    : {stats.get('subscriberCount', '?')}")
    print(f"Views   : {stats.get('viewCount', '?')}")
    return 0


def _report(meta: metadata.VideoMeta) -> tuple[list[str], list[str]]:
    errors, warnings = metadata.validate(meta)

    print(f"Title       {meta.title}  ({len(meta.title)}/{config.MAX_TITLE})")
    print(f"Description {len(meta.description)}/{config.MAX_DESCRIPTION} chars")
    print(
        f"Tags        {len(meta.tags)} tags, "
        f"{metadata.tags_length(meta.tags)}/{config.MAX_TAGS_TOTAL} chars"
    )
    print(f"Category    {meta.category_id}")
    print(f"Privacy     {meta.privacy}" + (f"  (publish at {meta.publish_at})" if meta.publish_at else ""))
    print(f"Kids        {meta.made_for_kids}")
    if meta.video_file:
        size = meta.video_file.stat().st_size / 1024 / 1024 if meta.video_file.exists() else 0
        print(f"Video       {meta.video_file}  ({size:.1f} MB)")
    print(f"Thumbnail   {meta.thumbnail or '-'}")
    print(f"Playlist    {meta.playlist_id or '-'}")

    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(f"  ! {w}")
    if errors:
        print("\nErrors:")
        for e in errors:
            print(f"  x {e}")
    return errors, warnings


def cmd_validate(args) -> int:
    meta = metadata.load(args.sidecar)
    errors, _ = _report(meta)
    if errors:
        return 2
    print("\nValid.")
    return 0


def cmd_upload(args) -> int:
    meta = metadata.load(args.sidecar)
    errors, _ = _report(meta)
    if errors:
        _err("\nRefusing to upload — fix the errors above.")
        return 2

    if args.dry_run:
        print("\nDry run — nothing uploaded.")
        return 0

    if not args.yes:
        answer = input("\nUpload this? [y/N] ").strip().lower()
        if answer not in {"y", "yes"}:
            print("Aborted.")
            return 1

    creds = auth.load()
    service = upload_mod.youtube(creds)

    last = -1

    def progress(pct: int) -> None:
        nonlocal last
        if pct != last:
            print(f"\r  uploading… {pct:3d}%", end="", flush=True)
            last = pct

    try:
        video_id = upload_mod.upload_video(service, meta, on_progress=progress)
        print()
        print(f"Uploaded: {WATCH.format(id=video_id)}")

        if meta.thumbnail:
            try:
                upload_mod.set_thumbnail(service, video_id, meta.thumbnail)
                print("Thumbnail set.")
            except HttpError as exc:
                _err("Thumbnail failed: " + _http_error_hint(exc))

        if meta.playlist_id:
            try:
                upload_mod.add_to_playlist(service, video_id, meta.playlist_id)
                print(f"Added to playlist {meta.playlist_id}.")
            except HttpError as exc:
                _err("Playlist insert failed: " + _http_error_hint(exc))

    except HttpError as exc:
        print()
        _err("Upload failed: " + _http_error_hint(exc))
        return 1

    print(f"\nFinish in Studio: {STUDIO.format(id=video_id)}")
    print(
        "The video is private. If your API project has not passed a YouTube "
        "compliance audit, publish it from Studio rather than via the API."
    )
    return 0


def cmd_publish(args) -> int:
    creds = auth.load()
    service = upload_mod.youtube(creds)
    try:
        result = upload_mod.set_privacy(service, args.video_id, args.privacy)
    except HttpError as exc:
        _err("Publish failed: " + _http_error_hint(exc))
        return 1
    status = result.get("status", {}).get("privacyStatus")
    print(f"{args.video_id} is now {status}")
    if status != args.privacy:
        _err(
            f"Requested {args.privacy} but YouTube reports {status}. A video "
            "locked private by an unaudited API project cannot be unlocked."
        )
        return 1
    return 0


def cmd_stats(args) -> int:
    creds = auth.load()
    service = upload_mod.youtube(creds)
    rows = analytics_mod.recent_uploads(service, limit=args.limit)
    if not rows:
        print("No uploads found.")
        return 0

    ret: dict = {}
    try:
        ret = analytics_mod.retention(
            upload_mod.analytics(creds), [r["id"] for r in rows], days=args.days
        )
    except HttpError as exc:
        _err("(retention unavailable: " + _http_error_hint(exc) + ")")

    print(
        f"{'published':11}  {'views':>7}  {'avg%':>5}  {'subs':>5}  "
        f"{'privacy':8}  title"
    )
    for r in rows:
        a = ret.get(r["id"], {})
        avg = a.get("averageViewPercentage")
        subs = a.get("subscribersGained")
        print(
            f"{r['published_at'][:10]:11}  {r['views']:>7}  "
            f"{(f'{avg:.0f}' if avg is not None else '-'):>5}  "
            f"{(f'{subs:.0f}' if subs is not None else '-'):>5}  "
            f"{r['privacy']:8}  {r['title'][:52]}"
        )
    print(f"\navg% and subs are the trailing {args.days} days (Analytics lags ~2-3 days).")
    return 0


# --------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ytauto", description="YouTube upload automation (local)."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("login", help="authorise once in the browser")
    p.add_argument("--force", action="store_true", help="replace an existing token")
    p.set_defaults(func=cmd_login)

    p = sub.add_parser("whoami", help="show the authorised channel")
    p.set_defaults(func=cmd_whoami)

    p = sub.add_parser("validate", help="check a sidecar without uploading")
    p.add_argument("sidecar")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("upload", help="upload the video described by a sidecar")
    p.add_argument("sidecar")
    p.add_argument("--dry-run", action="store_true", help="validate and stop")
    p.add_argument("--yes", "-y", action="store_true", help="skip confirmation")
    p.set_defaults(func=cmd_upload)

    p = sub.add_parser("publish", help="change an existing video's privacy")
    p.add_argument("video_id")
    p.add_argument("--privacy", default="public", choices=sorted(metadata.VALID_PRIVACY))
    p.set_defaults(func=cmd_publish)

    p = sub.add_parser("stats", help="recent uploads with views and retention")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--days", type=int, default=28)
    p.set_defaults(func=cmd_stats)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except auth.AuthError as exc:
        _err(str(exc))
        return 1
    except (FileNotFoundError, ValueError) as exc:
        _err(str(exc))
        return 2
    except KeyboardInterrupt:
        _err("\nInterrupted.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
