"""Shared OpenAI-compatible HTTP chat metrics (streaming + non-streaming fallback)."""

from __future__ import annotations

import json
import time
from typing import Any

import aiohttp

from azimuth_bench.core.runtime import coerce_message_text


async def measure_chat_completion_metrics(
    session: aiohttp.ClientSession,
    *,
    chat_completions_url: str,
    model_id: str,
    user_prompt: str,
    max_tokens: int,
    temperature: float,
    chat_template_kwargs: dict[str, Any] | None,
) -> dict[str, Any]:
    """POST ``/v1/chat/completions`` and return throughput row fields aligned with the throughput suite."""
    payload: dict[str, Any] = {
        "model": model_id,
        "messages": [{"role": "user", "content": user_prompt}],
        "max_tokens": max_tokens,
        "temperature": float(temperature),
        "stream": False,
    }
    if chat_template_kwargs is not None:
        payload["chat_template_kwargs"] = chat_template_kwargs

    url = chat_completions_url
    start = time.perf_counter()
    first_output: float | None = None
    first_answer: float | None = None
    streamed_content: list[str] = []
    streamed_reasoning: list[str] = []
    usage: dict[str, Any] = {}
    request_payload = dict(payload)
    request_payload["stream"] = True
    request_payload["stream_options"] = {"include_usage": True}

    try:
        async with session.post(url, json=request_payload) as resp:
            resp.raise_for_status()
            buffer = ""
            async for chunk in resp.content:
                buffer += chunk.decode("utf-8", errors="ignore")
                while "\n\n" in buffer:
                    event, buffer = buffer.split("\n\n", 1)
                    for line in event.splitlines():
                        if not line.startswith("data:"):
                            continue
                        data_str = line[5:].strip()
                        if not data_str or data_str == "[DONE]":
                            continue
                        data = json.loads(data_str)
                        usage = data.get("usage", usage)
                        choices = data.get("choices", [])
                        if not choices:
                            continue
                        delta = choices[0].get("delta", {})
                        reasoning_piece = coerce_message_text(delta.get("reasoning"))
                        content_piece = coerce_message_text(delta.get("content"))
                        if (content_piece or reasoning_piece) and first_output is None:
                            first_output = time.perf_counter()
                        if content_piece and first_answer is None:
                            first_answer = time.perf_counter()
                        if reasoning_piece:
                            streamed_reasoning.append(reasoning_piece)
                        if content_piece:
                            streamed_content.append(content_piece)
        content = "".join(streamed_content)
        reasoning = "".join(streamed_reasoning)
        body = {
            "choices": [{"message": {"content": content, "reasoning": reasoning}}],
            "usage": usage,
        }
        used_stream = True
    except Exception:
        async with session.post(url, json=payload) as resp:
            resp.raise_for_status()
            body = await resp.json(content_type=None)
        message = body.get("choices", [{}])[0].get("message", {})
        content = coerce_message_text(message.get("content"))
        reasoning = coerce_message_text(message.get("reasoning"))
        mark = time.perf_counter()
        if content or reasoning:
            first_output = mark
        if content:
            first_answer = mark
        used_stream = False

    end = time.perf_counter()
    tokens_out = body.get("usage", {}).get("completion_tokens")
    token_count_source = "usage"
    if tokens_out is None:
        tokens_out = _rough_token_count(f"{reasoning}\n{content}")
        token_count_source = "rough_split"
    tokens_in = body.get("usage", {}).get("prompt_tokens", 0)
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
        "reasoning_chars": len(reasoning),
        "content_present": bool(content),
        "reasoning_present": bool(reasoning),
        "used_stream": used_stream,
        "token_count_source": token_count_source,
    }


def _rough_token_count(text: str) -> int:
    stripped = text.strip()
    if not stripped:
        return 0
    return len(stripped.split())
