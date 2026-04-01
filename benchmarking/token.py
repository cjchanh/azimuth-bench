#!/usr/bin/env python3
"""Benchmark-v2 throughput suite for MLX-served chat models."""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

import aiohttp

from benchmarking.roster import chat_template_kwargs_for_thinking_mode, slugify
from benchmarking.utils import DEFAULT_BENCHMARKS_DIR, coerce_message_text

PROMPT_SHORT = "Explain what a hash table is in one paragraph."

PROMPT_MEDIUM = """You are a senior software engineer reviewing code. Analyze the following requirements and produce a detailed technical specification:

1. A platform ingests customer support tickets from web forms and shared inboxes
2. Each ticket stores severity, category, owner, SLA deadline, and customer account metadata
3. Operators can assign, escalate, defer, resolve, or reopen tickets
4. All ticket changes are recorded in an append-only audit log
5. The system must tolerate downstream notification failures with retry and backoff
6. Search, analytics, and export are optional modules that can be enabled at runtime

Produce the specification as a structured JSON document with sections for: architecture, data model, validation rules, audit logging, and failure handling."""

PROMPT_LONG = PROMPT_MEDIUM + "\n\n" + ("Additional context: " + "x" * 500 + "\n") * 10

PROMPT_STRUCTURED = """You are triaging a customer support ticket for an internal software platform.

Ticket details:
- Requester: Morgan Lee
- Team: Finance Operations
- Summary: Users cannot export monthly invoice reports from the admin dashboard
- Impact: Blocking the monthly close workflow for 12 users
- Clues: Export button spins for 30 seconds and returns a timeout error

Respond with ONLY a JSON object:
{"priority":"low|medium|high|critical","category":"billing|bug|access|feature_request","summary":"one sentence","customer_impact":"one sentence","next_step":"one sentence"}"""

PROTOCOL_ID = "benchmark_v2_m5max_v1"
REQUEST_TEMPERATURE = 0.3
WARMUP_REQUESTS = 1
MEASURED_REPEAT_COUNTS = {"short": 3, "structured": 3, "medium": 3, "long": 2, "sustained": 10}
SMOKE_REPEAT_COUNTS = {"short": 1, "structured": 1, "medium": 1, "long": 1, "sustained": 2}


def _rough_token_count(text: str) -> int:
    stripped = text.strip()
    if not stripped:
        return 0
    return len(stripped.split())


def _avg_metric(rows: list[dict[str, Any]], key: str) -> float:
    values = [float(row[key]) for row in rows if row.get(key) is not None]
    if not values:
        return 0.0
    return round(mean(values), 1)


def _prompt_descriptor(prompt_id: str, prompt: str, token_cap: int) -> dict[str, Any]:
    return {
        "prompt_id": prompt_id,
        "sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "char_count": len(prompt),
        "token_cap": token_cap,
    }


def benchmark_protocol(*, max_tokens: int, smoke: bool) -> dict[str, Any]:
    repeat_counts = dict(SMOKE_REPEAT_COUNTS if smoke else MEASURED_REPEAT_COUNTS)
    return {
        "protocol_id": PROTOCOL_ID,
        "machine_class": "Apple Silicon M5 Max local MLX lane",
        "canonical_identity": "token_only",
        "gate_lane": "optional_secondary_validation",
        "stream_required_for_validity": True,
        "temperature": REQUEST_TEMPERATURE,
        "thinking_mode_policy": "explicit default/on/off via chat_template_kwargs.enable_thinking",
        "warmup_policy": {
            "enabled": True,
            "warmup_requests": WARMUP_REQUESTS,
            "prompt_id": "short",
            "counted_in_canonical_metrics": False,
        },
        "repeat_counts": repeat_counts,
        "prompt_set_id": "benchmark_v2_m5max_prompt_set_v1",
        "prompts": [
            _prompt_descriptor("short", PROMPT_SHORT, max_tokens),
            _prompt_descriptor("structured", PROMPT_STRUCTURED, max_tokens),
            _prompt_descriptor("medium", PROMPT_MEDIUM, 512),
            _prompt_descriptor("long", PROMPT_LONG, 512),
            _prompt_descriptor("sustained", PROMPT_SHORT, 128),
        ],
        "valid_run_requirements": [
            "all measured requests completed",
            "all measured requests used streaming path",
            "measured repeat counts match protocol",
            "single token count source across measured requests",
        ],
    }


def _measured_rows(
    short_results: list[dict[str, Any]],
    structured_results: list[dict[str, Any]],
    medium_results: list[dict[str, Any]],
    long_results: list[dict[str, Any]],
    sustained_runs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return short_results + structured_results + medium_results + long_results + sustained_runs


def _build_validity(
    *,
    protocol: dict[str, Any],
    short_results: list[dict[str, Any]],
    structured_results: list[dict[str, Any]],
    medium_results: list[dict[str, Any]],
    long_results: list[dict[str, Any]],
    sustained_runs: list[dict[str, Any]],
) -> dict[str, Any]:
    issues: list[str] = []
    repeat_counts = protocol["repeat_counts"]
    measured_rows = _measured_rows(
        short_results, structured_results, medium_results, long_results, sustained_runs
    )
    expected_counts = {
        "short": repeat_counts["short"],
        "structured": repeat_counts["structured"],
        "medium": repeat_counts["medium"],
        "long": repeat_counts["long"],
        "sustained": repeat_counts["sustained"],
    }
    observed_counts = {
        "short": len(short_results),
        "structured": len(structured_results),
        "medium": len(medium_results),
        "long": len(long_results),
        "sustained": len(sustained_runs),
    }
    if observed_counts != expected_counts:
        issues.append("repeat_count_mismatch")
    if any(not row.get("used_stream", False) for row in measured_rows):
        issues.append("stream_fallback_seen")
    token_count_sources = sorted({str(row.get("token_count_source", "unknown")) for row in measured_rows})
    if len(token_count_sources) != 1:
        issues.append("mixed_token_count_sources")
    if any(float(row.get("tok_per_sec", 0.0)) <= 0.0 for row in measured_rows):
        issues.append("non_positive_throughput")
    return {
        "valid_run": not issues,
        "issues": issues,
        "expected_counts": expected_counts,
        "observed_counts": observed_counts,
        "token_count_sources": token_count_sources,
    }


def _build_comparability(protocol: dict[str, Any], validity: dict[str, Any]) -> dict[str, Any]:
    return {
        "comparable": bool(validity.get("valid_run")),
        "protocol_id": protocol["protocol_id"],
        "prompt_set_id": protocol["prompt_set_id"],
        "warm_interpretation": "warm_after_load",
        "cold_interpretation": "model_load_receipt_only",
        "token_count_sources": validity.get("token_count_sources", []),
    }


async def time_request(
    session: aiohttp.ClientSession,
    url: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Send one request and measure reasoning-aware latency metrics."""
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


async def run_benchmark(
    *,
    port: int,
    max_tokens: int,
    thinking_mode: str,
    display_name: str | None,
    lane: str,
    source_label: str,
    source_badge: str,
    artifact_key: str | None,
    smoke: bool,
) -> dict[str, Any]:
    """Run the benchmark-v2 throughput suite."""
    run_started_at = datetime.now(timezone.utc).isoformat()
    url = f"http://localhost:{port}/v1/chat/completions"
    models_url = f"http://localhost:{port}/v1/models"
    protocol = benchmark_protocol(max_tokens=max_tokens, smoke=smoke)

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=300)) as session:
        async with session.get(models_url) as resp:
            resp.raise_for_status()
            models = await resp.json(content_type=None)
            model_id = models["data"][0]["id"]

        chat_template_kwargs = chat_template_kwargs_for_thinking_mode(thinking_mode)

        def make_payload(prompt: str, *, token_cap: int = max_tokens) -> dict[str, Any]:
            payload: dict[str, Any] = {
                "model": model_id,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": token_cap,
                "temperature": REQUEST_TEMPERATURE,
                "stream": False,
            }
            if chat_template_kwargs is not None:
                payload["chat_template_kwargs"] = chat_template_kwargs
            return payload

        print(f"Benchmarking: {display_name or model_id}")
        print(f"Lane: {lane}")
        print(f"Thinking mode: {thinking_mode}")
        print(f"Max tokens: {max_tokens}")
        print()

        repeats = dict(protocol["repeat_counts"])

        results: dict[str, Any] = {
            "model_id": model_id,
            "display_name": display_name or model_id,
            "lane": lane,
            "thinking_mode": thinking_mode,
            "source_label": source_label,
            "source_badge": source_badge,
            "artifact_key": artifact_key or slugify(model_id),
            "chat_template_kwargs": chat_template_kwargs,
            "smoke": smoke,
            "protocol": protocol,
            "benchmark_config": {
                "max_tokens": max_tokens,
                "repeat_counts": repeats,
            },
        }

        print("Warmup: 1 unmeasured short request...")
        warmup_results: list[dict[str, Any]] = []
        for index in range(WARMUP_REQUESTS):
            row = await time_request(session, url, make_payload(PROMPT_SHORT, token_cap=64))
            warmup_results.append(row)
            print(
                f"  Warmup {index + 1}: first_answer={row['first_answer_ms']:.0f}ms, "
                f"{row['tok_per_sec']:.1f} tok/s"
            )
        results["warmup"] = {
            "count": WARMUP_REQUESTS,
            "runs": warmup_results,
            "counted_in_canonical_metrics": False,
        }

        print("Test 1: Short prompt (TTFT + generation)...")
        short_results: list[dict[str, Any]] = []
        for index in range(repeats["short"]):
            row = await time_request(session, url, make_payload(PROMPT_SHORT))
            short_results.append(row)
            print(
                f"  Run {index + 1}: first_answer={row['first_answer_ms']:.0f}ms, "
                f"first_output={row['first_output_ms']:.0f}ms, {row['tok_per_sec']:.1f} tok/s"
            )
        results["short_prompt"] = short_results

        print("Test 2: Structured JSON output...")
        structured_results: list[dict[str, Any]] = []
        for index in range(repeats["structured"]):
            row = await time_request(session, url, make_payload(PROMPT_STRUCTURED))
            structured_results.append(row)
            print(
                f"  Run {index + 1}: first_answer={row['first_answer_ms']:.0f}ms, "
                f"{row['tok_per_sec']:.1f} tok/s, reasoning_chars={row['reasoning_chars']}"
            )
        results["structured_json"] = structured_results

        print("Test 3: Medium prompt (~500 tokens in)...")
        medium_results: list[dict[str, Any]] = []
        for index in range(repeats["medium"]):
            row = await time_request(session, url, make_payload(PROMPT_MEDIUM, token_cap=512))
            medium_results.append(row)
            print(
                f"  Run {index + 1}: first_answer={row['first_answer_ms']:.0f}ms, "
                f"{row['tok_per_sec']:.1f} tok/s"
            )
        results["medium_prompt"] = medium_results

        print("Test 4: Long prompt (~6K tokens in)...")
        long_results: list[dict[str, Any]] = []
        for index in range(repeats["long"]):
            row = await time_request(session, url, make_payload(PROMPT_LONG, token_cap=512))
            long_results.append(row)
            print(
                f"  Run {index + 1}: first_answer={row['first_answer_ms']:.0f}ms, "
                f"{row['tok_per_sec']:.1f} tok/s"
            )
        results["long_prompt"] = long_results

        print(f"Test 5: Sustained throughput ({repeats['sustained']} requests)...")
        sustained_start = time.perf_counter()
        sustained_runs: list[dict[str, Any]] = []
        for index in range(repeats["sustained"]):
            row = await time_request(session, url, make_payload(PROMPT_SHORT, token_cap=128))
            sustained_runs.append(row)
            if (index + 1) == repeats["sustained"] or (index + 1) % 5 == 0:
                print(f"  {index + 1}/{repeats['sustained']} done")
        sustained_elapsed = time.perf_counter() - sustained_start
        sustained_tokens = sum(int(row["tokens_out"]) for row in sustained_runs)
        results["sustained"] = {
            "runs": sustained_runs,
            "total_seconds": round(sustained_elapsed, 1),
            "total_tokens": sustained_tokens,
            "sustained_tok_per_sec": round(sustained_tokens / sustained_elapsed, 1) if sustained_elapsed > 0 else 0.0,
        }
        print(f"  Sustained: {results['sustained']['sustained_tok_per_sec']:.1f} tok/s")

    try:
        vm = subprocess.run(["vm_stat"], capture_output=True, text=True, check=False)
        for line in vm.stdout.splitlines():
            if "free" in line.lower():
                results["vm_pages_free"] = line.strip()
                break
    except Exception:
        pass

    summary = {
        "model_id": model_id,
        "display_name": display_name or model_id,
        "lane": lane,
        "thinking_mode": thinking_mode,
        "artifact_key": artifact_key or slugify(model_id),
        "source_label": source_label,
        "source_badge": source_badge,
        "short_tok_s": _avg_metric(short_results, "tok_per_sec"),
        "structured_json_tok_s": _avg_metric(structured_results, "tok_per_sec"),
        "sustained_tok_s": results["sustained"]["sustained_tok_per_sec"],
        "first_output_ms": _avg_metric(short_results, "first_output_ms"),
        "first_answer_ms": _avg_metric(short_results, "first_answer_ms"),
        "avg_ttft_ms": _avg_metric(short_results, "first_answer_ms"),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    validity = _build_validity(
        protocol=protocol,
        short_results=short_results,
        structured_results=structured_results,
        medium_results=medium_results,
        long_results=long_results,
        sustained_runs=sustained_runs,
    )
    comparability = _build_comparability(protocol, validity)
    summary["valid_run"] = validity["valid_run"]
    summary["comparable"] = comparability["comparable"]
    results["summary"] = summary
    results["validity"] = validity
    results["comparability"] = comparability
    results["receipts"] = {
        "run_start_utc": run_started_at,
        "run_finish_utc": datetime.now(timezone.utc).isoformat(),
    }

    print()
    print(f"=== SUMMARY: {display_name or model_id} ===")
    print(f"  Short prompt:    {summary['short_tok_s']:.1f} tok/s")
    print(f"  Structured JSON: {summary['structured_json_tok_s']:.1f} tok/s")
    print(f"  Sustained:       {summary['sustained_tok_s']:.1f} tok/s")
    print(f"  First output:    {summary['first_output_ms']:.0f}ms")
    print(f"  First answer:    {summary['first_answer_ms']:.0f}ms")
    print(f"  Valid run:       {summary['valid_run']}")
    print(f"  Comparable:      {summary['comparable']}")

    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark-v2 MLX throughput suite")
    parser.add_argument("--port", type=int, default=8899)
    parser.add_argument("--max-tokens", type=int, default=256)
    parser.add_argument("--output", type=str, default=None, help="Output JSON path")
    parser.add_argument("--thinking-mode", choices=["default", "on", "off"], default="default")
    parser.add_argument("--display-name", type=str, default=None)
    parser.add_argument("--lane", type=str, default="core")
    parser.add_argument("--source-label", type=str, default="local")
    parser.add_argument("--source-badge", type=str, default="Local")
    parser.add_argument("--artifact-key", type=str, default=None)
    parser.add_argument("--smoke", action="store_true", help="Run a minimal validation subset")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results = asyncio.run(
        run_benchmark(
            port=args.port,
            max_tokens=args.max_tokens,
            thinking_mode=args.thinking_mode,
            display_name=args.display_name,
            lane=args.lane,
            source_label=args.source_label,
            source_badge=args.source_badge,
            artifact_key=args.artifact_key,
            smoke=args.smoke,
        )
    )

    if args.output:
        out = Path(args.output)
    else:
        safe_name = results["summary"]["artifact_key"]
        out = DEFAULT_BENCHMARKS_DIR / f"{safe_name}.json"

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, default=str))
    print(f"\nResults: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
