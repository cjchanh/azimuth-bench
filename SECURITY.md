# Security

## Reporting

If you believe you have found a **security-relevant** issue (e.g. secret exposure in the repo, unsafe defaults that leak local paths or credentials in generated reports, or a dependency vulnerability with a concrete exploit path), please report it **privately** if your platform supports it; otherwise open a **non-public** maintainer channel if one is listed for this repository, or file a standard issue with **no exploit details** until maintainers respond.

For **general bugs** that are not security-sensitive, use the normal issue tracker.

## What this project tries to guarantee

- Public **report** and **export** JSON are built to avoid embedding operator home directories or raw endpoint secrets where the schema allows sanitization (see `azimuth_bench/schema/bundle.py` and tests).
- Throughput artifacts may still contain **machine receipts** and paths from the environment that produced them; treat raw JSON under `benchmarks/` as **operator data**, not as a sanitized public bundle until processed by report build.

## Out of scope for “security policy” theater

- This is an **OSS dev tool**, not a hosted service SLA.
- There is **no** bug bounty or formal disclosure program unless explicitly added later.

## Dependencies

Review `pyproject.toml` and your own supply-chain policy. Pin versions in production environments as you would for any Python ML tooling (networked adapters, local MLX/Ollama endpoints).
