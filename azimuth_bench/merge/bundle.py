"""Merge validated canonical bundles from multiple benchmark run directories."""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from azimuth_bench.errors import MergeCollisionError, MergeInputError
from azimuth_bench.schema.bundle import build_canonical_data_files
from azimuth_bench.schema.version import AZIMUTH_BENCH_SCHEMA_VERSION


def _identity(row: dict[str, Any]) -> tuple[str, str, str, str, str]:
    return (
        str(row.get("model_id")),
        str(row.get("lane")),
        str(row.get("thinking_mode")),
        str(row.get("adapter_name") or ""),
        str(row.get("route_label") or ""),
    )


def _apply_merge_prefix(run_bundle: dict[str, Any], merge_id: str) -> None:
    """Disambiguate artifact keys when multiple run roots are merged."""
    run = run_bundle.get("run.json") or {}
    old_key = run.get("artifact_key")
    if not isinstance(old_key, str) or not old_key:
        return
    new_key = f"{merge_id}__{old_key}"
    run["artifact_key"] = new_key
    ap = run.get("artifact_path")
    if isinstance(ap, str) and ap:
        if old_key in ap:
            run["artifact_path"] = ap.replace(old_key, new_key)
        else:
            run["artifact_path"] = f"{new_key}.json"


def merge_canonical_bundles(
    primary: Path,
    extras: list[Path],
    *,
    repo_root: Path | None = None,
    provider_id: str | None = None,
    provider_id_source: str | None = None,
) -> dict[str, Any]:
    """Merge ``build_canonical_data_files`` outputs from primary + extras.

    Each directory must pass integrity independently. Duplicate
    ``(model_id, lane, thinking_mode, adapter_name, route_label)``
    across sources raises ``MergeCollisionError``.

    Args:
        primary: Primary run directory (report is written under ``primary/report/``).
        extras: Additional run directories (must be non-empty).

    Returns:
        Same shape as ``build_canonical_data_files`` plus ``merge.json``.
    """
    if not extras:
        raise MergeInputError(
            "merge requires at least one --include-run-dir (use report build without it for a single tree)",
        )

    all_dirs = [primary.resolve()] + [p.resolve() for p in extras]
    if len(set(all_dirs)) != len(all_dirs):
        raise MergeInputError("duplicate run directory in merge list")

    bundles_data: list[tuple[str, Path, dict[str, Any]]] = []
    for i, d in enumerate(all_dirs):
        try:
            b = build_canonical_data_files(
                d,
                repo_root=repo_root,
                provider_id=provider_id,
                provider_id_source=provider_id_source,
            )
        except ValueError as exc:
            raise MergeInputError(str(exc)) from exc
        bundles_data.append((f"s{i}", d, b))

    protocol_ids: set[str] = set()
    for _mid, _d, bundle in bundles_data:
        for row in (bundle.get("summary.json") or {}).get("rows") or []:
            if not isinstance(row, dict):
                continue
            pid = row.get("protocol_id")
            if isinstance(pid, str) and pid.strip():
                protocol_ids.add(pid.strip())

    multi_protocol = len(protocol_ids) > 1
    any_row_not_comparable = False

    identities: set[tuple[str, str, str]] = set()
    merged_rows: list[dict[str, Any]] = []
    merged_run_bundles: list[dict[str, Any]] = []
    merged_machines: dict[str, Any] = {}
    all_fields: set[str] = set()

    for merge_id, dirpath, bundle in bundles_data:
        rows = (bundle.get("summary.json") or {}).get("rows") or []
        rbs = bundle.get("run_bundles") or []
        if len(rows) != len(rbs):
            raise MergeInputError(f"row/bundle count mismatch for {dirpath.name}")

        machines = (bundle.get("machines.json") or {}).get("machines") or {}
        for mk, mv in machines.items():
            nk = f"{merge_id}__{mk}"
            if nk in merged_machines:
                raise MergeCollisionError(f"machine key collision after prefix: {nk!r}")
            merged_machines[nk] = mv

        for row, rb in zip(rows, rbs):
            ident = _identity(row)
            if ident in identities:
                raise MergeCollisionError(
                    f"duplicate summary row identity across merge sources: model_id={ident[0]!r} "
                    f"lane={ident[1]!r} thinking_mode={ident[2]!r} adapter_name={ident[3]!r} route_label={ident[4]!r}",
                )
            identities.add(ident)

            row2 = dict(row)
            row2["merge_source"] = merge_id
            row2["merge_bundle_label"] = dirpath.name
            comparable = bool(row2.get("comparable", True))
            if not comparable:
                any_row_not_comparable = True
                row2["merge_row_comparability_class"] = "not_comparable"
            elif multi_protocol:
                row2["merge_row_comparability_class"] = "scoped_comparable"
            else:
                row2["merge_row_comparability_class"] = "fully_comparable"
            merged_rows.append(row2)
            for k in row2:
                all_fields.add(k)

            rb2 = copy.deepcopy(rb)
            _apply_merge_prefix(rb2, merge_id)
            merged_run_bundles.append(rb2)

    blockers: list[dict[str, Any]] = []
    comparability_class = "fully_comparable"
    if multi_protocol:
        comparability_class = "scoped_comparable"
        blockers.append(
            {
                "reason": "multiple_protocol_ids",
                "detail": "Merged sources contain more than one protocol_id; cross-protocol ranking is not allowed.",
                "protocol_ids": sorted(protocol_ids),
            },
        )
    if any_row_not_comparable:
        comparability_class = "not_comparable"
        blockers.append(
            {
                "reason": "non_comparable_rows_present",
                "detail": (
                    "At least one merged row is marked comparable=false; "
                    "do not treat the merged table as a fair ranking."
                ),
            },
        )

    merge_block: dict[str, Any] = {
        "schema": "azimuth_merge_v1",
        "sources": [{"merge_id": f"s{i}", "bundle_label": d.name} for i, d in enumerate(all_dirs)],
        "comparability_class": comparability_class,
        "protocol_ids_unique": sorted(protocol_ids),
        "cross_protocol_ranking_allowed": not multi_protocol,
        "blockers": blockers,
    }

    summary_fields = sorted(all_fields)
    for key in (
        "valid_run",
        "comparable",
        "comparable_scope",
        "comparability_blockers",
        "protocol_id",
        "prompt_set_id",
        "token_count_sources",
        "machine_class",
        "provider_id",
        "provider_kind",
        "adapter_name",
        "merge_source",
        "merge_bundle_label",
        "merge_row_comparability_class",
    ):
        if key not in summary_fields:
            summary_fields.append(key)

    top_run = dict(bundles_data[0][2]["run.json"])
    top_run["merge"] = merge_block

    top_summary = {
        "azimuth_bench_schema_version": AZIMUTH_BENCH_SCHEMA_VERSION,
        "kind": "token_summary",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "lane": "merged",
        "row_count": len(merged_rows),
        "fields": summary_fields,
        "rows": merged_rows,
    }

    top_machine = {
        "azimuth_bench_schema_version": AZIMUTH_BENCH_SCHEMA_VERSION,
        "snapshot": (bundles_data[0][2].get("machine.json") or {}).get("snapshot"),
        "selection": "merged:" + ";".join(str(b[1].name) for b in bundles_data),
    }

    providers_index: dict[str, Any] = {}
    for rb in merged_run_bundles:
        provider_identity = rb.get("provider.json") or {}
        provider_key = str(provider_identity.get("provider_kind") or provider_identity.get("provider_id") or "unknown")
        if provider_key not in providers_index:
            providers_index[provider_key] = provider_identity

    if len(providers_index) == 1:
        only_provider = next(iter(providers_index.values()))
        top_provider = {
            "azimuth_bench_schema_version": AZIMUTH_BENCH_SCHEMA_VERSION,
            **only_provider,
            "providers": list(providers_index.values()),
        }
    else:
        top_provider = {
            "azimuth_bench_schema_version": AZIMUTH_BENCH_SCHEMA_VERSION,
            "provider_id": "mixed",
            "provider_kind": "mixed",
            "provider_id_source": "artifact",
            "providers": list(providers_index.values()),
            "note": "multiple provider identities present across merged artifacts",
        }

    model_envelope = {
        "azimuth_bench_schema_version": AZIMUTH_BENCH_SCHEMA_VERSION,
        "models": [rb["model.json"] for rb in merged_run_bundles],
    }
    cases_envelope = {
        "azimuth_bench_schema_version": AZIMUTH_BENCH_SCHEMA_VERSION,
        "cases": [rb["cases.json"] for rb in merged_run_bundles],
    }
    machines_envelope = {
        "azimuth_bench_schema_version": AZIMUTH_BENCH_SCHEMA_VERSION,
        "machines": merged_machines,
    }

    integrity_ok = all((b[2].get("integrity") or {}).get("ok") for b in bundles_data)
    warnings: list[str] = []
    for b in bundles_data:
        warnings.extend((b[2].get("integrity") or {}).get("warnings") or [])

    return {
        "run.json": top_run,
        "summary.json": top_summary,
        "machine.json": top_machine,
        "provider.json": top_provider,
        "model.json": model_envelope,
        "cases.json": cases_envelope,
        "machines.json": machines_envelope,
        "run_bundles": merged_run_bundles,
        "integrity": {"ok": integrity_ok, "warnings": warnings},
        "merge.json": merge_block,
    }
