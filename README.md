# benchmark-v2

Standalone local MLX benchmark harness extracted from Agent Civilization.

## Scope

- Token and latency benchmarking
- Roster management
- Summary artifact generation
- Social card generation
- Optional external Agent Civilization gate via `AGENT_CIV_ROOT`

## Install

```bash
cd /Users/cj/Workspace/active/benchmark-v2
pip install -e ".[dev]"
```

## Verify

```bash
cd /Users/cj/Workspace/active/benchmark-v2
python3 -m pytest -q
```

## Optional external gate

`benchmarking.gate` can run a 5-tick Agent Civilization check if:

- a compatible checkout exists at `/Users/cj/Workspace/active/agent-civilization`, or
- `AGENT_CIV_ROOT` points at one.
