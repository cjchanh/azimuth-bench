# Changelog

All notable changes to this repository are documented here. The **truth boundary** for behavior remains [docs/azimuth_bench/SOURCE_OF_TRUTH.md](docs/azimuth_bench/SOURCE_OF_TRUTH.md) plus tests.

## [0.1.0] — 2026-04-01

First **public OSS release candidate** for Azimuth Bench: packaging hygiene, contributor/security docs, and a frozen **release pack** under `release/public/v0_1_0/` (notes, announcement draft, asset inventory). No change to throughput protocol semantics or benchmark prompts.

### Added

- `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md` at repository root.
- `release/public/v0_1_0/` — `README.md`, `RELEASE_NOTES.md`, `ANNOUNCEMENT.md`, `ASSET_INVENTORY.md`.
- Test guard for release-pack file presence (`tests/test_release_public_v0_1_0.py`).

### Unchanged (by design)

- Canonical package `azimuth_bench`; distribution name `benchmark-v2` (see `pyproject.toml`).
- Compatibility-only `signalbench` / `benchmarking` boundaries per SSOT.
- No new adapters; no benchmark reruns as part of this tag.
