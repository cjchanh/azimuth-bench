# `repo-agent-mini`

One **sample** source-anchored repo task. Real runs should add more rows and point `source_anchors` at **public** files
in a clone of this repository (e.g. `README.md`, `pyproject.toml`).

```bash
# After wiring a runner, point it at sample_fixtures.jsonl
```

Schema: `fixture_id`, `lane` = `repo_agent`, `source_anchors[]`, `prompt`, `grading` (rubric + `max_score`).
