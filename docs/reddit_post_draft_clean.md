# Same hardware ceiling, different behavior underneath: Qwen3.5 27B base vs Opus-distilled on M5 Max

I ran a matched local MLX benchmark — same 27B parameter count, same 4-bit quantization, same M5 Max, same harness — and found that peak throughput is basically identical. The interesting results are all below the surface.

**Setup:** Qwen3.5 27B Base (NexVeridian) vs Qwen3.5 27B Opus Distilled v2 (Jackrong). Both from Hugging Face. Both tested with `thinking=on` and `thinking=off` via `chat_template_kwargs.enable_thinking`. MLX-LM 0.31.1, Apple M5 Max 128GB, clean baseline.

---

## 1. Peak throughput converges at the hardware ceiling

| Model | Thinking | Short tok/s |
|-------|----------|-------------|
| Base | on | 32.4 |
| Base | off | 32.1 |
| Opus | on | 33.0 |
| Opus | off | 32.8 |

All four configs land within 1 tok/s of each other. At 27B 4-bit on M5 Max, the memory bandwidth is the dominant limiter. The model architecture and training objective barely matter at peak decode. This is not the headline.

## 2. Structured JSON throughput is where they separate

| Model | Thinking | JSON tok/s |
|-------|----------|------------|
| Base | on | 27.1 |
| Base | off | 29.6 |
| Opus | on | 31.3 |
| Opus | off | 31.9 |

Opus-distilled is 2-5 tok/s faster on constrained structured output. If you're using local models for tool calls, function calling, or JSON APIs, this is the metric that matters. Base with thinking on is the weakest here — it overthinks the format.

## 3. Sustained throughput is where the base model breaks

| Model | Thinking | Sustained tok/s |
|-------|----------|-----------------|
| Base | on | 31.3 |
| Base | off | **25.4** |
| Opus | on | 30.2 |
| Opus | off | 31.8 |

This is the most counterintuitive result. Turning thinking **off** on the base model drops sustained throughput by 19%. Opus stays flat regardless of thinking mode.

I don't have a confident explanation for why base-off degrades. One possibility: the reasoning path acts as an internal regulator that keeps generation on track. Without it, the base model's generation becomes less efficient over longer sequences. Regardless, the data is clear — off-mode is not automatically faster on sustained workloads.

## 4. First-answer latency reveals internalized reasoning

| Model | Thinking | TTFT | First Answer |
|-------|----------|------|--------------|
| Base | on | 206ms | 7,906ms |
| Base | off | 231ms | 231ms |
| Opus | on | 199ms | 7,771ms |
| Opus | off | 198ms | **4,393ms** |

TTFT (time to first token) is ~200ms across the board. No surprise there.

The deeper finding is first-answer latency. Base obeys the thinking toggle cleanly: on = 7.9s of reasoning, off = instant. Binary behavior.

Opus does not. With `enable_thinking: false`, Opus-distilled still takes 4.4s before producing an answer. Under this harness, off-mode still carries a substantial first-answer delay. The distillation appears to have partially internalized the reasoning process — you can suppress the visible thinking tokens, but the model still deliberates before answering.

Whether that's a feature or a limitation depends on your use case. For latency-sensitive streaming UIs, it matters. For quality-sensitive batch work, it might be exactly what you want.

---

## Methodology

- **Protocol:** `benchmark_v2_m5max_v1`
- **Warmup:** 1 request per prompt, not counted
- **Repeats:** 3x short/structured/medium, 2x long, 10x sustained
- **Temperature:** 0.3
- **Streaming:** Required for validity
- **Token counting:** `usage.completion_tokens` from MLX server API (not word-split approximation)
- **Validity:** All 4 rows `valid_run=true`, `comparable=true`
- **Machine:** M5 Max, 128GB unified memory, macOS 25.3, no other MLX workers

## What this benchmark can claim

- Local MLX throughput and latency under this specific harness
- Structured JSON throughput comparison between these two models
- Thinking-mode behavioral differences under `chat_template_kwargs.enable_thinking`
- Sustained throughput stability over 10 sequential requests

## What it cannot claim

- Universal model quality from token speed
- That these results transfer to different quantizations, context lengths, or hardware
- That the first-answer latency finding generalizes beyond this MLX harness

---

**Models:**
- `NexVeridian/Qwen3.5-27B-4bit`
- `Jackrong/MLX-Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled-v2-4bit`

Both on Hugging Face, MLX-compatible.

Visuals in carousel. Data and protocol in repo.
