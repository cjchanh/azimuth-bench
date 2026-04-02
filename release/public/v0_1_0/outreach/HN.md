# Hacker News — Show HN

**Title**

Show HN: Azimuth Bench — artifact-backed local LLM benchmarking with static reports

**First comment**

I just released Azimuth Bench v0.1.0.

Repo: https://github.com/cjchanh/azimuth-bench  
Release: https://github.com/cjchanh/azimuth-bench/releases/tag/v0.1.0  
Live report: https://cjchanh.github.io/azimuth-bench/report/index.html  

I also ran a small fresh local batch for launch and used that to generate the chart I’m posting alongside it.

The angle is pretty simple: fixed throughput benchmarking, artifact-backed JSON, and static reports that are explicit about comparability limits instead of flattening everything into one fake global ranking.

Implemented today:

- throughput suite
- MLX / Ollama / OpenAI-compatible HTTP adapters
- static report build
- compare projection
- Markdown + deterministic SVG export
- validated multi-run merge for Azimuth-shaped run trees

Not implemented:

- hosted product / SPA
- production `llama.cpp` / `vLLM` adapters
- PyPI automation

If this sounds useful, the feedback I'd care about most is whether the comparability model feels too strict, not strict enough, or roughly right.
