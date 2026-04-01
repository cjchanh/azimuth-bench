"""Deterministic SVG share cards from canonical report data (no paths, no CDN)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Match Azimuth Report dark surface (same family as report/builder.py).
_BG = "#0b0f14"
_PANEL = "#111821"
_TEXT = "#e7edf5"
_MUTED = "#93a0b3"
_ACCENT = "#7aa2d6"
_BORDER = "#273241"


def write_share_leaderboard_svg(*, output_path: Path, summary_rows: list[dict[str, Any]], top_n: int = 5) -> Path:
    """Horizontal bar chart of top-N structured JSON tok/s (deterministic sort)."""
    output_path = output_path.resolve()
    ranked = sorted(
        summary_rows,
        key=lambda r: float(r.get("structured_json_tok_s") or 0.0),
        reverse=True,
    )[: max(1, top_n)]
    labels = [str(r.get("display_name") or r.get("model_id") or "?")[:42] for r in ranked]
    values = [float(r.get("structured_json_tok_s") or 0.0) for r in ranked]

    fig, ax = plt.subplots(figsize=(10, 3.2), dpi=120)
    fig.patch.set_facecolor(_BG)
    ax.set_facecolor(_PANEL)
    ax.barh(labels[::-1], values[::-1], color=_ACCENT)
    ax.set_title("Azimuth snapshot — structured JSON tok/s (top rows)", color=_TEXT, fontsize=11)
    ax.set_xlabel("tok/s", color=_TEXT, fontsize=9)
    ax.tick_params(colors=_MUTED, labelsize=8)
    ax.grid(axis="x", linestyle="--", alpha=0.2, color=_ACCENT)
    for spine in ax.spines.values():
        spine.set_color(_BORDER)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, format="svg", bbox_inches="tight", facecolor=_BG)
    plt.close(fig)
    return output_path


def write_share_compare_svg(*, output_path: Path, compare_projection: dict[str, Any]) -> Path:
    """Bar chart of frontier pairwise deltas when present; otherwise a note."""
    output_path = output_path.resolve()
    pairs = (compare_projection.get("projection") or {}).get("pairs") or []
    if not pairs:
        fig, ax = plt.subplots(figsize=(8, 2.5), dpi=120)
        fig.patch.set_facecolor(_BG)
        ax.set_facecolor(_PANEL)
        ax.text(
            0.5,
            0.5,
            "No scoped comparison pairs in this snapshot",
            ha="center",
            va="center",
            color=_MUTED,
            fontsize=11,
            transform=ax.transAxes,
        )
        ax.axis("off")
        for spine in ax.spines.values():
            spine.set_visible(False)
        fig.tight_layout()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, format="svg", bbox_inches="tight", facecolor=_BG)
        plt.close(fig)
        return output_path

    labels: list[str] = []
    deltas: list[float] = []
    for p in pairs:
        scope = p.get("scope") or {}
        lab = f"{scope.get('lane', '')} · think={scope.get('thinking_mode', '')}"
        labels.append(str(lab)[:48])
        d = (p.get("deltas") or {}).get("structured_json_tok_s")
        deltas.append(float(d) if d is not None else 0.0)

    fig, ax = plt.subplots(figsize=(9, max(2.8, 0.45 * len(labels))), dpi=120)
    fig.patch.set_facecolor(_BG)
    ax.set_facecolor(_PANEL)
    ax.barh(labels[::-1], deltas[::-1], color=_ACCENT)
    ax.set_title("Azimuth compare — structured JSON tok/s delta (scoped pairs)", color=_TEXT, fontsize=11)
    ax.set_xlabel("delta tok/s (candidate minus reference)", color=_TEXT, fontsize=9)
    ax.tick_params(colors=_MUTED, labelsize=8)
    ax.grid(axis="x", linestyle="--", alpha=0.2, color=_ACCENT)
    for spine in ax.spines.values():
        spine.set_color(_BORDER)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, format="svg", bbox_inches="tight", facecolor=_BG)
    plt.close(fig)
    return output_path


def write_share_svgs_from_report_data(*, report_data_dir: Path, exports_dir: Path) -> tuple[Path, Path]:
    """Load canonical JSON from ``report/data`` and write both share SVGs."""
    report_data_dir = report_data_dir.resolve()
    exports_dir = exports_dir.resolve()
    summary_path = report_data_dir / "summary.json"
    compare_path = report_data_dir / "compare.json"
    if not summary_path.is_file():
        raise FileNotFoundError(f"missing summary.json: {summary_path}")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    rows = summary.get("rows") if isinstance(summary.get("rows"), list) else []
    compare_obj: dict[str, Any] = {}
    if compare_path.is_file():
        compare_obj = json.loads(compare_path.read_text(encoding="utf-8"))
    lb = write_share_leaderboard_svg(
        output_path=exports_dir / "share_leaderboard.svg",
        summary_rows=[r for r in rows if isinstance(r, dict)],
    )
    sc = write_share_compare_svg(
        output_path=exports_dir / "share_compare.svg",
        compare_projection=compare_obj,
    )
    return lb, sc
