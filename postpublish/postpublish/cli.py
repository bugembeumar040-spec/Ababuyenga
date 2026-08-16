"""Command line entry point.

    python -m postpublish audit    <videoId> [--json] [--no-playlists]
    python -m postpublish init     <videoId>
    python -m postpublish validate <videoId>
    python -m postpublish apply    <videoId> [--apply]

`audit` and `validate` are read-only. `apply` is a dry run unless you pass
--apply, and even then it refuses to run against a pack that does not
validate.
"""

import argparse
import os
import sys

from . import audit as auditlib
from . import pack as packlib
from . import rules
from .api import ApiError, YouTube
from .auth import AuthError, Credentials

PACKS_DIR = os.environ.get(
    "POSTPUBLISH_PACKS",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "packs"),
)


def pack_path(video_id):
    return os.path.join(PACKS_DIR, video_id, "pack.json")


def _client():
    return YouTube(Credentials.from_env())


def cmd_audit(args):
    yt = _client()
    ctx = auditlib.build_context(yt, args.video_id,
                                 check_playlists=not args.no_playlists)
    findings = auditlib.run(ctx)
    if args.json:
        print(auditlib.to_json(ctx, findings))
    else:
        print(auditlib.format_report(ctx, findings))
    return 0


def cmd_init(args):
    path = pack_path(args.video_id)
    if os.path.exists(path) and not args.force:
        print("pack already exists: %s (use --force to overwrite)" % path)
        return 1
    pk = packlib.new_skeleton(args.video_id)
    try:
        snippet = _client().video(args.video_id, parts="snippet")["snippet"]
        pk["title"]["current"] = snippet.get("title", "")
        pk["description"]["body"] = snippet.get("description", "")
        pk["tags"] = snippet.get("tags", [])
        print("seeded from the live video")
    except (AuthError, ApiError) as exc:
        print("could not read live video (%s); writing an empty skeleton" % exc)
    packlib.save(pk, path)
    print("wrote %s" % path)
    return 0


def cmd_validate(args):
    path = pack_path(args.video_id)
    if not os.path.exists(path):
        print("no pack at %s -- run `init` first" % path)
        return 1
    pk = packlib.load(path)
    duration = None
    try:
        ctx = auditlib.build_context(_client(), args.video_id,
                                     check_playlists=False)
        duration = ctx.get("duration_seconds")
    except (AuthError, ApiError) as exc:
        print("offline validation only (%s)\n" % exc)
    findings = packlib.validate(pk, duration_seconds=duration)
    for f in findings:
        print("[%-4s] %-28s %s" % (f.status, f.rule, f.message))
    print()
    print("--- rendered description (%d chars) ---"
          % len(packlib.render_description(pk)))
    print(packlib.render_description(pk))
    return 1 if packlib.has_blocking_failure(findings) else 0


def cmd_apply(args):
    from . import apply as applylib

    path = pack_path(args.video_id)
    if not os.path.exists(path):
        print("no pack at %s -- run `init` first" % path)
        return 1
    pk = packlib.load(path)
    creds = Credentials.from_env()
    if args.apply:
        creds.check_write_scope()
    yt = YouTube(creds)
    ctx = auditlib.build_context(yt, args.video_id, check_playlists=False)
    report, ok = applylib.execute(
        yt, args.video_id, pk, os.path.dirname(path),
        apply_changes=args.apply, duration_seconds=ctx.get("duration_seconds"),
    )
    print(report)
    return 0 if ok else 1


def cmd_playbook(args):
    for name, text in rules.MANUAL_STEPS:
        print("[ ] %-22s %s" % (name, text))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="postpublish",
        description="Audit and execute the post-publish playbook on a video.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("audit", help="read-only scoring of a live video")
    p.add_argument("video_id")
    p.add_argument("--json", action="store_true")
    p.add_argument("--no-playlists", action="store_true",
                   help="skip playlist membership (saves quota)")
    p.set_defaults(func=cmd_audit)

    p = sub.add_parser("init", help="create a pack skeleton")
    p.add_argument("video_id")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("validate", help="check an authored pack")
    p.add_argument("video_id")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("apply", help="push the pack (dry run by default)")
    p.add_argument("video_id")
    p.add_argument("--apply", action="store_true",
                   help="actually write to YouTube")
    p.set_defaults(func=cmd_apply)

    p = sub.add_parser("playbook", help="print the manual checklist")
    p.set_defaults(func=cmd_playbook)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except AuthError as exc:
        print("auth error: %s" % exc, file=sys.stderr)
        return 2
    except ApiError as exc:
        print("api error: %s" % exc, file=sys.stderr)
        return 3
