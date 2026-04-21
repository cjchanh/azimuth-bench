"""Promotion gate classification — evidence-backed routing labels."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

PROMOTION_GATE_VERSION = "azimuth_promotion_gate_v1"

Classification = Literal["default", "candidate", "specialist", "rejected"]


def build_promotion_report(payload: dict[str, Any]) -> dict[str, Any]:
    """Classify a route using throughput, semantic summaries, and explicit blockers.

    Payload keys (all optional aside from discriminator fields you choose to include):

    - ``throughput``: ``{"valid_run": bool, "comparable": bool}``
    - ``semantic``: ``{"gate_pass": bool | None}`` — ``None`` means no semantic evidence.
    - ``blockers``: list[str] blocking reasons (semantic failures, adapter limits, leakage, etc.).
    - ``approve_default_route``: bool — explicit human approval for **default** classification.
    - ``specialist_lane``: bool — prefer **specialist** when semantics fail but throughput is usable.

    Rules:

    - **No** route may be classified **default** without semantic ``gate_pass is True``, clean blockers,
      valid+comparable throughput, and ``approve_default_route``.
    - Throughput alone never yields **default**.
    """
    throughput = payload.get("throughput") if isinstance(payload.get("throughput"), dict) else {}
    semantic = payload.get("semantic") if isinstance(payload.get("semantic"), dict) else {}
    blockers = [str(b) for b in (payload.get("blockers") or []) if str(b).strip()]
    approve_default = payload.get("approve_default_route") is True
    specialist_lane = payload.get("specialist_lane") is True

    thr_valid = throughput.get("valid_run") is True
    thr_cmp = throughput.get("comparable") is True
    sem_raw = semantic.get("gate_pass")
    sem_known = isinstance(sem_raw, bool)
    sem_pass = sem_raw if sem_known else None

    classification: Classification
    notes: list[str] = []

    if not thr_valid:
        classification = "rejected"
        notes.append("throughput_invalid")
    elif blockers:
        classification = "rejected"
        notes.extend(blockers)
    elif thr_valid and thr_cmp and sem_pass is True and not blockers and approve_default:
        classification = "default"
        notes.append("explicit_default_approval_with_semantic_gate")
    elif thr_valid and thr_cmp and sem_pass is False:
        classification = "specialist" if specialist_lane else "candidate"
        notes.append("semantic_gate_failed")
    elif thr_valid and thr_cmp and "gate_pass" in semantic and not sem_known:
        classification = "candidate"
        notes.append("semantic_evidence_malformed")
    elif thr_valid and thr_cmp and not sem_known:
        classification = "candidate"
        notes.append("semantic_evidence_missing")
    elif thr_valid and not thr_cmp:
        classification = "candidate"
        notes.append("throughput_not_comparable")
    else:
        classification = "candidate"
        notes.append("insufficient_evidence")

    return {
        "schema": PROMOTION_GATE_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "classification": classification,
        "notes": notes,
        "inputs_echo": {
            "throughput": throughput,
            "semantic": semantic,
            "blockers": blockers,
            "approve_default_route": approve_default,
            "specialist_lane": specialist_lane,
        },
        "policy": {
            "no_default_without_semantic_pass": True,
            "throughput_only_never_default": True,
        },
    }
