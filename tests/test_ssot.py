"""Prove canonical vs compatibility ownership (no duplicate throughput truth)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from azimuth_bench.cli import throughput as throughput_cli
from azimuth_bench.core import runtime
from azimuth_bench.suites import throughput as throughput_suite
from azimuth_bench.suites.summary import TOKEN_FIELDS as SSOT_TOKEN_FIELDS
from azimuth_bench.suites.summary import token_row_from_artifact_payload
from benchmarking import summary as bench_summary
from benchmarking import token as bench_token


def test_token_fields_single_definition() -> None:
    assert bench_summary.TOKEN_FIELDS is SSOT_TOKEN_FIELDS


def test_protocol_id_defined_only_in_azimuth_bench_throughput() -> None:
    assert bench_token.PROTOCOL_ID is throughput_suite.PROTOCOL_ID
    assert throughput_suite.PROTOCOL_ID == "benchmark_v2_m5max_v1"


def test_benchmarking_token_main_is_canonical_throughput_main() -> None:
    assert bench_token.main is throughput_cli.main
    assert bench_token.parse_args is throughput_cli.parse_args


def test_resolve_model_id_matches_runtime() -> None:
    from benchmarking.utils import resolve_model_id as bench_resolve

    payload = {"data": [{"id": "a"}, {"id": "b"}]}
    assert bench_resolve(payload, target_model_id="b") == runtime.resolve_model_id(payload, target_model_id="b")


def test_token_row_extraction_delegates_to_ssot() -> None:
    entry = {
        "model_id": "m",
        "display_name": "M",
        "lane": "core",
        "thinking_mode": "default",
        "source_label": "s",
        "source_badge": "b",
    }
    payload = {
        "validity": {"valid_run": True},
        "comparability": {"comparable": True},
        "summary": {
            "short_tok_s": 1.0,
            "structured_json_tok_s": 2.0,
            "sustained_tok_s": 3.0,
            "first_output_ms": 4.0,
            "first_answer_ms": 5.0,
        },
    }
    row = token_row_from_artifact_payload(entry, payload)
    assert row is not None
    assert row["short_tok_s"] == 1.0


def test_subprocess_canonical_cli_help() -> None:
    root = Path(__file__).resolve().parent.parent
    for module in ("azimuth_bench", "signalbench"):
        proc = subprocess.run(
            [sys.executable, "-m", module, "bench", "throughput", "--help"],
            capture_output=True,
            text=True,
            check=False,
            cwd=root,
        )
        assert proc.returncode == 0, (module, proc.stderr)
        assert "throughput" in proc.stdout.lower()


def test_subprocess_legacy_token_module_invokes_same_package() -> None:
    """``python -m benchmarking.token`` loads the same module object as ``bench_token``."""
    cmd = "import benchmarking.token as t; import azimuth_bench.cli.throughput as c; print(t.main is c.main)"
    proc = subprocess.run(
        [sys.executable, "-c", cmd],
        capture_output=True,
        text=True,
        check=False,
        cwd=Path(__file__).resolve().parent.parent,
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "True"


def test_signalbench_shim_main_matches_azimuth_bench() -> None:
    import azimuth_bench.cli.entrypoint as ab_entry
    import signalbench.cli.entrypoint as sb_entry

    assert sb_entry.main is ab_entry.main
