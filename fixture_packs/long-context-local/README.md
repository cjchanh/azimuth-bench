# `long-context-local`

Placeholder for **long-context** harness tests: duplicate or pad prompts locally, measure behavior at configured
`max_tokens` / context limits. The sample uses **short** text; replace `prompt` with generated padding for real runs.

Telemetry belongs in throughput artifacts (`telemetry` block), not in fixture files.
