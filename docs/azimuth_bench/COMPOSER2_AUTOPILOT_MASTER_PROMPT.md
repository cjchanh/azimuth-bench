# Composer 2 Master Autopilot Prompt

**Role:** This file remains the **conceptual** execution-plan anchor for Composer / autopilot-style work. **Truth boundary for what is implemented today:** `docs/azimuth_bench/SOURCE_OF_TRUTH.md` and the code. Do not claim or document features as current until `SOURCE_OF_TRUTH.md` is updated accordingly and **committed** with the matching implementation.

**Canonical copy-paste prompt for a new Composer window:** use **`docs/azimuth_bench/COMPOSER2_UPGRADE_SESSION_V2.md`**. It is **v2** (2026-04-01): SSOT-first gate, explicit “implemented vs roadmap” alignment with `SOURCE_OF_TRUTH.md`, and the same A–E target work with clearer boundaries. Open that file and copy **only** the body of the fenced `text` code block (omit the triple-backtick lines).

## Repo-grounded upgrades already baked into v2

- **SSOT-first** block at the top of the session prompt (execution plan vs `SOURCE_OF_TRUTH.md` + tests + code).
- **Implemented vs not** aligned with `SOURCE_OF_TRUTH` (MLX/throughput/report today; non-MLX production path = roadmap until SSOT says otherwise).
- **Same** identity freeze, canonical vs compatibility lists, verification commands, A–E deliverables, and handoff format as the classic prompt, tightened so Composer does not confuse targets with shipped behavior.
- Last verified: `34 passed` (re-run `pytest` on handoff and refresh if changed).
