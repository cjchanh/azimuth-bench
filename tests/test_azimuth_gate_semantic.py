"""Semantic summary + promotion gate coverage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import aiohttp
import pytest

from azimuth_bench.adapters.base import BenchmarkAdapter
from azimuth_bench.adapters.capabilities import AdapterCapabilities
from azimuth_bench.adapters.factory import build_throughput_adapter
from azimuth_bench.adapters.identity import ProviderIdSource
from azimuth_bench.adapters.llama_cpp import LlamaCppServerAdapter
from azimuth_bench.adapters.openai_compatible import OpenAICompatibleAdapter
from azimuth_bench.cli.entrypoint import main as azbench_main
from azimuth_bench.core.cases import CaseSpec
from azimuth_bench.errors import UnsupportedAdapterFeatureError
from azimuth_bench.gates.promotion import build_promotion_report
from azimuth_bench.semantic.summary import build_semantic_summary
from azimuth_bench.suites import throughput as throughput_suite
from azimuth_bench.suites.throughput import BenchmarkIdentity, run_benchmark


class _TinyAdapter(BenchmarkAdapter):
    def capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            adapter_name="TinyAdapter",
            streaming=True,
            model_listing=True,
            model_selection=True,
            thinking_toggle=True,
            structured_output=True,
            openai_compatible_http=False,
            deployment_class="local",
        )

    def build_backend_identity(
        self,
        *,
        operator_provider_id: str | None,
        provider_id_source: ProviderIdSource,
    ) -> dict[str, Any]:
        return {
            "provider_id": operator_provider_id or "tiny",
            "provider_kind": "tiny",
            "adapter_name": "TinyAdapter",
            "provider_id_source": provider_id_source,
        }

    def list_models(self) -> list[str]:
        return ["tiny/model"]

    def healthcheck(self) -> bool:
        return True

    def prepare_target(self, target_model_id: str) -> dict[str, Any]:
        return {"served_model": target_model_id}

    def resolve_served_models(self) -> list[str]:
        return ["tiny/model"]

    def run_case(self, spec: CaseSpec, *, thinking_mode: str) -> dict[str, Any]:
        return {
            "prompt_id": spec.prompt_id,
            "first_answer_ms": 10.0,
            "first_output_ms": 12.0,
            "tok_per_sec": 100.0,
            "reasoning_chars": 0,
            "tokens_out": 10,
            "used_stream": True,
            "token_count_source": "adapter",
            "thinking_mode": thinking_mode,
        }

    def shutdown(self) -> None:
        return None


def test_llama_cpp_maps_thinking_http_errors_to_unsupported(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = LlamaCppServerAdapter(base_url="http://127.0.0.1:9")
    adapter._active_target_model_id = "dummy-model"  # noqa: SLF001

    async def _boom(
        self: OpenAICompatibleAdapter,
        spec: CaseSpec,
        *,
        thinking_mode: str,
    ) -> dict[str, object]:
        raise aiohttp.ClientResponseError(
            request_info=MagicMock(),
            history=(),
            status=400,
            message="Bad Request",
        )

    monkeypatch.setattr(OpenAICompatibleAdapter, "_run_case_async", _boom)

    spec = CaseSpec(
        suite_family="throughput",
        prompt_id="short",
        prompt="hi",
        max_tokens=8,
        metadata={"temperature": 0.3, "target_model_id": "dummy-model"},
    )

    with pytest.raises(UnsupportedAdapterFeatureError):
        adapter.run_case(spec, thinking_mode="off")


def test_llama_cpp_factory_identity_is_distinct_and_honest(tmp_path: Path) -> None:
    adapter = build_throughput_adapter(
        adapter_name="llama_cpp",
        repo_root=tmp_path,
        bench_port=8899,
        base_url="http://127.0.0.1:8001",
        max_tokens_default=512,
    )
    assert isinstance(adapter, LlamaCppServerAdapter)
    caps = adapter.capabilities()
    assert caps.thinking_toggle is True
    ident = adapter.build_backend_identity(operator_provider_id=None, provider_id_source="default")
    assert ident["provider_kind"] == "llama_cpp_server"
    assert ident["api_surface"] == "openai_compatible_http_llama_cpp"
    assert ident["verified"]["thinking_controls_expected"] is True
    assert ident["verified"]["thinking_controls_verified"] is False


def test_semantic_summary_gate_pass_with_human_scores(tmp_path: Path) -> None:
    fx = tmp_path / "fx.jsonl"
    fx.write_text(
        json.dumps(
            {
                "fixture_id": "f1",
                "lane": "repo_agent",
                "grading": {"max_score": 5},
            },
        )
        + "\n",
        encoding="utf-8",
    )
    out = tmp_path / "out.jsonl"
    out.write_text(json.dumps({"fixture_id": "f1", "response": "ok"}) + "\n", encoding="utf-8")
    hs = tmp_path / "hs.jsonl"
    hs.write_text(
        json.dumps({"fixture_id": "f1", "human_score": 5.0, "trusted": True, "source": "human"}) + "\n",
        encoding="utf-8",
    )
    summary = build_semantic_summary(
        fixtures_path=fx,
        outputs_path=out,
        scorer_identity="test",
        human_scores_path=hs,
    )
    assert summary["aggregate"]["semantic_gate_pass"] is True


def test_semantic_summary_rejected_self_grade_blocks_gate(tmp_path: Path) -> None:
    fx = tmp_path / "fx.jsonl"
    fx.write_text(
        "\n".join(
            [
                json.dumps({"fixture_id": "f1", "lane": "repo_agent", "grading": {"max_score": 5}}),
                json.dumps({"fixture_id": "f2", "lane": "repo_agent", "grading": {"max_score": 5}}),
            ],
        )
        + "\n",
        encoding="utf-8",
    )
    out = tmp_path / "out.jsonl"
    out.write_text(
        "\n".join(
            [
                json.dumps({"fixture_id": "f1", "response": "ok"}),
                json.dumps({"fixture_id": "f2", "response": "ok"}),
            ],
        )
        + "\n",
        encoding="utf-8",
    )
    hs = tmp_path / "hs.jsonl"
    hs.write_text(
        "\n".join(
            [
                json.dumps({"fixture_id": "f1", "human_score": 5.0, "trusted": True, "source": "human"}),
                json.dumps(
                    {
                        "fixture_id": "f2",
                        "human_score": 5.0,
                        "trusted": False,
                        "source": "model_self_grade",
                    },
                ),
            ],
        )
        + "\n",
        encoding="utf-8",
    )
    summary = build_semantic_summary(
        fixtures_path=fx,
        outputs_path=out,
        scorer_identity="test",
        human_scores_path=hs,
    )
    assert summary["aggregate"]["semantic_gate_pass"] is False
    assert summary["aggregate"]["rejected_count"] == 1


def test_semantic_summary_string_false_trusted_self_grade_is_rejected(tmp_path: Path) -> None:
    fx = tmp_path / "fx.jsonl"
    fx.write_text(json.dumps({"fixture_id": "f1", "grading": {"max_score": 5}}) + "\n", encoding="utf-8")
    out = tmp_path / "out.jsonl"
    out.write_text(json.dumps({"fixture_id": "f1", "response": "ok"}) + "\n", encoding="utf-8")
    hs = tmp_path / "hs.jsonl"
    hs.write_text(
        json.dumps(
            {
                "fixture_id": "f1",
                "human_score": 5.0,
                "trusted": "false",
                "source": "model_self_grade",
            },
        )
        + "\n",
        encoding="utf-8",
    )
    summary = build_semantic_summary(
        fixtures_path=fx,
        outputs_path=out,
        scorer_identity="test",
        human_scores_path=hs,
    )
    assert summary["aggregate"]["semantic_gate_pass"] is False
    assert summary["aggregate"]["rejected_count"] == 1


def test_semantic_summary_untrusted_human_score_is_rejected(tmp_path: Path) -> None:
    fx = tmp_path / "fx.jsonl"
    fx.write_text(json.dumps({"fixture_id": "f1", "grading": {"max_score": 5}}) + "\n", encoding="utf-8")
    out = tmp_path / "out.jsonl"
    out.write_text(json.dumps({"fixture_id": "f1", "response": "ok"}) + "\n", encoding="utf-8")
    hs = tmp_path / "hs.jsonl"
    hs.write_text(
        json.dumps({"fixture_id": "f1", "human_score": 5.0, "trusted": False, "source": "human"}) + "\n",
        encoding="utf-8",
    )
    summary = build_semantic_summary(
        fixtures_path=fx,
        outputs_path=out,
        scorer_identity="test",
        human_scores_path=hs,
    )
    assert summary["aggregate"]["semantic_gate_pass"] is False
    assert summary["aggregate"]["rejected_count"] == 1
    assert summary["fixtures"][0]["reason"] == "score_not_trusted"


def test_semantic_summary_integrity_errors_block_gate(tmp_path: Path) -> None:
    fx = tmp_path / "fx.jsonl"
    fx.write_text(json.dumps({"fixture_id": "f1", "grading": {"max_score": 5}}) + "\n", encoding="utf-8")
    out = tmp_path / "out.jsonl"
    out.write_text(json.dumps({"fixture_id": "f1", "response": "ok"}) + "\n", encoding="utf-8")
    hs = tmp_path / "hs.jsonl"
    hs.write_text(
        "\n".join(
            [
                json.dumps({"fixture_id": "f1", "human_score": 5.0, "trusted": True, "source": "human"}),
                json.dumps({"fixture_id": "unknown", "human_score": 5.0, "trusted": True, "source": "human"}),
            ],
        )
        + "\n",
        encoding="utf-8",
    )
    summary = build_semantic_summary(
        fixtures_path=fx,
        outputs_path=out,
        scorer_identity="test",
        human_scores_path=hs,
    )
    assert summary["aggregate"]["semantic_gate_pass"] is False
    assert summary["aggregate"]["integrity_error_count"] == 1


def test_semantic_summary_missing_fixture_id_blocks_gate(tmp_path: Path) -> None:
    fx = tmp_path / "fx.jsonl"
    fx.write_text(
        "\n".join(
            [
                json.dumps({"fixture_id": "f1", "grading": {"max_score": 5}}),
                json.dumps({"grading": {"max_score": 5}}),
            ],
        )
        + "\n",
        encoding="utf-8",
    )
    out = tmp_path / "out.jsonl"
    out.write_text(json.dumps({"fixture_id": "f1", "response": "ok"}) + "\n", encoding="utf-8")
    hs = tmp_path / "hs.jsonl"
    hs.write_text(
        json.dumps({"fixture_id": "f1", "human_score": 5.0, "trusted": True, "source": "human"}) + "\n",
        encoding="utf-8",
    )
    summary = build_semantic_summary(
        fixtures_path=fx,
        outputs_path=out,
        scorer_identity="test",
        human_scores_path=hs,
    )
    assert summary["aggregate"]["semantic_gate_pass"] is False
    assert {"fixture_index": 2, "error": "fixture_missing_fixture_id"} in summary["integrity_errors"]


def test_semantic_summary_bad_join_rows_block_gate(tmp_path: Path) -> None:
    fx = tmp_path / "fx.jsonl"
    fx.write_text(json.dumps({"fixture_id": "f1", "grading": {"max_score": 5}}) + "\n", encoding="utf-8")
    out = tmp_path / "out.jsonl"
    out.write_text(
        "\n".join(
            [
                json.dumps({"fixture_id": "f1", "response": "ok"}),
                json.dumps({"fixture_id": "extra", "response": "orphan"}),
                json.dumps({"response": "missing id"}),
            ],
        )
        + "\n",
        encoding="utf-8",
    )
    hs = tmp_path / "hs.jsonl"
    hs.write_text(
        "\n".join(
            [
                json.dumps({"fixture_id": "f1", "human_score": 5.0, "trusted": True, "source": "human"}),
                json.dumps({"human_score": 5.0, "trusted": True, "source": "human"}),
            ],
        )
        + "\n",
        encoding="utf-8",
    )
    summary = build_semantic_summary(
        fixtures_path=fx,
        outputs_path=out,
        scorer_identity="test",
        human_scores_path=hs,
    )
    assert summary["aggregate"]["semantic_gate_pass"] is False
    assert {"fixture_id": "extra", "error": "output_without_fixture"} in summary["integrity_errors"]
    assert {"output_index": 3, "error": "output_missing_fixture_id"} in summary["integrity_errors"]
    assert {"score_index": 2, "error": "score_missing_fixture_id"} in summary["integrity_errors"]


def test_semantic_summary_output_without_content_blocks_gate(tmp_path: Path) -> None:
    fx = tmp_path / "fx.jsonl"
    fx.write_text(json.dumps({"fixture_id": "f1", "grading": {"max_score": 5}}) + "\n", encoding="utf-8")
    out = tmp_path / "out.jsonl"
    out.write_text(json.dumps({"fixture_id": "f1"}) + "\n", encoding="utf-8")
    hs = tmp_path / "hs.jsonl"
    hs.write_text(
        json.dumps({"fixture_id": "f1", "human_score": 5.0, "trusted": True, "source": "human"}) + "\n",
        encoding="utf-8",
    )
    summary = build_semantic_summary(
        fixtures_path=fx,
        outputs_path=out,
        scorer_identity="test",
        human_scores_path=hs,
    )
    assert summary["aggregate"]["semantic_gate_pass"] is False
    assert summary["fixtures"][0]["output_present"] is False
    assert {"fixture_id": "f1", "error": "output_missing_content"} in summary["integrity_errors"]


def test_semantic_summary_cli_writes_artifact_and_fail_on_gate(tmp_path: Path) -> None:
    fx = tmp_path / "fx.jsonl"
    fx.write_text(json.dumps({"fixture_id": "f1", "grading": {"max_score": 5}}) + "\n", encoding="utf-8")
    out = tmp_path / "out.jsonl"
    out.write_text(json.dumps({"fixture_id": "f1", "response": "ok"}) + "\n", encoding="utf-8")
    hs = tmp_path / "hs.jsonl"
    hs.write_text(
        json.dumps({"fixture_id": "f1", "human_score": 5.0, "trusted": False, "source": "model_self_grade"}) + "\n",
        encoding="utf-8",
    )
    artifact = tmp_path / "semantic.json"
    code = azbench_main(
        [
            "bench",
            "semantic-summary",
            "--fixtures",
            str(fx),
            "--outputs",
            str(out),
            "--human-scores",
            str(hs),
            "--scorer",
            "cli-test",
            "--output",
            str(artifact),
            "--fail-on-gate",
        ],
    )
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    assert code == 1
    assert payload["schema"] == "azimuth_semantic_summary_v1"
    assert payload["aggregate"]["semantic_gate_pass"] is False


def test_promotion_gate_defaults_only_with_semantics() -> None:
    report = build_promotion_report(
        {
            "throughput": {"valid_run": True, "comparable": True},
            "semantic": {"gate_pass": True},
            "blockers": [],
            "approve_default_route": True,
        },
    )
    assert report["classification"] == "default"


def test_promotion_gate_rejects_throughput_only_default() -> None:
    report = build_promotion_report(
        {
            "throughput": {"valid_run": True, "comparable": True},
            "semantic": {},
            "blockers": [],
            "approve_default_route": True,
        },
    )
    assert report["classification"] == "candidate"


def test_promotion_gate_rejects_string_false_booleans() -> None:
    report = build_promotion_report(
        {
            "throughput": {"valid_run": "false", "comparable": "true"},
            "semantic": {"gate_pass": True},
            "blockers": [],
            "approve_default_route": "true",
        },
    )
    assert report["classification"] == "rejected"
    assert "throughput_invalid" in report["notes"]


def test_promotion_gate_string_approval_cannot_default() -> None:
    report = build_promotion_report(
        {
            "throughput": {"valid_run": True, "comparable": True},
            "semantic": {"gate_pass": True},
            "blockers": [],
            "approve_default_route": "true",
        },
    )
    assert report["classification"] == "candidate"


def test_promotion_gate_malformed_semantic_gate_cannot_default() -> None:
    report = build_promotion_report(
        {
            "throughput": {"valid_run": True, "comparable": True},
            "semantic": {"gate_pass": "true"},
            "blockers": [],
            "approve_default_route": True,
        },
    )
    assert report["classification"] == "candidate"
    assert "semantic_evidence_malformed" in report["notes"]


def test_promotion_gate_cli_writes_report(tmp_path: Path) -> None:
    payload = tmp_path / "evidence.json"
    payload.write_text(
        json.dumps(
            {
                "throughput": {"valid_run": True, "comparable": True},
                "semantic": {"gate_pass": True},
                "blockers": [],
                "approve_default_route": True,
            },
        ),
        encoding="utf-8",
    )
    out = tmp_path / "promotion.json"
    code = azbench_main(["bench", "promotion-gate", "--input", str(payload), "--output", str(out)])
    report = json.loads(out.read_text(encoding="utf-8"))
    assert code == 0
    assert report["schema"] == "azimuth_promotion_gate_v1"
    assert report["classification"] == "default"


def test_throughput_artifact_records_route_identity_and_telemetry(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(throughput_suite, "_vm_pages_free", lambda: "Pages free: 42.")
    results = run_benchmark(
        adapter=_TinyAdapter(),
        identity=BenchmarkIdentity(
            target_model_id="tiny/model",
            display_name="Tiny",
            lane="repo_agent",
            thinking_mode="off",
            source_label="test",
            source_badge="Test",
            route_label="repo_default",
            sampling_policy="test_policy",
        ),
        max_tokens=64,
        smoke=True,
        machine_class="test_machine",
    )
    assert results["route_identity"]["adapter_name"] == "TinyAdapter"
    assert results["route_identity"]["route_label"] == "repo_default"
    assert results["route_identity"]["sampling_policy"] == "test_policy"
    assert results["telemetry"]["memory_vm_pages_free_before"] == "Pages free: 42."
    assert results["telemetry"]["context_length_status"] == "unavailable"
    assert results["summary"]["valid_run"] is True


def test_fixture_pack_samples_are_valid_jsonl() -> None:
    root = Path(__file__).resolve().parents[1] / "fixture_packs"
    for sub in ("repo-agent-mini", "tool-calling-mini", "json-reliability", "long-context-local"):
        path = root / sub / "sample_fixtures.jsonl"
        assert path.is_file(), path
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                json.loads(line)
