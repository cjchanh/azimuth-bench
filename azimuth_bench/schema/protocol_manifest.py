"""Protocol ownership and version surface for manifests (no live network I/O)."""

from __future__ import annotations

from typing import Any

from azimuth_bench.schema.version import AZIMUTH_BENCH_SCHEMA_VERSION


def build_protocol_manifest(*, protocol: dict[str, Any], suite_family: str) -> dict[str, Any]:
    """Emit a small protocol manifest for static site / export consumers."""
    return {
        "azimuth_bench_schema_version": AZIMUTH_BENCH_SCHEMA_VERSION,
        "suite_family": suite_family,
        "protocol_id": protocol.get("protocol_id"),
        "prompt_set_id": protocol.get("prompt_set_id"),
        "machine_class": protocol.get("machine_class"),
        "claims": {
            "protocol_fields": "measured_from_suite_definition",
            "machine_class": "operator_supplied_or_suite_default",
        },
    }
