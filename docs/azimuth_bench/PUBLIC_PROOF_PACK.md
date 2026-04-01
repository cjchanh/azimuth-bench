# Public proof pack (reference snapshot)

**Purpose:** A single place for **outreach** (README links, release notes, partner email, blog draft) that stays within **facts** from this repository. Refresh numbers if the committed `benchmarks/benchmark_v2_token_summary.json` changes.

**Do not** treat this file as SSOT — [SOURCE_OF_TRUTH.md](SOURCE_OF_TRUTH.md) + code + tests are authoritative.

## What is Azimuth?

**Azimuth** is the product name for a portable inference **benchmark** toolchain: **Azimuth Bench** (`azimuth_bench`) produces artifacts; **Azimuth Report** (`azbench report build`) turns a run directory into static HTML + JSON. See the root [README.md](../../README.md).

## What this repo’s sample run contains

| Fact | Value |
| --- | --- |
| Summary rows | **18** (`benchmarks/benchmark_v2_token_summary.json`, `lane: all`) |
| Suite family | Throughput (`suite_family` in artifacts) |
| Protocol id | **`benchmark_v2_m5max_v1`** |
| Prompt set id | **`benchmark_v2_m5max_prompt_set_v1`** |
| Machine class (protocol label) | **`Apple Silicon M5 Max local MLX lane`** — a **declared** lane label in protocol JSON, not third-party hardware certification |
| Typical stack | MLX LM **local** server (OpenAI-compatible HTTP) for these artifacts |
| Validity | Artifacts include `validity` / `comparability`; report rows enrich **`comparable`** and blockers |

Lanes in the 18-row set include **`core`** (many models) and **`frontier_27b`** (four runs: base vs distilled × thinking on/off).

## What “comparable” means here

A run is **`comparable: true`** when it passes the throughput suite’s **validity** checks for that protocol (e.g. streaming requirements, repeat counts, consistent token count source). It does **not** mean all 18 rows are interchangeable without reading lane, thinking mode, and protocol.

## Top-line results (illustrative, not a ranking claim)

From **`structured_json_tok_s`** in the committed summary JSON (core lane highlights; verify in `benchmarks/benchmark_v2_token_summary.json`):

1. **Phi 4 Mini** — ~146 tok/s structured  
2. **Gemma 3 4B** — ~134 tok/s structured  
3. **Qwen2.5 Coder 7B** — ~107 tok/s structured  

Several other **core** models sit in a similar band (~95–170 tok/s on short prompts; structured values vary). **Frontier 27B** rows are much lower (~25–32 tok/s structured in this snapshot) and include **thinking on** paths with very high **first_answer_ms** in some rows — read artifacts before comparing to core lane numbers.

These numbers are **one machine / one protocol / one snapshot**. They are not a universal “best model” verdict.

## What this does **not** prove

- Performance on **non-MLX** stacks (other adapters exist in code but this dataset is MLX LM artifacts).
- **Quality** of answers — only throughput/latency-style metrics from fixed prompts.
- **Reproducibility** on your hardware without re-running the harness.

## Where receipts and reports live

| Asset | Location |
| --- | --- |
| Source artifacts | `benchmarks/*.json` (historical inputs) |
| Compiled summary | `benchmarks/benchmark_v2_token_summary.json` |
| Built report (after `azbench report build`) | `benchmarks/report/` (gitignored by default — regenerate locally) |
| Report data bundle | `benchmarks/report/data/` |
| How to read outputs | [READING_REPORTS.md](READING_REPORTS.md) |

## How to regenerate the proof surface locally

```bash
source .venv/bin/activate
pip install -e ".[dev]"
azbench report build benchmarks --repo-root "$(pwd)"
azbench export markdown benchmarks --output /tmp/azimuth_summary.md
```

## Trust model (short)

Outputs are **artifact-backed**, **integrity-checked**, and **sanitized** for public JSON (relative paths). Gaps (e.g. missing commit SHA) are **surfaced** in bundles, not hidden. See [METHODOLOGY.md](METHODOLOGY.md).
