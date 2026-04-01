"""v0.1.0 public OSS release candidate: docs and release pack exist."""

from __future__ import annotations

import re
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _markdown_targets(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)


def test_root_oss_hygiene_files_exist() -> None:
    root = _repo_root()
    for name in ("CHANGELOG.md", "CONTRIBUTING.md", "SECURITY.md"):
        assert (root / name).is_file(), name


def test_release_public_v0_1_0_pack_exists() -> None:
    root = _repo_root()
    pack = root / "release/public/v0_1_0"
    for name in ("README.md", "RELEASE_NOTES.md", "ANNOUNCEMENT.md", "ASSET_INVENTORY.md"):
        assert (pack / name).is_file(), name


def test_release_public_v0_1_0_markdown_links_resolve() -> None:
    root = _repo_root()
    pack = root / "release/public/v0_1_0"
    for path in sorted(pack.glob("*.md")):
        for target in _markdown_targets(path):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = target.split("#", 1)[0]
            if not target:
                continue
            assert (path.parent / target).resolve().exists(), f"{path.name}: {target}"
