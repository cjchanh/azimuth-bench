"""Canonical CLI implementation for the throughput suite."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from azimuth_bench.adapters.factory import (
    build_throughput_adapter,
    default_machine_class_for_adapter,
    resolve_provider_fields,
)
from azimuth_bench.core.paths import find_repo_root
from azimuth_bench.core.runtime import DEFAULT_BENCHMARKS_DIR, ROOT, slugify
from azimuth_bench.suites.throughput import BenchmarkIdentity, run_benchmark


def add_throughput_arguments(parser: argparse.ArgumentParser) -> None:
    """Register throughput suite CLI flags (shared by ``azbench bench throughput`` and legacy wrappers)."""
    parser.add_argument(
        "--adapter",
        choices=("mlx", "openai_compatible", "ollama"),
        default="mlx",
        help="Backend adapter (default: mlx local MLX LM server).",
    )
    parser.add_argument("--port", type=int, default=8899)
    parser.add_argument("--max-tokens", type=int, default=256)
    parser.add_argument("--model-id", type=str, default=None)
    parser.add_argument("--output", type=str, default=None, help="Output JSON path")
    parser.add_argument("--thinking-mode", choices=["default", "on", "off"], default="default")
    parser.add_argument("--display-name", type=str, default=None)
    parser.add_argument("--lane", type=str, default="core")
    parser.add_argument("--source-label", type=str, default="local")
    parser.add_argument("--source-badge", type=str, default="Local")
    parser.add_argument("--artifact-key", type=str, default=None)
    parser.add_argument("--smoke", action="store_true", help="Run a minimal validation subset")
    parser.add_argument(
        "--base-url",
        type=str,
        default=None,
        help="HTTP base URL for openai_compatible or ollama (or set AZIMUTH_BENCH_OPENAI_BASE_URL / OLLAMA_HOST).",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root for MLX server cwd and paths (default: auto-detect from this package).",
    )
    parser.add_argument(
        "--machine-class",
        type=str,
        default=None,
        help="Protocol machine_class label (default: mlx legacy string or unspecified_host for HTTP adapters).",
    )
    parser.add_argument(
        "--provider-id",
        type=str,
        default=None,
        help="Operator provider label for artifacts (overrides AZIMUTH_BENCH_PROVIDER_ID).",
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Azimuth Bench throughput suite")
    add_throughput_arguments(parser)
    return parser.parse_args(argv)


def run_throughput(args: argparse.Namespace) -> int:
    """Execute one throughput run using the selected adapter."""
    repo_root = args.repo_root or find_repo_root(Path(__file__)) or ROOT
    op_pid, pid_src = resolve_provider_fields(cli_provider_id=args.provider_id)
    machine_class = args.machine_class or default_machine_class_for_adapter(args.adapter)
    adapter = build_throughput_adapter(
        adapter_name=args.adapter,
        repo_root=repo_root.resolve(),
        bench_port=args.port,
        base_url=args.base_url,
        max_tokens_default=max(512, args.max_tokens),
    )
    results = run_benchmark(
        adapter=adapter,
        identity=BenchmarkIdentity(
            target_model_id=args.model_id,
            display_name=args.display_name,
            lane=args.lane,
            thinking_mode=args.thinking_mode,
            source_label=args.source_label,
            source_badge=args.source_badge,
            artifact_key=args.artifact_key,
            operator_provider_id=op_pid,
            provider_id_source=pid_src,
        ),
        max_tokens=args.max_tokens,
        smoke=args.smoke,
        machine_class=machine_class,
    )
    adapter.shutdown()

    if args.output:
        out = Path(args.output)
    else:
        safe_name = results["summary"]["artifact_key"] or slugify(results["model_id"])
        out = DEFAULT_BENCHMARKS_DIR / f"{safe_name}.json"

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, default=str))
    print(f"\nResults: {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entry for standalone ``python -m azimuth_bench.cli.throughput`` or legacy wrappers."""
    return run_throughput(parse_args(argv))
