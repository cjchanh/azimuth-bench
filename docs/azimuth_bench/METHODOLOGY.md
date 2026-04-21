# Methodology and proof boundary

This document explains what Azimuth Bench **measures**, how **comparability** is defined, and what outputs **do and do not** justify. It is not marketing copy; it matches [SOURCE_OF_TRUTH.md](SOURCE_OF_TRUTH.md) and the code.

## Implemented and tested (today)

- **Throughput suite** with fixed prompts, repeat counts, and validity rules (`azimuth_bench.suites.throughput`).
- **Adapters** (MLX LM local server, OpenAI-compatible HTTP, Ollama HTTP, **llama.cpp / llama-server** via `llama_cpp`) implementing the same `BenchmarkAdapter` contract; tests cover delegation, integrity, and report build.
- **Artifacts** per run: JSON payloads with protocol, timings, token estimates, validity, and comparability blocks.
- **Report bundle** under `report/data/`: normalized JSON with **no absolute local paths** in public fields; relative artifact paths and sanitized provider metadata.
- **Integrity gate**: ambiguous or duplicate artifact mapping fails closed (blockers).
- **Compare projection** (`compare.json`, `azimuth_compare_v1`): scoped pairwise rows with stable `comparison_key`, explicit **`blocked_comparisons`** for pairs that are *not* emitted, and deterministic share SVGs under `report/exports/`.
- **Multi-run merge** (M5): `azbench report build <primary> --include-run-dir <other> …` combines validated Azimuth-shaped run directories only; emits `merge.json`, copies comparability metadata onto `leaderboard.json`, and records **`comparability_class`** plus **`blockers`** when cross-protocol or non-comparable rows apply.
- **Design-partner evaluation** (M6): [DESIGN_PARTNER_EVAL.md](DESIGN_PARTNER_EVAL.md) and [release/evaluator/README.md](../../release/evaluator/README.md) document a single offline proof path; `pyproject.toml` distinguishes distribution name from import package.

## Designed or partial (do not over-claim)

- **vLLM** adapter: planned only (`azimuth_bench.adapters.planned`).
- **Cold-load seconds**: throughput artifacts record `telemetry.cold_load_status` (`unavailable` unless the adapter exposes load timing).
- **Semantic automation**: `azbench bench semantic-summary` joins fixtures + outputs + optional human scores; models never self-score unless explicitly marked trusted.
- **Promotion gates**: `azbench bench promotion-gate` emits classifications from structured evidence — **never** promotes to **default** on throughput alone.
- **Hosted SPA**: static HTML + JSON only.

## Fixture packs vs private eval sets

Public **fixture packs** live under `fixture_packs/` with minimal JSONL samples. Private, repo-anchored bakeoffs remain under `evals/` and are **not** imported automatically into Azimuth throughput artifacts.

## Protocol identity

Each throughput artifact records:

- **`protocol_id`** — e.g. `benchmark_v2_m5max_v1` for the reference tree in this repo.
- **`prompt_set_id`** — e.g. `benchmark_v2_m5max_prompt_set_v1`.
- **`machine_class`** — a **label** in the protocol (often describing the intended lane, e.g. Apple Silicon MLX). It is **not** independently verified hardware telemetry unless receipts supply it.

Comparing two runs requires matching protocol and understanding what changed (**model**, **adapter**, **thinking mode**, optional **route_label**, sampling policy, software versions). **Model name alone is not a sufficient comparison key** when adapters differ.

Throughput artifacts include **`route_identity`** (adapter name, lane, protocol hashes, optional route label). Merge collision detection keys include **`adapter_name`** and **`route_label`** when present on enriched summary rows so identical `model_id` rows from different routes do not silently collide.

## Comparability

### Compare JSON vs leaderboard

- **`leaderboard.json`** orders rows within one summary for exploration; it is not a claim that every row is mutually comparable.
- **`compare.json`** adds **only** explicit projections (e.g. scoped frontier base-vs-distilled pairs) plus **blocked** entries explaining what was *not* auto-compared (e.g. cross-lane).

The **`comparable`** flag on artifacts and enriched summary rows means: the run satisfied the suite’s **validity** rules for that protocol (streaming, repeat counts, consistent token count source, etc.). It does **not** mean:

- cross-machine fairness without reading `machine_class` and receipts;
- equal quality of model outputs;
- portability to every other stack without adapter-specific caveats.

Rows in `report/data/summary.json` include **`comparable_scope`**, **`comparability_blockers`**, **`protocol_id`**, and provider fields so readers see **why** something might not be apples-to-apples.

## Measured vs operator-supplied vs inferred

| Class | Examples |
| --- | --- |
| **Measured** | Timings, streamed token throughput estimates, validity flags from the harness. |
| **Operator-supplied** | `display_name`, `source_label`, optional `provider_id` via CLI/env for reports. |
| **Inferred / rough** | Token counts when the API omits usage (documented as `token_count_source` on rows). |

## Historical artifacts and normalization

Older JSON under `benchmarks/` may lack `backend_identity` or full receipts. The **report builder** fills a consistent provider envelope and marks gaps (e.g. missing benchmark commit SHA). The bundle **does not** invent proof it does not have.

## Why trust the outputs?

1. **Deterministic pipeline**: same inputs → same bundle shape; integrity errors surface as blockers.
2. **Explicit gaps**: provenance gaps and blockers are listed in JSON, not hidden.
3. **No path leakage**: public report JSON uses run-relative paths so casual sharing does not embed your home directory.
4. **Tests**: `python3 -m pytest -q` locks core behavior (see SOURCE_OF_TRUTH for last count).

## What the outputs do not prove

- **Industry-wide ranking** across unrelated hardware or providers without controlled conditions.
- **Model quality** or safety — only throughput/latency-style metrics from the defined prompts.
- **Future reproducibility** if upstream models or servers change silently.

For reading generated HTML/JSON, see [READING_REPORTS.md](READING_REPORTS.md).
