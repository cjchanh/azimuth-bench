"""Shared utilities for benchmark-v2 package modules."""

from __future__ import annotations

from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ROSTER = ROOT / "configs" / "benchmark_v2_models.json"
DEFAULT_BENCHMARKS_DIR = ROOT / "benchmarks"
DEFAULT_SOCIALS_DIR = ROOT / "visuals" / "social" / "benchmark_v2"


def coerce_message_text(value: Any) -> str:
    """Collapse OpenAI-compatible message payload shapes into plain text."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                for key in ("text", "content", "value"):
                    piece = item.get(key)
                    if isinstance(piece, str):
                        parts.append(piece)
                        break
        return "".join(parts)
    return str(value)


def model_ids_from_payload(payload: Any) -> list[str]:
    """Extract model ids from an OpenAI-compatible /v1/models payload."""
    if not isinstance(payload, dict):
        return []
    data = payload.get("data")
    if not isinstance(data, list):
        return []
    model_ids: list[str] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        model_id = item.get("id")
        if isinstance(model_id, str) and model_id:
            model_ids.append(model_id)
    return model_ids


def resolve_model_id(payload: Any, *, target_model_id: str | None = None) -> str:
    """Resolve the intended model id from a /v1/models payload."""
    model_ids = model_ids_from_payload(payload)
    if not model_ids:
        raise ValueError("models payload did not contain any model ids")
    if target_model_id is None:
        return model_ids[0]
    if target_model_id not in model_ids:
        raise ValueError(f"target model {target_model_id!r} not present in models payload")
    return target_model_id
