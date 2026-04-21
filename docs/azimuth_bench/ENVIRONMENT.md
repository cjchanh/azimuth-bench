# Environment variables (Azimuth Bench)

All variables are **optional** and **non-secret**. They exist so operators can name paths and metadata without editing code.

**Preferred names** (current):

| Variable | Purpose |
| --- | --- |
| `AZIMUTH_BENCH_PROVIDER_ID` | Public label written to `report/data/provider.json` when building reports (e.g. `mlx_lm`). Not verified against artifacts. |
| `AZIMUTH_BENCH_MLX_SERVER_LOG` | Path for MLX LM server stdout/stderr when using the roster runner (default: under system temp). |
| `AZIMUTH_BENCH_FLEET_GUARD_PATH` | Path for fleet guard JSON output when that tool is used (default: under system temp). |
| `AZIMUTH_BENCH_OPENAI_BASE_URL` | Base URL for `--adapter openai_compatible` **or** `--adapter llama_cpp` when `--base-url` is omitted (no default endpoint). Raw endpoint URLs are operator config and are not serialized into public report JSON. |
| `AZIMUTH_BENCH_OLLAMA_BASE_URL` | Ollama base URL when `--adapter ollama` and `--base-url` are omitted. Raw endpoint URLs are not serialized into public report JSON. |
| `OLLAMA_HOST` | Host or URL for Ollama (e.g. `127.0.0.1:11434`); used when `AZIMUTH_BENCH_OLLAMA_BASE_URL` is unset. |
| `AZIMUTH_BENCH_API_KEY` | Optional bearer token for OpenAI-compatible HTTP adapters (**secret** — never logged or embedded in JSON artifacts). |

**Legacy aliases** (still honored):

| Variable | Same as |
| --- | --- |
| `SIGNALBENCH_PROVIDER_ID` | `AZIMUTH_BENCH_PROVIDER_ID` |
| `SIGNALBENCH_MLX_SERVER_LOG` | `AZIMUTH_BENCH_MLX_SERVER_LOG` |
| `SIGNALBENCH_FLEET_GUARD_PATH` | `AZIMUTH_BENCH_FLEET_GUARD_PATH` |
| `OPENAI_BASE_URL` | `AZIMUTH_BENCH_OPENAI_BASE_URL` |
| `OPENAI_API_KEY` | `AZIMUTH_BENCH_API_KEY` |

| Variable | Purpose |
| --- | --- |
| `TMPDIR`, `TEMP`, `TMP` | Standard temp directory selection (POSIX / Python `tempfile`). |

Commit SHA in `run.json` requires a `.git` directory discoverable from the run directory or an explicit `--repo-root` pointing at the Git work tree.
