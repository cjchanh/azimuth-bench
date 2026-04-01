# Repo evolution plan (Azimuth Bench)

## Phase 1 (current)

- Introduce `azimuth_bench` package boundaries and documentation (public brand: **Azimuth**).
- Move MLX server lifecycle behind `MLXLmServerAdapter` (Azimuth Adapters).
- Define canonical schema version `1.0.0` and report outputs under `report/` (Azimuth Report).
- Preserve existing `benchmarking` modules and `signalbench` import alias via thin compatibility.

## Phase 2

- Add a second adapter (e.g. Ollama or OpenAI-compatible URL) behind the same interface.
- Split suite runners so `run_case` maps cleanly to suite families in `azimuth_bench/core/suites.py`.
- Expand `cases.json` with explicit suite ids per row.

## Phase 3

- Publish static site bundles (`site/` JSON) from CI and serve via static hosting.
- Optional: compare and leaderboard UIs consuming the site contract JSON.

## Compatibility

- Existing artifact JSON and `benchmark_v2_token_summary.json` remain source-of-truth inputs until a migration tool rewrites historical runs into a new on-disk layout.
