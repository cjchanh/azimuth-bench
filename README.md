# benchmark-v2 · **Azimuth Bench**

**Azimuth** is a portable inference **benchmark platform**: run throughput suites against MLX / OpenAI-compatible / Ollama backends, emit honest artifacts, and build static **Azimuth Report** pages plus JSON bundles for comparison.

**Canonical code:** `azimuth_bench` · **CLI:** `azbench` · **Truth boundary:** [docs/azimuth_bench/SOURCE_OF_TRUTH.md](docs/azimuth_bench/SOURCE_OF_TRUTH.md)

**First-time evaluator (install → proof path → merge overview):** [docs/azimuth_bench/DESIGN_PARTNER_EVAL.md](docs/azimuth_bench/DESIGN_PARTNER_EVAL.md) · **Repeatable commands + packaging check:** [release/evaluator/README.md](release/evaluator/README.md)

**Public OSS release candidate (v0.1.0):** [CHANGELOG.md](CHANGELOG.md) · [CONTRIBUTING.md](CONTRIBUTING.md) · [SECURITY.md](SECURITY.md) · **Release pack:** [release/public/v0_1_0/README.md](release/public/v0_1_0/README.md)

**Public sample report (static, GitHub Pages — from committed `benchmarks/` artifacts, no live backend):**  
https://cjchanh.github.io/benchmark-v2/report/index.html

## Implemented today (tested)

- Throughput suite, MLX + OpenAI-compatible + Ollama adapters, integrity gate (fail-closed on ambiguity).
- `azbench report build` → static HTML + `report/data/*.json` (paths sanitized for public sharing).
- **Multi-run merge:** `azbench report build <run_dir> --include-run-dir <other_run_dir> ...` merges additional validated Azimuth benchmark trees into the primary `run_dir` report (see `report/data/merge.json`, `leaderboard.json` field `merge`).
- Provider / protocol host surfaces + enriched summary rows (`comparable`, protocol, provider fields).
- `azbench export markdown` from built report data.

**Compatibility only (do not fork SSOT):** `signalbench/*` (import/`python -m` shim), `benchmarking/*` (delegation to `azimuth_bench`). New code should import `azimuth_bench`.

## Not implemented (see SOURCE_OF_TRUTH)

- llama.cpp / vLLM adapters (stubs only).
- Hosted SPA; full social/image export pipeline beyond Markdown.

## 5-minute quickstart

```bash
git clone <this-repo> && cd benchmark-v2
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

The **distribution name** in `pyproject.toml` is `benchmark-v2`; **import** `azimuth_bench` in Python. Console scripts: `azbench` (canonical), `signalbench` (alias).

**Read the truth boundary:**

- [docs/azimuth_bench/SOURCE_OF_TRUTH.md](docs/azimuth_bench/SOURCE_OF_TRUTH.md)
- [docs/azimuth_bench/DESIGN_PARTNER_EVAL.md](docs/azimuth_bench/DESIGN_PARTNER_EVAL.md) — external evaluator path
- [docs/azimuth_bench/METHODOLOGY.md](docs/azimuth_bench/METHODOLOGY.md)
- [docs/azimuth_bench/READING_REPORTS.md](docs/azimuth_bench/READING_REPORTS.md)

**Build the sample report** (uses committed `benchmarks/` artifacts; does not rerun benchmarks):

```bash
azbench report build benchmarks --repo-root "$(pwd)"
```

**Merge two portable run trees** (each must look like a normal `benchmarks/` directory with token summary + artifacts; no directory scanning):

```bash
azbench report build /path/to/primary_bench --repo-root "$(pwd)" --include-run-dir /path/to/other_bench
```

Output: `benchmarks/report/` (see `.gitignore` if you do not commit generated trees).

**Export Markdown** from that report:

```bash
azbench export markdown benchmarks --output /tmp/azimuth_summary.md
```

**Regenerate deterministic share SVGs** (leaderboard + compare cards under `report/exports/`):

```bash
azbench export svg benchmarks --output-dir benchmarks/report/exports
```

**Run throughput** (requires a live backend — see `--adapter` and [docs/azimuth_bench/ENVIRONMENT.md](docs/azimuth_bench/ENVIRONMENT.md)):

```bash
azbench bench throughput --help
```

**Legacy entrypoints** (same CLI): `signalbench`, `python -m signalbench`, `python -m azimuth_bench`, `python -m benchmarking.token`.

## Proof & outreach

- **Snapshot facts for the 18-row reference summary:** [docs/azimuth_bench/PUBLIC_PROOF_PACK.md](docs/azimuth_bench/PUBLIC_PROOF_PACK.md)

## Verify

```bash
ruff check . && ruff format --check .
python3 -m pytest -q
```

**Optional — confirm wheel/sdist build locally** (does not publish to PyPI):

```bash
pip install build
python -m build --outdir /tmp/azimuth_dist
```

See [release/evaluator/README.md](release/evaluator/README.md).

## Optional: Agent Civilization gate

`benchmarking.gate` can run an external simulation if `AGENT_CIV_ROOT` is set — optional, not required for core benchmarking.

## License

MIT — see [LICENSE](LICENSE).
