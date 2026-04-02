# Composer 2 — Upgrade session prompt (v2)

**Use this** when opening a **new Composer window** to continue Azimuth platform work. Copy **only** the plain text inside the fenced **text** block below (omit the triple-backtick lines).

**Relationship to SSOT:** This prompt is the **execution plan**. **`SOURCE_OF_TRUTH.md`** plus **tests** plus **code** are the **truth boundary** for what is implemented *right now*. Read `docs/azimuth_bench/SOURCE_OF_TRUTH.md` first; do not treat sections A–E as already shipped unless that file and tests say so.

---

```text
SESSION: repo | composer-upgrade | azimuth-platform | v2 | 2026-04-01

================================================================================
TRUTH BOUNDARY (READ FIRST — GOVERNS ALL “SHIPPED / DONE” CLAIMS)
================================================================================
- EXECUTION PLAN: everything below (A–E, deliverables, verification expectations).
- IMPLEMENTATION TRUTH: docs/azimuth_bench/SOURCE_OF_TRUTH.md + code + tests.
- At session start: READ SOURCE_OF_TRUTH.md and align narrative with its tables,
  especially “Implemented vs not implemented.”
- If this prompt and SOURCE_OF_TRUTH disagree on current behavior, SOURCE_OF_TRUTH
  wins until you change the code and update SOURCE_OF_TRUTH.md.
- Do not describe a capability as production-ready in docs, CLI help, or emitted
  JSON until SOURCE_OF_TRUTH.md reflects it and the change is committed with tests.
- Re-run pytest before final handoff; update the “last verified” pass count if it
  changed.

================================================================================
REPO
================================================================================
- Target repo: $(pwd)
- Treat the current working tree as in-flight; prefer explicit repo-root flags over
  hardcoded paths in new code.
- Do not restart the naming debate.
- Do not revert the Azimuth rename.

================================================================================
IDENTITY FREEZE
================================================================================
- Public product brand: Azimuth
- Canonical technical package: azimuth_bench
- Canonical CLI: azbench
- Temporary compatibility package: signalbench
- Legacy compatibility layer: benchmarking/*

This pass is not about deciding SignalBench vs Azimuth. That is already decided:
- Azimuth = public product identity
- azimuth_bench = canonical namespace
- signalbench = compatibility shim only

Treat this as platform hardening + expansion, not cosmetic churn.

================================================================================
PRIMARY OBJECTIVE
================================================================================
Upgrade Azimuth from a single-backend benchmark harness toward a portable,
open-source-ready benchmark platform with:
1. multi-backend adapters (real contracts; no silent MLX-only assumptions in suites)
2. host companion surfaces (static-hostable results + comparison UX contracts)
3. share outputs (social/export artifacts)
4. standardized protocol / comparability discipline

Build to production-grade OSS standards:
- no fake claims
- no silent fallback on ambiguity
- no secrets in code, docs, tests, or defaults
- fail closed when integrity or comparability is uncertain

================================================================================
AUTHORITY ORDER
================================================================================
1. correctness and integrity
2. canonical ownership / SSOT clarity
3. OSS portability
4. reproducibility / comparability
5. operator UX
6. visual polish

================================================================================
NON-NEGOTIABLE INVARIANTS
================================================================================
- Fail Closed: ambiguous artifact mapping, backend identity ambiguity, protocol
  mismatch, or unverifiable comparability → explicit errors or blockers.
- Signal Over Noise: public claims traceable to code or artifacts.
- No Local Hardwiring: no fixed /tmp, no machine-specific assumptions in defaults;
  use config and portable discovery.
- Planes Stay Separated: adapters, protocol, summary extraction, report, export,
  site contracts stay distinct modules.
- Canonical Ownership: azimuth_bench/* is product; signalbench/* is shim;
  benchmarking/* is compatibility unless explicitly promoted.
- OSS Safe: no secrets, tokens, personal paths, internal URLs, misleading provider
  attribution.
- Comparability First: incomparable runs must be labeled explicitly.

================================================================================
SSOT SNAPSHOT — “IMPLEMENTED NOW” (from SOURCE_OF_TRUTH; VERIFY IN CODE)
================================================================================
Implemented today (high level):
- Throughput suite + MLX / OpenAI-compatible / Ollama adapters + summary compile + report build + integrity
- bench throughput CLI (canonical path; legacy -m benchmarking.token delegates)
- Static report output + site manifest scaffolding (not a hosted SPA)
- Compare projection (`azimuth_compare_v1`) + deterministic share SVG exports

Explicitly NOT implemented as production CLI yet (see azimuth_bench.adapters.planned):
- llama.cpp and vLLM production adapters / execution paths

Portable merge of validated Azimuth run bundles (M5) and design-partner eval surface (M6) are documented in `SOURCE_OF_TRUTH.md` when shipped.

Do not claim multi-provider production parity until adapters + CLI + SSOT say so.

================================================================================
REPO FACTS (BASELINE — DO NOT REGRESS)
================================================================================
- azimuth_bench/* is the canonical platform boundary
- signalbench/* is thin re-export / shim
- benchmarking/* is compatibility / delegation only — no duplicated protocol SSOT
- throughput is the canonical suite today; MLX adapter path exists
- schema + integrity + report builder + CLI exist
- docs under docs/azimuth_bench/*
- provider metadata operator-supplied where applicable; env-driven temp/log paths

Last verified in this checkout (re-run and refresh numbers):
- source .venv/bin/activate && ruff check .            -> pass
- source .venv/bin/activate && ruff format --check .   -> pass
- source .venv/bin/activate && python3 -m pytest -q    -> see SOURCE_OF_TRUTH.md (60 passed as of v0.1.0 RC pack)

Also exercise:
- source .venv/bin/activate && azbench report build benchmarks --repo-root $(pwd)
- source .venv/bin/activate && azbench bench throughput --help
- source .venv/bin/activate && python3 -m azimuth_bench --help
- source .venv/bin/activate && python3 -m signalbench --help

Do not undo working behavior. Do not reintroduce SignalBench as canonical.
Do not claim the bare module name azimuth.

================================================================================
CANONICAL VS COMPATIBILITY BOUNDARY
================================================================================
Canonical:
- azimuth_bench/adapters/*
- azimuth_bench/core/*
- azimuth_bench/suites/*
- azimuth_bench/schema/*
- azimuth_bench/report/*
- azimuth_bench/site/*
- azimuth_bench/cli/*
- docs/azimuth_bench/SOURCE_OF_TRUTH.md
- docs/azimuth_bench/ARCHITECTURE.md
- docs/azimuth_bench/ENVIRONMENT.md
- docs/azimuth_bench/EVOLUTION.md
- tests/test_azimuth_bench.py
- tests/test_ssot.py

Compatibility-only:
- signalbench/*
- benchmarking/token.py, summary.py, utils.py, runner.py, roster.py, gate.py, socials.py

Do not duplicate SSOT logic into compatibility files.

================================================================================
WHAT TO BUILD (TARGET WORK — NOT ALL SHIPPED YET)
================================================================================

----------------------------------------
A. MULTI-BACKEND ADAPTER SYSTEM
----------------------------------------
Goal: True provider abstraction across MLX LM server, Ollama, OpenAI-compatible
HTTP, llama.cpp server, vLLM-compatible endpoints.

Required outcomes:
1. Document canonical adapter contract in azimuth_bench/adapters.
2. No suite depends on MLX-specific internals.
3. Add at least: OpenAICompatibleAdapter, OllamaAdapter (when implemented, update
   SOURCE_OF_TRUTH and tests — do not claim in prose before then).
4. Keep planned adapters documented if not fully implemented: llama.cpp, vLLM.
5. Capability metadata per adapter: streaming, model listing, model selection,
   thinking/reasoning toggle, structured output, local vs remote class.
6. Backend identity envelope: provider_id, provider_kind, adapter_name,
   provider_id_source, capabilities; clear operator vs artifact vs verified.
7. No silent /v1/models assumptions without adapter mediation.
8. Explicit errors for unsupported features.

Deliverables: base interface, MLX aligned, OpenAI-compatible + Ollama adapters when
real, capability schema, tests, docs.

----------------------------------------
B. HOST COMPANION SURFACES
----------------------------------------
Goal: Static-hostable results with clean data contract: index, leaderboard, runs,
machines, providers, protocols, compare; raw vs derived vs projections;
comparability flags; offline, no CDN, generic static hosting.

Deliverables: contract.py beyond scaffold, host JSON, route artifacts, tests for
layout and stability.

----------------------------------------
C. SHARE OUTPUTS
----------------------------------------
Goal: Social card, markdown summary, comparison card, leaderboard image, machine
profile; from canonical data; CLI; deterministic offline assets; branding config
without personal defaults.

Deliverables: export pipeline, CLI, tests, docs with example workflows.

----------------------------------------
D. STANDARDIZATION / COMPARABILITY
----------------------------------------
Goal: protocol/version ownership, comparability rules, manifests, claims taxonomy
(measured vs operator-supplied vs inferred), honest reports.

Deliverables: protocol manifest/schema, comparability module, docs, tests.

----------------------------------------
E. HARDENING / OSS CLEANUP
----------------------------------------
Audit: CLI ergonomics, package layout, naming, paths, errors, README, packaging,
repo-root detection, JSON field hygiene, portability tests.

Verify: no personal paths in public outputs, no sensitive serialization, no
mislabeling, no SSOT duplication in benchmarking/*, no hidden legacy dependency
from canonical paths where suites should own behavior.

================================================================================
EXPECTED TECHNICAL DESIGN
================================================================================
Before large edits, update or add a short design under docs/azimuth_bench/ covering:
module map, adapter contract, provider identity, protocol/comparability, host model,
export model, migration plan, explicit implemented-now vs planned-later.

Baseline docs: ARCHITECTURE, SOURCE_OF_TRUTH, ENVIRONMENT, EVOLUTION.

================================================================================
IMPLEMENTATION RULES
================================================================================
- Small modules; reuse hardened code; tests with substantive changes.
- Transitional behavior documented explicitly.
- No marketing fiction; planned = labeled planned.
- If generalization is dishonest now, isolate + document.
- Build on azimuth_bench; signalbench stays a shim.
- When “implemented” scope changes, update SOURCE_OF_TRUTH.md in the same change set.

================================================================================
VERIFICATION REQUIREMENTS
================================================================================
Run and report exact commands and outcomes:
- ruff check . ; ruff format --check . ; python3 -m pytest -q
- azbench report build benchmarks --repo-root <repo>
- azbench --help ; azbench bench throughput --help
- python3 -m azimuth_bench --help ; python3 -m signalbench --help

Prove at least one path: adapter -> suite -> artifact -> summary -> site/report -> export
(when exports exist).

Tests (add/extend as needed): adapter capabilities, unsupported paths, identity
envelope, comparability, manifests, exports, repo-root behavior, no CDN in HTML,
no path leakage in public JSON, shim + benchmarking delegation.

================================================================================
DELIVERABLE FORMAT (END OF SESSION)
================================================================================
1. Canonical vs compatibility summary
2. Files changed (grouped)
3. Design summary (adapters, host, exports, comparability)
4. Proof ledger (claim -> file/test)
5. Verification commands + outcomes
6. OSS readiness: safe / risky / next steps
7. Remaining debt (highest value only)

================================================================================
QUALITY BAR
================================================================================
Serious OSS benchmark platform, not a demo. Smallest correct foundation over broad
shallow scaffolding. Isolate what cannot be honestly generalized yet.

End state:
“This is Azimuth as a real benchmark platform foundation, not benchmark-v2 with
a prettier name.”
```

---

## Repo-grounded upgrades in v2

- **SSOT-first gate** at the top of the paste block: execution plan vs `SOURCE_OF_TRUTH.md` + code.
- **Implemented vs roadmap** aligned with `SOURCE_OF_TRUTH` (MLX / OpenAI-compatible / Ollama throughput, report, compare, SVG exports, M5 merge, M6 evaluator path today; llama.cpp / vLLM remain roadmap).
- **Commit coupling**: SSOT updates when “implemented” scope changes.
- **Refresh** pytest count on handoff against `SOURCE_OF_TRUTH.md`.
