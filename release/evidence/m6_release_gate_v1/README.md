# M6 release gate — independent audit (`m6_release_gate_v1`)

**Auditor role:** Adversarial verification of shipped claims against `docs/azimuth_bench/SOURCE_OF_TRUTH.md`, tests, and live commands.  
**Repository state:** Evidence recorded from a clean checkout; re-run commands on your machine to reproduce. **Pytest count** is authoritative in `docs/azimuth_bench/SOURCE_OF_TRUTH.md` (not a frozen number in every file here).

## Verdict

**`implemented+tested` — release-gate clean** for the scope defined in SSOT (throughput + report + exports + merge + M6 evaluator/packaging docs).  
**`designed/unverified` (explicit):** llama.cpp / vLLM production adapters, hosted SPA, PyPI publish automation, arbitrary third-party JSON as merge input — per SSOT "Not implemented" table.

This bundle does **not** assert PyPI publication, ecosystem adoption, or external benchmark universality.

## What was audited

- Canonical package `azimuth_bench`, CLI `azbench` / `python -m azimuth_bench`
- Compatibility-only `signalbench` / `benchmarking` (delegation, not duplicate SSOT) — spot-checked via tests + `pyproject.toml` entry points
- Report build, Markdown export, SVG export from committed `benchmarks/`
- Merge semantics — covered by `tests/test_merge.py` (not re-run benchmarks here)
- M6 docs (`DESIGN_PARTNER_EVAL.md`, `release/evaluator/README.md`) and `python -m build` smoke
- Public JSON path hygiene — `benchmarks/report/data/*.json` scanned for absolute home-directory prefixes in this audit (none found in generated bundle)

## Files in this bundle

| File | Role |
| --- | --- |
| `commands.txt` | Exact commands executed |
| `results.md` | Concise outcomes (exit codes / key lines) |
| `artifacts_manifest.txt` | Key outputs and paths |
| `claims_ledger.md` | Claim → evidence anchor |

## Reproducing

Run from repository root with `.venv` activated (see `commands.txt`). Replace `$(pwd)` with your checkout path if needed.
