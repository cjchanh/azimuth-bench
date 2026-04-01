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

