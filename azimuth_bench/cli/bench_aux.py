"""Additional bench subcommands (semantic summary + promotion gates)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from azimuth_bench.gates.promotion import build_promotion_report
from azimuth_bench.semantic.summary import build_semantic_summary


def add_semantic_summary_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--fixtures", type=Path, required=True, help="Semantic fixture JSONL.")
    parser.add_argument("--outputs", type=Path, required=True, help="Model outputs JSONL.")
    parser.add_argument(
        "--human-scores",
        type=Path,
        default=None,
        help="Optional JSONL with fixture_id/human_score rows.",
    )
    parser.add_argument(
        "--scorer",
        type=str,
        default="manual_rubric_v1",
        help="Recorded scorer_identity on the semantic artifact.",
    )
    parser.add_argument("--output", type=Path, required=True, help="Semantic summary JSON path.")
    parser.add_argument(
        "--fail-on-gate",
        action="store_true",
        help="Exit non-zero when semantic_gate_pass is false.",
    )


def run_semantic_summary_cli(args: argparse.Namespace) -> int:
    summary = build_semantic_summary(
        fixtures_path=args.fixtures.resolve(),
        outputs_path=args.outputs.resolve(),
        scorer_identity=args.scorer,
        human_scores_path=args.human_scores.resolve() if args.human_scores else None,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    gate = summary["aggregate"]["semantic_gate_pass"]
    if args.fail_on_gate and not gate:
        return 1
    print(f"Wrote semantic summary: {args.output}")
    return 0


def add_promotion_gate_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--input", type=Path, required=True, help="JSON payload describing evidence.")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Destination JSON (default: alongside --input with _promotion_gate suffix).",
    )


def run_promotion_gate_cli(args: argparse.Namespace) -> int:
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    report = build_promotion_report(payload)
    out_path = args.output.resolve() if args.output else args.input.with_name(args.input.stem + "_promotion_gate.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    print(f"Wrote promotion gate artifact: {out_path}")
    return 0
