# Claims ledger — m6_release_gate_v1

| Claim | Evidence anchor |
| --- | --- |
| Canonical package is `azimuth_bench` | `pyproject.toml` package discovery; `import azimuth_bench` in tests |
| Canonical CLI is `azbench` | `[project.scripts]` → `azimuth_bench.cli.entrypoint:main`; `azbench --help` exit 0 |
| `python -m azimuth_bench` matches CLI | Same entrypoint; help output in `results.md` |
| `signalbench` is compatibility shim | `signalbench/__init__.py` re-exports; `tests/test_ssot.py::test_signalbench_shim_main_matches_azimuth_bench`; same `--help` |
| `benchmarking/*` delegates | `tests/test_ssot.py`, token/main delegation tests; SSOT table |
| Report build produces static JSON + HTML | `azbench report build` exit 0; `benchmarks/report/data/*.json` |
| No `/Users/` in generated public report JSON | `rg '/Users/' benchmarks/report/data/*.json` → no matches (this audit) |
| Markdown export works | `azbench export markdown` exit 0; reads `report/data/summary.json` |
| SVG export deterministic | `tests/test_azimuth_bench.py`; export exit 0 |
| `compare.json` is `azimuth_compare_v1` | `tests/test_azimuth_bench.py`; SSOT |
| Merge is validated Azimuth trees only | `tests/test_merge.py`; SSOT; merge.json absent for single-run sample build |
| Merge fail-closed on duplicate identity | `tests/test_merge.py::test_merge_blocks_duplicate_row_identity` |
| M6 evaluator docs exist | `docs/azimuth_bench/DESIGN_PARTNER_EVAL.md`, `release/evaluator/README.md`; `tests/test_m6_eval.py` |
| Packaging builds without setuptools deprecation in test | `tests/test_m6_eval.py::test_python_m_build_produces_wheel_and_sdist`; live build in `results.md` |
| PyPI **not** claimed as automated | SSOT “Not implemented: PyPI publication…” |
| llama.cpp / vLLM **not** shipped | SSOT; `azimuth_bench/adapters/planned.py` |
| Tests pass | `python3 -m pytest -q` → 56 passed |
| Governance clean | `validate_governance.py --strict`, bootstrap, full verification, post_session — all exit 0 in `results.md` |
