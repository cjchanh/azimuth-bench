# Benchmark-v2 Implementation Note

- Canonical protocol doc: `docs/benchmark_v2_m5max_protocol.md`

## Roster contract

- Source of truth: `configs/benchmark_v2_models.json`
- Package source of truth for benchmark logic: `benchmarking/`
  - `benchmarking/roster.py`
  - `benchmarking/token.py`
  - `benchmarking/gate.py`
  - `benchmarking/summary.py`
  - `benchmarking/socials.py`
  - `benchmarking/runner.py`
- Wrapper/entrypoint plane:
  - `scripts/benchmark_all_models.sh`
  - `scripts/benchmark_v2_utils.py`
  - `scripts/mlx_benchmark.py`
  - `scripts/gate_mlx_model.py`
  - `scripts/compile_benchmark_summary.py`
  - `scripts/generate_benchmark_socials.py`
- The `scripts/` files are thin wrappers only. The durable benchmark contracts live in `benchmarking/`.
- Each entry defines:
  - `model_id`
  - `display_name`
  - `variant`
  - `lane`
  - `thinking_mode`
  - `source_label`
  - `source_badge`
  - `required_cache`
- Artifact naming is derived from the manifest via `benchmarking/roster.py`.
- `lane=core` is the existing MLX sweep.
- `lane=frontier_27b` is the matched Qwen3.5 27B base vs Opus-distilled comparison.

## Thinking-mode contract

- `thinking_mode` values are `default`, `on`, and `off`.
- MLX request plumbing converts those values into `chat_template_kwargs.enable_thinking`.
- Runtime entrypoint:
  - `scripts/run_experiment.py` reads `MLX_CHAT_TEMPLATE_ARGS` from env as JSON.
- Benchmark package modules:
  - `benchmarking/token.py`
  - `benchmarking/gate.py`
  - `benchmarking/summary.py`
  - `benchmarking/socials.py`
- Runtime transport:
  - `core/agent_runner.py`

## Artifact planes

- Source plane:
  - `benchmarking/`
- Config plane:
  - `configs/benchmark_v2_models.json`
- Generated artifacts are derived outputs, not source. The repo ignores:
  - `benchmarks/`
  - `visuals/`
- Per-model token benchmark artifact:
  - `benchmarks/<artifact_key>.json`
- Per-model gate artifact:
  - `benchmarks/gate_<artifact_key>/gate_result.json`

## Canonical summaries

- Primary token-only summary outputs:
  - `benchmarks/benchmark_v2_token_summary.json`
  - `benchmarks/benchmark_v2_token_summary.csv`
  - `benchmarks/benchmark_v2_token_summary.md`
- Optional gate validation outputs:
  - `benchmarks/benchmark_v2_gate_summary.json`
  - `benchmarks/benchmark_v2_gate_summary.csv`
  - `benchmarks/benchmark_v2_gate_summary.md`
- Optional combined outputs exist only when explicitly requested as a non-canonical convenience output:
  - `benchmarks/benchmark_v2_combined_summary.json`
  - `benchmarks/benchmark_v2_combined_summary.csv`
  - `benchmarks/benchmark_v2_combined_summary.md`

## Primary benchmark schema

- The benchmark identity is token/latency only:
  - `model_id`
  - `display_name`
  - `lane`
  - `thinking_mode`
  - `short_tok_s`
  - `structured_json_tok_s`
  - `sustained_tok_s`
  - `first_output_ms`
  - `first_answer_ms`
  - `source_label`
  - `source_badge`
- `structured_json_tok_s` now refers to a domain-neutral structured JSON workload in the canonical token lane, not an Agent Civilization action schema.

## Optional gate schema

- Agent Civilization validation remains available, but outside the primary benchmark identity:
  - `model_id`
  - `display_name`
  - `lane`
  - `thinking_mode`
  - `gate_decision`
  - `status`
  - `synthetic_failures`
  - `synthetic_rate`
  - `invalid_location_rate`
  - `share_count_5tick`
  - `agent_civ_usable`

## Safe run contract

- The benchmark lane is offline-only and must not overlap the experiment server on `:8899`.
- `benchmarking/runner.py` derives repo root from package location and can be launched from any working directory.
- `scripts/benchmark_all_models.sh` is a wrapper that sets `PYTHONPATH` and dispatches into the package runner.
- Before a real sweep, run fleet guard for the repo, benchmark port, and GPU claim.
- Recommended preflight:

```bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
fleet guard --repo "$REPO_ROOT" --port 9700 --gpu 22000 --json
```

- Dry-run first:

```bash
bash scripts/benchmark_all_models.sh --dry-run
```

- Dry-run writes to stdout only. It validates roster resolution, cache presence, and derived artifact paths without creating repo-local benchmark summaries, logs, or renders. If you want a file, redirect stdout explicitly.
- Receipt layer for execute mode:
  - `benchmarks/receipts/<artifact_key>/machine_pre_run.json`
  - `benchmarks/receipts/<artifact_key>/model_load.json`
  - `benchmarks/receipts/<artifact_key>/token_run_start.json`
  - `benchmarks/receipts/<artifact_key>/token_run_finish.json`
  - `benchmarks/receipts/<artifact_key>/artifact_complete.json`
  - `benchmarks/receipts/<artifact_key>/failure.json` on error

- Frontier-only token sweep:

```bash
bash scripts/benchmark_all_models.sh --lane frontier_27b
```

- Optional gate validation on top of the token sweep:

```bash
bash scripts/benchmark_all_models.sh --lane frontier_27b --with-gate
```

- Full token sweep:

```bash
bash scripts/benchmark_all_models.sh
```

- Social/mobile outputs:

```bash
python3 scripts/generate_benchmark_socials.py \
  --summary benchmarks/benchmark_v2_token_summary.json
```

- Optional gate appendix card:

```bash
python3 scripts/generate_benchmark_socials.py \
  --summary benchmarks/benchmark_v2_token_summary.json \
  --gate-summary benchmarks/benchmark_v2_gate_summary.json
```

## Downstream consumers

- `scripts/generate_visuals.py` is downstream/paper-facing consumption only.
- `papers/` and social copy consume benchmark summaries and images; they do not own benchmark contracts.
