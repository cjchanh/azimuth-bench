"""JSON shapes for a static results site (scaffold)."""

from __future__ import annotations

from typing import Any

# Stable route keys for host companions (JSON contract; static hosting only).
HOST_ROUTE_KEYS: tuple[str, ...] = (
    "home",
    "leaderboard",
    "run_detail",
    "compare",
    "machine_detail",
    "providers",
    "protocols",
)


def build_host_index_payload(bundle: dict[str, Any]) -> dict[str, Any]:
    """Minimal host-facing index payload (derived; no raw secrets)."""
    run_meta = bundle.get("run.json") or {}
    summary = bundle.get("summary.json") or {}
    rows = summary.get("rows") if isinstance(summary.get("rows"), list) else []
    run_bundles = bundle.get("run_bundles") if isinstance(bundle.get("run_bundles"), list) else []
    provider_ids = {
        str(provider.get("provider_id"))
        for rb in run_bundles
        if isinstance(rb, dict)
        for provider in [rb.get("provider.json") or {}]
        if isinstance(provider, dict) and provider.get("provider_id")
    }
    protocol_ids = {
        str(cases.get("protocol_id"))
        for rb in run_bundles
        if isinstance(rb, dict)
        for cases in [rb.get("cases.json") or {}]
        if isinstance(cases, dict) and cases.get("protocol_id")
    }
    return {
        "azimuth_bench_schema_version": run_meta.get("azimuth_bench_schema_version")
        or run_meta.get("signalbench_schema_version"),
        "row_count": len(rows),
        "provider_count": len(provider_ids),
        "protocol_count": len(protocol_ids),
        "comparability": {"note": "see per-row comparable flags in summary rows"},
    }


def build_site_manifest(run_dir, bundle: dict[str, Any]) -> dict[str, Any]:
    """Emit a manifest describing routes and payload roles for static hosting."""
    run_dir = run_dir.resolve()
    summary = bundle.get("summary.json") or {}
    rows = summary.get("rows") or []
    run_meta = bundle.get("run.json") or {}
    run_bundles = bundle.get("run_bundles") or []
    machines = (bundle.get("machines.json") or {}).get("machines") or {}
    provider_ids = {
        str(provider.get("provider_id"))
        for rb in run_bundles
        if isinstance(rb, dict)
        for provider in [rb.get("provider.json") or {}]
        if isinstance(provider, dict) and provider.get("provider_id")
    }
    protocol_ids = {
        str(cases.get("protocol_id"))
        for rb in run_bundles
        if isinstance(rb, dict)
        for cases in [rb.get("cases.json") or {}]
        if isinstance(cases, dict) and cases.get("protocol_id")
    }

    manifest: dict[str, Any] = {
        "azimuth_bench_schema_version": run_meta.get("azimuth_bench_schema_version")
        or run_meta.get("signalbench_schema_version"),
        "routes": list(HOST_ROUTE_KEYS),
        "host_index": build_host_index_payload(bundle),
        "home": {
            "description": "Latest report index and headline metrics",
            "artifact": "report/index.html",
            "data": ["report/data/run.json", "report/data/summary.json"],
        },
        "leaderboard": {
            "description": "Sortable table over summary rows",
            "artifact": "report/leaderboard.html",
            "data": "report/data/leaderboard.json",
            "primary_metric": "structured_json_tok_s",
        },
        "run_detail": {
            "description": "Per-artifact detail pages emitted under report/runs/",
            "data_root": "report/data/runs/",
            "artifact": "report/runs/",
            "count": len(run_bundles),
        },
        "compare": {
            "description": "Pairwise comparison view for selected rows",
            "artifact": "report/compare.html",
            "data": "report/data/compare.json",
        },
        "machine_detail": {
            "description": "Machine snapshot pages emitted under report/machines/",
            "artifact": "report/machines/",
            "data": "report/data/machines.json",
            "count": len(machines),
        },
        "providers": {
            "description": "Provider summary pages emitted under report/providers/",
            "artifact": "report/providers/",
            "data": "report/data/providers/index.json",
            "count": len(provider_ids),
        },
        "protocols": {
            "description": "Protocol summary pages emitted under report/protocols/",
            "artifact": "report/protocols/",
            "data": "report/data/protocols/index.json",
            "count": len(protocol_ids),
        },
        "row_count": len(rows) if isinstance(rows, list) else 0,
        "status": "scaffold_static_first",
    }
    return manifest
