"""Azimuth Bench CLI entry point (`azbench`, ``python -m azimuth_bench``)."""

from __future__ import annotations

import argparse
from pathlib import Path

from azimuth_bench.cli.bench_aux import (
    add_promotion_gate_arguments,
    add_semantic_summary_arguments,
    run_promotion_gate_cli,
    run_semantic_summary_cli,
)
from azimuth_bench.cli.throughput import add_throughput_arguments, run_throughput
from azimuth_bench.core.paths import find_repo_root
from azimuth_bench.export.markdown import write_markdown_export
from azimuth_bench.export.svg_cards import write_share_svgs_from_report_data
from azimuth_bench.report.builder import build_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="azbench",
        description="Azimuth Bench — portable inference benchmark CLI (reports, suites, adapters).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    report_p = sub.add_parser("report", help="Azimuth Report commands")
    report_sub = report_p.add_subparsers(dest="report_cmd", required=True)
    build_p = report_sub.add_parser("build", help="Build static report from a run directory")
    build_p.add_argument(
        "run_dir",
        type=Path,
        help="Directory containing benchmark artifacts (e.g. benchmarks/)",
    )
    build_p.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Git repository root for report build metadata (default: auto-detect)",
    )
    build_p.add_argument(
        "--include-run-dir",
        action="append",
        default=[],
        type=Path,
        metavar="DIR",
        help="Additional benchmark run directory to merge (repeatable; no auto-discovery). "
        "Each DIR must contain a valid token summary + artifacts like the primary run_dir.",
    )

    export_p = sub.add_parser("export", help="Offline exports from built report data")
    export_sub = export_p.add_subparsers(dest="export_cmd", required=True)
    md_p = export_sub.add_parser("markdown", help="Write Markdown summary from report/data/")
    md_p.add_argument(
        "run_dir",
        type=Path,
        help="Run directory containing report/data/ (e.g. benchmarks/ after report build)",
    )
    md_p.add_argument("--output", type=Path, required=True, help="Output .md path")

    svg_p = export_sub.add_parser("svg", help="Write deterministic share SVGs from report/data/")
    svg_p.add_argument(
        "run_dir",
        type=Path,
        help="Run directory containing report/data/ (e.g. benchmarks/ after report build)",
    )
    svg_p.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for SVG files (default: <run_dir>/report/exports)",
    )

    bench_p = sub.add_parser("bench", help="Benchmark suite commands (canonical execution path)")
    bench_sub = bench_p.add_subparsers(dest="bench_cmd", required=True)
    tp_p = bench_sub.add_parser(
        "throughput",
        help="Run the throughput suite (same implementation as legacy python -m benchmarking.token)",
    )
    add_throughput_arguments(tp_p)

    sem_p = bench_sub.add_parser(
        "semantic-summary",
        help="Join semantic fixtures + outputs (+ optional human scores) into an artifact.",
    )
    add_semantic_summary_arguments(sem_p)

    promo_p = bench_sub.add_parser(
        "promotion-gate",
        help="Emit a promotion gate classification JSON from structured evidence.",
    )
    add_promotion_gate_arguments(promo_p)

    args = parser.parse_args(argv)
    if args.command == "report" and args.report_cmd == "build":
        root = args.repo_root or find_repo_root(Path(__file__))
        extra = tuple(args.include_run_dir) if args.include_run_dir else ()
        out = build_report(args.run_dir.resolve(), repo_root=root, include_run_dirs=extra)
        print(f"Wrote report: {out}")
        return 0
    if args.command == "export" and args.export_cmd == "markdown":
        data_dir = args.run_dir.resolve() / "report" / "data"
        path = write_markdown_export(report_data_dir=data_dir, output_path=args.output.resolve())
        print(f"Wrote export: {path}")
        return 0
    if args.command == "export" and args.export_cmd == "svg":
        run_dir = args.run_dir.resolve()
        exports_dir = args.output_dir.resolve() if args.output_dir else run_dir / "report" / "exports"
        lb, sc = write_share_svgs_from_report_data(
            report_data_dir=run_dir / "report" / "data",
            exports_dir=exports_dir,
        )
        print(f"Wrote exports: {lb}")
        print(f"Wrote exports: {sc}")
        return 0
    if args.command == "bench" and args.bench_cmd == "throughput":
        return run_throughput(args)
    if args.command == "bench" and args.bench_cmd == "semantic-summary":
        return run_semantic_summary_cli(args)
    if args.command == "bench" and args.bench_cmd == "promotion-gate":
        return run_promotion_gate_cli(args)

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
