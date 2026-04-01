"""Canonical token-summary field list and row extraction from artifact JSON."""

from __future__ import annotations

from typing import Any

TOKEN_FIELDS = [
    "model_id",
    "display_name",
    "lane",
    "thinking_mode",
    "short_tok_s",
    "structured_json_tok_s",
    "sustained_tok_s",
    "first_output_ms",
    "first_answer_ms",
    "source_label",
    "source_badge",
]


def _round_numeric(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 4)
    return value


def token_row_from_artifact_payload(
    entry: dict[str, Any],
    bench_payload: dict[str, Any],
) -> dict[str, Any] | None:
    """Build one token-summary row if the artifact is valid and comparable; else ``None``."""
    validity = bench_payload.get("validity")
    comparability = bench_payload.get("comparability")
    if not isinstance(validity, dict) or not bool(validity.get("valid_run")):
        return None
    if not isinstance(comparability, dict) or not bool(comparability.get("comparable")):
        return None
    summary = bench_payload.get("summary", {})
    if not isinstance(summary, dict):
        return None
    row = {
        "model_id": entry["model_id"],
        "display_name": entry["display_name"],
        "lane": entry["lane"],
        "thinking_mode": entry["thinking_mode"],
        "short_tok_s": summary.get("short_tok_s", 0.0),
        "structured_json_tok_s": summary.get("structured_json_tok_s", 0.0),
        "sustained_tok_s": summary.get("sustained_tok_s", 0.0),
        "first_output_ms": summary.get("first_output_ms", 0.0),
        "first_answer_ms": summary.get("first_answer_ms", 0.0),
        "source_label": entry["source_label"],
        "source_badge": entry["source_badge"],
    }
    return {field: _round_numeric(row[field]) for field in TOKEN_FIELDS}
