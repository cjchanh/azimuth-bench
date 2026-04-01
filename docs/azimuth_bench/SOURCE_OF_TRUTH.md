# Source of truth (`azimuth_bench` vs `signalbench` vs `benchmarking/`)

**Product:** **Azimuth** (surfaces: Azimuth Bench, Azimuth Report, Azimuth Compare, Azimuth Adapters). **Repo direction:** `azimuth-bench`. **Do not** claim the bare module/CLI name `azimuth`.

This document is the **single** place that defines **current** ownership and what is **implemented + tested** today. There is no parallel “eventual” story for SSOT boundaries.

**How sessions should use the other docs:** **`docs/azimuth_bench/COMPOSER2_UPGRADE_SESSION_V2.md`** is the **recommended execution plan** for a **new Composer window** (copy the inner `text` block). `docs/azimuth_bench/COMPOSER2_AUTOPILOT_MASTER_PROMPT.md` is the **anchor** that points at v2. **This file** plus the **code** are the **truth boundary for current implementation**: do not treat those prompts’ target deliverables as “shipped” unless they appear here and in tests, and **do not override this boundary with the execution plan** until `SOURCE_OF_TRUTH.md` is updated to match and that change is **committed** with the behavior it describes.

**Last verified tests (this checkout):** `python3 -m pytest -q` → **60 passed** (refresh when behavior changes).

**Public proof docs (methodology + how to read reports + outreach snapshot):** [METHODOLOGY.md](METHODOLOGY.md), [READING_REPORTS.md](READING_REPORTS.md), [PUBLIC_PROOF_PACK.md](PUBLIC_PROOF_PACK.md).

**Not SSOT (by design):** The Composer prompts are **instruction sets** for planned platform work (multi-backend, host surfaces, exports, comparability). They state **target outcomes** and verification expectations; they do **not** assert that every listed deliverable is shipped. If something conflicts with this file (`SOURCE_OF_TRUTH`) and the code, **this file wins** for “what is true now.”

## Canonical product surface

| Surface | Location | Role |
| --- | --- | --- |
| **Package** | `azimuth_bench/` | Product code: suites, adapters, schema, report, CLI. |
| **CLI (canonical)** | `azbench` → `azimuth_bench.cli.entrypoint:main` | Subcommands: `report build`, `bench throughput`. |
| **Module CLI** | `python -m azimuth_bench` | Same entry as `azbench`. |
| **Report build** | `azbench report build <run_dir> [--include-run-dir DIR …]` | Static `report/` output from artifacts; optional merge of additional validated run directories. |
| **Throughput execution** | `azbench bench throughput …` | Same code path as legacy `python -m benchmarking.token`. |

## Compatibility-only

### `signalbench/` (temporary import alias)

The **`signalbench`** Python package remains as a **thin re-export** of `azimuth_bench` so older imports and `python -m signalbench` keep working. It is **not** a second implementation. Prefer new code to import **`azimuth_bench`** directly.

The legacy **`signalbench`** console script also forwards to the same `main` as **`azbench`** (see `pyproject.toml`).

### `benchmarking/` (legacy harness)

These exist so **existing scripts and `-m` module paths keep working**. They **must not** define benchmark protocol truth.

| Module | Role |
| --- | --- |
| `benchmarking/token.py` | Re-exports prompts/protocol helpers and **delegates** `main`/`parse_args` to `azimuth_bench.cli.throughput`. |
| `benchmarking/utils.py` | Re-exports `azimuth_bench.core.runtime` (paths, `resolve_model_id`, message coercion). |
| `benchmarking/summary.py` | Compiles CSV/JSON/MD summaries; **imports** `TOKEN_FIELDS` and row extraction from `azimuth_bench.suites.summary`. |
| `benchmarking/runner.py` | Roster orchestration; subprocess to `-m benchmarking.token` (which resolves to canonical throughput). |
| `benchmarking/roster.py` | Roster manifest I/O; imports `slugify` / `chat_template_kwargs` from `azimuth_bench.core.runtime`. |
| `benchmarking/gate.py`, `socials.py` | Optional / ancillary; not throughput SSOT. |

## Throughput suite: who owns what

| Concern | Owner |
| --- | --- |
| Prompt text, protocol id, repeat counts, validity rules, summary metric math | **`azimuth_bench.suites.throughput`** |
| Token-summary **field list** and row extraction from artifact JSON | **`azimuth_bench.suites.summary`** |
| OpenAI-style target model resolution (`resolve_model_id` / `resolve_target_model`) | **`azimuth_bench.core.runtime`** |
| HTTP/stream timing for MLX LM | **`azimuth_bench.adapters.mlx`** (adapter `run_case`) |

**Rule:** `benchmarking/*` must **import** these definitions or delegate; it must not copy protocol constants or duplicate row logic.

## Schema versioning

- Canonical JSON bundles use **`azimuth_bench_schema_version`** (constant `AZIMUTH_BENCH_SCHEMA_VERSION`).
- **`SIGNALBENCH_SCHEMA_VERSION`** remains a Python alias for the same semver string (deprecated name only).
- Older bundles may still contain **`signalbench_schema_version`**; readers (e.g. Azimuth Report) accept both keys when displaying.

## Implemented vs not implemented

| Implemented | Notes |
| --- | --- |
| Throughput suite + MLX adapter + summary compile + report build + integrity | Covered by tests. |
| `bench throughput` CLI | Canonical mirror of `python -m benchmarking.token`; supports `--adapter mlx` (default), `openai_compatible`, `ollama` with explicit `--base-url` or env (see `docs/azimuth_bench/ENVIRONMENT.md`). |
| OpenAI-compatible + Ollama HTTP adapters | Real `BenchmarkAdapter` implementations (`OpenAICompatibleAdapter`, `OllamaAdapter`); same throughput suite; capability metadata + backend identity on artifacts. |
| Adapter capabilities + identity envelope | `AdapterCapabilities`, `build_backend_identity`, `backend_identity` on throughput JSON. |
| Comparability helper + protocol manifest helper | `azimuth_bench.core.comparability`, `azimuth_bench.schema.protocol_manifest`. |
| Static site manifest + host index payload | `azimuth_bench.site.contract` (`routes`, `host_index`). |
| Markdown export CLI | `azbench export markdown <run_dir> --output …` (requires built `report/data/`). |
| Compare projection + share SVGs | `compare.json` uses `azimuth_compare_v1` (`azimuth_bench.compare.projection`); deterministic `report/exports/share_leaderboard.svg` and `share_compare.svg`; `azbench export svg`. |
| Portable merge of validated run bundles (M5) | `azbench report build <primary> --include-run-dir <other> …`; `azimuth_bench.merge.bundle.merge_canonical_bundles`; outputs `report/data/merge.json`, merge section on `leaderboard.json`, comparability classes + blockers; fail-closed on integrity/collision/duplicate identity. **Merge row identity** (duplicate blocking): `(model_id, lane, thinking_mode)`; artifact keys are prefixed per source (`s0__`, `s1__`, …). Covered by `tests/test_merge.py`. |
| Design-partner evaluation surface (M6) | Single evaluator narrative: [DESIGN_PARTNER_EVAL.md](DESIGN_PARTNER_EVAL.md). Repeatable offline proof + optional wheel/sdist instructions: [release/evaluator/README.md](../../release/evaluator/README.md). Independent release-gate evidence bundle: [release/evidence/m6_release_gate_v1/README.md](../../release/evidence/m6_release_gate_v1/README.md). `pyproject.toml` metadata (keywords/classifiers) documents distribution vs import name. Covered by `tests/test_m6_eval.py` (includes `python -m build` smoke). |
| Public OSS release candidate (v0.1.0) | Root [CHANGELOG.md](../../CHANGELOG.md), [CONTRIBUTING.md](../../CONTRIBUTING.md), [SECURITY.md](../../SECURITY.md); pack [release/public/v0_1_0/README.md](../../release/public/v0_1_0/README.md). **Public sample report (static GitHub Pages):** https://cjchanh.github.io/benchmark-v2/report/index.html — generated from committed artifacts in `docs/report/`; not a live service. Tagging aligns with `version = "0.1.0"` in `pyproject.toml`. Covered by `tests/test_release_public_v0_1_0.py` (two file-presence tests). |

| Not implemented (by design in this repo) | Notes |
| --- | --- |
| llama.cpp / vLLM adapters | See `azimuth_bench.adapters.planned` (stubs only). |
| Hosted SPA | Static `report/` + `site_manifest.json` only. |
| Interactive compare picker / arbitrary pairwise UI | Static JSON + scoped pairs + explicit `blocked_comparisons` only. |
| Arbitrary third-party JSON trees as merge inputs | Only Azimuth-shaped run directories (token summary + artifacts) are supported; no silent directory sweeps. |
| PyPI publication / verified release automation | Local `python -m build` is documented and tested; publishing is out of scope unless explicitly added. |

## Transitional debt (explicit)

- **`signalbench` import package** — remove after downstream callers migrate to `azimuth_bench`.
- **Roster** remains under `benchmarking/roster.py` (data + filtering). Moving it under `azimuth_bench` would be a separate migration; behavior already imports shared helpers from `azimuth_bench.core.runtime`.
- **Gate / socials** remain under `benchmarking/` until a future consolidation pass explicitly moves them.
