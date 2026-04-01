"""Run directory integrity checks (fail-closed on uncertainty)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from azimuth_bench.schema.artifact_lookup import matching_artifact_paths
from azimuth_bench.schema.io import read_json_dict


@dataclass
class IntegrityReport:
    """Result of validating a benchmarks run directory."""

    ok: bool
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate_run_directory(run_dir: Path, *, summary_name: str = "benchmark_v2_token_summary.json") -> IntegrityReport:
    """Ensure summary rows have exactly one backing artifact JSON file each."""
    blockers: list[str] = []
    warnings: list[str] = []

    summary_path = run_dir / summary_name
    summary = read_json_dict(summary_path)
    if summary is None:
        blockers.append(f"missing or invalid summary: {summary_path}")
        return IntegrityReport(ok=False, blockers=blockers, warnings=warnings)

    rows = summary.get("rows")
    if not isinstance(rows, list):
        blockers.append("summary.rows is not a list")
        return IntegrityReport(ok=False, blockers=blockers, warnings=warnings)

    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            blockers.append(f"summary.rows[{index}] is not an object")
            continue
        model_id = row.get("model_id")
        thinking = row.get("thinking_mode")
        lane = row.get("lane")
        if not isinstance(model_id, str) or not isinstance(thinking, str) or not isinstance(lane, str):
            blockers.append(f"summary.rows[{index}] missing model_id/lane/thinking_mode")
            continue

        paths = matching_artifact_paths(
            run_dir,
            summary_name=summary_name,
            model_id=model_id,
            lane=lane,
            thinking_mode=thinking,
        )
        if len(paths) == 0:
            blockers.append(
                f"no artifact JSON for row {index}: model_id={model_id!r} lane={lane!r} thinking={thinking!r}"
            )
        elif len(paths) > 1:
            names = ", ".join(sorted(p.name for p in paths))
            blockers.append(f"ambiguous artifacts for row {index} (model_id/lane/thinking_mode): {names}")

    if not rows:
        warnings.append("summary contains zero rows")

    ok = not blockers
    return IntegrityReport(ok=ok, blockers=blockers, warnings=warnings)
