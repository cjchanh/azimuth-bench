# Asset inventory — what to share or inspect (v0.1.0 RC)

All paths are **relative to the repository root**. Generated files assume you have run `azbench report build benchmarks --repo-root "$(pwd)"` (does not rerun benchmarks).

## Committed inputs (reference snapshot)

| Path | Role |
| --- | --- |
| `benchmarks/benchmark_v2_token_summary.json` | Token summary (**18 rows** in current tree; see [PUBLIC_PROOF_PACK.md](../../../docs/azimuth_bench/PUBLIC_PROOF_PACK.md)) |
| `benchmarks/*.json` | Per-model throughput artifacts (protocol, validity, comparability) |
| `docs/azimuth_bench/SOURCE_OF_TRUTH.md` | What is implemented + tested vs not ([link](../../../docs/azimuth_bench/SOURCE_OF_TRUTH.md)) |

## Generated static report (after `report build`)

| Path | Role |
| --- | --- |
| `benchmarks/report/index.html` | Landing page |
| `benchmarks/report/leaderboard.html` | Sortable-style table view |
| `benchmarks/report/compare.html` | Compare view (scoped pairs) |
| `benchmarks/report/data/leaderboard.json` | Machine-readable leaderboard |
| `benchmarks/report/data/compare.json` | `azimuth_compare_v1` projection + blockers |
| `benchmarks/report/data/summary.json` | Enriched summary rows |
| `benchmarks/report/data/site_manifest.json` | Static site manifest / routes |
| `benchmarks/report/data/runs/<artifact_key>/` | Per-run JSON bundles |
| `benchmarks/report/data/providers/`, `protocols/` | Provider/protocol indexes + pages |

## Charts (matplotlib SVG under report)

| Path | Role |
| --- | --- |
| `benchmarks/report/charts/throughput_structured.svg` | Bar chart — structured JSON tok/s |
| `benchmarks/report/charts/latency_tradeoff.svg` | Latency vs throughput scatter |
| `benchmarks/report/charts/frontier_compare.svg` | Frontier-oriented comparison chart |

## Share exports (deterministic PNG-free SVG; regenerate without full rebuild)

| Path | Role |
| --- | --- |
| `benchmarks/report/exports/share_leaderboard.svg` | Deterministic leaderboard snapshot |
| `benchmarks/report/exports/share_compare.svg` | Deterministic compare card |

Produce or refresh with:

```bash
azbench export svg benchmarks --output-dir benchmarks/report/exports
```

## Markdown export

After building the report:

```bash
azbench export markdown benchmarks --output /tmp/azimuth_summary.md
```

Reads `benchmarks/report/data/summary.json` only.

## What not to oversell

- Charts and SVGs are **derived** from the same summary rows; they are not independent measurements.
- **Merge** outputs (`merge.json`) appear only when using `--include-run-dir`; read `comparability_class` and `blockers` before ranking across sources.
