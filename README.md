# benchmark-v2

**Azimuth** — a portable inference benchmark platform for MLX, Ollama, and other OpenAI-compatible backends. This repository contains the **Azimuth Bench** reference implementation (`azimuth_bench`), **Azimuth Report** (static HTML/MD from real artifacts), and compatibility modules for the original benchmark-v2 workflows.

Technical package: **`azimuth_bench`**. CLI: **`azbench`**. The legacy name **`signalbench`** remains as a temporary import and console-script alias; new code should use `azimuth_bench` / `azbench`. See [docs/azimuth_bench/SOURCE_OF_TRUTH.md](docs/azimuth_bench/SOURCE_OF_TRUTH.md).

Standalone local MLX benchmark harness, with roots in [Agent Civilization](https://github.com/cjchanh/agent-civilization).

## Scope

- Token and latency benchmarking for MLX, Ollama, and OpenAI-compatible adapters
- Roster management and model configuration
- Summary artifact generation (CSV, JSON, Markdown)
- Social card generation (matplotlib)
- **Azimuth Report** generation: `azbench report build <run_dir>`
- Static host surfaces for runs, machines, providers, and protocols
- Optional external Agent Civilization gate via `AGENT_CIV_ROOT`

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## CLI (canonical)

```bash
azbench --help
azbench report build benchmarks --repo-root "$(pwd)"
azbench bench throughput --help
python -m azimuth_bench --help
```

Compatibility:

```bash
signalbench --help   # same entrypoint as azbench
python -m signalbench --help
```

## Verify

```bash
python3 -m pytest -q
```

## Lint

```bash
ruff check .
ruff format --check .
```

All three commands require the venv to be active.

## Optional external gate

`benchmarking.gate` can run a 5-tick Agent Civilization simulation check if:

- `AGENT_CIV_ROOT` environment variable points at a compatible checkout, or
- a checkout exists at the default path

This is optional and not required for the core benchmark harness.

## License

MIT — see [LICENSE](LICENSE).
