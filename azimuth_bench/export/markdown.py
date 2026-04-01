"""Deterministic Markdown export from built report ``data/`` JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_markdown_export(*, report_data_dir: Path, output_path: Path) -> Path:
    """Write a short Markdown summary from ``report_data_dir`` (expects ``summary.json``)."""
    report_data_dir = report_data_dir.resolve()
    summary_path = report_data_dir / "summary.json"
    if not summary_path.is_file():
        raise FileNotFoundError(f"missing summary.json under {report_data_dir}")
    summary: dict[str, Any] = json.loads(summary_path.read_text(encoding="utf-8"))
    rows = summary.get("rows") if isinstance(summary.get("rows"), list) else []
    lines: list[str] = [
        "# Azimuth Bench export",
        "",
        f"- Rows: {len(rows)}",
        "",
    ]
    for row in rows[:50]:
        if not isinstance(row, dict):
            continue
        mid = row.get("model_id", "")
        st = row.get("structured_json_tok_s")
        tok = row.get("sustained_tok_s")
        comp = row.get("comparable")
        lines.append(f"- **{mid}** — structured ~{st} tok/s, sustained ~{tok} tok/s, comparable={comp}")
    lines.append("")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path
