# Cursor Milestone Prompt Pack

This file is the **operator pack** for Cursor / Composer execution. It is **not SSOT**. For current shipped truth, use [SOURCE_OF_TRUTH.md](SOURCE_OF_TRUTH.md). If this file conflicts with SSOT, **SSOT wins**.

## Current exact milestone

**Current exact milestone:** **M6 complete — Design-Partner Release Surface**  
**Overall build-path progress:** **90%**

Why this is the honest mark in the current tree:

- `implemented+tested`: canonical package = `azimuth_bench`, canonical CLI = `azbench`.
- `implemented+tested`: real throughput adapters exist for **MLX**, **OpenAI-compatible HTTP**, and **Ollama**.
- `implemented+tested`: static report build, provider/protocol surfaces, comparability-enriched summary rows, Markdown export, **`azimuth_compare_v1` compare projection** (`report/data/compare.json`), and deterministic **`report/exports/share_*.svg`** + `azbench export svg`.
- `implemented+tested`: **validated multi-run merge** via `azbench report build <run_dir> --include-run-dir …`, `report/data/merge.json`, merge-aware `leaderboard.json`, explicit comparability classes + blockers (`tests/test_merge.py`).
- `implemented+tested`: **design-partner path**: [DESIGN_PARTNER_EVAL.md](DESIGN_PARTNER_EVAL.md), [release/evaluator/README.md](../../release/evaluator/README.md), README quickstart clarifications, `pyproject` OSS metadata; `tests/test_m6_eval.py`.
- `implemented+tested`: public-proof docs exist: [METHODOLOGY.md](METHODOLOGY.md), [READING_REPORTS.md](READING_REPORTS.md), [PUBLIC_PROOF_PACK.md](PUBLIC_PROOF_PACK.md).
- `implemented+tested`: baseline verification in this checkout is **57 passing tests** per [SOURCE_OF_TRUTH.md](SOURCE_OF_TRUTH.md) (refresh count when behavior changes).

What is **not** done yet, and why this is not further along:

- `designed/unverified`: `llama.cpp` / `vLLM` production adapters.
- `designed/unverified`: hosted product surface beyond static report artifacts.
- `designed/unverified`: company-value layer driven by real usage, design partners, and public benchmark adoption.

## Milestone ladder

| Milestone | Status | Build-path % | Meaning |
| --- | --- | ---: | --- |
| **M1 — Truthful benchmark foundation** | complete | 25% | Full roster, provenance, canonical summary, integrity-preserving truth path. |
| **M2 — Azimuth platform boundary** | complete | 45% | `azimuth_bench` canonical, `signalbench` shim, `benchmarking/*` compatibility-only, adapters/report/schema/CLI split. |
| **M3 — Public-Proof OSS Foundation** | complete | 60% | README + methodology + report-reading + proof pack, sanitized public outputs, clean OSS-facing surface. |
| **M4 — Shareable Compare Surface** | **complete** | **70%** | `azimuth_compare_v1` compare.json + blocked comparisons + deterministic share SVGs + `azbench export svg`. |
| **M5 — Portable Run Bundle / Merge Layer** | **complete** | **80%** | Validated Azimuth run dirs only; `azbench report build … --include-run-dir …`; `merge.json` + comparability classes + collision blocking. |
| **M6 — Design-Partner Release Surface** | **complete** | **90%** | [DESIGN_PARTNER_EVAL.md](DESIGN_PARTNER_EVAL.md), [release/evaluator/README.md](../../release/evaluator/README.md), README + `pyproject` metadata; offline proof path; optional `python -m build`. |

The last **10%** is **not** another repo refactor. It is design partners, repeated usage, trusted public claims, and adoption.

## Use order

1. Run **Prompt 1** now.
2. If Prompt 1 lands cleanly, run **Prompt 2**.
3. If Prompt 2 lands cleanly, run **Prompt 3**.
4. Use **Prompt 4** as the independent audit / release gate after the build prompts.

## Prompt 1 — M4 Shareable Compare Surface

Copy only the plain text inside the fenced block.

```text
SESSION: repo | strike | azimuth-share-compare-surface | 2026-04-01

REPO
- Target repo: /Users/cj/Workspace/active/benchmark-v2
- Read docs/azimuth_bench/SOURCE_OF_TRUTH.md first.
- Treat SOURCE_OF_TRUTH.md + code + tests as the truth boundary.
- Do not reopen naming or canonical-boundary debates.

CURRENT TRUE STATE TO RESPECT
- Canonical package: azimuth_bench
- Canonical CLI: azbench
- signalbench/* is compatibility-only shim
- benchmarking/* is compatibility-only delegation
- Implemented adapters today: MLX, OpenAI-compatible HTTP, Ollama
- Implemented today: throughput suite, report build, provider/protocol surfaces, markdown export
- Public-proof docs already exist and are committed
- Baseline verification in this checkout: python3 -m pytest -q -> see SOURCE_OF_TRUTH.md (57 passed as of independent quality gate)

PRIMARY OBJECTIVE
Upgrade Azimuth from a truthful proof surface to a shareable comparison surface without widening into another deep architecture cycle.

REQUIRED OUTCOME
1. Build deterministic compare artifacts from canonical report data:
   - compare JSON projections for valid side-by-side comparisons
   - stable comparison keys
   - explicit comparability blockers when rows should not be compared
2. Add richer export assets generated from canonical report data:
   - at minimum one deterministic SVG share card for leaderboard snapshot
   - at minimum one deterministic SVG comparison card
3. Strengthen static report output only where needed to support those surfaces:
   - no SPA
   - no CDN
   - no hidden runtime dependency
4. Keep exports and compare surfaces honest:
   - no claims beyond current artifacts
   - no universal ranking language
   - no path leakage in public outputs
5. Update docs/tests for the new surfaces.

CONSTRAINTS
- Do not rerun benchmarks.
- Do not add new adapters in this pass.
- Do not widen into hosted app work.
- Do not replace canonical data flow with one-off export logic.
- Keep implemented+tested separate from designed/unverified everywhere.

DELIVERABLES
1. compare/data contract additions
2. SVG export pipeline additions
3. docs updates for how to use/share/interpret them
4. exact tests and command results
5. explicit remaining debt

VERIFICATION REQUIRED
- source .venv/bin/activate && ruff check .
- source .venv/bin/activate && ruff format --check .
- source .venv/bin/activate && python3 -m pytest -q
- source .venv/bin/activate && azbench report build benchmarks --repo-root /Users/cj/Workspace/active/benchmark-v2
- source .venv/bin/activate && azbench export markdown benchmarks --output /tmp/azimuth_export.md
- source .venv/bin/activate && azbench --help
- source .venv/bin/activate && azbench export --help

REPORT FORMAT
1. Canonical vs compatibility summary
2. Files changed grouped by area
3. Compare/export design summary
4. Proof ledger: claim -> file/test
5. Exact verification commands and outcomes
6. Remaining debt

SUCCESS CRITERIA
- repo still reads as Azimuth, not a renamed benchmark script
- compare surfaces are generated from canonical data only
- exported assets are static, deterministic, and honest
- no benchmark semantics drift
```

## Prompt 2 — M5 Portable Run Bundle / Merge Layer

Copy only the plain text inside the fenced block.

```text
SESSION: repo | strike | azimuth-run-bundle-merge-layer | 2026-04-01

REPO
- Target repo: /Users/cj/Workspace/active/benchmark-v2
- Read docs/azimuth_bench/SOURCE_OF_TRUTH.md first.
- Assume M4 share/compare work is already landed and committed before starting.

PRIMARY OBJECTIVE
Make Azimuth capable of importing and merging external run bundles into one truthful comparison surface, without pretending incomparable runs are directly comparable.

CURRENT TRUE STATE TO RESPECT
- azimuth_bench is canonical
- throughput suite is the only shipped suite family unless SSOT says otherwise
- report/site/export already operate on canonical bundle data
- comparability is already a first-class invariant

REQUIRED OUTCOME
1. Define and implement a portable run-bundle intake layer:
   - stable bundle discovery
   - schema/version checks
   - duplicate run/artifact blocking
   - clear failure modes for malformed or incomplete bundles
2. Support merged report inputs from multiple run directories or imported bundles.
3. Make merged comparison rules explicit:
   - fully comparable
   - limited / scoped comparable
   - not comparable
4. Emit merge-aware site/report projections:
   - merged leaderboard data
   - provider/machine/protocol grouping across bundles
   - blockers surfaced in JSON and public views
5. Update docs so outsiders know what imported bundles do and do not prove.

CONSTRAINTS
- Do not add fake suite generalization.
- Do not silently coerce incompatible bundles into one ranking.
- Do not rerun benchmarks.
- Do not hide missing provenance.

DELIVERABLES
1. portable run-bundle intake module
2. merge-aware report/data contract
3. tests for duplicate blocking, malformed bundle rejection, and comparability classes
4. docs updates
5. exact verification outcomes

VERIFICATION REQUIRED
- source .venv/bin/activate && ruff check .
- source .venv/bin/activate && ruff format --check .
- source .venv/bin/activate && python3 -m pytest -q
- source .venv/bin/activate && azbench report build benchmarks --repo-root /Users/cj/Workspace/active/benchmark-v2
- source .venv/bin/activate && azbench export markdown benchmarks --output /tmp/azimuth_export.md
- source .venv/bin/activate && azbench --help

REPORT FORMAT
1. Canonical vs compatibility summary
2. Files changed grouped by area
3. Bundle-merge design summary
4. Proof ledger: claim -> file/test
5. Exact verification commands and outcomes
6. Remaining debt

SUCCESS CRITERIA
- Azimuth can ingest external bundles without lying about comparability
- merged outputs stay static-hostable and artifact-backed
- invalid bundles fail closed with explicit blockers
```

## Prompt 3 — M6 Design-Partner Release Surface

Copy only the plain text inside the fenced block.

```text
SESSION: repo | strike | azimuth-design-partner-release-surface | 2026-04-01

REPO
- Target repo: /Users/cj/Workspace/active/benchmark-v2
- Read docs/azimuth_bench/SOURCE_OF_TRUTH.md first.
- Assume M5 bundle/merge work is already landed and committed before starting.

PRIMARY OBJECTIVE
Make Azimuth design-partner-ready: installable, explainable, releasable, and easy to evaluate by an external infra engineer without private handholding.

REQUIRED OUTCOME
1. Tighten release/install path:
   - package/install docs verified outside the happy path
   - CLI entrypoints documented cleanly
   - examples that do not rely on personal machine assumptions
2. Add one-command release-style proof packaging:
   - release-facing bundle or example artifact pack
   - clear README / docs path for first-time evaluators
3. Harden public docs around:
   - what Azimuth is
   - what is implemented+tested
   - what is designed/unverified
   - how to run one local proof path
4. Improve OSS legibility:
   - contributor-facing boundaries
   - compatibility notes
   - truthful roadmap framing

CONSTRAINTS
- Do not invent traction or customer language.
- Do not widen into unrelated frontend polish.
- Do not claim hosted-product maturity beyond static artifacts.
- Keep all public claims pinned to code/tests/artifacts.

DELIVERABLES
1. install/release-path improvements
2. design-partner-facing docs and example flow
3. proof package or release bundle path
4. exact verification outcomes
5. explicit remaining debt before outreach

VERIFICATION REQUIRED
- source .venv/bin/activate && ruff check .
- source .venv/bin/activate && ruff format --check .
- source .venv/bin/activate && python3 -m pytest -q
- source .venv/bin/activate && azbench report build benchmarks --repo-root /Users/cj/Workspace/active/benchmark-v2
- source .venv/bin/activate && azbench export markdown benchmarks --output /tmp/azimuth_export.md
- source .venv/bin/activate && python3 -m azimuth_bench --help
- source .venv/bin/activate && python3 -m signalbench --help

REPORT FORMAT
1. What changed in the release/install surface
2. Files changed grouped by area
3. Proof ledger: claim -> file/test
4. Exact verification commands and outcomes
5. Remaining debt before real outreach

SUCCESS CRITERIA
- an external engineer can understand, install, and inspect Azimuth faster
- repo stays honest about implemented vs planned
- the release surface is materially stronger without architecture drift
```

## Prompt 4 — Independent audit / release gate

Copy only the plain text inside the fenced block.

```text
SESSION: repo | audit | azimuth-independent-release-audit | 2026-04-01

REPO
- Target repo: /Users/cj/Workspace/active/benchmark-v2
- This is an independent verification pass after the latest Azimuth milestone lands.
- Read docs/azimuth_bench/SOURCE_OF_TRUTH.md first.

PRIMARY OBJECTIVE
Audit the latest Azimuth state for overclaims, SSOT drift, public-output hygiene, comparability honesty, and OSS release readiness.

REQUIRED OUTCOME
1. Independently verify:
   - README / docs claims match code + tests
   - public report/data outputs do not leak personal paths or sensitive fields
   - compare / export / bundle claims are actually emitted by code
   - compatibility layers do not redefine SSOT
2. Run the real verification commands.
3. Identify only substantive findings:
   - incorrect claims
   - missing test coverage for a claim
   - unstable or misleading output behavior
   - release blockers
4. If issues exist, fix them or fail closed with the exact blocker.

RESPONSE SHAPE
1. Findings
2. Evidence
3. Concrete Actions
4. Risk
5. Decision

VERIFICATION REQUIRED
- source .venv/bin/activate && ruff check .
- source .venv/bin/activate && ruff format --check .
- source .venv/bin/activate && python3 -m pytest -q
- source .venv/bin/activate && azbench report build benchmarks --repo-root /Users/cj/Workspace/active/benchmark-v2
- source .venv/bin/activate && azbench export markdown benchmarks --output /tmp/azimuth_export.md
- python3 ~/.codex/validators/post_session.py /Users/cj/Workspace/active/benchmark-v2

SUCCESS CRITERIA
- no public claim survives without a code/test/artifact anchor
- no hidden hygiene regressions remain
- repo is either ship-clean or halted with one exact blocker
```
