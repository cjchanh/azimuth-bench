# Design-partner evaluation guide

This document is for an **external engineer** deciding whether Azimuth Bench is worth adopting: **install**, **inspect static output**, and **understand claims**—without private context and without rerunning benchmarks.

**Truth boundary:** [SOURCE_OF_TRUTH.md](SOURCE_OF_TRUTH.md) plus tests. This page summarizes; SSOT wins on any conflict.

## What Azimuth is

- **Azimuth** is the product name. The **canonical Python package** is **`azimuth_bench`**. The **canonical CLI** is **`azbench`**.
- The repo ships a **throughput** suite (prompts, protocol, validity rules), **adapters** (MLX LM server, OpenAI-compatible HTTP, Ollama HTTP), and a **static report** pipeline that turns committed JSON artifacts into HTML + JSON + exports.
- **`signalbench`** and **`benchmarking/`** exist only for **compatibility** with older imports and scripts. They delegate to `azimuth_bench`; they are not a second implementation.

## Implemented + tested (today)

| Area | Notes |
| --- | --- |
| Throughput suite + adapters above | Same protocol math and artifact shape; fail-closed integrity on ambiguous artifact mapping. |
| `azbench report build <run_dir>` | Static `report/` under the run directory; sanitized public paths. |
| Compare + exports | `report/data/compare.json` (`azimuth_compare_v1`), Markdown export, deterministic share SVGs. |
| Multi-run merge (M5) | `azbench report build <primary> --include-run-dir <other> …` for **Azimuth-shaped** trees only (token summary + per-row artifacts). Emits `merge.json` and explicit comparability classes; no silent directory sweep. |

See SSOT for the authoritative table and file pointers.

## Designed / not claimed here

- **llama.cpp / vLLM** production adapters (stubs / planned only).
- **Hosted SPA** (static site + JSON only).
- **Universal rankings** or ecosystem-wide claims—comparability is row- and protocol-scoped.

## What the committed `benchmarks/` tree proves

The repo includes a **reference run directory** (`benchmarks/`) with a token summary and per-model JSON artifacts. It demonstrates:

- Real **protocol_id** / **prompt_set_id** linkage on artifacts.
- **Integrity** behavior (exactly one artifact per summary row).
- **Report output** you can build offline: HTML pages, `leaderboard.json`, `compare.json`, provider/protocol indexes.

It does **not** prove anything about your hardware or your endpoints until you run throughput yourself.

## One local proof path (no benchmark rerun)

From a clean clone, after `pip install -e ".[dev]"` (see repo README):

```bash
# 1) Static report from committed artifacts
azbench report build benchmarks --repo-root "$(pwd)"

# 2) Exports (read built report/data/)
azbench export markdown benchmarks --output /tmp/azimuth_eval_summary.md
azbench export svg benchmarks --output-dir benchmarks/report/exports

# 3) Optional: confirm merge semantics (two disjoint minimal trees — see tests/test_merge.py for construction rules)
# azbench report build /path/to/primary --repo-root "$(pwd)" --include-run-dir /path/to/other
```

Expected artifacts (paths under `benchmarks/report/` after step 1):

- `data/summary.json`, `data/leaderboard.json`, `data/compare.json`, `data/site_manifest.json`
- `data/runs/<artifact_key>/` per row
- `exports/share_leaderboard.svg`, `exports/share_compare.svg` (regenerated in step 2)

Single-run builds **do not** emit `data/merge.json`. Merged builds emit **`azimuth_merge_v1`** metadata and comparability blockers where applicable.

## Merge at a high level

Merge **combines already-valid** Azimuth run directories. It:

- Blocks duplicate **(model_id, lane, thinking_mode)** across sources.
- Prefixes artifact keys per source (`s0__`, `s1__`, …) to avoid collisions.
- Surfaces **protocol mismatch** and other blockers in `merge.json` / `leaderboard.json`—it does **not** flatten incomparable runs into an unlabeled single ranking.

## Where to go next

- **Methodology / comparability:** [METHODOLOGY.md](METHODOLOGY.md)
- **Reading JSON and pages:** [READING_REPORTS.md](READING_REPORTS.md)
- **Snapshot numbers for outreach (not SSOT):** [PUBLIC_PROOF_PACK.md](PUBLIC_PROOF_PACK.md)
- **Environment variables:** [ENVIRONMENT.md](ENVIRONMENT.md)

## Packaging note

The distribution name on PyPI (if published) may differ from the import package (`azimuth_bench`). Install from this repo with `pip install -e ".[dev]"` for development. Wheel/sdist builds are documented in [release/evaluator/README.md](../../release/evaluator/README.md).
