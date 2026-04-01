# Ollama MLX Support: Strategic Impact on Your Stack

**Date:** 2026-04-01  
**Context:** Ollama v0.19 (March 2026) added MLX backend support for Apple Silicon

---

## What Just Happened

**Ollama now supports MLX as a backend** (preview, March 2026), replacing their default llama.cpp engine on Apple Silicon.

### Performance Gains (Ollama's Numbers)
- **Prefill:** 1,154 → 1,810 tok/s (+57%)
- **Decode:** 58 → 112 tok/s (+93%)
- **Model:** Qwen3.5-35B-A3B (only supported model currently)

### What This Means
Ollama is now using the same MLX framework you're already using directly, but wrapped in Ollama's convenience layer.

---

## Your Current Stack

```
┌─────────────────────────────────────────────────────┐
│ Your Applications                                    │
│  - agent-civilization (experiments, benchmarks)     │
│  - sovereign-stack/OP (122B chat server)            │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│ Direct MLX-LM Server                                 │
│  - mlx_lm.server (ports 8100, 9700)                 │
│  - Python API + OpenAI-compatible HTTP              │
│  - Full control over model loading, quantization    │
│  - chat_template_kwargs.enable_thinking support     │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│ MLX Framework (Apple, 0.31.1)                       │
│  - Unified memory architecture                       │
│  - Metal GPU acceleration                            │
│  - Highest sustained throughput on Apple Silicon    │
└─────────────────────────────────────────────────────┘
```

---

## Ollama MLX Stack (New)

```
┌─────────────────────────────────────────────────────┐
│ User Applications                                    │
│  - Any OpenAI-compatible client                     │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│ Ollama Convenience Layer                            │
│  - Simple CLI: ollama run qwen3.5                   │
│  - Automatic model downloads                         │
│  - Model version management                          │
│  - Multi-model switching                             │
│  - REST API: localhost:11434                        │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│ MLX Backend (NEW in v0.19, preview)                 │
│  - Same MLX framework you're using                  │
│  - Ollama's MLX adapter layer                       │
│  - Limited model support (1 model currently)        │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│ MLX Framework (Apple)                               │
│  - Unified memory, Metal GPU                        │
└─────────────────────────────────────────────────────┘
```

---

## Performance Comparison

| Metric | Direct MLX-LM | Ollama (MLX) | Ollama (llama.cpp) |
|--------|---------------|--------------|---------------------|
| **Sustained tok/s** | ⭐⭐⭐⭐⭐ Highest | ⭐⭐⭐⭐ High | ⭐⭐⭐ Good |
| **Prefill speed** | ⭐⭐⭐⭐⭐ ~1,900+ | ⭐⭐⭐⭐ ~1,810 | ⭐⭐⭐ ~1,154 |
| **Decode speed** | ⭐⭐⭐⭐⭐ Variable | ⭐⭐⭐⭐ ~112 | ⭐⭐ ~58 |
| **Setup complexity** | ⭐⭐ Moderate | ⭐⭐⭐⭐⭐ Trivial | ⭐⭐⭐⭐⭐ Trivial |
| **Fine control** | ⭐⭐⭐⭐⭐ Full | ⭐⭐ Limited | ⭐⭐ Limited |
| **Model support** | ⭐⭐⭐⭐⭐ All HF MLX | ⭐ 1 model | ⭐⭐⭐⭐⭐ Many |

**Research finding (2026 study):**
> "MLX achieved the highest sustained generation throughput, while llama.cpp excelled at lightweight single-stream inference. Ollama prioritizes developer ergonomics but lags behind both MLX and llama.cpp in throughput and TTFT."

---

## Strategic Impact on Your Stack

### ❌ Does NOT Change Your Core Strategy

**Reason:** You're already using MLX directly, which is faster than Ollama's MLX wrapper.

**Your architecture requirements:**
- ✅ Air-gapped, deterministic
- ✅ Full control over model loading
- ✅ Custom chat template kwargs (thinking mode)
- ✅ Benchmark-grade timing precision
- ✅ Multi-model concurrent serving (different ports)

**Ollama MLX limitations:**
- ❌ Preview-only (1 model supported)
- ❌ Less control over loading/quantization
- ❌ Convenience layer adds latency overhead
- ❌ May not expose thinking-mode controls
- ❌ Harder to instrument for benchmarking

**Verdict:** Ollama MLX is a step in your direction, but you're already past where it's going.

---

## When Ollama MLX Would Make Sense

### Scenarios Where Ollama Wins

**1. Rapid prototyping / exploratory work**
```bash
# Ollama
ollama run qwen3.5
> How do I...

# Your stack
python3 -m mlx_lm.server --model ... --port 9700 &
curl http://localhost:9700/v1/chat/completions -d '...'
```

**Ollama is faster to iterate** when you don't need custom controls.

**2. Multi-model switching**
```bash
ollama run qwen3.5
ollama run llama3.1
ollama run mistral
```

**Ollama manages model lifecycles** automatically. Your stack requires manual server restarts per model.

**3. Team/collaborative environments**
- Ollama: predictable `localhost:11434` endpoint
- Your stack: custom ports, manual coordination

**4. When you don't need thinking-mode control**
- If you're not using `chat_template_kwargs.enable_thinking`, Ollama's abstraction doesn't lose you anything.

---

## When Direct MLX-LM Still Wins (Your Use Cases)

### 1. Benchmarking (Your Primary Use Case)
**You need:**
- Exact control over `stream_options`
- Precise timing without abstraction layers
- Custom warmup protocols
- Thinking-mode toggles
- Deterministic artifact naming

**Ollama:** Abstraction layer adds variables, hides controls.

### 2. Production Inference (sovereign-stack/OP)
**You need:**
- 122B models (Ollama MLX: 35B only, preview)
- Custom chat template kwargs
- Stable API contracts
- No "preview" features in prod

**Ollama:** Not production-ready for your requirements.

### 3. Air-Gapped Research (agent-civilization)
**You need:**
- Reproducible runs across months
- Frozen dependencies
- No automatic model updates
- Full artifact control

**Ollama:** Model management is a feature for UX, but a liability for reproducibility.

### 4. Multi-Model Concurrent Serving
**You do:**
```
:8100 → 122B (sovereign-stack)
:9700 → 27B (benchmarks)
```

**Ollama:** Single-model server, switching requires unload/reload.

---

## Architecture Options Going Forward

### Option A: Stay Pure MLX-LM (RECOMMENDED)

**When:**
- Benchmarking remains a priority
- You need custom controls
- Air-gapped reproducibility matters

**Pros:**
- Highest performance
- Full control
- No "preview" risk
- Already invested in this stack

**Cons:**
- More manual model management
- No convenience CLI

---

### Option B: Hybrid Stack

**Use Ollama for:**
- Quick exploratory chats
- Model discovery
- Non-critical prototyping

**Use direct MLX-LM for:**
- Benchmarking
- Production inference (OP)
- Agent Civ experiments
- Anything requiring thinking-mode control

**Implementation:**
```
Ollama:       localhost:11434  (exploratory)
MLX-LM bench: localhost:9700   (benchmarks)
MLX-LM prod:  localhost:8100   (OP/sovereign-stack)
```

**Pros:**
- Best of both worlds
- Ollama for speed, MLX for precision

**Cons:**
- Three inference stacks to manage
- Port/memory coordination complexity

---

### Option C: Migrate to Ollama MLX (NOT RECOMMENDED)

**When:**
- Convenience > control
- You abandon benchmarking
- Thinking-mode isn't critical

**Pros:**
- Simpler UX
- Easier model switching

**Cons:**
- Give up thinking-mode control
- Lower peak performance
- Preview-only (1 model)
- Lose benchmark precision
- Incompatible with your air-gap philosophy

**Verdict:** This would be **backwards** for your use cases.

---

## Specific Impact on Your Projects

### agent-civilization Benchmarks
**Impact:** None. You need MLX-LM's controls.

**Why:**
- Your benchmark protocol requires `stream_options.include_usage`
- You need deterministic thinking-mode toggles
- Ollama's abstraction layer would add timing noise

**Recommendation:** Stay on direct MLX-LM.

---

### sovereign-stack / OP (122B Chat)
**Impact:** None. Ollama doesn't support your model.

**Why:**
- You're running 122B (Qwen3.5-122B-A10B)
- Ollama MLX: preview, 35B only
- Even if supported, you need chat_template_kwargs

**Recommendation:** Stay on direct MLX-LM.

---

### Exploratory / Ad-Hoc Work
**Impact:** Positive. Ollama could speed up quick tests.

**Example:**
```bash
# Quick test without your harness
ollama run qwen3.5
> Test this edge case...
```

**Recommendation:** Add Ollama as a convenience tool, but keep MLX-LM as SSOT.

---

## What This Means for the Ecosystem

### Good News
1. **MLX adoption growing** - More people will see what you already know (MLX > llama.cpp on Apple Silicon)
2. **Pressure on MLX-LM** - Ollama's UX will push ml-explore to improve ergonomics
3. **Validation of your approach** - You chose MLX early, ecosystem is catching up

### Risks
1. **MLX-LM may lose focus** - If Ollama becomes "the way" to run MLX, ml-explore may deprioritize `mlx_lm.server`
2. **Fragmentation** - Multiple MLX runtimes (Ollama, MLX-LM, custom) could fragment the ecosystem

---

## Recommendation

**DO NOT change your fundamental stack.**

**Reasons:**
1. You're already on the fastest path (direct MLX)
2. Ollama MLX is preview-only, limited models
3. You need controls Ollama doesn't expose
4. Your benchmarking requires precision Ollama can't provide

**DO consider Ollama as a convenience layer** for quick exploratory work:
- Install: `brew install ollama`
- Use for: rapid model testing, non-critical chats
- Keep MLX-LM for: benchmarks, production, experiments

**Your stack in 3 months (if Ollama MLX matures):**
```
Exploratory:  ollama (convenience)
Benchmarking: mlx_lm.server (precision)
Production:   mlx_lm.server (control)
```

**Your stack today:**
```
Everything:   mlx_lm.server
```

**No urgent changes needed.**

---

## Action Items

### Immediate (Optional)
1. Install Ollama 0.19: `brew install ollama`
2. Test Ollama MLX with Qwen3.5-35B
3. Compare UX vs. your MLX-LM workflow
4. Decide if convenience layer is worth the tradeoff

### Short-Term (Monitor)
1. Watch Ollama MLX model support expansion
2. Check if Ollama exposes `chat_template_kwargs`
3. Benchmark Ollama MLX vs. direct MLX-LM on same model
4. Evaluate if Ollama's abstraction layer adds <5% latency overhead

### Long-Term (Strategic)
1. If Ollama MLX matures to 10+ models + thinking-mode support:
   - Consider hybrid stack (Ollama for UX, MLX-LM for precision)
2. If ml-explore abandons `mlx_lm.server`:
   - Fork and maintain internally (you have the expertise)
3. If Ollama becomes dominant:
   - Lobby for benchmark-grade controls in Ollama

---

## Bottom Line

**Ollama MLX is Ollama catching up to where you already are.**

It's good for the ecosystem (more MLX adoption), but it doesn't change your strategic position. You're already running the highest-performance inference stack on Apple Silicon.

**Your fundamental stack remains:**
- Direct MLX-LM for precision work
- Air-gapped, deterministic, full control
- Optionally add Ollama for quick exploratory chats

**No migration needed. No architecture change needed.**

You're still on the fastest path.

