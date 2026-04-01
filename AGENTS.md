# AGENTS.md — Azimuth Bench

## Scope

Portable inference benchmark platform repository at
`/Users/cj/Workspace/active/benchmark-v2`.

Canonical product surface:
- Python package: `azimuth_bench`
- CLI: `azbench` / `python3 -m azimuth_bench`

Compatibility-only surfaces:
- `signalbench/*`
- `benchmarking/*`

## Canonical Commands

- Test: `python3 -m pytest -q`
- Lint: `ruff check .`
- Format: `ruff format --check .`
- Report build: `azbench report build benchmarks --repo-root /Users/cj/Workspace/active/benchmark-v2`
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

## Governance Gate

```bash
cd /Users/cj/Workspace/active/benchmark-v2
python3 ~/.codex/scripts/validate_governance.py --root . --strict
bash ~/.codex/scripts/bootstrap_codex_governance.sh --repo-root . --check-only
python3 ~/.codex/validators/pre_session.py /Users/cj/Workspace/active/benchmark-v2
python3 ~/.codex/validators/post_session.py /Users/cj/Workspace/active/benchmark-v2
```

## Session Contract

- No `implemented+tested` claim without passing the canonical test command.
- Any blocked gate must report the exact command, exit code, and impacted path.
- Keep `implemented+tested` and `designed/unverified` separate in docs and
  closeout reports.
