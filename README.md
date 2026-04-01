# benchmark-v2

Standalone local MLX benchmark harness extracted from [Agent Civilization](https://github.com/cjchanh/agent-civilization).

## Scope

- Token and latency benchmarking for MLX models
- Roster management and model configuration
- Summary artifact generation (CSV, JSON, Markdown)
- Social card generation (matplotlib)
- Optional external Agent Civilization gate via `AGENT_CIV_ROOT`

## Install

```bash
pip install -e ".[dev]"
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

## Optional external gate

`benchmarking.gate` can run a 5-tick Agent Civilization simulation check if:

- `AGENT_CIV_ROOT` environment variable points at a compatible checkout, or
- a checkout exists at the default path

This is optional and not required for the core benchmark harness.

## License

MIT — see [LICENSE](LICENSE).
