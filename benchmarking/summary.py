#!/usr/bin/env python3
"""Compile benchmark-v2 token and optional gate summary artifacts."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from azimuth_bench.suites.summary import TOKEN_FIELDS, token_row_from_artifact_payload
from benchmarking.roster import artifact_key, filter_roster, load_roster
from benchmarking.utils import DEFAULT_BENCHMARKS_DIR, DEFAULT_ROSTER

GATE_FIELDS = [
    "model_id",
    "display_name",
    "lane",
    "thinking_mode",
    "gate_decision",
    "status",
    "synthetic_failures",
    "synthetic_rate",
    "invalid_location_rate",
    "share_count_5tick",
    "agent_civ_usable",
]

COMBINED_FIELDS = TOKEN_FIELDS + [
    "gate_decision",
    "status",
    "synthetic_failures",
    "synthetic_rate",
    "invalid_location_rate",
    "share_count_5tick",
    "agent_civ_usable",
]


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def _round_numeric(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 4)
    return value


def _write_summary(
    *,
    output_prefix: Path,
    lane: str,
    fields: list[str],
    rows: list[dict[str, Any]],
) -> dict[str, str]:
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "lane": lane,
        "row_count": len(rows),
        "fields": fields,
        "rows": rows,
    }

    json_path = output_prefix.with_suffix(".json")
    csv_path = output_prefix.with_suffix(".csv")
    md_path = output_prefix.with_suffix(".md")

    json_path.write_text(json.dumps(payload, indent=2))
    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    md_path.write_text(_render_markdown(fields, rows))
    return {"json": str(json_path), "csv": str(csv_path), "md": str(md_path)}


def _render_markdown(fields: list[str], rows: list[dict[str, Any]]) -> str:
    pretty = {
        "model_id": "Model ID",
        "display_name": "Display",
        "lane": "Lane",
        "thinking_mode": "Think",
        "short_tok_s": "Short tok/s",
        "structured_json_tok_s": "JSON tok/s",
        "sustained_tok_s": "Sustain tok/s",
        "first_output_ms": "First out ms",
        "first_answer_ms": "First ans ms",
        "source_label": "Source",
        "source_badge": "Badge",
        "gate_decision": "Gate",
        "status": "Status",
        "synthetic_failures": "Synthetic fails",
        "synthetic_rate": "Synthetic rate",
        "invalid_location_rate": "Invalid loc rate",
        "share_count_5tick": "5-tick shares",
        "agent_civ_usable": "Usable",
    }

    headers = [pretty[field] for field in fields]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        values: list[str] = []
        for field in fields:
            value = row.get(field, "")
            if isinstance(value, float):
                values.append(f"{value:.4f}".rstrip("0").rstrip("."))
            else:
                values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines) + "\n"


def _status_for(gate_payload: dict[str, Any]) -> str:
    stage2 = gate_payload.get("stage2")
    if isinstance(stage2, dict) and stage2.get("status"):
        return str(stage2["status"])
    return "gate_failed"


def _token_row_for_entry(entry: dict[str, Any], benchmarks_dir: Path) -> dict[str, Any] | None:
    """Load artifact JSON and delegate row shape to :mod:`azimuth_bench.suites.summary`."""
    bench_payload = _read_json(benchmarks_dir / f"{artifact_key(entry)}.json")
    if not isinstance(bench_payload, dict):
        return None
    return token_row_from_artifact_payload(entry, bench_payload)


def _gate_row_for_entry(entry: dict[str, Any], benchmarks_dir: Path) -> dict[str, Any] | None:
    gate_payload = _read_json(benchmarks_dir / f"gate_{artifact_key(entry)}" / "gate_result.json")
    if not isinstance(gate_payload, dict):
        return None
    stage2 = gate_payload.get("stage2", {})
    row = {
        "model_id": entry["model_id"],
        "display_name": entry["display_name"],
        "lane": entry["lane"],
        "thinking_mode": entry["thinking_mode"],
        "gate_decision": gate_payload.get("decision", "missing"),
        "status": _status_for(gate_payload),
        "synthetic_failures": stage2.get("synthetic_failures", 0),
        "synthetic_rate": stage2.get("synthetic_rate", 0.0),
        "invalid_location_rate": stage2.get("invalid_location_rate", 0.0),
        "share_count_5tick": stage2.get("share_count_5tick", 0),
        "agent_civ_usable": gate_payload.get("agent_civ_usable", "missing"),
    }
    return {field: _round_numeric(row[field]) for field in GATE_FIELDS}


def _combine_rows(
    token_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    gate_index = {
        (
            row["model_id"],
            row["display_name"],
            row["lane"],
            row["thinking_mode"],
        ): row
        for row in gate_rows
    }
    combined: list[dict[str, Any]] = []
    for token_row in token_rows:
        key = (
            token_row["model_id"],
            token_row["display_name"],
            token_row["lane"],
            token_row["thinking_mode"],
        )
        gate_row = gate_index.get(key, {})
        row = dict(token_row)
        for field in GATE_FIELDS[4:]:
            row[field] = gate_row.get(field, "")
        combined.append(row)
    return combined


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compile benchmark-v2 summary artifacts")
    parser.add_argument("--benchmarks-dir", type=Path, default=DEFAULT_BENCHMARKS_DIR)
    parser.add_argument("--roster", type=Path, default=DEFAULT_ROSTER)
    parser.add_argument("--lane", type=str, default="all")
    parser.add_argument(
        "--write-gate",
        action="store_true",
        help="Write the optional Agent Civilization gate summary artifacts.",
    )
    parser.add_argument(
        "--write-combined",
        action="store_true",
        help="Write an explicit combined token+gate summary artifact.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.benchmarks_dir.mkdir(parents=True, exist_ok=True)
    entries = filter_roster(load_roster(args.roster), args.lane)

    token_rows = [
        row for row in (_token_row_for_entry(entry, args.benchmarks_dir) for entry in entries) if row is not None
    ]
    outputs = {
        "token": _write_summary(
            output_prefix=args.benchmarks_dir / "benchmark_v2_token_summary",
            lane=args.lane,
            fields=TOKEN_FIELDS,
            rows=token_rows,
        )
    }

    gate_rows: list[dict[str, Any]] = []
    if args.write_gate or args.write_combined:
        gate_rows = [
            row for row in (_gate_row_for_entry(entry, args.benchmarks_dir) for entry in entries) if row is not None
        ]

    if args.write_gate:
        outputs["gate"] = _write_summary(
            output_prefix=args.benchmarks_dir / "benchmark_v2_gate_summary",
            lane=args.lane,
            fields=GATE_FIELDS,
            rows=gate_rows,
        )

    if args.write_combined:
        outputs["combined"] = _write_summary(
            output_prefix=args.benchmarks_dir / "benchmark_v2_combined_summary",
            lane=args.lane,
            fields=COMBINED_FIELDS,
            rows=_combine_rows(token_rows, gate_rows),
        )

    print(json.dumps(outputs, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
