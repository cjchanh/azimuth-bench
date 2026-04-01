"""Benchmark suite family definitions (platform shape; not all suites are fully wired)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SuiteFamily(str, Enum):
    """High-level benchmark families supported by the platform."""

    THROUGHPUT = "throughput"
    LATENCY_TTFT = "latency_ttft"
    STRUCTURED_RELIABILITY = "structured_reliability"
    LONG_CONTEXT = "long_context"
    THINKING_OVERHEAD = "thinking_overhead"
    LOAD_SWAP = "load_swap"
    SYSTEM_THERMAL = "system_thermal"


@dataclass(frozen=True)
class SuiteFamilyInfo:
    """Describes a suite family for documentation and future runners."""

    family: SuiteFamily
    summary: str
    status: str


SUITE_REGISTRY: tuple[SuiteFamilyInfo, ...] = (
    SuiteFamilyInfo(
        SuiteFamily.THROUGHPUT,
        "Sustained and prompt-class token throughput (short, structured, medium, long, sustained).",
        "implemented_mlx",
    ),
    SuiteFamilyInfo(
        SuiteFamily.LATENCY_TTFT,
        "Time to first token / first answer on streaming paths.",
        "implemented_mlx",
    ),
    SuiteFamilyInfo(
        SuiteFamily.STRUCTURED_RELIABILITY,
        "JSON-shaped outputs and parse or schema adherence.",
        "implemented_mlx",
    ),
    SuiteFamilyInfo(
        SuiteFamily.LONG_CONTEXT,
        "Long-input prompt stress (token budget and completion).",
        "implemented_mlx",
    ),
    SuiteFamilyInfo(
        SuiteFamily.THINKING_OVERHEAD,
        "Reasoning-channel vs answer-channel timing when applicable.",
        "partial_mlx",
    ),
    SuiteFamilyInfo(
        SuiteFamily.LOAD_SWAP,
        "Model load and swap receipts (pages, wall time).",
        "implemented_mlx",
    ),
    SuiteFamilyInfo(
        SuiteFamily.SYSTEM_THERMAL,
        "Optional power/thermal sampling (OS-specific).",
        "designed",
    ),
)
