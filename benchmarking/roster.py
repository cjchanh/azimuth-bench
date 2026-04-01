#!/usr/bin/env python3
"""Roster and naming contract for the benchmark-v2 package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

from azimuth_bench.core.runtime import DEFAULT_ROSTER, slugify

REQUIRED_ENTRY_KEYS = {
    "model_id",
    "display_name",
    "variant",
    "lane",
    "thinking_mode",
    "source_label",
    "source_badge",
    "required_cache",
}


def load_roster(path: Path | str = DEFAULT_ROSTER) -> list[dict[str, Any]]:
    """Load and validate the benchmark roster manifest."""
    roster_path = Path(path)
    payload = json.loads(roster_path.read_text())
    if not isinstance(payload, dict):
        raise ValueError(f"Roster must be a JSON object: {roster_path}")
    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise ValueError(f"Roster missing 'entries' list: {roster_path}")

    validated: list[dict[str, Any]] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError(f"Roster entry {index} is not an object")
        missing = REQUIRED_ENTRY_KEYS - set(entry)
        if missing:
            raise ValueError(f"Roster entry {index} missing keys: {sorted(missing)}")
        thinking_mode = entry["thinking_mode"]
        if thinking_mode not in {"default", "on", "off"}:
            raise ValueError(f"Roster entry {index} has unsupported thinking_mode={thinking_mode!r}")
        validated.append(entry)
    return validated


def filter_roster(entries: Iterable[dict[str, Any]], lane: str = "all") -> list[dict[str, Any]]:
    """Filter entries by lane while preserving order."""
    if lane == "all":
        return list(entries)
    return [entry for entry in entries if entry.get("lane") == lane]


def artifact_key(entry: dict[str, Any]) -> str:
    """Build a stable artifact key from manifest metadata."""
    return "__".join(
        [
            slugify(str(entry["lane"])),
            slugify(str(entry["variant"])),
            f"thinking-{slugify(str(entry['thinking_mode']))}",
        ]
    )


def hf_cache_dir(model_id: str) -> Path:
    """Resolve the local Hugging Face cache directory for a model."""
    return Path.home() / ".cache" / "huggingface" / "hub" / f"models--{model_id.replace('/', '--')}"


def emit_tsv(entries: Iterable[dict[str, Any]]) -> str:
    """Render manifest entries as TSV for shell consumption."""
    lines = []
    for entry in entries:
        lines.append(
            "\t".join(
                [
                    str(entry["model_id"]),
                    str(entry["display_name"]),
                    str(entry["lane"]),
                    str(entry["thinking_mode"]),
                    str(entry["source_label"]),
                    str(entry["source_badge"]),
                    artifact_key(entry),
                    "1" if entry.get("required_cache") else "0",
                ]
            )
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect the benchmark-v2 roster.")
    parser.add_argument("--roster", type=Path, default=DEFAULT_ROSTER)
    parser.add_argument("--lane", type=str, default="all")
    parser.add_argument("--emit-tsv", action="store_true")
    args = parser.parse_args()

    entries = filter_roster(load_roster(args.roster), args.lane)
    if args.emit_tsv:
        print(emit_tsv(entries))
        return 0

    print(json.dumps(entries, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
