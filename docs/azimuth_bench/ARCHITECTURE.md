# Azimuth Bench platform architecture

**Public product brand:** **Azimuth**. Technical package: **`azimuth_bench`** (CLI: **`azbench`**). This avoids claiming the crowded bare PyPI/module name `azimuth`.

**Source-of-truth split (canonical vs compatibility):** see [SOURCE_OF_TRUTH.md](SOURCE_OF_TRUTH.md).

Azimuth Bench is a portable inference benchmark platform: runners with provider adapters (Azimuth Adapters), a canonical artifact and report schema, static **Azimuth Report** generation, and a hostable comparison surface. It is not tied to a single backend; MLX LM is one adapter path.

Operator configuration (paths, optional provider labels) is **environment-driven** — see [ENVIRONMENT.md](ENVIRONMENT.md). Nothing in the schema **infers** a backend provider name from free-text protocol fields without a documented operator override (to avoid false claims in published JSON).

## Layering

| Layer | Responsibility |
| --- | --- |
| **CLI** (`azimuth_bench/cli`) | Operator entry points (`report build`, `bench throughput`). |
| **Core** (`azimuth_bench/core`) | Suite taxonomy, shared types, repository roots. |
| **Adapters** (`azimuth_bench/adapters`) | Azimuth Adapters: list models, health, load target, run cases, shutdown. |
| **Schema** (`azimuth_bench/schema`) | Canonical run bundle shapes, integrity checks, versioning. |
| **Report** (`azimuth_bench/report`) | Azimuth Report — HTML/Markdown/charts from real artifacts. |
| **Site** (`azimuth_bench/site`) | JSON contracts for a static hosted results site. |

CLI logic lives in `azimuth_bench/cli/entrypoint.py` (not `main.py`) so `import azimuth_bench.cli.main` cannot accidentally resolve to the `main()` function instead of a submodule—a common Python foot-gun when a package re-exports `main` from `main.py`.

## Benchmark core vs providers

- **Suite definitions** (throughput, latency/TTFT, structured reliability, long-context, thinking overhead, load/swap, optional thermal) live in core as named families; concrete prompts and repeat counts remain in the throughput implementation until additional suites are wired.
- **Providers** implement `BenchmarkAdapter` with explicit `capabilities()` and `build_backend_identity()`. **MLX LM**, **OpenAI-compatible HTTP**, and **Ollama** are implemented for throughput (`--adapter` on `azbench bench throughput`). **llama.cpp** and **vLLM** remain planned only (see `azimuth_bench/adapters/planned.py`).

## Canonical run bundle

A run directory (for example `benchmarks/`) may contain per-model JSON artifacts, `receipts/`, and compiled `benchmark_v2_token_summary.json`. The report builder emits a normalized bundle under `report/data/`:

| File | Role |
| --- | --- |
| `run.json` | Run id, UTC timestamps, optional repo commit SHA, schema version (`azimuth_bench_schema_version`), lane. |
| `summary.json` | Rows and fields aligned with the compiled token summary (Azimuth envelope). |
| `machine.json` | Host snapshot when receipts exist; selection rule is explicit in JSON (`selection` field). |
| `provider.json` | Provider envelope: `provider_id`, `provider_kind`, adapter name, capabilities, and safe verified fields only. |
| `model.json` | Target model id, served model ids, thinking/prompt modes, provenance pointers. |
| `cases.json` | Per-artifact `suite_family` + `protocol_id` from each artifact JSON. |

`receipts/` and `plots/` remain at the run root when present; the report references them. Charts are generated under `report/charts/`.

## Integrity

- Target model resolution must never silently fall back to the first `/v1/models` entry when a target is specified (see `azimuth_bench.core.runtime.resolve_model_id`).
- Summary rows must have **exactly one** matching `*.json` artifact (same `model_id`, `lane`, `thinking_mode`). **Zero** or **multiple** matches fail closed with blockers.

## Visual direction

Azimuth Report uses a restrained dark surface, system UI font stack (no required external CDN), muted accent, metrics-first layout—instrument-like, no neon or crypto-terminal styling.

## Implemented vs designed (this slice)

**Implemented and tested:** MLX, OpenAI-compatible HTTP, and Ollama throughput adapters; canonical bundle fields; integrity (including ambiguity detection); `azbench report build`; static report outputs; site/provider/protocol manifest scaffolding.

**Designed / unverified:** llama.cpp and vLLM adapters, full suite matrix beyond the current throughput protocol, hosted SPA deployment, thermal telemetry, richer share-card/image exports.

## Public documentation

- [METHODOLOGY.md](METHODOLOGY.md) — measurement and comparability boundaries.
- [READING_REPORTS.md](READING_REPORTS.md) — how to interpret static report pages and JSON.
- [PUBLIC_PROOF_PACK.md](PUBLIC_PROOF_PACK.md) — compact facts for outreach using the reference benchmark snapshot (not SSOT).
