#!/usr/bin/env python3
"""Compatibility entrypoint for ``python -m benchmarking.token``.

Canonical implementation lives in :mod:`azimuth_bench.cli.throughput` and :mod:`azimuth_bench.suites.throughput`.
"""

from __future__ import annotations

from azimuth_bench.cli.throughput import main, parse_args
from azimuth_bench.suites.throughput import (
    PROMPT_LONG,
    PROMPT_MEDIUM,
    PROMPT_SHORT,
    PROMPT_STRUCTURED,
    PROTOCOL_ID,
    benchmark_protocol,
)

__all__ = [
    "PROTOCOL_ID",
    "PROMPT_LONG",
    "PROMPT_MEDIUM",
    "PROMPT_SHORT",
    "PROMPT_STRUCTURED",
    "benchmark_protocol",
    "main",
    "parse_args",
]

if __name__ == "__main__":
    raise SystemExit(main())
