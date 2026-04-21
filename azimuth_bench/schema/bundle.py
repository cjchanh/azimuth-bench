"""Assemble canonical JSON files for report/data from a benchmarks run directory."""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from azimuth_bench.schema.artifact_lookup import matching_artifact_paths
from azimuth_bench.schema.integrity import validate_run_directory
from azimuth_bench.schema.io import read_json_dict
from azimuth_bench.schema.version import AZIMUTH_BENCH_SCHEMA_VERSION


def _git_sha(repo_root: Path | None) -> str | None:
    if repo_root is None:
        return None
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            return None
        sha = proc.stdout.strip()
        return sha or None
    except OSError:
        return None


def _first_machine_receipt(run_dir: Path) -> tuple[dict[str, Any] | None, str]:
    receipts_root = run_dir / "receipts"
    if not receipts_root.is_dir():
        return None, "no receipts directory"
    paths = sorted(receipts_root.glob("**/machine_pre_run.json"))
    if not paths:
        return None, "no machine_pre_run.json under receipts"
    first = paths[0]
    data = read_json_dict(first)
    note = f"lexicographic_first_receipt:{first.relative_to(run_dir)}"
    return data, note


def _extract_model_family(display_name: str | None, model_id: str | None) -> str | None:
    source = display_name or model_id
    if not source:
        return None
    return source.split()[0]


def _extract_quantization(model_id: str | None) -> str | None:
    if not model_id:
        return None
    lower = model_id.lower()
    for token in ("4bit", "8bit", "fp16", "q4", "q8"):
        if token in lower:
            return token
    return None


def _public_relative_path(path_value: str | Path, *, run_dir: Path) -> str:
    path = Path(path_value)
    try:
        if path.is_absolute():
            return str(path.relative_to(run_dir))
    except ValueError:
        return path.name or str(path)
    return str(path)


def _public_receipt_paths(receipt_paths: dict[str, Any], *, run_dir: Path) -> dict[str, str]:
    public_paths: dict[str, str] = {}
    for key, value in receipt_paths.items():
        if isinstance(value, str) and value:
            public_paths[key] = _public_relative_path(value, run_dir=run_dir)
    return public_paths


def _fallback_provider_identity(*, provider_id: str | None, provider_id_source: str | None) -> dict[str, Any]:
    return {
        "provider_id": provider_id or "mlx_lm",
        "provider_kind": "mlx_lm",
        "adapter_name": None,
        "provider_id_source": provider_id_source or ("default" if provider_id is None else "cli"),
        "capabilities": None,
        "verified": {"historical_artifact": True},
        "note": "historical artifact missing backend_identity; provider envelope is report metadata",
        "backend": "mlx_lm_server",
        "api_surface": "openai_compatible_http",
    }


def _provider_identity_from_artifact(
    *,
    artifact_payload: dict[str, Any],
    provider_id: str | None,
    provider_id_source: str | None,
) -> dict[str, Any]:
    backend_identity = artifact_payload.get("backend_identity")
    if isinstance(backend_identity, dict) and backend_identity:
        verified = backend_identity.get("verified")
        if isinstance(verified, dict):
            verified = {
                key: value
                for key, value in verified.items()
                if key not in {"repo_root", "base_url", "endpoint_url", "artifact_path"}
            }
        provider_json = {
            "provider_id": backend_identity.get("provider_id") or provider_id or "unknown",
            "provider_kind": backend_identity.get("provider_kind"),
            "adapter_name": backend_identity.get("adapter_name"),
            "provider_id_source": backend_identity.get("provider_id_source")
            or provider_id_source
            or ("default" if provider_id is None else "cli"),
            "capabilities": backend_identity.get("capabilities"),
            "verified": verified,
        }
        return provider_json
    return _fallback_provider_identity(provider_id=provider_id, provider_id_source=provider_id_source)


def _enrich_summary_row(
    *,
    row: dict[str, Any],
    artifact_payload: dict[str, Any],
    provider_identity: dict[str, Any],
) -> dict[str, Any]:
    enriched = dict(row)
    validity = artifact_payload.get("validity") if isinstance(artifact_payload.get("validity"), dict) else {}
    comparability = (
        artifact_payload.get("comparability") if isinstance(artifact_payload.get("comparability"), dict) else {}
    )
    protocol = artifact_payload.get("protocol") if isinstance(artifact_payload.get("protocol"), dict) else {}
    enriched["valid_run"] = bool(validity.get("valid_run"))
    enriched["comparable"] = bool(comparability.get("comparable", enriched.get("comparable")))
    enriched["comparable_scope"] = comparability.get("comparable_scope") or (
        "protocol_exact" if enriched["comparable"] else "not_comparable"
    )
    enriched["comparability_blockers"] = list(
        comparability.get("comparability_blockers") or validity.get("issues") or []
    )
    enriched["protocol_id"] = comparability.get("protocol_id") or protocol.get("protocol_id")
    enriched["prompt_set_id"] = comparability.get("prompt_set_id") or protocol.get("prompt_set_id")
    enriched["token_count_sources"] = list(comparability.get("token_count_sources") or [])
    enriched["machine_class"] = protocol.get("machine_class")
    enriched["provider_id"] = provider_identity.get("provider_id")
    enriched["provider_kind"] = provider_identity.get("provider_kind")
    if provider_identity.get("adapter_name") is not None:
        enriched["adapter_name"] = provider_identity.get("adapter_name")
    route_identity = artifact_payload.get("route_identity")
    if isinstance(route_identity, dict):
        rl = route_identity.get("route_label")
        if isinstance(rl, str) and rl.strip():
            enriched["route_label"] = rl.strip()
        sp = route_identity.get("sampling_policy")
        if isinstance(sp, str) and sp.strip():
            enriched["sampling_policy"] = sp.strip()
        pch = route_identity.get("protocol_content_sha256")
        if isinstance(pch, str) and pch.strip():
            enriched["protocol_content_sha256"] = pch.strip()
    return enriched


def _normalize_artifact(
    *,
    run_dir: Path,
    artifact_path: Path,
    artifact_payload: dict[str, Any],
    row: dict[str, Any],
    provider_id: str | None,
    provider_id_source: str | None,
) -> dict[str, dict[str, Any]]:
    receipts = artifact_payload.get("receipts")
    receipt_paths = artifact_payload.get("receipt_paths")
    receipts = receipts if isinstance(receipts, dict) else {}
    receipt_paths = receipt_paths if isinstance(receipt_paths, dict) else {}
    public_receipt_paths = _public_receipt_paths(receipt_paths, run_dir=run_dir)
    machine_snapshot = receipts.get("machine_pre_run") if isinstance(receipts.get("machine_pre_run"), dict) else {}
    model_load = receipts.get("model_load") if isinstance(receipts.get("model_load"), dict) else {}
    protocol = artifact_payload.get("protocol") if isinstance(artifact_payload.get("protocol"), dict) else {}
    summary = artifact_payload.get("summary") if isinstance(artifact_payload.get("summary"), dict) else {}
    validity = artifact_payload.get("validity") if isinstance(artifact_payload.get("validity"), dict) else {}
    comparability = (
        artifact_payload.get("comparability") if isinstance(artifact_payload.get("comparability"), dict) else {}
    )
    prompts = protocol.get("prompts") if isinstance(protocol.get("prompts"), list) else []

    benchmark_commit_sha = artifact_payload.get("benchmark_commit_sha")
    if not isinstance(benchmark_commit_sha, str) or not benchmark_commit_sha:
        benchmark_commit_sha = None

    exact_invocation = None
    token_run_start = receipts.get("token_run_start")
    if isinstance(token_run_start, dict):
        command = token_run_start.get("command")
        if isinstance(command, str) and command:
            exact_invocation = command

    target_model_id = model_load.get("expected_model") or artifact_payload.get("model_id") or row.get("model_id")
    served_model_ids = model_load.get("served_model_ids")
    if not isinstance(served_model_ids, list):
        served_model = model_load.get("served_model")
        served_model_ids = [served_model] if isinstance(served_model, str) else [target_model_id]

    provenance_gaps: list[str] = []
    if benchmark_commit_sha is None:
        provenance_gaps.append("benchmark_commit_sha_missing_from_source_artifact")
    if exact_invocation is None:
        provenance_gaps.append("exact_invocation_missing_from_source_artifact")

    run_json = {
        "azimuth_bench_schema_version": AZIMUTH_BENCH_SCHEMA_VERSION,
        "artifact_key": artifact_payload.get("artifact_key"),
        "artifact_path": _public_relative_path(artifact_path, run_dir=run_dir),
        "artifact_path_kind": "run_dir_relative",
        "benchmark_suite_name": protocol.get("suite_family", "throughput"),
        "benchmark_commit_sha": benchmark_commit_sha,
        "timestamps": {
            "run_start_utc": receipts.get("run_start_utc"),
            "run_finish_utc": receipts.get("run_finish_utc"),
            "model_load_started_at_utc": model_load.get("started_at_utc"),
            "model_load_finished_at_utc": model_load.get("finished_at_utc"),
            "summary_timestamp_utc": summary.get("timestamp_utc"),
        },
        "exact_invocation": exact_invocation,
        "artifact_provenance": {
            "receipt_paths": public_receipt_paths,
            "valid_run": validity.get("valid_run"),
            "comparable": comparability.get("comparable"),
            "provenance_gaps": provenance_gaps,
        },
    }

    summary_json = {
        "azimuth_bench_schema_version": AZIMUTH_BENCH_SCHEMA_VERSION,
        "metrics": summary,
        "validity": validity,
        "comparability": comparability,
    }

    machine_json = {
        "azimuth_bench_schema_version": AZIMUTH_BENCH_SCHEMA_VERSION,
        "machine_profile": machine_snapshot,
    }

    provider_json = {
        "azimuth_bench_schema_version": AZIMUTH_BENCH_SCHEMA_VERSION,
        **_provider_identity_from_artifact(
            artifact_payload=artifact_payload,
            provider_id=provider_id,
            provider_id_source=provider_id_source,
        ),
    }

    model_json = {
        "azimuth_bench_schema_version": AZIMUTH_BENCH_SCHEMA_VERSION,
        "model_id": artifact_payload.get("model_id"),
        "target_model_id": target_model_id,
        "served_model_ids": served_model_ids,
        "display_name": artifact_payload.get("display_name"),
        "thinking_mode": artifact_payload.get("thinking_mode"),
        "prompt_mode": "chat_completions",
        "source_label": artifact_payload.get("source_label"),
        "source_badge": artifact_payload.get("source_badge"),
        "quantization": _extract_quantization(artifact_payload.get("model_id")),
        "model_family": _extract_model_family(artifact_payload.get("display_name"), artifact_payload.get("model_id")),
    }

    cases_json = {
        "azimuth_bench_schema_version": AZIMUTH_BENCH_SCHEMA_VERSION,
        "suite_family": protocol.get("suite_family", "throughput"),
        "protocol_id": protocol.get("protocol_id"),
        "prompt_set_id": protocol.get("prompt_set_id"),
        "thinking_mode_policy": protocol.get("thinking_mode_policy"),
        "prompts": prompts,
        "benchmark_config": artifact_payload.get("benchmark_config"),
    }

    return {
        "run.json": run_json,
        "summary.json": summary_json,
        "machine.json": machine_json,
        "provider.json": provider_json,
        "model.json": model_json,
        "cases.json": cases_json,
    }


def build_canonical_data_files(
    run_dir: Path,
    *,
    repo_root: Path | None = None,
    summary_name: str = "benchmark_v2_token_summary.json",
    provider_id: str | None = None,
    provider_id_source: str | None = None,
) -> dict[str, Any]:
    """Build canonical dicts for report/data from a run directory."""
    run_dir = run_dir.resolve()
    integrity = validate_run_directory(run_dir, summary_name=summary_name)
    if not integrity.ok:
        msg = "; ".join(integrity.blockers)
        raise ValueError(f"run directory integrity failed: {msg}")

    summary_path = run_dir / summary_name
    summary_raw = read_json_dict(summary_path)
    if summary_raw is None:
        raise ValueError(f"summary file unreadable after integrity pass: {summary_path}")

    report_build_commit_sha = _git_sha(repo_root.resolve() if repo_root else None)
    machine_payload, machine_selection = _first_machine_receipt(run_dir)

    top_run = {
        "azimuth_bench_schema_version": AZIMUTH_BENCH_SCHEMA_VERSION,
        "run_id": f"azimuth_bench_{summary_raw.get('generated_at_utc', 'unknown').replace(':', '-').replace('+', '_')}",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "report_build_commit_sha": report_build_commit_sha,
        "benchmark_commit_sha": None,
        "benchmark_commit_sha_status": "missing_in_source_artifacts",
        "lane": summary_raw.get("lane"),
        "summary_source": str(summary_path.name),
        "platform": "Azimuth Bench",
    }

    top_machine = {
        "azimuth_bench_schema_version": AZIMUTH_BENCH_SCHEMA_VERSION,
        "snapshot": machine_payload,
        "selection": machine_selection,
    }

    run_bundles: list[dict[str, Any]] = []
    models: list[dict[str, Any]] = []
    cases: list[dict[str, Any]] = []
    machines_index: dict[str, dict[str, Any]] = {}
    enriched_rows: list[dict[str, Any]] = []
    providers_index: dict[str, dict[str, Any]] = {}

    for row in summary_raw.get("rows") or []:
        if not isinstance(row, dict):
            continue
        model_id = row.get("model_id")
        lane = row.get("lane")
        thinking_mode = row.get("thinking_mode")
        if not isinstance(model_id, str) or not isinstance(lane, str) or not isinstance(thinking_mode, str):
            continue

        paths = matching_artifact_paths(
            run_dir,
            summary_name=summary_name,
            model_id=model_id,
            lane=lane,
            thinking_mode=thinking_mode,
        )
        if len(paths) != 1:
            raise RuntimeError(
                "integrity invariant violated: expected exactly one artifact per summary row; "
                f"got {len(paths)} for model_id={model_id!r} lane={lane!r} thinking={thinking_mode!r}"
            )
        artifact_path = paths[0]
        artifact_payload = read_json_dict(artifact_path)
        if artifact_payload is None:
            raise ValueError(f"artifact file unreadable after integrity pass: {artifact_path}")

        bundle = _normalize_artifact(
            run_dir=run_dir,
            artifact_path=artifact_path,
            artifact_payload=artifact_payload,
            row=row,
            provider_id=provider_id,
            provider_id_source=provider_id_source,
        )
        run_bundles.append(bundle)
        models.append(bundle["model.json"])
        cases.append(bundle["cases.json"])
        provider_identity = bundle["provider.json"]
        enriched_rows.append(
            _enrich_summary_row(
                row=row,
                artifact_payload=artifact_payload,
                provider_identity=provider_identity,
            )
        )
        provider_key = str(provider_identity.get("provider_kind") or provider_identity.get("provider_id") or "unknown")
        if provider_key not in providers_index:
            providers_index[provider_key] = provider_identity

        machine_profile = bundle["machine.json"].get("machine_profile")
        if isinstance(machine_profile, dict):
            machine_key = str(
                machine_profile.get("hardware_model")
                or machine_profile.get("hostname")
                or f"machine-{len(machines_index) + 1}"
            )
            machines_index[machine_key] = machine_profile

    summary_fields = list(summary_raw.get("fields") or [])
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
    ):
        if key not in summary_fields:
            summary_fields.append(key)

    top_summary = {
        "azimuth_bench_schema_version": AZIMUTH_BENCH_SCHEMA_VERSION,
        "kind": "token_summary",
        "generated_at_utc": summary_raw.get("generated_at_utc"),
        "lane": summary_raw.get("lane"),
        "row_count": summary_raw.get("row_count"),
        "fields": summary_fields,
        "rows": enriched_rows,
    }

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
            "note": "multiple provider identities present across artifacts",
        }

    model_envelope = {
        "azimuth_bench_schema_version": AZIMUTH_BENCH_SCHEMA_VERSION,
        "models": models,
    }

    cases_envelope = {
        "azimuth_bench_schema_version": AZIMUTH_BENCH_SCHEMA_VERSION,
        "cases": cases,
    }

    machines_envelope = {
        "azimuth_bench_schema_version": AZIMUTH_BENCH_SCHEMA_VERSION,
        "machines": machines_index,
    }

    return {
        "run.json": top_run,
        "summary.json": top_summary,
        "machine.json": top_machine,
        "provider.json": top_provider,
        "model.json": model_envelope,
        "cases.json": cases_envelope,
        "machines.json": machines_envelope,
        "run_bundles": run_bundles,
        "integrity": {
            "ok": integrity.ok,
            "warnings": integrity.warnings,
        },
    }
