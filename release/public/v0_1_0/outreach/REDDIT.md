# Reddit — r/LocalLLaMA or adjacent

**Title**

I open-sourced Azimuth Bench v0.1.0 — local LLM benchmarking with static reports

**Body**

I just released Azimuth Bench v0.1.0.

Repo: https://github.com/cjchanh/azimuth-bench  
Release: https://github.com/cjchanh/azimuth-bench/releases/tag/v0.1.0  
Live report: https://cjchanh.github.io/azimuth-bench/report/index.html

It's an open-source inference benchmarking toolchain built around a fixed throughput suite, artifact-backed outputs, and static reports you can inspect without a hosted service.

I also ran a small fresh local batch for launch and attached one of the charts from that run.

What it does today:

- runs a throughput suite against MLX, Ollama, or OpenAI-compatible HTTP backends
- emits JSON artifacts with explicit protocol, validity, and comparability metadata
- builds static HTML + JSON reports
- exports Markdown summaries and deterministic SVG share cards
- supports merging multiple Azimuth-shaped run directories with explicit comparability blockers

What it does not claim:

- no hosted benchmark product / SPA
- no production llama.cpp or vLLM adapter yet
- no "universal best model" ranking
- no PyPI automation

The part I cared most about was honesty. The report surface carries comparability limits instead of pretending every row belongs in one magic leaderboard.

One important caveat on the fresh chart: it's a mixed local batch. The core rows came from an existing OpenAI-compatible local serving path, and the 27B thinking rows came from a dedicated MLX benchmark lane. Useful, real, but not one fake universal apples-to-apples ranking.

If you try it, the feedback I care about most is:

1. whether the report / compare surface is actually useful
2. where the comparability model feels too strict or not strict enough
3. what backend support would matter next
