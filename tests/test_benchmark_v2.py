from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from benchmarking import token as benchmark_token
from benchmarking.gate import _parse_probe_message
from benchmarking.roster import artifact_key, chat_template_kwargs_for_thinking_mode
from benchmarking.socials import main as generate_benchmark_socials_main
from benchmarking.summary import main as compile_benchmark_summary_main
from benchmarking.utils import resolve_model_id


def test_chat_template_kwargs_for_thinking_mode():
    assert chat_template_kwargs_for_thinking_mode("default") is None
    assert chat_template_kwargs_for_thinking_mode("on") == {"enable_thinking": True}
    assert chat_template_kwargs_for_thinking_mode("off") == {"enable_thinking": False}
    with pytest.raises(ValueError):
        chat_template_kwargs_for_thinking_mode("sideways")


def test_artifact_key_is_deterministic():
    entry = {
        "lane": "frontier_27b",
        "variant": "qwen35_27b_opus_distilled_v2",
        "thinking_mode": "off",
    }
    assert artifact_key(entry) == "frontier_27b__qwen35_27b_opus_distilled_v2__thinking-off"


def test_parse_probe_message_reads_reasoning_channel():
    parsed, source = _parse_probe_message("", '{"test": true}')
    assert parsed == {"test": True}
    assert source == "reasoning"


def test_canonical_token_prompts_are_domain_neutral():
    payload = "\n".join(
        [
            benchmark_token.PROMPT_MEDIUM.lower(),
            benchmark_token.PROMPT_STRUCTURED.lower(),
        ]
    )
    blocked_terms = [
        "agent civilization",
        "shared resource environment",
        "gather_food",
        "share_food",
        "share_tools",
        "move_location",
        "read_board",
        "post_knowledge",
        "yield_turn",
        "food pool",
        "tools pool",
    ]
    for term in blocked_terms:
        assert term not in payload


def test_resolve_model_id_prefers_explicit_target():
    payload = {"data": [{"id": "model-a"}, {"id": "model-b"}]}
    assert resolve_model_id(payload, target_model_id="model-b") == "model-b"


def test_resolve_model_id_raises_when_target_missing():
    payload = {"data": [{"id": "model-a"}]}
    with pytest.raises(ValueError):
        resolve_model_id(payload, target_model_id="model-b")


def _write_sample_roster(tmp_path: Path) -> tuple[Path, Path, dict[str, str]]:
    roster_path = tmp_path / "roster.json"
    entry = {
        "model_id": "NexVeridian/Qwen3.5-27B-4bit",
        "display_name": "Qwen3.5 27B Base",
        "variant": "qwen35_27b_base",
        "lane": "frontier_27b",
        "thinking_mode": "off",
        "source_label": "NexVeridian / Hugging Face",
        "source_badge": "Hugging Face",
        "required_cache": True,
    }
    roster_path.write_text(json.dumps({"entries": [entry]}))

    benchmarks_dir = tmp_path / "benchmarks"
    benchmarks_dir.mkdir()
    key = artifact_key(entry)
    (benchmarks_dir / f"{key}.json").write_text(
        json.dumps(
            {
                "validity": {
                    "valid_run": True,
                    "issues": [],
                    "token_count_sources": ["usage"],
                },
                "comparability": {
                    "comparable": True,
                    "protocol_id": "benchmark_v2_m5max_v1",
                    "prompt_set_id": "benchmark_v2_m5max_prompt_set_v1",
                },
                "summary": {
                    "short_tok_s": 42.5,
                    "structured_json_tok_s": 38.1,
                    "sustained_tok_s": 40.0,
                    "first_output_ms": 120.0,
                    "first_answer_ms": 150.0,
                },
            }
        )
    )
    gate_dir = benchmarks_dir / f"gate_{key}"
    gate_dir.mkdir()
    (gate_dir / "gate_result.json").write_text(
        json.dumps(
            {
                "decision": "run",
                "agent_civ_usable": "usable",
                "stage2": {
                    "status": "complete",
                    "synthetic_failures": 0,
                    "synthetic_rate": 0.0,
                    "invalid_location_rate": 0.1,
                    "share_count_5tick": 7,
                },
            }
        )
    )
    return roster_path, benchmarks_dir, entry


def test_compile_benchmark_summary_writes_token_summary_by_default(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    roster_path, benchmarks_dir, entry = _write_sample_roster(tmp_path)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "compile_benchmark_summary.py",
            "--benchmarks-dir",
            str(benchmarks_dir),
            "--roster",
            str(roster_path),
        ],
    )
    assert compile_benchmark_summary_main() == 0

    summary = json.loads((benchmarks_dir / "benchmark_v2_token_summary.json").read_text())
    row = summary["rows"][0]
    assert row["display_name"] == "Qwen3.5 27B Base"
    assert row["model_id"] == entry["model_id"]
    assert row["structured_json_tok_s"] == 38.1
    assert row["first_answer_ms"] == 150.0
    assert row["source_badge"] == "Hugging Face"
    assert "gate_decision" not in row
    assert not (benchmarks_dir / "benchmark_v2_gate_summary.json").exists()


def test_compile_benchmark_summary_writes_gate_summary_when_requested(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    roster_path, benchmarks_dir, _entry = _write_sample_roster(tmp_path)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "compile_benchmark_summary.py",
            "--benchmarks-dir",
            str(benchmarks_dir),
            "--roster",
            str(roster_path),
            "--write-gate",
        ],
    )
    assert compile_benchmark_summary_main() == 0

    summary = json.loads((benchmarks_dir / "benchmark_v2_gate_summary.json").read_text())
    row = summary["rows"][0]
    assert row["display_name"] == "Qwen3.5 27B Base"
    assert row["gate_decision"] == "run"
    assert row["agent_civ_usable"] == "usable"
    assert row["share_count_5tick"] == 7
    assert row["status"] == "complete"


def test_compile_benchmark_summary_skips_invalid_token_rows(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    roster_path, benchmarks_dir, entry = _write_sample_roster(tmp_path)
    key = artifact_key(entry)
    (benchmarks_dir / f"{key}.json").write_text(
        json.dumps(
            {
                "validity": {
                    "valid_run": False,
                    "issues": ["stream_fallback_seen"],
                    "token_count_sources": ["usage"],
                },
                "comparability": {
                    "comparable": False,
                    "protocol_id": "benchmark_v2_m5max_v1",
                    "prompt_set_id": "benchmark_v2_m5max_prompt_set_v1",
                },
                "summary": {
                    "short_tok_s": 42.5,
                    "structured_json_tok_s": 38.1,
                    "sustained_tok_s": 40.0,
                    "first_output_ms": 120.0,
                    "first_answer_ms": 150.0,
                },
            }
        )
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "compile_benchmark_summary.py",
            "--benchmarks-dir",
            str(benchmarks_dir),
            "--roster",
            str(roster_path),
        ],
    )
    assert compile_benchmark_summary_main() == 0

    summary = json.loads((benchmarks_dir / "benchmark_v2_token_summary.json").read_text())
    assert summary["row_count"] == 0


def test_generate_benchmark_socials_creates_expected_cards(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    summary_path = tmp_path / "benchmark_v2_token_summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "display_name": "Qwen3.5 27B Base",
                        "lane": "frontier_27b",
                        "thinking_mode": "off",
                        "structured_json_tok_s": 40.0,
                        "first_answer_ms": 120.0,
                        "short_tok_s": 42.0,
                        "sustained_tok_s": 39.0,
                    },
                    {
                        "display_name": "Qwen3.5 27B Base",
                        "lane": "frontier_27b",
                        "thinking_mode": "on",
                        "structured_json_tok_s": 34.0,
                        "first_answer_ms": 180.0,
                        "short_tok_s": 36.0,
                        "sustained_tok_s": 31.0,
                    },
                    {
                        "display_name": "Qwen3.5 27B Opus Distilled v2",
                        "lane": "frontier_27b",
                        "thinking_mode": "off",
                        "structured_json_tok_s": 44.0,
                        "first_answer_ms": 140.0,
                        "short_tok_s": 45.0,
                        "sustained_tok_s": 42.0,
                    },
                    {
                        "display_name": "Qwen3.5 27B Opus Distilled v2",
                        "lane": "frontier_27b",
                        "thinking_mode": "on",
                        "structured_json_tok_s": 36.0,
                        "first_answer_ms": 220.0,
                        "short_tok_s": 38.0,
                        "sustained_tok_s": 33.0,
                    },
                    {
                        "display_name": "Qwen2.5 Coder 14B",
                        "lane": "core",
                        "thinking_mode": "default",
                        "structured_json_tok_s": 52.0,
                        "first_answer_ms": 90.0,
                        "short_tok_s": 54.0,
                        "sustained_tok_s": 50.0,
                    },
                ]
            }
        )
    )
    gate_summary_path = tmp_path / "benchmark_v2_gate_summary.json"
    gate_summary_path.write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "display_name": "Qwen3.5 27B Base",
                        "lane": "frontier_27b",
                        "thinking_mode": "off",
                        "gate_decision": "run",
                        "status": "complete",
                        "synthetic_failures": 0,
                        "synthetic_rate": 0.0,
                        "invalid_location_rate": 0.05,
                        "share_count_5tick": 6,
                        "agent_civ_usable": "usable",
                    }
                ]
            }
        )
    )
    output_dir = tmp_path / "social"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "generate_benchmark_socials.py",
            "--summary",
            str(summary_path),
            "--gate-summary",
            str(gate_summary_path),
            "--output-dir",
            str(output_dir),
        ],
    )
    assert generate_benchmark_socials_main() == 0
    for name in (
        "27b_matchup_hero.png",
        "27b_thinking_delta.png",
        "speed_vs_latency_tradeoff.png",
        "full_mlx_ladder.png",
        "gate_validation_appendix.png",
    ):
        assert (output_dir / name).exists()
