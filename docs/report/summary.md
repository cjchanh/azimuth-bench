# Azimuth Report summary

## Measurement status

- Integrity gate: **PASS**
- Row count: **18**

## Implemented and tested

- Canonical per-run JSON bundle emitted under `report/data/runs/<artifact_key>/`
- Static pages emitted for latest report, leaderboard, compare, run detail, and machine detail
- Compare projection emitted under `report/data/compare.json` with deterministic share SVGs under `report/exports/`
- Multi-run merge: `azbench report build <run_dir> --include-run-dir <other_run_dir> ...` merges validated Azimuth run trees; see `report/data/merge.json` and `leaderboard.json` field `merge`

## Designed / unverified

- llama.cpp and vLLM adapters
- Full hosted app beyond static-first site data contract

## Site manifest

- Status: `scaffold_static_first`
- Run detail pages: `18`
- Machine detail pages: `1`

## Leaderboard snapshot

| Display | Lane | Think | JSON tok/s | Sustained tok/s | First answer ms |
| --- | --- | --- | ---: | ---: | ---: |
| Phi 4 Mini | core | default | 146.3 | 162.2 | 95.1 |
| Gemma 3 4B | core | default | 134.4 | 125.9 | 137.7 |
| Qwen2.5 Coder 7B | core | default | 107.3 | 112.2 | 72.1 |
| Qwen2.5 Instruct 7B | core | default | 107.2 | 110.8 | 80.0 |
| DeepSeek R1 Distill Llama 8B | core | default | 103.9 | 103.1 | 93.4 |
| Llama 3.1 8B | core | default | 99.9 | 102.3 | 70.9 |
| Qwen3.5 9B | core | default | 97.3 | 84.6 | 2073.4 |
| Ministral 3 8B | core | default | 94.0 | 93.8 | 78.6 |
| Ministral 3 14B | core | default | 61.5 | 61.8 | 84.7 |
| Qwen2.5 Coder 14B | core | default | 55.3 | 45.6 | 93.3 |
