"""Case specifications for adapter-level single-case runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CaseSpec:
    """Identifies one measured case inside a suite."""

    suite_family: str
    prompt_id: str
    prompt: str = ""
    max_tokens: int = 256
    metadata: dict[str, Any] = field(default_factory=dict)
