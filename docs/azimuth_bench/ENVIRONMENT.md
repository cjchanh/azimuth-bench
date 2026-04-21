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

## `llama_cpp` adapter smoke check (operators)

Use this to confirm the **OpenAI-compatible route and thinking control surface** before you point Azimuth at the same base URL. It is **not** a benchmark: it does not produce throughput, semantic, or promotion artifacts, and it does not expand eval scope.

1. **Start from an already-running** llama-server (or equivalent) on a known host and port. **Azimuth does not start, supervise, or own** that process; lifecycle is always **bring-your-own-server**.
2. **Verify** `GET {base_url}/v1/models` returns a normal models payload (e.g. with `curl` or any HTTP client; exact flags are your environment’s choice).
3. **Run one** `POST {base_url}/v1/chat/completions` request with a **thinking-off** control, e.g. `chat_template_kwargs` including `enable_thinking: false` (or the field your build uses for the same effect). This checks the same class of control the `llama_cpp` adapter may send under non-default thinking modes.
4. **Confirm** the server either **honors** the control in the response shape you expect or **fails visibly** (e.g. clear HTTP 4xx) so you are not assuming a silent no-op.
5. **Scope:** this is a **route / control-surface** smoke only. **Full** throughput runs, semantic summaries, and promotion decisions still require the corresponding **Azimuth** commands and **artifact outputs** (JSON under your run tree as produced by the suite/CLI), not this checklist alone.

**Command shape (placeholder, not a launch recipe):** `curl -sS "http://<host>:<port>/v1/models"` and a second `curl` (or script) `POST`ing JSON to `.../v1/chat/completions` with your model id, messages, and `chat_template_kwargs` as required by your server build. Adjust host, port, auth, and body to match your deployment; Azimuth does not prescribe the server binary or its flags.

Commit SHA in `run.json` requires a `.git` directory discoverable from the run directory or an explicit `--repo-root` pointing at the Git work tree.
