"""v0.1.0 public OSS release candidate: docs and release pack exist."""

from __future__ import annotations

from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def test_root_oss_hygiene_files_exist() -> None:
    root = _repo_root()
    for name in ("CHANGELOG.md", "CONTRIBUTING.md", "SECURITY.md"):
        assert (root / name).is_file(), name


def test_release_public_v0_1_0_pack_exists() -> None:
    root = _repo_root()
    pack = root / "release/public/v0_1_0"
    for name in ("README.md", "RELEASE_NOTES.md", "ANNOUNCEMENT.md", "ASSET_INVENTORY.md"):
        assert (pack / name).is_file(), name
