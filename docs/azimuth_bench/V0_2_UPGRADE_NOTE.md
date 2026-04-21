# Azimuth Bench v0.2 evaluation upgrade — implementation note (2026-04-21)

## Independent verification commands

- `python3 -m pytest -q` → `80 passed`.
- `python3 -m ruff check .` → pass.
- `python3 -m ruff format --check .` → pass.
- CLI probes: `azbench bench semantic-summary` and `azbench bench promotion-gate` both wrote and re-read valid temp artifacts.

## Summary

| Area | Status |
| --- | --- |
| llama.cpp (`llama_cpp`) adapter | **Implemented**: `LlamaCppServerAdapter` distinct from generic OpenAI-compatible; `thinking_toggle=True`; HTTP failures on thinking kwargs → `UnsupportedAdapterFeatureError`. **Not implemented**: spawning llama-server binaries. |
| Semantic scoring lanes | **Implemented**: `azbench bench semantic-summary` → `azimuth_semantic_summary_v1`. Throughput stays separate. Human/trusted scores required for PASS; model self-grade rejected unless `trusted` is the JSON boolean `true`. |
| Route identity | **Implemented**: `route_identity` + `telemetry` on throughput artifacts; CLI `--route-label`, `--sampling-policy`; merge duplicate key extended with `adapter_name` + `route_label`. |
| Promotion gate reports | **Implemented**: `azbench bench promotion-gate` → `azimuth_promotion_gate_v1`; **default** classification blocked without semantic gate pass + `approve_default_route`. |
| Cold-load / memory telemetry | **Partial**: `telemetry.memory_vm_pages_free_*` via `vm_stat` when available; `cold_load_seconds` and `context_length` explicitly `unavailable` with reasons (no invented load times or context settings). |
| Fixture packs | **Implemented**: `fixture_packs/` with four packs + sample JSONL lines (public-only). |

## Canonical `benchmarks/` directory

Unchanged by this upgrade (no intentional writes to committed canonical benchmark trees).

## Files touched (high level)

- **Adapters**: `azimuth_bench/adapters/llama_cpp.py`, `factory.py`, `planned.py`
- **Throughput**: `suites/throughput.py`, `cli/throughput.py`
- **Schema / merge**: `schema/bundle.py`, `merge/bundle.py`
- **Semantic / gates**: `azimuth_bench/semantic/`, `azimuth_bench/gates/`, `cli/bench_aux.py`, `cli/entrypoint.py`
- **Docs**: `SOURCE_OF_TRUTH.md`, `METHODOLOGY.md`, `READING_REPORTS.md`, this note
- **Samples**: `fixture_packs/**`
- **Tests**: `tests/test_azimuth_gate_semantic.py`, `tests/test_m6_eval.py` (skip when `python -m build` unavailable)

## Partial / designed-unverified boundaries

- **Cold-load timing and context length**: adapters do not uniformly expose these values; fields remain explicitly unavailable rather than guessed.
- **Semantic automation**: no LLM-as-judge in-repo; operators supply score rows with `trusted: true` or treat rows as `manual_required`. Untrusted scores, duplicate IDs, unknown score IDs, skipped rows, missing outputs, and output rows without content block the semantic gate.
