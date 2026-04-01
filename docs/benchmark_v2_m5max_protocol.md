# Benchmark-v2 M5 Max Protocol

## Purpose

This protocol defines the canonical local MLX benchmark for the M5 Max lane.
It is a token benchmark first. Agent Civilization gate data is secondary and
must not define the primary benchmark identity.

## Machine assumptions

- Target class: Apple Silicon M5 Max workstation or laptop running local MLX.
- Single active benchmark lane at a time on benchmark port `9700`.
- No concurrent experiment server on `:8899`.
- No concurrent MLX/Ollama/vLLM model workload on the benchmark machine.
- Background macOS system services are tolerated, but heavy foreground work is not.

## Required idle state

- Close active builds, local training jobs, and ad hoc model inference outside the benchmark lane.
- Do not run parallel benchmark lanes.
- Capture a pre-run machine receipt before each model row.
- If the pre-run receipt shows obviously abnormal load or memory pressure relative to the session baseline, treat the row as suspect and rerun later.

## Power and thermal assumptions

- The harness records only low-intrusion snapshots such as `pmset -g batt`, load average, and `vm_stat` free pages before the run.
- The harness does not continuously sample thermal or power state during the benchmark.
- This benchmark may claim local MLX throughput/latency under the captured machine baseline.
- This benchmark may not claim stable thermally saturated performance under unobserved long-duration heat load.

## Benchmark port and single-run assumptions

- Canonical benchmark port: `9700`.
- One model loaded at a time.
- One benchmark artifact per `(lane, variant, thinking_mode)` artifact key.
- Canonical benchmark interpretation is warm-after-load, not cold-start end-user latency.

## Model roster rules

- Source of truth: `configs/benchmark_v2_models.json`.
- Canonical roster selection is resolved through `benchmarking/roster.py`.
- Core lane and frontier 27B lane may be run separately, but rows are only comparable when they use the same protocol version.

## Prompt set

- Prompt set id: `benchmark_v2_m5max_prompt_set_v1`.
- The canonical token prompt set is domain-neutral. It must not depend on Agent Civilization action schema, world state, or simulation semantics.
- Prompt ids:
  - `short`
  - `structured`
  - `medium`
  - `long`
  - `sustained`
- Prompt hashes are recorded in the token artifact protocol block.

## Token limits and repetition counts

- Default measured repetition counts:
  - `short=3`
  - `structured=3`
  - `medium=3`
  - `long=2`
  - `sustained=10`
- Smoke repetition counts:
  - `short=1`
  - `structured=1`
  - `medium=1`
  - `long=1`
  - `sustained=2`
- Default token caps:
  - benchmark default `max_tokens=256`
  - `medium=512`
  - `long=512`
  - `sustained=128`

## Thinking-mode policy

- Thinking mode is explicit and must be one of:
  - `default`
  - `on`
  - `off`
- Thinking mode is applied via `chat_template_kwargs.enable_thinking`.
- Rows are comparable only when the recorded thinking mode matches the artifact metadata.

## Warmup policy

- One unmeasured warmup request is required after model load and before measured requests.
- Warmup prompt id: `short`.
- Warmup is never counted in canonical token metrics.

## Cold vs warm interpretation

- Cold behavior is represented only by the model-load receipt.
- Canonical throughput and latency claims are warm-after-load measurements.
- Do not compare model-load time with canonical token metrics as if they were the same quantity.

## Artifact naming

- Per-model token artifact: `benchmarks/<artifact_key>.json`
- Canonical token summaries:
  - `benchmarks/benchmark_v2_token_summary.json`
  - `benchmarks/benchmark_v2_token_summary.csv`
  - `benchmarks/benchmark_v2_token_summary.md`
- Secondary gate summaries:
  - `benchmarks/benchmark_v2_gate_summary.json`
  - `benchmarks/benchmark_v2_gate_summary.csv`
  - `benchmarks/benchmark_v2_gate_summary.md`
- Non-canonical convenience output only:
  - `benchmarks/benchmark_v2_combined_summary.*`

## Valid run conditions

- All measured repeat counts match protocol.
- All measured requests use the streaming path.
- Measured requests use a single token-count source within the artifact.
- Artifact contains:
  - `protocol`
  - `summary`
  - `validity`
  - `comparability`
  - `receipts`
- Model id, lane, and thinking mode match the artifact key and receipt layer.

## Invalid run conditions

- Stream fallback appears in measured requests.
- Repeat counts are incomplete.
- Token-count source mixes within one artifact.
- Required artifact or receipt blocks are missing.
- Failure receipt exists for the row.

Invalid rows must not enter the canonical token summary.

## Minimal observability

- Required receipts:
  - pre-run machine receipt
  - model-load receipt
  - token-run start receipt
  - token-run finish receipt
  - artifact-completeness receipt
  - failure receipt on any run-stage error
- Observability is snapshot-only.
- Continuous polling during measured requests is intentionally prohibited.

## What not to monitor during the benchmark

- No continuous thermal watchers.
- No high-frequency memory pollers.
- No background token counters separate from the measured request path.
- No live dashboard refresh loop.
- No periodic `top`/`powermetrics`/GPU tracing during measured requests.

## Public claim boundary

- Can claim:
  - local MLX throughput and latency under this harness
  - structured JSON throughput for a neutral ticket-triage JSON task under this harness
  - thinking on/off deltas under this harness
  - warm-after-load model comparisons under this harness
- Cannot claim:
  - universal model quality from token speed alone
  - Agent Civilization behavior from the token benchmark alone
  - cold-start user experience from warm token metrics alone
  - long-duration thermal saturation behavior without separate measurement
