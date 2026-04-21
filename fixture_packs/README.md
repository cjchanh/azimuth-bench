# Public fixture packs (local agent evals)

These are **small, non-proprietary** sample fixture lines for operator self-serve testing. They are **not** a replacement
for private, repository-anchored eval sets under `evals/`.

| Pack | Directory | Intent |
| --- | --- | --- |
| `repo-agent-mini` | [repo-agent-mini](repo-agent-mini) | Readme/contract questions with in-repo anchors. |
| `tool-calling-mini` | [tool-calling-mini](tool-calling-mini) | Command / tool-synthesis style tasks. |
| `json-reliability` | [json-reliability](json-reliability) | Strict JSON output shape checks. |
| `long-context-local` | [long-context-local](long-context-local) | Long-prompt local context (synthetic padding). |

Run with your own `run_bakeoff.py` or any OpenAI-compatible loop. **Do not** copy private `evals/qwen36_bakeoff/`
fixtures into this tree.
