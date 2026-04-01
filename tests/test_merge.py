"""Portable multi-bundle merge (M5): validated Azimuth run directories only."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from azimuth_bench.errors import MergeCollisionError, MergeInputError
from azimuth_bench.export.markdown import write_markdown_export
from azimuth_bench.merge.bundle import merge_canonical_bundles
from azimuth_bench.report.builder import build_report


def _minimal_bench(
    dest: Path,
    repo_benchmarks: Path,
    *,
    model_id: str,
    artifact_filename: str,
    protocol_patch: dict[str, str] | None = None,
) -> None:
    """Copy one summary row and its artifact into ``dest``."""
    summary_src = json.loads((repo_benchmarks / "benchmark_v2_token_summary.json").read_text(encoding="utf-8"))
    rows = [r for r in summary_src["rows"] if r.get("model_id") == model_id]
    assert len(rows) == 1, model_id
    summary_src["row_count"] = 1
    summary_src["rows"] = rows
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "benchmark_v2_token_summary.json").write_text(json.dumps(summary_src, indent=2), encoding="utf-8")
    shutil.copy2(repo_benchmarks / artifact_filename, dest / artifact_filename)
    if protocol_patch:
        art = json.loads((dest / artifact_filename).read_text(encoding="utf-8"))
        if "protocol" in art and isinstance(art["protocol"], dict):
            art["protocol"].update(protocol_patch)
        if "comparability" in art and isinstance(art["comparability"], dict):
            art["comparability"].update({k: v for k, v in protocol_patch.items() if k.endswith("_id")})
        (dest / artifact_filename).write_text(json.dumps(art, indent=2), encoding="utf-8")


def _collect_json_texts(root: Path) -> list[str]:
    out: list[str] = []
    for p in sorted(root.rglob("*.json")):
        out.append(p.read_text(encoding="utf-8"))
    return out


@pytest.fixture
def repo_benchmarks() -> Path:
    return Path(__file__).resolve().parent.parent / "benchmarks"


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def test_merge_requires_at_least_one_include(repo_root: Path, repo_benchmarks: Path, tmp_path: Path) -> None:
    a = tmp_path / "a"
    _minimal_bench(
        a,
        repo_benchmarks,
        model_id="mlx-community/Phi-4-mini-instruct-4bit",
        artifact_filename="core__phi4_mini__thinking-default.json",
    )
    with pytest.raises(MergeInputError, match="at least one"):
        merge_canonical_bundles(a, [], repo_root=repo_root)


def test_merge_rejects_duplicate_run_directories(repo_root: Path, repo_benchmarks: Path, tmp_path: Path) -> None:
    a = tmp_path / "a"
    _minimal_bench(
        a,
        repo_benchmarks,
        model_id="mlx-community/Phi-4-mini-instruct-4bit",
        artifact_filename="core__phi4_mini__thinking-default.json",
    )
    with pytest.raises(MergeInputError, match="duplicate run directory"):
        merge_canonical_bundles(a, [a], repo_root=repo_root)


def test_merge_rejects_malformed_extra_bundle(repo_root: Path, repo_benchmarks: Path, tmp_path: Path) -> None:
    a = tmp_path / "a"
    b = tmp_path / "b"
    _minimal_bench(
        a,
        repo_benchmarks,
        model_id="mlx-community/Phi-4-mini-instruct-4bit",
        artifact_filename="core__phi4_mini__thinking-default.json",
    )
    b.mkdir()
    (b / "empty.json").write_text("{}", encoding="utf-8")
    with pytest.raises(MergeInputError, match="integrity|summary"):
        merge_canonical_bundles(a, [b], repo_root=repo_root)


def test_merge_blocks_duplicate_row_identity(repo_root: Path, repo_benchmarks: Path, tmp_path: Path) -> None:
    a = tmp_path / "a"
    b = tmp_path / "b"
    for d in (a, b):
        _minimal_bench(
            d,
            repo_benchmarks,
            model_id="mlx-community/Phi-4-mini-instruct-4bit",
            artifact_filename="core__phi4_mini__thinking-default.json",
        )
    with pytest.raises(MergeCollisionError, match="duplicate summary row identity"):
        merge_canonical_bundles(a, [b], repo_root=repo_root)


def test_merge_two_bundles_fully_comparable(repo_root: Path, repo_benchmarks: Path, tmp_path: Path) -> None:
    a = tmp_path / "a"
    b = tmp_path / "b"
    _minimal_bench(
        a,
        repo_benchmarks,
        model_id="mlx-community/Phi-4-mini-instruct-4bit",
        artifact_filename="core__phi4_mini__thinking-default.json",
    )
    _minimal_bench(
        b,
        repo_benchmarks,
        model_id="mlx-community/Qwen2.5-Coder-7B-Instruct-4bit",
        artifact_filename="core__qwen25_coder_7b__thinking-default.json",
    )
    out = build_report(a, repo_root=repo_root, include_run_dirs=(b,))
    data = out / "data"
    assert (data / "merge.json").exists()
    merge_meta = json.loads((data / "merge.json").read_text(encoding="utf-8"))
    assert merge_meta["schema"] == "azimuth_merge_v1"
    assert merge_meta["comparability_class"] == "fully_comparable"
    assert merge_meta["cross_protocol_ranking_allowed"] is True
    lb = json.loads((data / "leaderboard.json").read_text(encoding="utf-8"))
    assert lb.get("merge") == merge_meta
    summary = json.loads((data / "summary.json").read_text(encoding="utf-8"))
    assert summary["row_count"] == 2
    assert {r["merge_row_comparability_class"] for r in summary["rows"]} == {"fully_comparable"}
    runs_index = json.loads((data / "runs" / "index.json").read_text(encoding="utf-8"))
    assert len(runs_index["runs"]) == 2
    keys = {r["artifact_key"] for r in runs_index["runs"]}
    assert all(k.startswith("s0__") or k.startswith("s1__") for k in keys)
    for blob in _collect_json_texts(data):
        assert "/Users/" not in blob
        assert str(tmp_path) not in blob


def test_merge_protocol_mismatch_is_scoped_comparable(repo_root: Path, repo_benchmarks: Path, tmp_path: Path) -> None:
    a = tmp_path / "a"
    b = tmp_path / "b"
    _minimal_bench(
        a,
        repo_benchmarks,
        model_id="mlx-community/Phi-4-mini-instruct-4bit",
        artifact_filename="core__phi4_mini__thinking-default.json",
    )
    _minimal_bench(
        b,
        repo_benchmarks,
        model_id="mlx-community/Qwen2.5-Coder-7B-Instruct-4bit",
        artifact_filename="core__qwen25_coder_7b__thinking-default.json",
        protocol_patch={"protocol_id": "synthetic_other_protocol_v1", "prompt_set_id": "synthetic_other_prompt_set_v1"},
    )
    out = build_report(a, repo_root=repo_root, include_run_dirs=(b,))
    merge_meta = json.loads((out / "data" / "merge.json").read_text(encoding="utf-8"))
    assert merge_meta["comparability_class"] == "scoped_comparable"
    assert merge_meta["cross_protocol_ranking_allowed"] is False
    reasons = {b["reason"] for b in merge_meta["blockers"]}
    assert "multiple_protocol_ids" in reasons
    summary = json.loads((out / "data" / "summary.json").read_text(encoding="utf-8"))
    assert {r["merge_row_comparability_class"] for r in summary["rows"]} == {"scoped_comparable"}


def test_single_run_has_no_merge_json(repo_root: Path, repo_benchmarks: Path, tmp_path: Path) -> None:
    bench = tmp_path / "bench"
    _minimal_bench(
        bench,
        repo_benchmarks,
        model_id="mlx-community/Phi-4-mini-instruct-4bit",
        artifact_filename="core__phi4_mini__thinking-default.json",
    )
    build_report(bench, repo_root=repo_root)
    assert not (bench / "report" / "data" / "merge.json").exists()
    lb = json.loads((bench / "report" / "data" / "leaderboard.json").read_text(encoding="utf-8"))
    assert "merge" not in lb


def test_merge_export_markdown_and_stable_paths(repo_root: Path, repo_benchmarks: Path, tmp_path: Path) -> None:
    a = tmp_path / "a"
    b = tmp_path / "b"
    _minimal_bench(
        a,
        repo_benchmarks,
        model_id="mlx-community/Phi-4-mini-instruct-4bit",
        artifact_filename="core__phi4_mini__thinking-default.json",
    )
    _minimal_bench(
        b,
        repo_benchmarks,
        model_id="mlx-community/Qwen2.5-Coder-7B-Instruct-4bit",
        artifact_filename="core__qwen25_coder_7b__thinking-default.json",
    )
    build_report(a, repo_root=repo_root, include_run_dirs=(b,))
    md_path = tmp_path / "export.md"
    write_markdown_export(report_data_dir=a / "report" / "data", output_path=md_path)
    text = md_path.read_text(encoding="utf-8")
    assert "Azimuth Bench export" in text
    assert "Rows: 2" in text
    assert "/Users/" not in text
    assert str(tmp_path) not in text
