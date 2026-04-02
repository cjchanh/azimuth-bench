# Fresh local batch — 2026-04-01

This note records the fresh local batch used for launch visuals after `v0.1.0`.

It is **not** a replacement for the committed reference snapshot under `benchmarks/`. It is a small, real batch run to show the tool on a live local setup.

## Provenance

- **Core lane** ran through an existing local `openai_compatible` serving path on `:8080`.
- **Frontier 27B thinking lane** ran through a dedicated local MLX benchmark lane on `:8001`.

That means this batch is useful, but it is **not** one pure universal apples-to-apples ranking. The mixed provenance should stay explicit anywhere these visuals are reused.

## Rows

| Model | Lane | Think | JSON tok/s | Sustained tok/s | First answer ms |
| --- | --- | --- | ---: | ---: | ---: |
| Llama 3.2 3B | core | default | 190.9 | 199.6 | 59.7 |
| Gemma 3 4B | core | default | 134.9 | 142.3 | 136.0 |
| Llama 3.1 8B | core | default | 102.8 | 83.2 | 74.0 |
| Qwen2.5 Instruct 14B | core | default | 47.7 | 56.1 | 100.5 |
| Qwen3.5 27B Base | frontier_27b | off | 29.3 | 30.9 | 236.0 |
| Qwen3.5 27B Base | frontier_27b | on | 31.7 | 31.5 | 8000.9 |
| Qwen3.5 27B Opus Distilled v2 | frontier_27b | off | 31.7 | 31.2 | 6388.3 |
| Qwen3.5 27B Opus Distilled v2 | frontier_27b | on | 32.0 | 19.2 | 5630.9 |

## Launch assets

The preferred launch visuals from this batch are:

1. `27b_matchup_hero.png`
2. `speed_vs_latency_tradeoff.png`
3. `27b_thinking_delta.png`

The browsable scratch report for this batch was generated locally and used to sanity-check the visuals before launch.
