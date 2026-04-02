# Results — m6_release_gate_v1

Recorded on independent re-verification (same session as bundle creation).

| Step | Outcome |
| --- | --- |
| `ruff check .` | All checks passed |
| `ruff format --check .` | 93 files already formatted (final audit) |
| `python3 -m pytest -q` | 60 passed (matches current SSOT; refresh after changes) |
| `azbench report build benchmarks --repo-root <repo>` | Exit 0; `Wrote report: …/benchmarks/report` |
| `azbench export markdown … --output /tmp/azimuth_export.md` | Exit 0; wrote Markdown summary |
| `azbench export svg benchmarks` | Exit 0; wrote `share_leaderboard.svg`, `share_compare.svg` |
| `python3 -m azimuth_bench --help` | Exit 0; shows `report`, `export`, `bench` |
| `python3 -m signalbench --help` | Exit 0; same surface as `azimuth_bench` |
| `python3 -m build --outdir /tmp/azimuth_release_gate_dist --no-isolation` | Exit 0; `Successfully built benchmark_v2-0.1.0.tar.gz and benchmark_v2-0.1.0-py3-none-any.whl` |

**Notes**

- `python -m build` may print a `NO_COLOR`/`FORCE_COLOR` warning from the environment; output did **not** contain `SetuptoolsDeprecationWarning` (also asserted in `tests/test_m6_eval.py`).
- This evidence bundle is clone-portable by design. Re-run `commands.txt` from your repository root after any substantive change rather than relying on a stale recorded checkout path or commit pin.
