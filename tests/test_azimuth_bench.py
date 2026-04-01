from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from azimuth_bench.adapters.factory import build_throughput_adapter, default_machine_class_for_adapter
from azimuth_bench.adapters.mlx import MLXLmServerAdapter
from azimuth_bench.adapters.ollama import OllamaAdapter
from azimuth_bench.adapters.openai_compatible import OpenAICompatibleAdapter
from azimuth_bench.compare.projection import build_compare_projection
from azimuth_bench.core.cases import CaseSpec
from azimuth_bench.core.comparability import comparability_block
from azimuth_bench.core.env import (
    default_fleet_guard_path,
    default_mlx_server_log_path,
    default_temp_dir,
    provider_id_from_env,
)
from azimuth_bench.core.paths import find_repo_root
from azimuth_bench.errors import AdapterConfigurationError, UnsupportedAdapterFeatureError
from azimuth_bench.export.markdown import write_markdown_export
from azimuth_bench.report.builder import build_report
from azimuth_bench.schema.artifact_lookup import matching_artifact_paths
from azimuth_bench.schema.bundle import build_canonical_data_files
from azimuth_bench.schema.integrity import validate_run_directory
from azimuth_bench.schema.protocol_manifest import build_protocol_manifest
from azimuth_bench.schema.version import AZIMUTH_BENCH_SCHEMA_VERSION, SIGNALBENCH_SCHEMA_VERSION
from azimuth_bench.suites.throughput import BenchmarkIdentity, run_benchmark


def test_azimuth_bench_schema_version_is_semver() -> None:
    parts = AZIMUTH_BENCH_SCHEMA_VERSION.split(".")
    assert len(parts) == 3
    assert all(p.isdigit() for p in parts)
    assert SIGNALBENCH_SCHEMA_VERSION == AZIMUTH_BENCH_SCHEMA_VERSION


def test_validate_run_directory_real_benchmarks(repo_benchmarks: Path) -> None:
    rep = validate_run_directory(repo_benchmarks)
    assert rep.ok, rep.blockers


@pytest.fixture
def repo_benchmarks() -> Path:
    return Path(__file__).resolve().parent.parent / "benchmarks"


def test_build_canonical_data_files_real(repo_benchmarks: Path) -> None:
    root = Path(__file__).resolve().parent.parent
    bundle = build_canonical_data_files(repo_benchmarks, repo_root=root)
    assert "run.json" in bundle
    assert bundle["run.json"]["azimuth_bench_schema_version"] == AZIMUTH_BENCH_SCHEMA_VERSION
    assert isinstance(bundle["summary.json"]["rows"], list)
    prov = bundle["provider.json"]
    assert prov.get("provider_id") == "mlx_lm"
    assert prov.get("provider_kind") == "mlx_lm"
    assert prov.get("provider_id_source") == "default"
    assert bundle["run.json"]["benchmark_commit_sha"] is None
    assert bundle["run.json"]["benchmark_commit_sha_status"] == "missing_in_source_artifacts"
    assert len(bundle["run_bundles"]) == bundle["summary.json"]["row_count"]
    first_row = bundle["summary.json"]["rows"][0]
    assert "comparable" in first_row
    assert "comparability_blockers" in first_row


def test_build_canonical_data_files_with_explicit_provider(repo_benchmarks: Path) -> None:
    root = Path(__file__).resolve().parent.parent
    bundle = build_canonical_data_files(
        repo_benchmarks,
        repo_root=root,
        provider_id="test_provider_label",
        provider_id_source="cli",
    )
    assert bundle["provider.json"]["provider_id"] == "test_provider_label"
    assert bundle["provider.json"]["provider_id_source"] == "cli"


def test_build_report_emits_outputs(repo_benchmarks: Path, tmp_path: Path) -> None:
    """Copy a minimal valid tree so report writes do not touch the repo artifact tree."""
    bench = tmp_path / "bench"
    bench.mkdir()
    summary_src = repo_benchmarks / "benchmark_v2_token_summary.json"
    art_name = "core__phi4_mini__thinking-default.json"
    (bench / "benchmark_v2_token_summary.json").write_text(summary_src.read_text(encoding="utf-8"))
    (bench / art_name).write_text((repo_benchmarks / art_name).read_text(encoding="utf-8"))

    sub = json.loads(summary_src.read_text(encoding="utf-8"))
    sub["row_count"] = 1
    sub["rows"] = [r for r in sub["rows"] if r.get("model_id") == "mlx-community/Phi-4-mini-instruct-4bit"]
    assert len(sub["rows"]) == 1
    (bench / "benchmark_v2_token_summary.json").write_text(json.dumps(sub, indent=2))

    root = Path(__file__).resolve().parent.parent
    out = build_report(bench, repo_root=root)
    assert (out / "index.html").exists()
    assert (out / "leaderboard.html").exists()
    assert (out / "compare.html").exists()
    assert (out / "summary.md").exists()
    assert (out / "data" / "run.json").exists()
    lb = json.loads((out / "data" / "leaderboard.json").read_text(encoding="utf-8"))
    assert lb.get("azimuth_bench_schema_version") == AZIMUTH_BENCH_SCHEMA_VERSION
    cmp_data = json.loads((out / "data" / "compare.json").read_text(encoding="utf-8"))
    assert cmp_data.get("compare_schema") == "azimuth_compare_v1"
    assert "projection" in cmp_data
    assert "blocked_comparisons" in (cmp_data.get("projection") or {})
    assert (out / "exports" / "share_leaderboard.svg").exists()
    assert (out / "exports" / "share_compare.svg").exists()
    share_lb = (out / "exports" / "share_leaderboard.svg").read_text(encoding="utf-8")
    assert str(tmp_path) not in share_lb
    assert (out / "data" / "site_manifest.json").exists()
    assert (out / "data" / "runs" / "index.json").exists()
    assert (out / "data" / "runs" / "core__phi4_mini__thinking-default" / "run.json").exists()
    assert (out / "runs" / "core__phi4_mini__thinking-default.html").exists()
    assert (out / "charts" / "throughput_structured.svg").exists()
    assert (out / "charts" / "latency_tradeoff.svg").exists()
    provider = json.loads((out / "data" / "provider.json").read_text(encoding="utf-8"))
    assert provider.get("provider_id") == "mlx_lm"
    assert provider.get("provider_kind") == "mlx_lm"
    report_summary = json.loads((out / "data" / "summary.json").read_text(encoding="utf-8"))
    assert report_summary["rows"][0]["comparable"] is True
    assert "comparability_blockers" in report_summary["rows"][0]
    site_manifest = json.loads((out / "data" / "site_manifest.json").read_text(encoding="utf-8"))
    assert site_manifest["run_detail"]["count"] == 1
    assert "routes" in site_manifest and "host_index" in site_manifest
    assert site_manifest["providers"]["count"] == 1
    assert site_manifest["protocols"]["count"] == 1
    assert (out / "data" / "providers" / "index.json").exists()
    assert (out / "data" / "protocols" / "index.json").exists()
    assert any((out / "providers").glob("*.html"))
    assert any((out / "protocols").glob("*.html"))
    for rel in (
        out / "data" / "run.json",
        out / "data" / "provider.json",
        out / "data" / "runs" / "core__phi4_mini__thinking-default" / "run.json",
    ):
        assert str(tmp_path) not in rel.read_text(encoding="utf-8")


def test_mlx_adapter_run_case_requires_prepare_target(tmp_path: Path) -> None:
    log_path = tmp_path / "mlx.log"
    adapter = MLXLmServerAdapter(
        repo_root=tmp_path,
        bench_port=59998,
        server_log_path=log_path,
    )
    spec = CaseSpec(suite_family="throughput", prompt_id="short", max_tokens=64)
    with pytest.raises(ValueError, match="prepare_target|target_model_id"):
        adapter.run_case(spec, thinking_mode="default")


def test_mlx_adapter_shutdown_is_safe(tmp_path: Path) -> None:
    adapter = MLXLmServerAdapter(
        repo_root=tmp_path,
        bench_port=59997,
        server_log_path=tmp_path / "mlx.log",
    )
    with patch("azimuth_bench.adapters.mlx._kill_port_holders"):
        adapter.shutdown()


def test_integrity_fail_when_artifact_missing(tmp_path: Path) -> None:
    summary = {
        "generated_at_utc": "2026-01-01T00:00:00+00:00",
        "lane": "all",
        "row_count": 1,
        "fields": ["model_id"],
        "rows": [
            {
                "model_id": "missing/model",
                "display_name": "X",
                "lane": "core",
                "thinking_mode": "default",
            }
        ],
    }
    (tmp_path / "benchmark_v2_token_summary.json").write_text(json.dumps(summary))
    rep = validate_run_directory(tmp_path)
    assert not rep.ok


def test_integrity_fails_on_ambiguous_duplicate_artifacts(tmp_path: Path) -> None:
    summary = {
        "generated_at_utc": "2026-01-01T00:00:00+00:00",
        "lane": "all",
        "row_count": 1,
        "fields": [],
        "rows": [
            {
                "model_id": "org/model",
                "lane": "core",
                "thinking_mode": "default",
            }
        ],
    }
    (tmp_path / "benchmark_v2_token_summary.json").write_text(json.dumps(summary))
    dup = {
        "model_id": "org/model",
        "lane": "core",
        "thinking_mode": "default",
        "artifact_key": "a",
    }
    (tmp_path / "a.json").write_text(json.dumps(dup))
    (tmp_path / "b.json").write_text(json.dumps({**dup, "artifact_key": "b"}))
    rep = validate_run_directory(tmp_path)
    assert not rep.ok
    assert any("ambiguous" in b for b in rep.blockers)


def test_matching_artifact_paths_single_match(tmp_path: Path) -> None:
    summary_name = "benchmark_v2_token_summary.json"
    summary = {"rows": []}
    (tmp_path / summary_name).write_text(json.dumps(summary))
    art = {
        "model_id": "m",
        "lane": "core",
        "thinking_mode": "default",
    }
    (tmp_path / "only.json").write_text(json.dumps(art))
    paths = matching_artifact_paths(
        tmp_path,
        summary_name=summary_name,
        model_id="m",
        lane="core",
        thinking_mode="default",
    )
    assert [p.name for p in paths] == ["only.json"]


def test_find_repo_root_finds_git(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    (tmp_path / "pkg").mkdir()
    found = find_repo_root(tmp_path / "pkg" / "dummy.py")
    assert found == tmp_path


def test_find_repo_root_returns_none_without_git(tmp_path: Path) -> None:
    (tmp_path / "a" / "b").mkdir(parents=True)
    assert find_repo_root(tmp_path / "a" / "b" / "file.py") is None


def test_default_paths_use_tmpdir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    for key in (
        "AZIMUTH_BENCH_MLX_SERVER_LOG",
        "SIGNALBENCH_MLX_SERVER_LOG",
        "AZIMUTH_BENCH_FLEET_GUARD_PATH",
        "SIGNALBENCH_FLEET_GUARD_PATH",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    assert default_temp_dir() == tmp_path
    assert default_mlx_server_log_path().parent == tmp_path
    assert default_fleet_guard_path().parent == tmp_path


def test_provider_id_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in ("AZIMUTH_BENCH_PROVIDER_ID", "SIGNALBENCH_PROVIDER_ID"):
        monkeypatch.delenv(key, raising=False)
    assert provider_id_from_env() is None
    monkeypatch.setenv("AZIMUTH_BENCH_PROVIDER_ID", "  mlx ")
    assert provider_id_from_env() == "mlx"
    monkeypatch.delenv("AZIMUTH_BENCH_PROVIDER_ID", raising=False)
    monkeypatch.setenv("SIGNALBENCH_PROVIDER_ID", "legacy")
    assert provider_id_from_env() == "legacy"


def test_build_report_respects_provider_env(
    repo_benchmarks: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bench = tmp_path / "bench"
    bench.mkdir()
    summary_src = repo_benchmarks / "benchmark_v2_token_summary.json"
    art_name = "core__phi4_mini__thinking-default.json"
    (bench / "benchmark_v2_token_summary.json").write_text(summary_src.read_text(encoding="utf-8"))
    (bench / art_name).write_text((repo_benchmarks / art_name).read_text(encoding="utf-8"))
    sub = json.loads(summary_src.read_text(encoding="utf-8"))
    sub["row_count"] = 1
    sub["rows"] = [r for r in sub["rows"] if r.get("model_id") == "mlx-community/Phi-4-mini-instruct-4bit"]
    (bench / "benchmark_v2_token_summary.json").write_text(json.dumps(sub, indent=2))

    root = Path(__file__).resolve().parent.parent
    monkeypatch.setenv("AZIMUTH_BENCH_PROVIDER_ID", "env_named_provider")
    build_report(bench, repo_root=root)
    provider = json.loads((bench / "report" / "data" / "provider.json").read_text(encoding="utf-8"))
    assert provider.get("provider_id") == "env_named_provider"
    assert provider.get("provider_id_source") == "env"


def test_index_html_has_no_external_font_cdn(repo_benchmarks: Path, tmp_path: Path) -> None:
    bench = tmp_path / "bench"
    bench.mkdir()
    summary_src = repo_benchmarks / "benchmark_v2_token_summary.json"
    art_name = "core__phi4_mini__thinking-default.json"
    (bench / "benchmark_v2_token_summary.json").write_text(summary_src.read_text(encoding="utf-8"))
    (bench / art_name).write_text((repo_benchmarks / art_name).read_text(encoding="utf-8"))
    sub = json.loads(summary_src.read_text(encoding="utf-8"))
    sub["row_count"] = 1
    sub["rows"] = [r for r in sub["rows"] if r.get("model_id") == "mlx-community/Phi-4-mini-instruct-4bit"]
    (bench / "benchmark_v2_token_summary.json").write_text(json.dumps(sub, indent=2))
    root = Path(__file__).resolve().parent.parent
    build_report(bench, repo_root=root)
    html = (bench / "report" / "index.html").read_text(encoding="utf-8")
    assert "fonts.googleapis.com" not in html
    assert "Azimuth Bench" in html


def test_openai_compatible_adapter_capabilities() -> None:
    adapter = OpenAICompatibleAdapter(base_url="http://127.0.0.1:9")
    assert adapter.capabilities().openai_compatible_http is True
    assert adapter.capabilities().thinking_toggle is False


def test_factory_requires_openai_base_url() -> None:
    with pytest.raises(AdapterConfigurationError):
        build_throughput_adapter(
            adapter_name="openai_compatible",
            repo_root=Path("."),
            bench_port=1,
            base_url=None,
            max_tokens_default=512,
        )


def test_default_machine_class_mlx_vs_http() -> None:
    assert "MLX" in default_machine_class_for_adapter("mlx")
    assert default_machine_class_for_adapter("ollama") == "unspecified_host"


def test_comparability_block() -> None:
    proto = {"protocol_id": "p", "prompt_set_id": "ps"}
    validity = {"valid_run": True, "token_count_sources": ["usage"]}
    block = comparability_block(protocol=proto, validity=validity)
    assert block["comparable"] is True
    assert block["comparable_scope"] == "protocol_exact"
    assert block["comparability_blockers"] == []
    assert block["protocol_id"] == "p"


def test_compare_projection_has_schema_and_blockers() -> None:
    """Minimal rows still emit compare_schema and explicit non-compare reasons."""
    rows = [{"lane": "core", "display_name": "X", "structured_json_tok_s": 1.0, "artifact_key": "k"}]
    payload = build_compare_projection(rows)
    assert payload["compare_schema"] == "azimuth_compare_v1"
    assert isinstance(payload["projection"]["blocked_comparisons"], list)
    assert len(payload["projection"]["blocked_comparisons"]) >= 1


def test_protocol_manifest() -> None:
    proto = {"protocol_id": "p", "prompt_set_id": "ps", "machine_class": "m"}
    manifest = build_protocol_manifest(protocol=proto, suite_family="throughput")
    assert manifest["suite_family"] == "throughput"
    assert manifest["protocol_id"] == "p"


def test_export_markdown_writes(tmp_path: Path) -> None:
    data = tmp_path / "data"
    data.mkdir()
    (data / "summary.json").write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "model_id": "m",
                        "structured_json_tok_s": 1.0,
                        "sustained_tok_s": 2.0,
                        "comparable": True,
                    }
                ]
            }
        )
    )
    out = write_markdown_export(report_data_dir=data, output_path=tmp_path / "out.md")
    text = out.read_text(encoding="utf-8")
    assert text.startswith("# Azimuth Bench export")
    assert "m" in text


def test_thinking_mode_rejected_on_ollama() -> None:
    adapter = OllamaAdapter(base_url="http://127.0.0.1:9")
    with patch.object(OllamaAdapter, "healthcheck", return_value=True):
        with pytest.raises(UnsupportedAdapterFeatureError):
            run_benchmark(
                adapter=adapter,
                identity=BenchmarkIdentity(
                    target_model_id="m",
                    display_name="m",
                    lane="core",
                    thinking_mode="on",
                    source_label="s",
                    source_badge="b",
                ),
                max_tokens=64,
                smoke=True,
                machine_class="unspecified_host",
            )


def test_backend_identity_hides_sensitive_endpoint_and_path_details(tmp_path: Path) -> None:
    mlx = MLXLmServerAdapter(repo_root=tmp_path, bench_port=9999, server_log_path=tmp_path / "mlx.log")
    mlx_identity = mlx.build_backend_identity(operator_provider_id=None, provider_id_source="default")
    assert "repo_root" not in (mlx_identity.get("verified") or {})

    openai = OpenAICompatibleAdapter(base_url="https://internal.example.invalid", api_key="secret")
    openai_identity = openai.build_backend_identity(operator_provider_id=None, provider_id_source="default")
    assert "base_url" not in (openai_identity.get("verified") or {})
    assert openai_identity["verified"]["api_key_set"] is True
