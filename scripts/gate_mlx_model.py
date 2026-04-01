#!/usr/bin/env python3
"""Thin wrapper for the benchmark-v2 optional gate CLI."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from benchmarking.gate import main


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
