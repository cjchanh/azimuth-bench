# Contributing

## Scope

This repo is **Azimuth Bench** (`azimuth_bench`). **`signalbench/`** and **`benchmarking/`** are compatibility shims only — do **not** add new source-of-truth logic there. See [docs/azimuth_bench/SOURCE_OF_TRUTH.md](docs/azimuth_bench/SOURCE_OF_TRUTH.md).

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Before you open a PR

From the repository root:

```bash
ruff check .
ruff format --check .
python3 -m pytest -q
```

- Match existing style and type hints in `azimuth_bench/`.
- Prefer **fail-closed** behavior for integrity and comparability (see SSOT).
- If behavior changes, update **SOURCE_OF_TRUTH.md** and tests in the **same** change.

## What we will not merge in drive-by PRs

- New benchmark semantics or prompt/protocol edits without an explicit maintainer decision.
- Duplicated throughput or summary field logic outside `azimuth_bench`.
- Secrets, hardcoded personal paths, or unverifiable claims in public JSON or docs.

## Release pack

Public-facing notes for the current candidate live under `release/public/v0_1_0/`. Refresh them when the release story changes.
