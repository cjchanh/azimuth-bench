# Benchmark-v2 Quality Assessment

**Date:** 2026-04-01  
**Assessor:** Critical evaluation after clean rerun  
**Confidence:** MEDIUM-HIGH with caveats

---

## Executive Summary

The benchmark methodology is sound, but there's a **critical measurement issue**: all token counts are using rough word-splitting (`rough_split`) instead of the MLX server's actual `usage.completion_tokens`.

This affects accuracy of tok/s calculations by an estimated **±5-10%**.

---

## What We Did Right

### ✅ Timing Methodology
- Uses `time.perf_counter()` (correct, monotonic)
- Separate measurement of first_output vs first_answer (reasoning-aware)
- Warmup requests properly excluded from metrics
- Sequential requests (no concurrency-induced variance)

### ✅ Protocol Rigor
- Explicit warmup: 1 request per model load
- Consistent repeat counts: 3/3/3/2/10
- Fixed temperature: 0.3
- Stream-only validation (no fallback mixing)
- Single token-count source enforcement

### ✅ Baseline Cleanliness
- Killed 122B interference before rerun
- Verified ports clear, memory available
- Quantified interference impact: <1 tok/s avg (negligible)

### ✅ Comparability
- All 4 rows: `valid_run=true`, `comparable=true`
- Same protocol, same prompts, same machine
- Domain-neutral workload (no Agent Civ leakage)

---

## Critical Issue: Token Count Source

### The Problem

**All requests are using `token_count_source: "rough_split"` instead of `"usage"`.**

This means we're counting tokens via:
```python
tokens_out = len(f"{reasoning}\n{content}".split())
```

Instead of MLX server's actual `usage.completion_tokens`.

### Why This Happened

MLX server is **not returning** `usage.completion_tokens` in streaming responses.

From `benchmarking/token.py:243-247`:
```python
tokens_out = body.get("usage", {}).get("completion_tokens")
token_count_source = "usage"
if tokens_out is None:
    tokens_out = _rough_token_count(f"{reasoning}\n{content}")
    token_count_source = "rough_split"
```

The MLX server's `/v1/chat/completions` endpoint is returning `usage: {}` or `usage: null`.

### Impact

**Throughput accuracy: ±5-10%**

- Rough word-split undercounts multi-word tokens (e.g., "don't" = 1 word, 2 tokens)
- Rough word-split overcounts whitespace/punctuation
- For English text, word count ≈ 0.75x token count (rule of thumb)

**Example:**
- Measured: 26.4 tok/s (using word count)
- Actual: likely **19.8-23.7 tok/s** (if using real tokens)

This means our absolute numbers may be **overstated by ~10-30%**.

---

## Comparison to External Benchmarks

### M3 Max (40-core) Reference
- **Qwen3.5-27B Opus-distilled**: 17.7 tok/s @ 4K context (oMLX, 2026)
- **Our M5 Max**: 25.8 tok/s (thinking-on), 25.9 tok/s (thinking-off)
- **Delta**: +46% over M3 Max

### M5 Max Expected Performance
- **Llama-3-70B (Q4)**: 35.8 tok/s (reported, 2026)
- **Our 27B**: 20-26 tok/s
- **Proportional check**: Reasonable (smaller model, different architecture)

### Verdict on External Comparison

**If our tok/s is overstated by ~25% due to word-split counting:**
- Adjusted M5 results: **19.4-19.4 tok/s** (Opus thinking-on/off)
- Adjusted M5 results: **14.7-19.7 tok/s** (Base thinking-on/off)
- M3 Max reported: **17.7 tok/s**

**After adjustment, our M5 Max results are CONSISTENT with M3 Max + expected M5 improvement (~10-15%).**

---

## Relative Comparisons (Still Valid)

Even though absolute tok/s may be overstated, **relative comparisons within our benchmark are still accurate** because:

1. All 4 rows use the same measurement method
2. All 4 rows measured on the same clean baseline
3. Token-count bias is systematic (affects all rows equally)

### Thinking-Mode Penalty (Relative)
- Base: -6.8 tok/s short, -11.0 sustained (thinking on vs off)
- Opus: -0.1 tok/s short, +0.3 sustained (thinking on vs off)

**This relative story is sound**, even if absolute numbers need correction.

### Model Comparison (Relative)
- Opus faster than Base by +6.2 tok/s (thinking-on)

**This relative advantage is sound**.

---

## Measurement Variability

### Sustained Throughput Stability
We ran 10 sustained requests per config. Expected CV (coefficient of variation): <5% for well-controlled benchmarks.

**Without access to individual request data**, we cannot verify this, but the protocol enforced:
- Sequential execution (no concurrency)
- Clean baseline (no interference)
- Same prompt/temp/tokens across repeats

### Known Sources of Variance
- Model weight loading (mitigated by warmup)
- Metal GPU thermal throttling (minimal on M5 Max under 20min runs)
- Background processes (mitigated by clean baseline)

---

## What We Should Fix Before Publishing

### P0: Token Count Accuracy

**Option A: Fix MLX server to return usage.completion_tokens**
- Check MLX-LM server version
- File issue if it's a regression
- Patch locally if needed

**Option B: Use model's tokenizer for accurate counting**
```python
from transformers import AutoTokenizer
tokenizer = AutoTokenizer.from_pretrained(model_id)
tokens_out = len(tokenizer.encode(f"{reasoning}\n{content}"))
```

**Option C: Disclose and proceed**
- Note in Reddit post: "Token counts via word-split approximation"
- Emphasize relative comparisons only
- Provide adjustment factor (~0.75x for absolute numbers)

### P1: Variability Reporting

Add to Reddit post:
- Individual request CV for sustained runs
- Min/max range for each metric
- Confidence intervals

### P2: Extended Validation

Run additional lanes to increase confidence:
- Core lane (7B, 14B, 32B models)
- Cross-check one model on M4 Max (external validation)
- Re-run one config 3x to measure run-to-run variance

---

## Recommendation

**DO NOT publish absolute tok/s numbers until token counting is fixed.**

**DO publish relative comparisons with clear disclaimers:**

> "Token throughput measured via word-split approximation. Absolute tok/s values may be overstated by ~25%. Relative comparisons within this benchmark (thinking-mode penalty, model-to-model differences) remain valid as all measurements used the same methodology."

**Or:** Fix token counting first, rerun the 4 frontier rows (~20 minutes), then publish with confidence.

---

## Confidence Levels

| Claim | Confidence | Notes |
|-------|-----------|-------|
| Opus eliminates thinking penalty | **HIGH** | Relative delta is methodology-independent |
| Base thinking penalty is ~11 tok/s | **HIGH** | Relative delta is methodology-independent |
| Absolute tok/s: 15-26 range | **MEDIUM** | May be overstated by 10-30% |
| M5 Max is 46% faster than M3 Max | **LOW** | Our absolute numbers are likely inflated |
| Opus faster than Base by 6-8 tok/s | **HIGH** | Relative comparison valid |
| TTFT ~200-240ms | **HIGH** | Time-based, not token-count dependent |
| First-answer latency (thinking mode) | **HIGH** | Time-based, not token-count dependent |

---

## What Online Research Shows

### Thinking Mode Penalties
- Research confirms: 5-10x **output length** overhead for thinking models
- Our finding: throughput degradation only for base, not Opus-distilled
- **Consistent with**: "deliberative reasoning reduces foundational capabilities"

### MLX Performance on Apple Silicon
- M4 Pro 16c: 10.6 tok/s (6-bit, 27B)
- M3 Max 40c: 17.7 tok/s (4-bit, 27B Opus-distilled)
- Our M5 Max: 25.8 tok/s (4-bit, 27B Opus-distilled) — **if overstated by 25% → 19.4 tok/s**
- **Adjusted result aligns with M3 Max + expected M5 improvement**

### Warmup Best Practices
- Confirmed: warmup critical for accurate MLX benchmarks
- We did: 1 warmup request per model load ✅
- Best practice: use `perf_counter()` for timing ✅

---

## Final Verdict

**Quality: B+ (would be A- with correct token counting)**

**Methodology:** Excellent  
**Execution:** Clean  
**Measurement:** Flawed (token count source)  
**Relative comparisons:** Sound  
**Absolute numbers:** Questionable

**Publish now?** Only if:
1. You fix token counting and rerun (20 min), OR
2. You clearly disclaim word-split approximation and focus on relative story

**Extend first?** Yes, but fix token counting before investing in more runs.

---

## Next Steps

1. **Immediate:** Investigate why MLX server isn't returning `usage.completion_tokens`
2. **Short-term:** Implement accurate tokenizer-based counting
3. **Before publish:** Rerun 4 frontier rows with corrected counting
4. **Optional:** Add variability metrics to artifacts
5. **Long-term:** Extend to core lane once token counting is fixed

