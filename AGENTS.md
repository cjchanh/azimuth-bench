# AGENTS.md — Azimuth Bench

## Scope

Portable inference benchmark platform. **Repository root** is the directory
containing `pyproject.toml` (use `$(pwd)` after `cd` into your clone).

Canonical product surface:
- Python package: `azimuth_bench`
- CLI: `azbench` / `python3 -m azimuth_bench`

Compatibility-only surfaces:
- `signalbench/*`
- `benchmarking/*`

## Canonical Commands

Run from repository root with the dev virtualenv activated.

- Test: `python3 -m pytest -q`
- Lint: `ruff check .`
- Format: `ruff format --check .`
- Report build: `azbench report build benchmarks --repo-root "$(pwd)"`
- Export markdown: `azbench export markdown benchmarks --output /tmp/azimuth_export.md`
- Export SVG: `azbench export svg benchmarks`

## Project Constraints

- `azimuth_bench/*` owns product behavior; compatibility layers may delegate but
  must not redefine source of truth.
- Do not rerun benchmarks unless explicitly required to resolve an integrity
  issue.
- Public report JSON and exports must not leak personal paths, secrets, or
  unverifiable provider claims.
- Comparability must fail closed when protocol, identity, or provenance is
  ambiguous.
- Historical benchmark artifacts under `benchmarks/*.json` are inputs; hygiene
  corrections belong in the generated report/data layer unless a source artifact
  is demonstrably invalid.

## Session Contract

- No `implemented+tested` claim without passing the canonical test command.
- Any blocked gate must report the exact command, exit code, and impacted path.
- Keep `implemented+tested` and `designed/unverified` separate in docs and
  closeout reports.
