"""Adapters that remain roadmap-only (explicit stubs; not production parity)."""

from __future__ import annotations

# Implemented in this repo (see SOURCE_OF_TRUTH.md): mlx, openai_compatible, ollama,
# llama_cpp (OpenAI-compatible llama-server surface; no binary lifecycle management here).
# Planned interfaces only:
# - vLLM: HTTP OpenAI-compatible; multi-GPU and tensor parallel out of scope here.

PLANNED_ADAPTERS: tuple[str, ...] = ("vllm",)
