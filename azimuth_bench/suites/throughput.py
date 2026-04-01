"""Azimuth Bench throughput suite runner and protocol."""

from __future__ import annotations

import hashlib
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from statistics import mean
from typing import Any

from azimuth_bench.adapters.base import BenchmarkAdapter
from azimuth_bench.adapters.identity import ProviderIdSource
from azimuth_bench.core.cases import CaseSpec
from azimuth_bench.core.comparability import comparability_block
from azimuth_bench.core.runtime import chat_template_kwargs_for_thinking_mode, resolve_target_model, slugify
from azimuth_bench.errors import UnsupportedAdapterFeatureError

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
MEASURED_REPEAT_COUNTS = {
    "short": 3,
    "structured": 3,
    "medium": 3,
    "long": 2,
    "sustained": 10,
}
SMOKE_REPEAT_COUNTS = {
    "short": 1,
    "structured": 1,
    "medium": 1,
    "long": 1,
    "sustained": 2,
}


@dataclass(frozen=True)
class BenchmarkIdentity:
    """Stable identity fields for one benchmark artifact."""

    target_model_id: str | None
    display_name: str | None
    lane: str
    thinking_mode: str
    source_label: str
    source_badge: str
    artifact_key: str | None = None
    operator_provider_id: str | None = None
    provider_id_source: ProviderIdSource = "default"


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


def benchmark_protocol(*, max_tokens: int, smoke: bool, machine_class: str) -> dict[str, Any]:
    repeat_counts = dict(SMOKE_REPEAT_COUNTS if smoke else MEASURED_REPEAT_COUNTS)
    return {
        "protocol_id": PROTOCOL_ID,
        "suite_family": "throughput",
        "machine_class": machine_class,
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
    measured_rows = _measured_rows(short_results, structured_results, medium_results, long_results, sustained_runs)
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


def _vm_pages_free() -> str | None:
    result = subprocess.run(["vm_stat"], capture_output=True, text=True, check=False)
    for line in result.stdout.splitlines():
        if "Pages free" in line:
            return line.strip()
    return None


def _spec(prompt_id: str, prompt: str, *, token_cap: int, target_model_id: str) -> CaseSpec:
    return CaseSpec(
        suite_family="throughput",
        prompt_id=prompt_id,
        prompt=prompt,
        max_tokens=token_cap,
        metadata={"temperature": REQUEST_TEMPERATURE, "target_model_id": target_model_id},
    )


def run_benchmark(
    *,
    adapter: BenchmarkAdapter,
    identity: BenchmarkIdentity,
    max_tokens: int,
    smoke: bool,
    machine_class: str,
) -> dict[str, Any]:
    """Run the throughput suite over a concrete adapter."""
    if not adapter.healthcheck():
        raise RuntimeError("benchmark provider did not pass healthcheck")

    caps = adapter.capabilities()
    if identity.thinking_mode != "default" and not caps.thinking_toggle:
        raise UnsupportedAdapterFeatureError(
            f"adapter {caps.adapter_name!r} does not support thinking_mode={identity.thinking_mode!r}",
        )

    run_started_at = datetime.now(timezone.utc).isoformat()
    protocol = benchmark_protocol(max_tokens=max_tokens, smoke=smoke, machine_class=machine_class)
    model_id = resolve_target_model(adapter.resolve_served_models(), target_model_id=identity.target_model_id)

    print(f"Benchmarking: {identity.display_name or model_id}")
    print(f"Lane: {identity.lane}")
    print(f"Thinking mode: {identity.thinking_mode}")
    print(f"Max tokens: {max_tokens}")
    print()

    repeats = dict(protocol["repeat_counts"])
    results: dict[str, Any] = {
        "model_id": model_id,
        "display_name": identity.display_name or model_id,
        "lane": identity.lane,
        "thinking_mode": identity.thinking_mode,
        "source_label": identity.source_label,
        "source_badge": identity.source_badge,
        "artifact_key": identity.artifact_key or slugify(model_id),
        "chat_template_kwargs": chat_template_kwargs_for_thinking_mode(identity.thinking_mode),
        "smoke": smoke,
        "protocol": protocol,
        "benchmark_config": {
            "max_tokens": max_tokens,
            "repeat_counts": repeats,
        },
        "backend_identity": adapter.build_backend_identity(
            operator_provider_id=identity.operator_provider_id,
            provider_id_source=identity.provider_id_source,
        ),
    }

    print("Warmup: 1 unmeasured short request...")
    warmup_results: list[dict[str, Any]] = []
    for index in range(WARMUP_REQUESTS):
        row = adapter.run_case(
            _spec("short", PROMPT_SHORT, token_cap=64, target_model_id=model_id),
            thinking_mode=identity.thinking_mode,
        )
        warmup_results.append(row)
        print(f"  Warmup {index + 1}: first_answer={row['first_answer_ms']:.0f}ms, {row['tok_per_sec']:.1f} tok/s")
    results["warmup"] = {
        "count": WARMUP_REQUESTS,
        "runs": warmup_results,
        "counted_in_canonical_metrics": False,
    }

    print("Test 1: Short prompt (TTFT + generation)...")
    short_results = [
        adapter.run_case(
            _spec("short", PROMPT_SHORT, token_cap=max_tokens, target_model_id=model_id),
            thinking_mode=identity.thinking_mode,
        )
        for _ in range(repeats["short"])
    ]
    for index, row in enumerate(short_results, start=1):
        print(
            f"  Run {index}: first_answer={row['first_answer_ms']:.0f}ms, "
            f"first_output={row['first_output_ms']:.0f}ms, {row['tok_per_sec']:.1f} tok/s"
        )
    results["short_prompt"] = short_results

    print("Test 2: Structured JSON output...")
    structured_results = [
        adapter.run_case(
            _spec("structured", PROMPT_STRUCTURED, token_cap=max_tokens, target_model_id=model_id),
            thinking_mode=identity.thinking_mode,
        )
        for _ in range(repeats["structured"])
    ]
    for index, row in enumerate(structured_results, start=1):
        print(
            f"  Run {index}: first_answer={row['first_answer_ms']:.0f}ms, "
            f"{row['tok_per_sec']:.1f} tok/s, reasoning_chars={row['reasoning_chars']}"
        )
    results["structured_json"] = structured_results

    print("Test 3: Medium prompt (~500 tokens in)...")
    medium_results = [
        adapter.run_case(
            _spec("medium", PROMPT_MEDIUM, token_cap=512, target_model_id=model_id),
            thinking_mode=identity.thinking_mode,
        )
        for _ in range(repeats["medium"])
    ]
    for index, row in enumerate(medium_results, start=1):
        print(f"  Run {index}: first_answer={row['first_answer_ms']:.0f}ms, {row['tok_per_sec']:.1f} tok/s")
    results["medium_prompt"] = medium_results

    print("Test 4: Long prompt (~6K tokens in)...")
    long_results = [
        adapter.run_case(
            _spec("long", PROMPT_LONG, token_cap=512, target_model_id=model_id),
            thinking_mode=identity.thinking_mode,
        )
        for _ in range(repeats["long"])
    ]
    for index, row in enumerate(long_results, start=1):
        print(f"  Run {index}: first_answer={row['first_answer_ms']:.0f}ms, {row['tok_per_sec']:.1f} tok/s")
    results["long_prompt"] = long_results

    print(f"Test 5: Sustained throughput ({repeats['sustained']} requests)...")
    sustained_runs: list[dict[str, Any]] = []
    sustained_tokens = 0
    sustained_start = datetime.now(timezone.utc)
    for index in range(repeats["sustained"]):
        row = adapter.run_case(
            _spec("sustained", PROMPT_SHORT, token_cap=128, target_model_id=model_id),
            thinking_mode=identity.thinking_mode,
        )
        sustained_runs.append(row)
        sustained_tokens += int(row["tokens_out"])
        if (index + 1) == repeats["sustained"] or (index + 1) % 5 == 0:
            print(f"  {index + 1}/{repeats['sustained']} done")
    sustained_elapsed = (datetime.now(timezone.utc) - sustained_start).total_seconds()
    results["sustained"] = {
        "runs": sustained_runs,
        "total_seconds": round(sustained_elapsed, 1),
        "total_tokens": sustained_tokens,
        "sustained_tok_per_sec": round(sustained_tokens / sustained_elapsed, 1) if sustained_elapsed > 0 else 0.0,
    }
    print(f"  Sustained: {results['sustained']['sustained_tok_per_sec']:.1f} tok/s")

    results["vm_pages_free"] = _vm_pages_free()

    summary = {
        "model_id": model_id,
        "display_name": identity.display_name or model_id,
        "lane": identity.lane,
        "thinking_mode": identity.thinking_mode,
        "artifact_key": identity.artifact_key or slugify(model_id),
        "source_label": identity.source_label,
        "source_badge": identity.source_badge,
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
    comparability = comparability_block(protocol=protocol, validity=validity)
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
    print(f"=== SUMMARY: {identity.display_name or model_id} ===")
    print(f"  Short prompt:    {summary['short_tok_s']:.1f} tok/s")
    print(f"  Structured JSON: {summary['structured_json_tok_s']:.1f} tok/s")
    print(f"  Sustained:       {summary['sustained_tok_s']:.1f} tok/s")
    print(f"  First output:    {summary['first_output_ms']:.0f}ms")
    print(f"  First answer:    {summary['first_answer_ms']:.0f}ms")
    print(f"  Valid run:       {summary['valid_run']}")
    print(f"  Comparable:      {summary['comparable']}")

    return results
