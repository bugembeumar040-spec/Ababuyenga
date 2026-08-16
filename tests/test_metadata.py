"""Tests for the validation layer — the part that runs before quota is spent."""

import datetime as dt
import sys
import textwrap
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ytauto import metadata  # noqa: E402


def write(tmp_path: Path, body: str, video: bool = True) -> Path:
    if video:
        (tmp_path / "v.mp4").write_bytes(b"\x00" * 32)
    sidecar = tmp_path / "v.yml"
    sidecar.write_text(textwrap.dedent(body))
    return sidecar


BASE = """
    video_file: v.mp4
    title: A title
    description: {desc}
"""


def test_tags_length_counts_quotes_and_separators():
    assert metadata.tags_length([]) == 0
    assert metadata.tags_length(["abc"]) == 3
    # "a b" is quoted (+2) and one separator joins the two tags
    assert metadata.tags_length(["a b", "cd"]) == (3 + 2) + 2 + 1


def test_valid_sidecar_passes(tmp_path):
    meta = metadata.load(write(tmp_path, BASE.format(desc="x" * 700)))
    errors, warnings = metadata.validate(meta)
    assert errors == []
    assert warnings == []


def test_short_description_warns_but_does_not_block(tmp_path):
    meta = metadata.load(write(tmp_path, BASE.format(desc="too short")))
    errors, warnings = metadata.validate(meta)
    assert errors == []
    assert any("600+" in w for w in warnings)


def test_missing_video_file_is_an_error(tmp_path):
    meta = metadata.load(write(tmp_path, BASE.format(desc="x" * 700), video=False))
    errors, _ = metadata.validate(meta)
    assert any("not found" in e for e in errors)


def test_overlong_title_is_an_error(tmp_path):
    meta = metadata.load(
        write(tmp_path, f"video_file: v.mp4\ntitle: {'t' * 101}\ndescription: {'x' * 700}\n")
    )
    errors, _ = metadata.validate(meta)
    assert any("limit is 100" in e for e in errors)


def test_angle_brackets_rejected(tmp_path):
    meta = metadata.load(
        write(tmp_path, f'video_file: v.mp4\ntitle: "a <b>"\ndescription: {"x" * 700}\n')
    )
    errors, _ = metadata.validate(meta)
    assert any("< or >" in e for e in errors)


def test_tags_over_budget_is_an_error(tmp_path):
    tags = "\n".join(f"  - tag number {i:03d} padding" for i in range(30))
    meta = metadata.load(
        write(tmp_path, f"video_file: v.mp4\ntitle: t\ndescription: {'x' * 700}\ntags:\n{tags}\n")
    )
    errors, _ = metadata.validate(meta)
    assert any("limit is 500" in e for e in errors)


def test_publish_at_requires_private(tmp_path):
    future = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=2)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    meta = metadata.load(
        write(
            tmp_path,
            f"video_file: v.mp4\ntitle: t\ndescription: {'x' * 700}\n"
            f"privacy: unlisted\npublish_at: '{future}'\n",
        )
    )
    errors, _ = metadata.validate(meta)
    assert any("requires privacy: private" in e for e in errors)


def test_publish_at_in_the_past_is_an_error(tmp_path):
    past = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=1)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    meta = metadata.load(
        write(
            tmp_path,
            f"video_file: v.mp4\ntitle: t\ndescription: {'x' * 700}\npublish_at: '{past}'\n",
        )
    )
    errors, _ = metadata.validate(meta)
    assert any("in the past" in e for e in errors)


def test_naive_timestamp_rejected(tmp_path):
    meta = metadata.load(
        write(
            tmp_path,
            f"video_file: v.mp4\ntitle: t\ndescription: {'x' * 700}\n"
            "publish_at: '2099-01-01T10:00:00'\n",
        )
    )
    errors, _ = metadata.validate(meta)
    assert any("RFC3339" in e for e in errors)


def test_public_privacy_warns_about_locked_uploads(tmp_path):
    meta = metadata.load(
        write(tmp_path, f"video_file: v.mp4\ntitle: t\ndescription: {'x' * 700}\nprivacy: public\n")
    )
    _, warnings = metadata.validate(meta)
    assert any("locked private" in w for w in warnings)


def test_unknown_key_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="unknown key"):
        metadata.load(write(tmp_path, "video_file: v.mp4\ntitel: typo\n"))


def test_missing_video_file_key_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="video_file"):
        metadata.load(write(tmp_path, "title: t\n"))


def test_body_shape(tmp_path):
    future = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=2)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    meta = metadata.load(
        write(
            tmp_path,
            f"video_file: v.mp4\ntitle: t\ndescription: d\ntags: [a, b]\n"
            f"publish_at: '{future}'\n",
        )
    )
    body = meta.to_body()
    assert body["snippet"]["tags"] == ["a", "b"]
    assert body["status"]["privacyStatus"] == "private"
    assert body["status"]["publishAt"] == future
    assert body["status"]["selfDeclaredMadeForKids"] is False
