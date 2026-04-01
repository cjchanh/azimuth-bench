# M6 release / evaluator bundle (static)

This directory holds **documentation and contracts** for a repeatable **offline evaluation** of Azimuth Bench. It does **not** store benchmark secrets or live telemetry.

## Purpose

- Give design partners and CI a **single pointer** for “what to run” and “what files should appear.”
- Stay **artifact-backed**: all proof commands consume committed `benchmarks/` JSON or locally built `report/data/`.

## Deterministic local proof (committed artifacts)

Run from the repository root with the dev virtualenv active:

```bash
ruff check . && ruff format --check .
python3 -m pytest -q
azbench report build benchmarks --repo-root "$(pwd)"
azbench export markdown benchmarks --output /tmp/azimuth_export.md
azbench export svg benchmarks
```

**Expected:** `benchmarks/report/data/` populated; exports under `benchmarks/report/exports/`; pytest count matches [SOURCE_OF_TRUTH.md](../../docs/azimuth_bench/SOURCE_OF_TRUTH.md).

Narrated guide: [DESIGN_PARTNER_EVAL.md](../../docs/azimuth_bench/DESIGN_PARTNER_EVAL.md).

## Optional: sdist / wheel build (local packaging check)

This verifies `pyproject.toml` is buildable; it does **not** assert PyPI publication.

```bash
pip install build
python -m build --outdir /tmp/azimuth_dist
```

You should see wheel and sdist artifacts under `/tmp/azimuth_dist` with the project version from `pyproject.toml`.

## Evidence slots (operator use)

For audit workflows that require copying receipts, hashes, or session logs into the repo, use a **dated run id** under `release/evidence/<RUN_ID>/` (create the directory when needed). Nothing in that path is required for core product tests; CI does not depend on it.

**Example (in-repo):** [release/evidence/m6_release_gate_v1/](../evidence/m6_release_gate_v1/README.md) — independent release-gate audit commands, results, and claims ledger.

**Public release candidate (v0.1.0):** [release/public/v0_1_0/README.md](../public/v0_1_0/README.md) — notes, announcement draft, asset inventory.
