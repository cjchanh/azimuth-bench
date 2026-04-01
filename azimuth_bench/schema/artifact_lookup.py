"""Locate benchmark artifact JSON files for a summary row (deterministic, testable)."""

from __future__ import annotations

from pathlib import Path

from azimuth_bench.schema.io import read_json_dict


def matching_artifact_paths(
    run_dir: Path,
    *,
    summary_name: str,
    model_id: str,
    lane: str,
    thinking_mode: str,
) -> list[Path]:
    """Return sorted paths to ``*.json`` artifacts matching the row triple.

    Excludes summary files. Order is lexicographic by path name for stability.
    """
    matched: list[Path] = []
    for path in sorted(run_dir.glob("*.json")):
        if path.name == summary_name or path.name.endswith("_summary.json"):
            continue
        art = read_json_dict(path)
        if art is None:
            continue
        if art.get("model_id") == model_id and art.get("lane") == lane and art.get("thinking_mode") == thinking_mode:
            matched.append(path)
    return matched
