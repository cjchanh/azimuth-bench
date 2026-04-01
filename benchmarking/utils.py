"""Compatibility imports for legacy benchmark-v2 modules."""

from __future__ import annotations

from azimuth_bench.core.runtime import (
    DEFAULT_BENCHMARKS_DIR,
    DEFAULT_ROSTER,
    DEFAULT_SOCIALS_DIR,
    ROOT,
    coerce_message_text,
    model_ids_from_payload,
    resolve_model_id,
)

__all__ = [
    "ROOT",
    "DEFAULT_ROSTER",
    "DEFAULT_BENCHMARKS_DIR",
    "DEFAULT_SOCIALS_DIR",
    "coerce_message_text",
    "model_ids_from_payload",
    "resolve_model_id",
]
