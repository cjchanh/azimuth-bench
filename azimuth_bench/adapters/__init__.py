"""Azimuth Adapters — provider implementations for Azimuth Bench."""

from __future__ import annotations

from azimuth_bench.adapters.base import BenchmarkAdapter
from azimuth_bench.adapters.capabilities import AdapterCapabilities
from azimuth_bench.adapters.factory import build_throughput_adapter
from azimuth_bench.adapters.mlx import MLXLmServerAdapter
from azimuth_bench.adapters.ollama import OllamaAdapter
from azimuth_bench.adapters.openai_compatible import OpenAICompatibleAdapter

__all__ = [
    "AdapterCapabilities",
    "BenchmarkAdapter",
    "MLXLmServerAdapter",
    "OllamaAdapter",
    "OpenAICompatibleAdapter",
    "build_throughput_adapter",
]
