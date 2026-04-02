# Azimuth Bench v0.1.0 launch playbook

This is the one file to use for launch. It has the order of operations, the actual post copy, and the short replies for the obvious questions.

## First: the only real blocker

Do **not** post this publicly until the repo is public.

Configured links:

- Repo: `https://github.com/cjchanh/azimuth-bench`
- Release: `https://github.com/cjchanh/azimuth-bench/releases/tag/v0.1.0`
- Live report: `https://cjchanh.github.io/azimuth-bench/report/index.html`

Current blocker:

- The repo is still private, so the repo URL and release URL both 404 for the public right now.
- The Pages report is live, but that is not enough on its own. If you post before the repo is public, people will hit a dead end.

One-line fix:

```bash
gh repo edit cjchanh/azimuth-bench --visibility public --accept-visibility-change-consequences
```

If you do only one thing before posting, do that.

## What to lead with now

You now have more than a release and a sample report. You also have a fresh local batch that was actually run through the tool.

That matters because it gives you a better hook than "I released a benchmark repo."

The best first post is:

- the repo
- the release
- the live report
- one good image from the fresh batch

Best image order:

1. `27b_matchup_hero.png`
2. `speed_vs_latency_tradeoff.png`
3. `27b_thinking_delta.png`

Do **not** lead with the full ladder unless someone asks for more detail. It is more useful as the second or third image.

Also be explicit about what the fresh batch is:

- the core lane came from an existing local serving path
- the 27B thinking lane came from a dedicated MLX benchmark lane
- the charts are useful, but you should not talk about that mixed batch like it is one pure apples-to-apples universal ranking

That honesty is a strength here, not a weakness.

## What the project is

Short version:

Azimuth Bench is an open-source inference benchmarking toolchain that runs a fixed throughput suite, emits artifact-backed JSON, and builds static reports with explicit comparability limits.

Sharper version:

The useful thing here is not just "benchmarking." It's that the report surface is honest about what is and is not comparable instead of flattening everything into one fake global leaderboard.

What it is not:

- not a hosted benchmark product
- not a universal ranking claim
- not a production `llama.cpp` or `vLLM` surface yet

## Launch order

Keep this simple.

1. Make the repo public.
2. Click the repo, release, and report links yourself once.
3. Post Reddit first.
4. Watch replies for 30-60 minutes.
5. If there is no broken-link or obvious messaging problem, post HN.
6. Post the GitHub announcement after that.

Best window:

- Tuesday through Thursday
- Morning US time
- Roughly `8am-11am MT`

Why this order:

- Reddit is better for early signal and practical feedback.
- HN is harsher and more momentum-sensitive. Better to use it after you've confirmed the basic framing lands.
- GitHub is the durable record, not the main attention source.

## Link strategy

Reddit:

- repo
- release
- live report

Hacker News:

- submit the repo link
- put release + live report in the first comment

GitHub:

- release
- live report

Optional X / Discord:

- repo
- live report

## What not to do

- Don't call it a hosted product.
- Don't call it a universal benchmark.
- Don't pretend adoption you don't have.
- Don't lead with "benchmark-v2."
- Don't oversell the static report as if it's a live app.
- Don't post while the repo is private.

## Reddit post

### Primary version

**Title**

I open-sourced Azimuth Bench v0.1.0 — static benchmarking/reporting for MLX, Ollama, and OpenAI-compatible backends

**Body**

I just released Azimuth Bench v0.1.0.

Repo: https://github.com/cjchanh/azimuth-bench  
Release: https://github.com/cjchanh/azimuth-bench/releases/tag/v0.1.0  
Live report: https://cjchanh.github.io/azimuth-bench/report/index.html

It's an open-source inference benchmarking toolchain built around a fixed throughput suite, artifact-backed outputs, and static reports you can inspect without a hosted service.

What it does today:

- runs a throughput suite against MLX, Ollama, or OpenAI-compatible HTTP backends
- emits JSON artifacts with explicit protocol, validity, and comparability metadata
- builds static HTML + JSON reports
- exports Markdown summaries and deterministic SVG share cards
- supports merging multiple Azimuth-shaped run directories with explicit comparability blockers

What it does **not** claim:

- no hosted benchmark product / SPA
- no production `llama.cpp` or `vLLM` adapter yet
- no "universal best model" ranking
- no PyPI automation

The part I cared most about was honesty. The report surface carries comparability limits instead of pretending every row belongs in one magic leaderboard.

If you try it, the feedback I care about most is:

1. whether the report / compare surface is actually useful
2. where the comparability model feels too strict or not strict enough
3. what backend support would matter next

### Shorter version

I released Azimuth Bench v0.1.0:

Repo: https://github.com/cjchanh/azimuth-bench  
Release: https://github.com/cjchanh/azimuth-bench/releases/tag/v0.1.0  
Live report: https://cjchanh.github.io/azimuth-bench/report/index.html

It's an OSS inference benchmark toolchain for MLX, Ollama, and OpenAI-compatible backends with artifact-backed JSON, static reports, compare output, Markdown export, and explicit comparability limits.

Not claiming a hosted product or universal rankings. Mostly looking for feedback on whether the report/compare surface is actually useful and what backend support matters next.

### Version without live report

Use this if the report URL is down for any reason:

I just released Azimuth Bench v0.1.0.

Repo: https://github.com/cjchanh/azimuth-bench  
Release: https://github.com/cjchanh/azimuth-bench/releases/tag/v0.1.0

It's an open-source inference benchmarking toolchain built around a fixed throughput suite, artifact-backed outputs, and static reports with explicit comparability limits.

It supports MLX, Ollama, and OpenAI-compatible HTTP backends today. Not claiming a hosted product, universal rankings, or production `llama.cpp` / `vLLM` support yet.

### Version if repo is still private

Don't post publicly. Use this only for a private DM or warm intro:

I just finished Azimuth Bench v0.1.0, an inference benchmarking toolchain built around artifact-backed outputs and static reports with explicit comparability limits. The public repo isn't open yet, but if you're open to an early look I can share access plus a live report snapshot.

## Hacker News

### Title

Show HN: Azimuth Bench — artifact-backed local LLM benchmarking with static reports

### First comment

I just released Azimuth Bench v0.1.0.

Repo: https://github.com/cjchanh/azimuth-bench  
Release: https://github.com/cjchanh/azimuth-bench/releases/tag/v0.1.0  
Live report: https://cjchanh.github.io/azimuth-bench/report/index.html

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

### Shorter version

I released Azimuth Bench v0.1.0:

Repo: https://github.com/cjchanh/azimuth-bench  
Live report: https://cjchanh.github.io/azimuth-bench/report/index.html

It's an OSS benchmarking/reporting toolchain for MLX, Ollama, and OpenAI-compatible backends. Core idea: static reports plus explicit comparability metadata, not one fake global leaderboard.

### Version without live report

I released Azimuth Bench v0.1.0:

Repo: https://github.com/cjchanh/azimuth-bench  
Release: https://github.com/cjchanh/azimuth-bench/releases/tag/v0.1.0

It's an OSS benchmarking/reporting toolchain for MLX, Ollama, and OpenAI-compatible backends. The main angle is explicit comparability limits instead of flattening all runs into one universal ranking.

## GitHub announcement

GitHub Discussions is currently off, so use this as a pinned issue, repo announcement, or release follow-up comment.

### Title

Azimuth Bench v0.1.0 is live

### Body

Azimuth Bench v0.1.0 is live.

Release: https://github.com/cjchanh/azimuth-bench/releases/tag/v0.1.0  
Live report: https://cjchanh.github.io/azimuth-bench/report/index.html

Azimuth Bench is an open-source inference benchmarking toolchain with:

- a fixed throughput suite
- MLX, Ollama, and OpenAI-compatible HTTP support
- artifact-backed JSON outputs
- static HTML + JSON reports
- compare output with explicit comparability limits
- Markdown and deterministic SVG export
- validated multi-run merge for Azimuth-shaped run directories

Not in scope for v0.1.0:

- hosted UI / SPA
- production `llama.cpp` / `vLLM` adapters
- PyPI automation
- universal ranking claims

If you use it, the most useful feedback is on the report/compare surface, the comparability rules, and which backend support matters most next.

## Optional short post for X / Discord / Slack

Released Azimuth Bench v0.1.0: OSS inference benchmarking with MLX, Ollama, and OpenAI-compatible support, artifact-backed JSON, static reports, compare output, and explicit comparability limits.

Repo: https://github.com/cjchanh/azimuth-bench  
Report: https://cjchanh.github.io/azimuth-bench/report/index.html  
Release: https://github.com/cjchanh/azimuth-bench/releases/tag/v0.1.0

## Comment replies

### "Why not just use lm-eval or existing benchmarks?"

This is narrower and more operational. The point isn't general eval breadth. It's fixed throughput benchmarking, artifact-backed outputs, static reports, and explicit comparability metadata.

### "Why static reports?"

Because they're easy to host, easy to inspect, and easy to regenerate from artifacts. You don't have to trust a live service to look at the results.

### "Why no hosted UI?"

I wanted the benchmark and reporting pipeline to stand on its own first. Hosted product work is a separate scope and I didn't want to pretend it already existed.

### "Why no llama.cpp or vLLM yet?"

I kept v0.1.0 to what is actually implemented and tested. Those are still planned, not shipped.

### "How is comparability handled?"

Runs carry protocol, validity, and comparability metadata. Merged outputs surface blockers instead of flattening everything into one unlabeled ranking.

### "What does this do that Ollama or OpenAI dashboards don't?"

It gives you a fixed benchmark protocol, artifact-backed outputs, report generation, compare output, and explicit honesty about what is and isn't comparable across runs.

### "Why should anyone trust these numbers?"

They shouldn't trust them blindly. The point is that the artifacts, protocol, and report outputs are inspectable and the claims are scoped.

### "Is this just for MLX?"

No. MLX, Ollama, and OpenAI-compatible HTTP are implemented today. It's not MLX-only.

## Minimal checklist before posting

1. Make the repo public.
2. Open these three links yourself:
   - `https://github.com/cjchanh/azimuth-bench`
   - `https://github.com/cjchanh/azimuth-bench/releases/tag/v0.1.0`
   - `https://cjchanh.github.io/azimuth-bench/report/index.html`
3. Confirm the report URL returns `200`.
4. Post the Reddit version.
5. Watch replies for half an hour.
6. If there is no broken-link or obvious confusion problem, post HN.

## Exact first move

If you want the lowest-effort path:

1. Run the visibility change.
2. Post the Reddit primary version from this file.
3. Reuse the HN version a bit later the same morning.

If you do that, you have a clean enough public launch without needing to think through the messaging again.
