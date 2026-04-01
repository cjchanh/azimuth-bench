"""Repository path helpers."""

from __future__ import annotations

from pathlib import Path


def find_repo_root(start: Path | None = None) -> Path | None:
    """Walk parents from ``start`` until a directory containing ``.git`` is found.

    Returns ``None`` if no such directory exists (e.g. unpacked source tarball without VCS metadata).
    """
    cur = (start or Path(__file__)).resolve().parent
    while cur != cur.parent:
        if (cur / ".git").is_dir():
            return cur
        cur = cur.parent
    return None
