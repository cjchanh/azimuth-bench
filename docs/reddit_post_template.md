# Benchmark-v2 Reddit Post Template

## Title options

- I benchmarked a matched 27B Qwen3.5 base vs Opus-distilled pair on MLX, with thinking on and off
- Same 27B size, same MLX backend, different training objective: base Qwen3.5 vs Opus-distilled v2
- Local MLX 27B benchmark: throughput, latency, and thinking-mode tradeoffs on the same backend

## Carousel order

1. `visuals/social/benchmark_v2/27b_matchup_hero.png`
2. `visuals/social/benchmark_v2/27b_thinking_delta.png`
3. `visuals/social/benchmark_v2/speed_vs_latency_tradeoff.png`
4. `visuals/social/benchmark_v2/full_mlx_ladder.png`
5. `visuals/social/benchmark_v2/gate_validation_appendix.png` (optional appendix only)

## Post body

I split my local MLX benchmark lane into two planes:

- primary token benchmark
- optional Agent Civilization validation

The main benchmark is now token/latency only.

The centerpiece is a matched 27B comparison:

- `Qwen3.5 27B Base`
- `Qwen3.5 27B Opus Distilled v2`

Both run on the same MLX backend, and both are tested with:

- `thinking=on`
- `thinking=off`

That matters because reasoning-capable local models can change behavior depending on chat-template settings, and collapsing them into one number hides the real tradeoff.

Primary benchmark-v2 reports:

- `short_tok_s`
- `structured_json_tok_s` from a neutral structured JSON task
- `sustained_tok_s`
- `first_output_ms`
- `first_answer_ms`

The headline is simple:

- which local MLX model is faster
- how much thinking mode costs in throughput and latency
- whether Opus-distilled changes the tradeoff at the same 27B size

If I include Agent Civ at all, it is secondary validation:

- gate decision
- synthetic failure rate
- invalid-location rate
- 5-tick executed shares

Artifacts now land in:

- `benchmarks/benchmark_v2_token_summary.json`
- `benchmarks/benchmark_v2_token_summary.csv`
- `benchmarks/benchmark_v2_token_summary.md`

Optional gate validation lands in:

- `benchmarks/benchmark_v2_gate_summary.json`
- `benchmarks/benchmark_v2_gate_summary.csv`
- `benchmarks/benchmark_v2_gate_summary.md`

The benchmark logic itself now lives in a dedicated tracked package:

- `benchmarking/`

Visuals now land in:

- `visuals/social/benchmark_v2/`

If people want it, I can post the roster manifest, the offline-only runner, and the optional Agent Civ validation layer separately.
