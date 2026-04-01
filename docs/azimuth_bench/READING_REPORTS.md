# How to read an Azimuth Report

Azimuth Report is **static** output from `azbench report build <run_dir>`, usually under `<run_dir>/report/`. There is no live server requirement.

## Layout

| Path | Role |
| --- | --- |
| `report/index.html` | Landing page: top rows, charts, integrity/schema cards. |
| `report/leaderboard.html` | Full table sorted by structured JSON tok/s (default sort key). |
| `report/compare.html` | Frontier pair deltas where the data supports them. |
| `report/runs/<artifact_key>.html` | Per-model narrative view. |
| `report/providers/` | Provider summary pages + `report/data/providers/index.json`. |
| `report/protocols/` | Protocol summary pages + `report/data/protocols/index.json`. |
| `report/data/*.json` | Canonical machine-readable bundle (leaderboard, summary, site manifest). |
| `report/data/runs/<artifact_key>/` | Per-run `run.json`, `summary.json`, `provider.json`, `cases.json`, etc. |

## Leaderboard

- **Structured JSON tok/s** is the primary leaderboard metric in this tree (see charts and `leaderboard.json`).
- Rows can include **multiple lanes** (e.g. `core` vs `frontier_27b`); read the **Lane** column before comparing.

## Comparable flag

- **`comparable: true`** means the harness considered the run **valid** under the protocol rules (not that every row is comparable to every other row globally).
- Use **`comparable_scope`**, **`comparability_blockers`**, and **`protocol_id`** on enriched summary rows to see constraints.
- Do not treat **`comparable`** as a substitute for reading protocol and machine context.

## Provider and protocol pages

- **Providers**: summarize `provider_id` / `provider_kind` and capabilities metadata when present.
- **Protocols**: show `protocol_id`, prompt set, and suite family from bundled `cases.json`.

These pages are **derived** from the same bundle as the leaderboard; they are not a second source of truth.

## Run detail

Each **run** page corresponds to one artifact key. It links back to leaderboard/compare navigation. Deep metrics and provenance live under `report/data/runs/<artifact_key>/`.

## Machine detail

If machine receipts exist, **machine** pages show snapshot data; selection rules are described in JSON (`selection` / machine index). Missing receipts are normal for some trees.

## Markdown export

After building the report:

```bash
azbench export markdown <run_dir> --output summary.md
```

This reads **`report/data/summary.json`** only. Build the report first.

## Common misreadings

1. **Higher tok/s always wins** — Only within the same protocol, lane, and comparable context; thinking modes and model families differ.
2. **Comparable = universal** — It means protocol validity, not “equal hardware.”
3. **Provider name in JSON** — May be operator-supplied or default; read `provider_id_source`.
4. **Absolute paths** — Public bundle fields should be relative; if you see absolute paths, file a bug (they should not appear in normalized output).

Methodology background: [METHODOLOGY.md](METHODOLOGY.md). Truth boundary: [SOURCE_OF_TRUTH.md](SOURCE_OF_TRUTH.md).
