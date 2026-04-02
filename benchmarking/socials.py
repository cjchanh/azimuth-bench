#!/usr/bin/env python3
"""Generate mobile-first benchmark-v2 social cards."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch

from benchmarking.utils import DEFAULT_BENCHMARKS_DIR, DEFAULT_SOCIALS_DIR

FIGSIZE = (10.8, 13.5)
DPI = 100
BG = "#F5F1EA"
CARD = "#FFFFFF"
TEXT = "#111827"
SUBTEXT = "#6B7280"
GRID = "#E5E7EB"
BASE = "#0F766E"
OPUS = "#C2410C"
NEUTRAL = "#94A3B8"
GOOD = "#059669"
WARN = "#D97706"
BAD = "#DC2626"


def _pick_font_family() -> list[str]:
    candidates = ["SF Pro Display", "Helvetica Neue", "Arial"]
    available: list[str] = []
    for candidate in candidates:
        try:
            font_manager.findfont(candidate, fallback_to_default=False)
        except ValueError:
            continue
        available.append(candidate)
    available.append("sans-serif")
    return available


plt.rcParams.update(
    {
        "font.family": _pick_font_family(),
        "figure.dpi": DPI,
        "savefig.dpi": DPI,
        "savefig.bbox": "tight",
    }
)


def _load_rows(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text())
    rows = payload.get("rows", [])
    if not isinstance(rows, list):
        raise ValueError("summary must contain a rows list")
    return rows


def _as_float(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def _normalize_token_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        for key in (
            "short_tok_s",
            "structured_json_tok_s",
            "sustained_tok_s",
            "first_output_ms",
            "first_answer_ms",
        ):
            item[key] = _as_float(item.get(key, 0.0))
        normalized.append(item)
    return normalized


def _normalize_gate_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        for key in (
            "synthetic_failures",
            "synthetic_rate",
            "invalid_location_rate",
            "share_count_5tick",
        ):
            item[key] = _as_float(item.get(key, 0.0))
        normalized.append(item)
    return normalized


def _frontier_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    frontier = [row for row in rows if row.get("lane") == "frontier_27b"]
    if not frontier:
        raise ValueError("token summary is missing frontier_27b rows")
    order = {"Qwen3.5 27B Base": 0, "Qwen3.5 27B Opus Distilled v2": 1}
    think_order = {"off": 0, "on": 1, "default": 2}
    frontier.sort(
        key=lambda row: (
            order.get(str(row.get("display_name")), 99),
            think_order.get(str(row.get("thinking_mode")), 99),
        )
    )
    return frontier


def _card_background(fig: plt.Figure) -> None:
    fig.patch.set_facecolor(BG)


def _panel(ax: plt.Axes, x: float, y: float, w: float, h: float, *, facecolor: str = CARD) -> FancyBboxPatch:
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.012,rounding_size=0.03",
        linewidth=0,
        facecolor=facecolor,
        transform=ax.transAxes,
        zorder=1,
    )
    ax.add_patch(patch)
    return patch


def _hf_chip(ax: plt.Axes, x: float, y: float) -> None:
    chip = FancyBboxPatch(
        (x, y),
        0.14,
        0.035,
        boxstyle="round,pad=0.006,rounding_size=0.03",
        linewidth=0.5,
        edgecolor="#D4C87A",
        facecolor="#FEF3C7",
        transform=ax.transAxes,
        zorder=3,
    )
    ax.add_patch(chip)
    ax.text(
        x + 0.07,
        y + 0.0175,
        "Hugging Face",
        ha="center",
        va="center",
        fontsize=8,
        color="#92400E",
        fontweight="medium",
        transform=ax.transAxes,
        zorder=4,
    )


def _save(fig: plt.Figure, output_dir: Path, name: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_dir / f"{name}.png")
    plt.close(fig)


def _generate_hero(rows: list[dict[str, Any]], output_dir: Path) -> None:
    fig = plt.figure(figsize=FIGSIZE)
    _card_background(fig)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")

    ax.text(
        0.07,
        0.93,
        "Matched 27B Token Benchmark",
        fontsize=28,
        fontweight="bold",
        color=TEXT,
        transform=ax.transAxes,
    )
    ax.text(
        0.07,
        0.885,
        "Same size. Same backend. Base vs Opus-distilled, with thinking on and off.",
        fontsize=13,
        color=SUBTEXT,
        transform=ax.transAxes,
    )
    _hf_chip(ax, 0.72, 0.905)

    positions = [(0.07, 0.58), (0.52, 0.58), (0.07, 0.20), (0.52, 0.20)]
    for row, (x, y) in zip(rows, positions):
        accent = OPUS if "Opus" in str(row["display_name"]) else BASE
        _panel(ax, x, y, 0.4, 0.27)
        ax.text(
            x + 0.03,
            y + 0.22,
            row["display_name"],
            fontsize=17,
            fontweight="bold",
            color=TEXT,
            transform=ax.transAxes,
            zorder=4,
        )
        ax.text(
            x + 0.03,
            y + 0.18,
            f"thinking={row['thinking_mode']}",
            fontsize=11,
            color=accent,
            transform=ax.transAxes,
            zorder=4,
        )
        ax.text(
            x + 0.03,
            y + 0.12,
            f"{row['structured_json_tok_s']:.1f}",
            fontsize=32,
            fontweight="bold",
            color=accent,
            transform=ax.transAxes,
            zorder=4,
        )
        ax.text(
            x + 0.20,
            y + 0.125,
            "JSON tok/s",
            fontsize=12,
            color=SUBTEXT,
            transform=ax.transAxes,
            zorder=4,
        )
        ax.text(
            x + 0.03,
            y + 0.075,
            f"{row['first_answer_ms']:.0f} ms first answer",
            fontsize=13,
            color=TEXT,
            transform=ax.transAxes,
            zorder=4,
        )
        ax.text(
            x + 0.03,
            y + 0.04,
            f"{row['sustained_tok_s']:.1f} sustained tok/s",
            fontsize=13,
            color=TEXT,
            transform=ax.transAxes,
            zorder=4,
        )
        ax.text(
            x + 0.03,
            y + 0.01,
            f"{row['short_tok_s']:.1f} short tok/s",
            fontsize=12,
            color=SUBTEXT,
            transform=ax.transAxes,
            zorder=4,
        )

    _save(fig, output_dir, "27b_matchup_hero")


def _generate_thinking_delta(rows: list[dict[str, Any]], output_dir: Path) -> None:
    grouped: dict[str, dict[str, dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row["display_name"]), {})[str(row["thinking_mode"])] = row

    labels = list(grouped.keys())
    off_sustained = [grouped[label].get("off", {}).get("sustained_tok_s", 0.0) for label in labels]
    on_sustained = [grouped[label].get("on", {}).get("sustained_tok_s", 0.0) for label in labels]
    off_latency = [grouped[label].get("off", {}).get("first_answer_ms", 0.0) for label in labels]
    on_latency = [grouped[label].get("on", {}).get("first_answer_ms", 0.0) for label in labels]

    fig = plt.figure(figsize=FIGSIZE)
    _card_background(fig)
    title_ax = fig.add_axes([0, 0, 1, 1])
    title_ax.axis("off")
    title_ax.text(
        0.08,
        0.92,
        "Sustained Throughput & First-Answer Latency",
        fontsize=24,
        fontweight="bold",
        color=TEXT,
        transform=title_ax.transAxes,
    )
    title_ax.text(
        0.08,
        0.885,
        "Thinking on vs off. Base drops 19% sustained when thinking is off. Opus stays flat.",
        fontsize=12,
        color=SUBTEXT,
        transform=title_ax.transAxes,
    )
    _hf_chip(title_ax, 0.80, 0.85)

    x = np.arange(len(labels))
    width = 0.28
    ax_speed = fig.add_axes([0.08, 0.14, 0.38, 0.66])
    ax_latency = fig.add_axes([0.54, 0.14, 0.38, 0.66])
    for axis in (ax_speed, ax_latency):
        axis.set_facecolor(CARD)
        axis.grid(True, axis="y", color=GRID)
        for spine in axis.spines.values():
            spine.set_visible(False)

    ax_speed.bar(x - width / 2, off_sustained, width, color=BASE, label="thinking off")
    ax_speed.bar(x + width / 2, on_sustained, width, color="#14B8A6", label="thinking on")
    ax_speed.set_xticks(x)
    ax_speed.set_xticklabels(["Base", "Opus v2"][: len(labels)], fontsize=13)
    ax_speed.set_ylabel("Sustained tok/s", fontsize=12, color=TEXT)
    ax_speed.set_title("Sustained Throughput", fontsize=18, color=TEXT, loc="left", pad=12)
    ax_speed.legend(frameon=False, loc="lower right")

    ax_latency.bar(x - width / 2, off_latency, width, color=OPUS, label="thinking off")
    ax_latency.bar(x + width / 2, on_latency, width, color="#FB923C", label="thinking on")
    ax_latency.set_xticks(x)
    ax_latency.set_xticklabels(["Base", "Opus v2"][: len(labels)], fontsize=13)
    ax_latency.set_ylabel("First answer ms", fontsize=12, color=TEXT)
    ax_latency.set_title("First-Answer Latency", fontsize=18, color=TEXT, loc="left", pad=12)
    ax_latency.legend(frameon=False, loc="upper right")

    _save(fig, output_dir, "27b_thinking_delta")


def _generate_tradeoff(rows: list[dict[str, Any]], output_dir: Path) -> None:
    fig = plt.figure(figsize=FIGSIZE)
    _card_background(fig)
    ax = fig.add_axes([0.10, 0.12, 0.82, 0.76])
    ax.set_facecolor(CARD)

    for row in rows:
        is_frontier = row.get("lane") == "frontier_27b"
        color = OPUS if "Opus" in str(row.get("display_name")) else (BASE if is_frontier else NEUTRAL)
        size = 120 + 6 * row["sustained_tok_s"]
        ax.scatter(
            row["first_answer_ms"],
            row["structured_json_tok_s"],
            s=size,
            color=color,
            alpha=0.85,
            edgecolors="white",
            linewidths=1.5,
        )
        if is_frontier:
            ax.annotate(
                f"{row['display_name']} ({row['thinking_mode']})",
                (row["first_answer_ms"], row["structured_json_tok_s"]),
                xytext=(8, 8),
                textcoords="offset points",
                fontsize=10,
                color=TEXT,
            )

    ax.set_title(
        "Latency vs Structured JSON Throughput",
        fontsize=26,
        loc="left",
        pad=20,
        color=TEXT,
    )
    ax.text(
        0.0,
        1.02,
        "Lower is faster. Higher is better structured-token throughput. Point size reflects sustained tok/s.",
        fontsize=12,
        color=SUBTEXT,
        transform=ax.transAxes,
    )
    ax.set_xlabel("First answer latency (ms)", fontsize=13, color=TEXT)
    ax.set_ylabel("Structured JSON tok/s", fontsize=13, color=TEXT)
    ax.grid(True, color=GRID)
    for spine in ax.spines.values():
        spine.set_visible(False)

    _save(fig, output_dir, "speed_vs_latency_tradeoff")


def _generate_ladder(rows: list[dict[str, Any]], output_dir: Path) -> None:
    sorted_rows = sorted(rows, key=lambda row: row["structured_json_tok_s"], reverse=True)
    labels = [
        f"{row['display_name']} ({row['thinking_mode']})"
        if row.get("lane") == "frontier_27b"
        else str(row["display_name"])
        for row in sorted_rows
    ]
    values = [row["structured_json_tok_s"] for row in sorted_rows]
    colors = [
        OPUS if "Opus" in str(row.get("display_name")) else (BASE if row.get("lane") == "frontier_27b" else NEUTRAL)
        for row in sorted_rows
    ]

    fig = plt.figure(figsize=FIGSIZE)
    _card_background(fig)
    ax = fig.add_axes([0.18, 0.10, 0.72, 0.80])
    ax.set_facecolor(CARD)
    y = np.arange(len(labels))
    ax.barh(y, values, color=colors, height=0.65)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=11)
    ax.invert_yaxis()
    ax.set_xlabel("Structured JSON tokens / second", fontsize=13, color=TEXT)
    ax.set_title(
        "Full MLX Token Ladder with 27B Matchup Highlighted",
        fontsize=25,
        loc="left",
        pad=20,
        color=TEXT,
    )
    ax.text(
        0.0,
        1.02,
        "Core MLX token benchmark plus the matched 27B frontier lane.",
        fontsize=12,
        color=SUBTEXT,
        transform=ax.transAxes,
    )
    ax.grid(True, axis="x", color=GRID)
    for spine in ax.spines.values():
        spine.set_visible(False)

    _save(fig, output_dir, "full_mlx_ladder")


def _generate_gate_appendix(rows: list[dict[str, Any]], output_dir: Path) -> None:
    if not rows:
        return

    fig = plt.figure(figsize=FIGSIZE)
    _card_background(fig)
    ax = fig.add_axes([0.08, 0.10, 0.84, 0.80])
    ax.set_facecolor(CARD)
    ax.axis("off")

    ax.text(
        0.00,
        0.97,
        "Appendix: External Gate",
        fontsize=26,
        fontweight="bold",
        color=TEXT,
        transform=ax.transAxes,
    )
    ax.text(
        0.00,
        0.93,
        "Optional validation layer. This is not the main benchmark score.",
        fontsize=12,
        color=SUBTEXT,
        transform=ax.transAxes,
    )

    y = 0.82
    for row in rows:
        accent = (
            GOOD
            if row.get("external_gate_usable") == "usable"
            else (WARN if row.get("external_gate_usable") == "usable_with_caveat" else BAD)
        )
        _panel(ax, 0.00, y - 0.10, 0.96, 0.12)
        ax.text(
            0.03,
            y - 0.01,
            f"{row['display_name']} ({row['thinking_mode']})",
            fontsize=15,
            fontweight="bold",
            color=TEXT,
            transform=ax.transAxes,
        )
        ax.text(
            0.03,
            y - 0.05,
            f"gate={row['gate_decision']}  usable={row['external_gate_usable']}",
            fontsize=12,
            color=accent,
            transform=ax.transAxes,
        )
        ax.text(
            0.48,
            y - 0.05,
            f"synthetic_rate={row['synthetic_rate']:.3f}",
            fontsize=12,
            color=TEXT,
            transform=ax.transAxes,
        )
        ax.text(
            0.70,
            y - 0.05,
            f"invalid_loc={row['invalid_location_rate']:.3f}",
            fontsize=12,
            color=TEXT,
            transform=ax.transAxes,
        )
        ax.text(
            0.84,
            y - 0.05,
            f"shares={row['share_count_5tick']:.0f}",
            fontsize=12,
            color=TEXT,
            transform=ax.transAxes,
        )
        y -= 0.15
        if y < 0.14:
            break

    _save(fig, output_dir, "gate_validation_appendix")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate benchmark-v2 social/mobile visuals")
    parser.add_argument(
        "--summary",
        type=Path,
        default=DEFAULT_BENCHMARKS_DIR / "benchmark_v2_token_summary.json",
    )
    parser.add_argument("--gate-summary", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_SOCIALS_DIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = _normalize_token_rows(_load_rows(args.summary))
    frontier = _frontier_rows(rows)
    _generate_hero(frontier, args.output_dir)
    _generate_thinking_delta(frontier, args.output_dir)
    _generate_tradeoff(rows, args.output_dir)
    _generate_ladder(rows, args.output_dir)

    if args.gate_summary is not None and args.gate_summary.exists():
        gate_rows = _normalize_gate_rows(_load_rows(args.gate_summary))
        _generate_gate_appendix(gate_rows, args.output_dir)

    print(args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
