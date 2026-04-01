# Archive: Word-Count Run (Not Publishable)

**Date:** 2026-04-01  
**Status:** Archived - measurement flaw

## What This Is

This is the initial frontier_27b benchmark run that used **word-split token counting** instead of real tokens from the MLX server usage API.

## Why Archived

**Critical flaw:** All token counts calculated via:
```python
tokens = len(text.split())  # Word count, not token count
```

Instead of:
```python
tokens = response.usage.completion_tokens  # Real tokens from MLX
```

**Impact:** Absolute tok/s overstated by ~10-30%.

## What Was Correct

- Relative comparisons (thinking penalty, Opus vs Base)
- Latency/TTFT measurements (time-based)
- Methodology and protocol

## Corrected Run

The corrected run with accurate token counting lives in:
- `benchmarks/frontier_27b__*.json`
- `benchmarks/benchmark_v2_token_summary.*`

## Results (Word-Count, Inflated)

| Model | Thinking | Short | Sustained | TTFT |
|-------|----------|-------|-----------|------|
| Base | on | 19.6 | 15.2 | 201ms |
| Base | off | 26.4 | 26.2 | 239ms |
| Opus | on | 25.8 | 23.5 | 210ms |
| Opus | off | 25.9 | 23.2 | 213ms |

**Expected correction:** ~25% lower absolute tok/s with real token counts.
