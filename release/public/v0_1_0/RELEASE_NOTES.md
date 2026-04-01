# Release notes — v0.1.0 (release candidate)

**Distribution:** `benchmark-v2` **0.1.0** (`pyproject.toml`)  
**Import package:** `azimuth_bench`  
**CLI:** `azbench`

## What this release is

A **credible first public snapshot** of the Azimuth Bench toolchain: throughput suite, MLX + OpenAI-compatible + Ollama adapters, static **Azimuth Report** build, compare projection, SVG exports, and **validated multi-run merge** for Azimuth-shaped run directories. Community-facing docs (`CHANGELOG`, `CONTRIBUTING`, `SECURITY`) and this pack are included; **no** change to benchmark protocol math or prompts in this tagging pass.

## Implemented + tested (high level)

- `azbench report build`, `azbench export markdown`, `azbench export svg`
- Integrity gate on ambiguous artifact mapping (fail-closed)
- `compare.json` (`azimuth_compare_v1`) with explicit blocked comparisons
- Merge via `--include-run-dir` with `merge.json` / comparability metadata
- Tests and governance gates as documented in SSOT

## What this release does **not** claim

- Production **llama.cpp** / **vLLM** adapters (stubs / planned only).
- A hosted product, SPA, or managed benchmark service.
- PyPI publication automation (local `python -m build` is documented and tested; publishing is a separate step).
- Universal “best model” rankings — comparability is **scope-lane-protocol** aware.

## Verification

See root [README.md](../../README.md) and [release/evaluator/README.md](../../release/evaluator/README.md). Typical check:

```bash
pip install -e ".[dev]"
ruff check . && ruff format --check . && python3 -m pytest -q
azbench report build benchmarks --repo-root "$(pwd)"
```

## Known limitations

- Raw artifacts under `benchmarks/` may contain **machine-local** receipt fields from the original run environment; the **report** layer normalizes public-facing paths for sharing. Do not treat raw JSON as already redacted for every field.
