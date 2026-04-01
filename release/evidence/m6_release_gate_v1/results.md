# Results — m6_release_gate_v1

Recorded on independent re-verification (same session as bundle creation).

| Step | Outcome |
| --- | --- |
| `ruff check .` | All checks passed |
| `ruff format --check .` | 92 files already formatted |
| `python3 -m pytest -q` | 56 passed in ~3s |
| `azbench report build benchmarks --repo-root <repo>` | Exit 0; `Wrote report: …/benchmarks/report` |
| `azbench export markdown … --output /tmp/azimuth_export.md` | Exit 0; wrote `/private/tmp/azimuth_export.md` |
| `azbench export svg benchmarks` | Exit 0; wrote `share_leaderboard.svg`, `share_compare.svg` |
| `python3 -m azimuth_bench --help` | Exit 0; shows `report`, `export`, `bench` |
| `python3 -m signalbench --help` | Exit 0; same surface as `azimuth_bench` |
| `python3 -m build --outdir /tmp/azimuth_release_gate_dist --no-isolation` | Exit 0; `Successfully built benchmark_v2-0.1.0.tar.gz and benchmark_v2-0.1.0-py3-none-any.whl` |
| `validate_governance.py --strict` | Exit 0; PASS lines including repo-local `AGENTS.md` |
| `bootstrap_codex_governance.sh --check-only` | Exit 0; `BOOTSTRAP PASS` |
| `run_full_verification.sh` | Exit 0; `VERIFICATION PASS` |
| `post_session.py <repo>` | Exit 0; `POST_SESSION PASS: benchmark-v2 clean, grade=A` |

**Notes**

- `python -m build` may print a `NO_COLOR`/`FORCE_COLOR` warning from the environment; output did **not** contain `SetuptoolsDeprecationWarning` (also asserted in `tests/test_m6_eval.py`).
- Git HEAD (bundle + results pin): `7bb8fb9` (product baseline audited: `1130597`).
