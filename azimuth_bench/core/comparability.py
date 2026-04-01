"""Comparability rules derived from protocol + validity (explicit, no silent claims)."""

from __future__ import annotations

from typing import Any


def comparability_block(
    *,
    protocol: dict[str, Any],
    validity: dict[str, Any],
) -> dict[str, Any]:
    """Build the comparability envelope stored on artifacts and summaries."""
    token_count_sources = sorted({str(x) for x in validity.get("token_count_sources", [])})
    blockers = [str(x) for x in validity.get("issues", []) if isinstance(x, str)]
    comparable = bool(validity.get("valid_run"))
    return {
        "comparable": comparable,
        "comparable_scope": "protocol_exact" if comparable else "not_comparable",
        "comparability_blockers": blockers,
        "protocol_id": protocol["protocol_id"],
        "prompt_set_id": protocol["prompt_set_id"],
        "warm_interpretation": "warm_after_load",
        "cold_interpretation": "model_load_receipt_only",
        "token_count_sources": token_count_sources,
    }


def merge_comparability_flags(*blocks: dict[str, Any]) -> dict[str, Any]:
    """Merge multiple comparability blocks for host JSON (all must be comparable for AND semantics)."""
    comparable = all(bool(b.get("comparable")) for b in blocks) if blocks else False
    protocol_ids = sorted({str(b.get("protocol_id", "")) for b in blocks if b.get("protocol_id")})
    blockers = sorted(
        {
            str(blocker)
            for block in blocks
            for blocker in (block.get("comparability_blockers") or [])
            if isinstance(blocker, str)
        }
    )
    scopes = sorted({str(b.get("comparable_scope", "")) for b in blocks if b.get("comparable_scope")})
    return {
        "comparable": comparable,
        "protocol_ids": protocol_ids,
        "count": len(blocks),
        "comparable_scope": scopes[0] if len(scopes) == 1 else ("mixed" if scopes else None),
        "comparability_blockers": blockers,
    }
