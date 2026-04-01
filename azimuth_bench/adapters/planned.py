"""Adapters that remain roadmap-only (explicit stubs; not production parity)."""

from __future__ import annotations

# Implemented in this repo (see SOURCE_OF_TRUTH.md): mlx, openai_compatible, ollama.
# Planned interfaces only (no production CLI wiring yet):
# - llama.cpp: server binary + OpenAI-compatible HTTP; process lifecycle TBD.
# - vLLM: HTTP OpenAI-compatible; multi-GPU and tensor parallel out of scope here.

PLANNED_ADAPTERS: tuple[str, ...] = ("llama_cpp", "vllm")
