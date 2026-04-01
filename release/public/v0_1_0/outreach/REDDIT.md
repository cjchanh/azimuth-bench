# Reddit — r/LocalLLaMA or adjacent (copy-ready)

**Title**

I open-sourced Azimuth Bench v0.1.0 — static benchmarking/reporting for MLX, Ollama, and OpenAI-compatible backends

**Body**

I just released Azimuth Bench v0.1.0:

https://github.com/cjchanh/benchmark-v2  
https://github.com/cjchanh/benchmark-v2/releases/tag/v0.1.0  

It’s an OSS inference benchmarking toolchain built around a fixed throughput suite, artifact-backed outputs, and static reports you can inspect without a hosted service.

**Live sample report (static, from committed artifacts):**  
https://cjchanh.github.io/benchmark-v2/report/index.html  

**What it does today:**

- runs a throughput suite against MLX, Ollama, or OpenAI-compatible HTTP backends  
- emits JSON artifacts with explicit protocol / validity / comparability metadata  
- builds static HTML + JSON reports  
- exports Markdown summaries and deterministic SVG share cards  
- supports merge of multiple Azimuth-shaped run directories with explicit comparability blockers  

**What it does not claim:**

- no hosted benchmark product / SPA  
- no production llama.cpp or vLLM adapter yet  
- no “universal best model” ranking  
- no PyPI automation  

One thing I cared about was honesty: the report surface carries comparability limits instead of flattening everything into a single magic leaderboard.

If you try it, the feedback I care about most is:

1. whether the report / compare surface is actually useful  
2. where the comparability model feels too strict or not strict enough  
3. what backend support would matter next  
