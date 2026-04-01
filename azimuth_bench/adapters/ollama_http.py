"""Ollama HTTP ``/api/chat`` streaming metrics (NDJSON)."""

from __future__ import annotations

import json
import time
from typing import Any

import aiohttp


async def measure_ollama_chat_metrics(
    session: aiohttp.ClientSession,
    *,
    chat_url: str,
    model_id: str,
    user_prompt: str,
    max_tokens: int,
) -> dict[str, Any]:
    """POST Ollama ``/api/chat`` with ``stream: true`` and return throughput row fields."""
    payload: dict[str, Any] = {
        "model": model_id,
        "messages": [{"role": "user", "content": user_prompt}],
        "stream": True,
        "options": {"num_predict": max(1, int(max_tokens))},
    }
    start = time.perf_counter()
    first_output: float | None = None
    first_answer: float | None = None
    content_parts: list[str] = []
    tokens_out: int | None = None
    prompt_tokens: int | None = None
    buffer = b""

    async with session.post(chat_url, json=payload) as resp:
        resp.raise_for_status()
        async for chunk in resp.content:
            buffer += chunk
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    obj = json.loads(stripped.decode("utf-8"))
                except json.JSONDecodeError:
                    continue
                msg = obj.get("message")
                if isinstance(msg, dict):
                    piece = msg.get("content")
                    if isinstance(piece, str) and piece:
                        if first_output is None:
                            first_output = time.perf_counter()
                        if first_answer is None:
                            first_answer = time.perf_counter()
                        content_parts.append(piece)
                if obj.get("done") is True:
                    ec = obj.get("eval_count")
                    if isinstance(ec, int):
                        tokens_out = ec
                    pt = obj.get("prompt_eval_count")
                    if isinstance(pt, int):
                        prompt_tokens = pt

    end = time.perf_counter()
    content = "".join(content_parts)
    token_count_source = "usage"
    if tokens_out is None:
        tokens_out = len(content.split()) if content.strip() else 0
        token_count_source = "rough_split"
    tokens_in = prompt_tokens if prompt_tokens is not None else 0
    elapsed = end - start

    return {
        "first_output_ms": round(((first_output or end) - start) * 1000, 1),
        "first_answer_ms": round(((first_answer or end) - start) * 1000, 1),
        "ttft_ms": round(((first_answer or end) - start) * 1000, 1),
        "total_ms": round(elapsed * 1000, 1),
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "tok_per_sec": round(tokens_out / elapsed, 1) if elapsed > 0 else 0.0,
        "answer_chars": len(content),
        "reasoning_chars": 0,
        "content_present": bool(content),
        "reasoning_present": False,
        "used_stream": True,
        "token_count_source": token_count_source,
    }
