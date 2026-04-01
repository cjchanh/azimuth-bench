# Azimuth Bench platform design (v2 foundation)

**Truth boundary:** [SOURCE_OF_TRUTH.md](SOURCE_OF_TRUTH.md) + code + tests. This note maps modules and contracts; it does not override SSOT.

## Module map

| Area | Path | Role |
| --- | --- | --- |
| CLI | `azimuth_bench/cli/` | `azbench` entrypoint, throughput, export |
| Adapters | `azimuth_bench/adapters/` | `BenchmarkAdapter`, MLX / OpenAI-compatible / Ollama, factory |
| Suites | `azimuth_bench/suites/` | Throughput protocol, summary fields |
| Schema / integrity | `azimuth_bench/schema/` | Bundles, validation, protocol manifest helper |
| Comparability | `azimuth_bench/core/comparability.py` | Derived flags from protocol + validity |
| Report | `azimuth_bench/report/` | Static Azimuth Report |
| Site | `azimuth_bench/site/contract.py` | Host JSON routes + manifest |
| Export | `azimuth_bench/export/` | Offline Markdown from `report/data/` |

## Adapter contract

- **Interface:** `BenchmarkAdapter` — `capabilities()`, `build_backend_identity()`, model discovery, `prepare_target`, `run_case`, `shutdown`.
- **Identity:** `build_backend_identity` embeds `provider_kind`, `adapter_name`, `provider_id_source`, and capability booleans (no invented verification).
- **HTTP:** OpenAI-compatible paths go only through `OpenAICompatibleAdapter` (explicit base URL). Ollama uses `/api/tags` + `/api/chat` via `OllamaAdapter` (no silent `/v1/models` mapping).
- **Thinking modes:** Adapters declare `thinking_toggle`; non-MLX HTTP adapters reject `on`/`off` with `UnsupportedAdapterFeatureError`.

## Protocol / comparability

- **Protocol manifest helper:** `azimuth_bench/schema/protocol_manifest.py` — documents protocol id + machine_class sourcing.
- **Comparability:** `comparability_block()` merges validity + protocol ids; incomparable runs stay explicit in summaries.

## Host model

- **Manifest:** `build_site_manifest()` adds `routes`, `host_index`, and per-route file roles for static hosting (no SPA).

## Export model

- **Markdown:** `azbench export markdown <run_dir> --output path.md` reads `report/data/summary.json` (requires prior `azbench report build`).

## Implemented now vs later

| Implemented | Planned / partial |
| --- | --- |
| MLX + OpenAI-compatible + Ollama throughput adapters | llama.cpp, vLLM (`adapters/planned.py`) |
| Backend identity + capabilities | Full social card / leaderboard image pipeline |
| Host manifest + export Markdown | Hosted SPA, CDN-backed assets |
