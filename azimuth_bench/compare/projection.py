"""Build compare.json envelope: stable keys, scoped pairs, explicit limits."""

from __future__ import annotations

from typing import Any

from azimuth_bench.core.runtime import slugify
from azimuth_bench.schema.version import AZIMUTH_BENCH_SCHEMA_VERSION


def _metric_slice(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "structured_json_tok_s": float(row.get("structured_json_tok_s") or 0.0),
        "sustained_tok_s": float(row.get("sustained_tok_s") or 0.0),
        "short_tok_s": float(row.get("short_tok_s") or 0.0),
        "first_answer_ms": float(row.get("first_answer_ms") or 0.0),
        "first_output_ms": float(row.get("first_output_ms") or 0.0),
    }


def _protocol_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ids = sorted({str(r.get("protocol_id") or "") for r in rows if r.get("protocol_id")})
    ids = [x for x in ids if x]
    if len(ids) == 1:
        return {"protocol_id": ids[0], "status": "single_protocol"}
    if not ids:
        return {"protocol_id": None, "status": "unknown"}
    return {"protocol_id": "mixed", "protocol_ids": ids, "status": "mixed_protocols"}


def build_compare_projection(summary_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Return compare bundle: legacy frontier deltas + structured projection + explicit non-claims."""
    frontier = [row for row in summary_rows if row.get("lane") == "frontier_27b"]
    index = {(row.get("display_name"), row.get("thinking_mode")): row for row in frontier}

    frontier_pairs: list[dict[str, Any]] = []
    detailed_pairs: list[dict[str, Any]] = []
    wanted = [("on", "thinking_on"), ("off", "thinking_off")]
    for thinking_mode, label in wanted:
        base = index.get(("Qwen3.5 27B Base", thinking_mode))
        distilled = index.get(("Qwen3.5 27B Opus Distilled v2", thinking_mode))
        if not base or not distilled:
            continue
        sd = round(
            float(distilled.get("structured_json_tok_s") or 0.0) - float(base.get("structured_json_tok_s") or 0.0),
            1,
        )
        sus = round(
            float(distilled.get("sustained_tok_s") or 0.0) - float(base.get("sustained_tok_s") or 0.0),
            1,
        )
        fa = round(
            float(distilled.get("first_answer_ms") or 0.0) - float(base.get("first_answer_ms") or 0.0),
            1,
        )
        frontier_pairs.append(
            {
                "label": label,
                "structured_json_tok_s_delta": sd,
                "sustained_tok_s_delta": sus,
                "first_answer_ms_delta": fa,
            }
        )
        ck = f"frontier_27b|{thinking_mode}|qwen35_27b_base_vs_opus_distilled_v2"
        detailed_pairs.append(
            {
                "comparison_key": ck,
                "comparison_key_slug": slugify(ck),
                "scope": {"lane": "frontier_27b", "thinking_mode": thinking_mode},
                "left": {
                    "role": "reference",
                    "display_name": str(base.get("display_name") or ""),
                    "artifact_key": str(base.get("artifact_key") or slugify(str(base.get("model_id", "base")))),
                    "metrics": _metric_slice(base),
                    "comparable": bool(base.get("comparable", True)),
                },
                "right": {
                    "role": "candidate",
                    "display_name": str(distilled.get("display_name") or ""),
                    "artifact_key": str(
                        distilled.get("artifact_key") or slugify(str(distilled.get("model_id", "distilled")))
                    ),
                    "metrics": _metric_slice(distilled),
                    "comparable": bool(distilled.get("comparable", True)),
                },
                "deltas": {
                    "structured_json_tok_s": sd,
                    "sustained_tok_s": sus,
                    "first_answer_ms": fa,
                },
                "comparability": {
                    "status": "comparable_within_scope",
                    "blockers": [],
                    "note": "Scoped to frontier_27b lane and matching thinking_mode; not a universal model ranking.",
                },
            }
        )

    blocked = [
        {
            "comparison_key": "cross_lane_core_vs_frontier",
            "reason": "not_emitted",
            "detail": "No automatic base-vs-frontier numeric pairing; lanes encode different run contexts.",
        },
        {
            "comparison_key": "cross_protocol_merge",
            "reason": "not_emitted",
            "detail": "Rows with differing protocol_id values are not merged into one delta in this projection.",
        },
    ]

    return {
        "azimuth_bench_schema_version": AZIMUTH_BENCH_SCHEMA_VERSION,
        "compare_schema": "azimuth_compare_v1",
        "frontier_pairs": frontier_pairs,
        "projection": {
            "protocol_summary": _protocol_summary(summary_rows),
            "pairs": detailed_pairs,
            "blocked_comparisons": blocked,
            "honesty_notes": [
                "This projection only emits explicit pairwise rows; "
                "it does not establish a total order across all models.",
                "Use leaderboard.json for within-summary ordering; "
                "interpret lane and protocol fields before comparing numbers.",
            ],
        },
    }
