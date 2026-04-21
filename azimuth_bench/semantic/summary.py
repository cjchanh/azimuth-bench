"""Semantic summary builder for anchored JSONL fixtures."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SEMANTIC_SUMMARY_VERSION = "azimuth_semantic_summary_v1"


def _read_jsonl_rows(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append({"line": line_number, "error": str(exc)})
            continue
        if isinstance(row, dict):
            rows.append(row)
        else:
            errors.append({"line": line_number, "error": "row is not a JSON object"})
    return rows, errors


def _output_has_content(row: dict[str, Any] | None) -> bool:
    if not row:
        return False
    for key in ("response", "output", "content", "text"):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return True
    return False


def build_semantic_summary(
    *,
    fixtures_path: Path,
    outputs_path: Path,
    scorer_identity: str,
    human_scores_path: Path | None = None,
    pass_threshold_ratio: float = 0.8,
) -> dict[str, Any]:
    """Emit a semantic summary artifact aligned with throughput but scored separately.

    Fixtures must include ``fixture_id`` and ``grading.max_score``. Human scores are supplied
    out-of-band unless ``human_scores_path`` contains JSONL rows shaped like::

        {"fixture_id": "...", "human_score": 4.0, "scorer": "...", "trusted": true}

    Model self-grading is rejected unless ``trusted`` is explicitly true.

    Args:
        fixtures_path: Fixture JSONL (rubrics).
        outputs_path: Model outputs JSONL joined by ``fixture_id``.
        scorer_identity: Stable label for who applied ``human_scores`` when present.
        human_scores_path: Optional JSONL with per-fixture numeric scores.
        pass_threshold_ratio: Fraction of ``max_score`` needed for PASS (default ``0.8`` → ``4/5``).

    Returns:
        Canonical semantic summary dictionary.
    """
    fixtures, fx_err = _read_jsonl_rows(fixtures_path)
    outputs, out_err = _read_jsonl_rows(outputs_path)
    integrity_errors: list[dict[str, Any]] = []
    fixture_id_set: set[str] = set()
    for index, fx in enumerate(fixtures, start=1):
        fid_raw = fx.get("fixture_id")
        if not isinstance(fid_raw, str) or not fid_raw.strip():
            integrity_errors.append({"fixture_index": index, "error": "fixture_missing_fixture_id"})
            continue
        fid = fid_raw.strip()
        if fid in fixture_id_set:
            integrity_errors.append({"fixture_id": fid, "error": "duplicate_fixture_id"})
        fixture_id_set.add(fid)

    outputs_by_id: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(outputs, start=1):
        fid_raw = row.get("fixture_id")
        if not isinstance(fid_raw, str) or not fid_raw.strip():
            integrity_errors.append({"output_index": index, "error": "output_missing_fixture_id"})
            continue
        fid = fid_raw.strip()
        if fid in outputs_by_id:
            integrity_errors.append({"fixture_id": fid, "error": "duplicate_output_id"})
        if fid not in fixture_id_set:
            integrity_errors.append({"fixture_id": fid, "error": "output_without_fixture"})
        outputs_by_id[fid] = row

    scores_by_id: dict[str, dict[str, Any]] = {}
    if human_scores_path is not None:
        hs_rows, hs_err = _read_jsonl_rows(human_scores_path)
        if hs_err:
            raise ValueError(f"human_scores JSONL parse errors: {hs_err}")
        for index, row in enumerate(hs_rows, start=1):
            fid = str(row.get("fixture_id", "")).strip()
            if not fid:
                integrity_errors.append({"score_index": index, "error": "score_missing_fixture_id"})
                continue
            if fid in scores_by_id:
                integrity_errors.append({"fixture_id": fid, "error": "duplicate_score_id"})
            if fid not in fixture_id_set:
                integrity_errors.append({"fixture_id": fid, "error": "score_without_fixture"})
            scores_by_id[fid] = row

    fixture_rows: list[dict[str, Any]] = []
    for fx in fixtures:
        fid_raw = fx.get("fixture_id")
        if not isinstance(fid_raw, str) or not fid_raw.strip():
            continue
        fid = fid_raw.strip()
        grading = fx.get("grading") if isinstance(fx.get("grading"), dict) else {}
        max_score = grading.get("max_score")
        if max_score is None:
            fixture_rows.append(
                {
                    "fixture_id": fid,
                    "status": "skipped",
                    "reason": "fixture_missing_grading.max_score",
                },
            )
            continue
        try:
            max_val = float(max_score)
        except (TypeError, ValueError):
            fixture_rows.append(
                {"fixture_id": fid, "status": "skipped", "reason": "grading.max_score_not_numeric"},
            )
            continue

        output_row = outputs_by_id.get(fid)
        output_present = _output_has_content(output_row)
        if output_row is not None and not output_present:
            integrity_errors.append({"fixture_id": fid, "error": "output_missing_content"})
        score_row = scores_by_id.get(fid)

        trusted = False
        source = "unscored"
        human_score: float | None = None
        if score_row:
            trusted = score_row.get("trusted") is True
            raw_src = score_row.get("source") or score_row.get("scorer") or "human"
            source = str(raw_src)
            hs = score_row.get("human_score")
            if hs is not None:
                try:
                    human_score = float(hs)
                except (TypeError, ValueError):
                    human_score = None
            if not trusted:
                reason = (
                    "model_self_grade_not_trusted"
                    if str(score_row.get("source", "")).lower() == "model_self_grade"
                    else "score_not_trusted"
                )
                fixture_rows.append(
                    {
                        "fixture_id": fid,
                        "status": "rejected",
                        "reason": reason,
                    },
                )
                continue

        threshold = max_val * pass_threshold_ratio
        passed = human_score is not None and human_score >= threshold
        fixture_rows.append(
            {
                "fixture_id": fid,
                "lane": fx.get("lane"),
                "max_score": max_val,
                "human_score": human_score,
                "pass": passed if human_score is not None else None,
                "scoring_status": "scored" if human_score is not None else "manual_required",
                "score_source": source,
                "trusted": trusted,
                "output_present": output_present,
            },
        )

    graded = [r for r in fixture_rows if r.get("scoring_status") == "scored"]
    manual_required = [r for r in fixture_rows if r.get("scoring_status") == "manual_required"]
    rejected = [r for r in fixture_rows if r.get("status") == "rejected"]
    skipped = [r for r in fixture_rows if r.get("status") == "skipped"]
    gate_pass = (
        bool(graded)
        and len(graded) == len(fixture_rows)
        and not manual_required
        and not rejected
        and not skipped
        and all(bool(r.get("output_present")) for r in graded)
        and all(bool(r.get("pass")) for r in graded)
        and not fx_err
        and not out_err
        and not integrity_errors
    )

    return {
        "schema": SEMANTIC_SUMMARY_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scorer_identity": scorer_identity.strip(),
        "fixtures_path_sha256": hashlib.sha256(fixtures_path.read_bytes()).hexdigest(),
        "outputs_path_sha256": hashlib.sha256(outputs_path.read_bytes()).hexdigest(),
        "human_scores_path_sha256": (
            hashlib.sha256(human_scores_path.read_bytes()).hexdigest() if human_scores_path else None
        ),
        "fixture_parse_errors": fx_err,
        "output_parse_errors": out_err,
        "integrity_errors": integrity_errors,
        "fixtures": fixture_rows,
        "aggregate": {
            "fixture_count": len(fixture_rows),
            "scored_count": len(graded),
            "manual_required_count": len(manual_required),
            "rejected_count": len(rejected),
            "skipped_count": len(skipped),
            "integrity_error_count": len(integrity_errors),
            "semantic_gate_pass": gate_pass,
        },
    }
