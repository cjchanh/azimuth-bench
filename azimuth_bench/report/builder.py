"""Build static HTML and Markdown reports from a benchmarks run directory."""

from __future__ import annotations

import json
from html import escape
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from azimuth_bench.core.env import provider_id_from_env
from azimuth_bench.core.runtime import slugify
from azimuth_bench.schema.bundle import build_canonical_data_files
from azimuth_bench.schema.protocol_manifest import build_protocol_manifest
from azimuth_bench.site.contract import build_site_manifest

BG = "#0b0f14"
PANEL = "#111821"
PANEL_ALT = "#0f151d"
BORDER = "#273241"
TEXT = "#e7edf5"
MUTED = "#93a0b3"
ACCENT = "#7aa2d6"
ACCENT_SOFT = "#3f5f87"
GOOD = "#95d5b2"
WARN = "#f4c27a"


def _schema_version_display(run_meta: dict[str, Any]) -> str:
    """Prefer current key; accept legacy bundles that only set ``signalbench_schema_version``."""
    return str(run_meta.get("azimuth_bench_schema_version") or run_meta.get("signalbench_schema_version") or "")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _metric_card(label: str, value: str, sub: str = "") -> str:
    sub_html = f"<div class='metric-sub'>{escape(sub)}</div>" if sub else ""
    return (
        "<div class='metric-card'>"
        f"<div class='metric-label'>{escape(label)}</div>"
        f"<div class='metric-value'>{escape(value)}</div>"
        f"{sub_html}"
        "</div>"
    )


def _shared_css() -> str:
    return f"""
    :root {{
      --bg: {BG};
      --panel: {PANEL};
      --panel-alt: {PANEL_ALT};
      --border: {BORDER};
      --text: {TEXT};
      --muted: {MUTED};
      --accent: {ACCENT};
      --accent-soft: {ACCENT_SOFT};
      --good: {GOOD};
      --warn: {WARN};
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: radial-gradient(circle at top left, rgba(122,162,214,0.08), transparent 28%), var(--bg);
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      line-height: 1.5;
      min-height: 100vh;
      padding: 32px 28px 64px;
    }}
    a {{ color: var(--accent); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      gap: 24px;
      padding-bottom: 18px;
      border-bottom: 1px solid var(--border);
      margin-bottom: 28px;
    }}
    .title-block h1 {{
      font-size: 22px;
      font-weight: 600;
      letter-spacing: -0.02em;
      color: var(--text);
    }}
    .subtitle {{
      margin-top: 6px;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
    }}
    nav {{
      display: flex;
      gap: 14px;
      font-size: 13px;
      color: var(--muted);
    }}
    .hero-grid, .metrics-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
      gap: 12px;
      margin-bottom: 24px;
    }}
    .metric-card, .panel {{
      background: linear-gradient(180deg, rgba(255,255,255,0.01), rgba(255,255,255,0)), var(--panel);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 16px;
    }}
    .metric-label, .section-kicker {{
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
    }}
    .metric-value {{
      margin-top: 6px;
      font-size: 26px;
      font-weight: 600;
      font-variant-numeric: tabular-nums;
      color: var(--accent);
    }}
    .metric-sub {{
      margin-top: 4px;
      color: var(--muted);
      font-size: 12px;
    }}
    .section {{
      margin-bottom: 24px;
    }}
    .section h2 {{
      margin-bottom: 12px;
      font-size: 15px;
      font-weight: 600;
      color: var(--text);
    }}
    .section p, .evidence-list li {{
      color: var(--muted);
      font-size: 13px;
    }}
    .panel img {{
      width: 100%;
      height: auto;
      display: block;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }}
    th, td {{
      padding: 10px 12px;
      border-bottom: 1px solid var(--border);
      text-align: left;
    }}
    th {{
      color: var(--muted);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      font-weight: 600;
    }}
    td.metric {{
      font-variant-numeric: tabular-nums;
      color: var(--text);
    }}
    .split {{
      display: grid;
      grid-template-columns: 1.2fr 0.8fr;
      gap: 16px;
    }}
    .list {{
      list-style: none;
      display: grid;
      gap: 10px;
    }}
    .list li {{
      padding: 12px 14px;
      border-radius: 10px;
      border: 1px solid var(--border);
      background: var(--panel-alt);
    }}
    .mono {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }}
    footer {{
      margin-top: 32px;
      padding-top: 14px;
      border-top: 1px solid var(--border);
      color: var(--muted);
      font-size: 12px;
    }}
    @media (max-width: 900px) {{
      header, .split {{ grid-template-columns: 1fr; display: block; }}
      nav {{ margin-top: 12px; flex-wrap: wrap; }}
    }}
    """


def _render_table(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> str:
    head = "".join(f"<th>{escape(label)}</th>" for label, _key in columns)
    body_rows: list[str] = []
    for row in rows:
        cells = []
        for _label, key in columns:
            value = row.get(key, "")
            cells.append(f"<td class='metric'>{escape(str(value))}</td>")
        body_rows.append(f"<tr>{''.join(cells)}</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body_rows)}</tbody></table>"


def _render_summary_md(summary_rows: list[dict[str, Any]], *, integrity_ok: bool, site_manifest: dict[str, Any]) -> str:
    lines: list[str] = [
        "# Azimuth Report summary",
        "",
        "## Measurement status",
        "",
        f"- Integrity gate: **{'PASS' if integrity_ok else 'FAIL'}**",
        f"- Row count: **{len(summary_rows)}**",
        "",
        "## Implemented and tested",
        "",
        "- Canonical per-run JSON bundle emitted under `report/data/runs/<artifact_key>/`",
        "- Static pages emitted for latest report, leaderboard, compare, run detail, and machine detail",
        "",
        "## Designed / unverified",
        "",
        "- Additional adapters beyond MLX",
        "- Full hosted app beyond static-first site data contract",
        "",
        "## Site manifest",
        "",
        f"- Status: `{site_manifest.get('status')}`",
        f"- Run detail pages: `{site_manifest.get('run_detail', {}).get('count', 0)}`",
        f"- Machine detail pages: `{site_manifest.get('machine_detail', {}).get('count', 0)}`",
        "",
        "## Leaderboard snapshot",
        "",
        "| Display | Lane | Think | JSON tok/s | Sustained tok/s | First answer ms |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    ranked = sorted(summary_rows, key=lambda row: float(row.get("structured_json_tok_s") or 0.0), reverse=True)[:10]
    for row in ranked:
        lines.append(
            f"| {row.get('display_name', '')} | {row.get('lane', '')} | {row.get('thinking_mode', '')} | "
            f"{row.get('structured_json_tok_s', '')} | {row.get('sustained_tok_s', '')} | {row.get('first_answer_ms', '')} |"
        )
    lines.append("")
    return "\n".join(lines)


def _chart_bar_svg(out_path: Path, rows: list[dict[str, Any]], key: str, title: str, label: str) -> None:
    if not rows:
        return
    ranked = sorted(rows, key=lambda r: float(r.get(key) or 0.0), reverse=True)[:12]
    labels = [str(r.get("display_name", "")) for r in ranked]
    values = [float(r.get(key) or 0.0) for r in ranked]
    fig, ax = plt.subplots(figsize=(10, max(4.0, 0.45 * len(ranked))), dpi=120)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(PANEL)
    ax.barh(labels[::-1], values[::-1], color=ACCENT)
    ax.set_title(title, color=TEXT, fontsize=11)
    ax.set_xlabel(label, color=TEXT)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.grid(axis="x", linestyle="--", alpha=0.2, color=ACCENT_SOFT)
    for spine in ax.spines.values():
        spine.set_color(BORDER)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, format="svg", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


def _chart_scatter_svg(out_path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    fig, ax = plt.subplots(figsize=(8.5, 5.5), dpi=120)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(PANEL)
    for row in rows:
        ax.scatter(
            float(row.get("first_answer_ms") or 0.0),
            float(row.get("structured_json_tok_s") or 0.0),
            color=ACCENT,
            alpha=0.8,
            s=36,
        )
    ax.set_xlabel("First answer ms", color=TEXT)
    ax.set_ylabel("Structured JSON tok/s", color=TEXT)
    ax.set_title("Throughput vs first-answer latency", color=TEXT, fontsize=11)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.grid(alpha=0.2, linestyle="--", color=ACCENT_SOFT)
    for spine in ax.spines.values():
        spine.set_color(BORDER)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, format="svg", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


def _chart_frontier_svg(out_path: Path, rows: list[dict[str, Any]]) -> None:
    frontier = [row for row in rows if row.get("lane") == "frontier_27b"]
    if not frontier:
        return
    labels = [f"{row.get('display_name')} [{row.get('thinking_mode')}]" for row in frontier]
    values = [float(row.get("structured_json_tok_s") or 0.0) for row in frontier]
    fig, ax = plt.subplots(figsize=(9, 4.8), dpi=120)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(PANEL)
    ax.bar(labels, values, color=[ACCENT, ACCENT_SOFT, WARN, GOOD][: len(values)])
    ax.set_ylabel("Structured JSON tok/s", color=TEXT)
    ax.set_title("Frontier 27B comparison", color=TEXT, fontsize=11)
    ax.tick_params(axis="x", rotation=10, colors=MUTED, labelsize=9)
    ax.tick_params(axis="y", colors=MUTED, labelsize=9)
    ax.grid(axis="y", alpha=0.2, linestyle="--", color=ACCENT_SOFT)
    for spine in ax.spines.values():
        spine.set_color(BORDER)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, format="svg", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


def _render_index_html(
    summary_rows: list[dict[str, Any]], bundle: dict[str, Any], site_manifest: dict[str, Any]
) -> str:
    run_meta = bundle.get("run.json") or {}
    integrity_ok = bool((bundle.get("integrity") or {}).get("ok"))
    top_rows = sorted(summary_rows, key=lambda row: float(row.get("structured_json_tok_s") or 0.0), reverse=True)[:5]
    ranked_table = _render_table(
        top_rows,
        [
            ("Model", "display_name"),
            ("Lane", "lane"),
            ("Think", "thinking_mode"),
            ("JSON tok/s", "structured_json_tok_s"),
            ("First answer ms", "first_answer_ms"),
        ],
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Azimuth Bench</title>
  <style>{_shared_css()}</style>
</head>
<body>
  <header>
    <div class="title-block">
      <h1>Azimuth Bench</h1>
      <div class="subtitle">Azimuth Report · portable inference benchmark surface</div>
    </div>
    <nav>
      <a href="index.html">Latest</a>
      <a href="leaderboard.html">Leaderboard</a>
      <a href="compare.html">Compare</a>
    </nav>
  </header>
  <section class="hero-grid">
    {_metric_card("Rows", str(len(summary_rows)), f"lane={run_meta.get('lane')}")}
    {_metric_card("Integrity", "PASS" if integrity_ok else "BLOCKED", "fail-closed schema gate")}
    {_metric_card("Schema", _schema_version_display(run_meta), "canonical bundle")}
    {_metric_card("Run pages", str(site_manifest.get("run_detail", {}).get("count", 0)), "artifact detail pages")}
  </section>
  <section class="split section">
    <div class="panel">
      <div class="section-kicker">Chart</div>
      <h2>Structured throughput leaderboard</h2>
      <img src="charts/throughput_structured.svg" alt="Structured throughput" />
    </div>
    <div class="panel">
      <div class="section-kicker">Top rows</div>
      <h2>Latest leaderboard slice</h2>
      {ranked_table}
    </div>
  </section>
  <section class="split section">
    <div class="panel">
      <div class="section-kicker">Tradeoff</div>
      <h2>Latency vs throughput</h2>
      <img src="charts/latency_tradeoff.svg" alt="Latency tradeoff" />
    </div>
    <div class="panel">
      <div class="section-kicker">Evidence</div>
      <h2>Bundle</h2>
      <ul class="list evidence-list">
        <li><span class="mono">report/data/run.json</span><br/>run metadata and provenance status</li>
        <li><span class="mono">report/data/summary.json</span><br/>canonical leaderboard rows</li>
        <li><span class="mono">report/data/runs/&lt;artifact_key&gt;/</span><br/>per-run run/summary/machine/provider/model/cases bundle</li>
        <li><span class="mono">report/data/site_manifest.json</span><br/>hosted site route contract</li>
      </ul>
    </div>
  </section>
  <footer>Generated from real benchmark artifacts. Historical runs may lack exact benchmark commit SHA or invocation command; those gaps are surfaced in the bundle.</footer>
</body>
</html>"""


def _render_leaderboard_html(summary_rows: list[dict[str, Any]]) -> str:
    ranked = sorted(summary_rows, key=lambda row: float(row.get("structured_json_tok_s") or 0.0), reverse=True)
    table = _render_table(
        ranked,
        [
            ("Model", "display_name"),
            ("Lane", "lane"),
            ("Think", "thinking_mode"),
            ("Short tok/s", "short_tok_s"),
            ("JSON tok/s", "structured_json_tok_s"),
            ("Sustained tok/s", "sustained_tok_s"),
            ("First answer ms", "first_answer_ms"),
        ],
    )
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Azimuth Leaderboard</title><style>{_shared_css()}</style></head>
<body><header><div class="title-block"><h1>Azimuth Leaderboard</h1><div class="subtitle">Azimuth Report · sortable table + JSON contract</div></div><nav><a href="index.html">Latest</a><a href="leaderboard.html">Leaderboard</a><a href="compare.html">Compare</a></nav></header>
<section class="section"><div class="panel">{table}</div></section>
<footer>Static-first leaderboard sourced from report/data/leaderboard.json.</footer></body></html>"""


def _render_compare_html(compare_payload: dict[str, Any]) -> str:
    comparisons = compare_payload.get("frontier_pairs") or []
    items = []
    for item in comparisons:
        items.append(
            "<li>"
            f"<strong>{escape(item.get('label', 'pair'))}</strong><br/>"
            f"JSON tok/s delta: <span class='mono'>{escape(str(item.get('structured_json_tok_s_delta')))}</span><br/>"
            f"Sustained tok/s delta: <span class='mono'>{escape(str(item.get('sustained_tok_s_delta')))}</span><br/>"
            f"First answer ms delta: <span class='mono'>{escape(str(item.get('first_answer_ms_delta')))}</span>"
            "</li>"
        )
    body = "".join(items) if items else "<li>No compare pairs available.</li>"
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Azimuth Compare</title><style>{_shared_css()}</style></head>
<body><header><div class="title-block"><h1>Azimuth Compare</h1><div class="subtitle">Azimuth Report · pairwise diffs over the current data</div></div><nav><a href="index.html">Latest</a><a href="leaderboard.html">Leaderboard</a><a href="compare.html">Compare</a></nav></header>
<section class="split section"><div class="panel"><div class="section-kicker">Chart</div><h2>Frontier 27B comparison</h2><img src="charts/frontier_compare.svg" alt="Frontier comparison"/></div><div class="panel"><div class="section-kicker">Pairs</div><h2>Current comparison set</h2><ul class="list">{body}</ul></div></section>
<footer>Static compare view. Full interactive selection remains designed/unverified.</footer></body></html>"""


def _render_run_detail_html(artifact_key: str, bundle: dict[str, Any]) -> str:
    run_data = bundle["run.json"]
    summary = bundle["summary.json"].get("metrics", {})
    model = bundle["model.json"]
    evidence = run_data.get("artifact_provenance", {})
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{escape(artifact_key)}</title><style>{_shared_css()}</style></head>
<body><header><div class="title-block"><h1>{escape(str(model.get("display_name", artifact_key)))}</h1><div class="subtitle">{escape(artifact_key)}</div></div><nav><a href="../index.html">Latest</a><a href="../leaderboard.html">Leaderboard</a><a href="../compare.html">Compare</a></nav></header>
<section class="hero-grid">
  {_metric_card("JSON tok/s", str(summary.get("structured_json_tok_s", "")))}
  {_metric_card("Sustained tok/s", str(summary.get("sustained_tok_s", "")))}
  {_metric_card("First answer ms", str(summary.get("first_answer_ms", "")))}
  {_metric_card("Think", str(model.get("thinking_mode", "")))}
</section>
<section class="split section">
  <div class="panel"><div class="section-kicker">Model</div><h2>Model identity</h2><ul class="list"><li>Model ID: <span class="mono">{escape(str(model.get("model_id", "")))}</span></li><li>Target model: <span class="mono">{escape(str(model.get("target_model_id", "")))}</span></li><li>Served models: <span class="mono">{escape(str(model.get("served_model_ids", [])))}</span></li></ul></div>
  <div class="panel"><div class="section-kicker">Provenance</div><h2>Integrity surface</h2><ul class="list"><li>Valid run: <span class="mono">{escape(str(evidence.get("valid_run")))}</span></li><li>Comparable: <span class="mono">{escape(str(evidence.get("comparable")))}</span></li><li>Gaps: <span class="mono">{escape(str(evidence.get("provenance_gaps", [])))}</span></li></ul></div>
</section>
<footer>Per-run canonical bundle: <span class="mono">report/data/runs/{escape(artifact_key)}/</span></footer></body></html>"""


def _render_machine_html(machine_key: str, machine_profile: dict[str, Any]) -> str:
    items = "".join(
        f"<li>{escape(str(key))}: <span class='mono'>{escape(str(value))}</span></li>"
        for key, value in sorted(machine_profile.items())
    )
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{escape(machine_key)}</title><style>{_shared_css()}</style></head>
<body><header><div class="title-block"><h1>Machine detail</h1><div class="subtitle">{escape(machine_key)}</div></div><nav><a href="../index.html">Latest</a><a href="../leaderboard.html">Leaderboard</a><a href="../compare.html">Compare</a></nav></header>
<section class="section"><div class="panel"><ul class="list">{items}</ul></div></section>
<footer>Representative machine snapshot from benchmark receipts.</footer></body></html>"""


def _provider_key(provider_payload: dict[str, Any]) -> str:
    provider_kind = str(provider_payload.get("provider_kind") or "unknown")
    provider_id = str(provider_payload.get("provider_id") or provider_kind)
    if provider_id == provider_kind:
        return slugify(provider_kind)
    return slugify(f"{provider_kind}_{provider_id}")


def _protocol_key(protocol_id: str) -> str:
    return slugify(protocol_id or "unknown_protocol")


def _provider_index_payload(run_bundles: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, dict[str, Any]] = {}
    for run_bundle in run_bundles:
        provider = run_bundle.get("provider.json") or {}
        model = run_bundle.get("model.json") or {}
        summary_metrics = (run_bundle.get("summary.json") or {}).get("metrics") or {}
        key = _provider_key(provider)
        entry = grouped.setdefault(
            key,
            {
                "provider_key": key,
                "provider_id": provider.get("provider_id"),
                "provider_kind": provider.get("provider_kind"),
                "adapter_name": provider.get("adapter_name"),
                "capabilities": provider.get("capabilities"),
                "run_count": 0,
                "comparable_run_count": 0,
                "models": [],
            },
        )
        entry["run_count"] += 1
        if summary_metrics.get("comparable"):
            entry["comparable_run_count"] += 1
        entry["models"].append(
            {
                "display_name": model.get("display_name"),
                "artifact_key": summary_metrics.get("artifact_key"),
            }
        )
    rows = sorted(grouped.values(), key=lambda row: (str(row.get("provider_kind")), str(row.get("provider_id"))))
    return {"providers": rows}


def _protocol_index_payload(run_bundles: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, dict[str, Any]] = {}
    for run_bundle in run_bundles:
        cases = run_bundle.get("cases.json") or {}
        model = run_bundle.get("model.json") or {}
        summary_metrics = (run_bundle.get("summary.json") or {}).get("metrics") or {}
        protocol_id = str(cases.get("protocol_id") or "unknown_protocol")
        key = _protocol_key(protocol_id)
        entry = grouped.setdefault(
            key,
            {
                "protocol_key": key,
                "protocol_id": protocol_id,
                "prompt_set_id": cases.get("prompt_set_id"),
                "suite_family": cases.get("suite_family"),
                "machine_classes": [],
                "run_count": 0,
                "models": [],
            },
        )
        machine_class = summary_metrics.get("machine_class")
        if machine_class and machine_class not in entry["machine_classes"]:
            entry["machine_classes"].append(machine_class)
        entry["run_count"] += 1
        entry["models"].append(
            {
                "display_name": model.get("display_name"),
                "artifact_key": summary_metrics.get("artifact_key"),
            }
        )
    rows = sorted(grouped.values(), key=lambda row: str(row.get("protocol_id")))
    return {"protocols": rows}


def _render_provider_html(provider_payload: dict[str, Any]) -> str:
    model_items = "".join(
        f"<li>{escape(str(item.get('display_name', '')))}"
        f"<br/><span class='mono'>{escape(str(item.get('artifact_key', '')))}</span></li>"
        for item in provider_payload.get("models", [])
    )
    capabilities = provider_payload.get("capabilities")
    capabilities_text = (
        escape(json.dumps(capabilities, sort_keys=True)) if capabilities is not None else "historical_or_unspecified"
    )
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{escape(str(provider_payload.get("provider_key")))}</title><style>{_shared_css()}</style></head>
<body><header><div class="title-block"><h1>Provider detail</h1><div class="subtitle">{escape(str(provider_payload.get("provider_id")))}</div></div><nav><a href="../index.html">Latest</a><a href="../leaderboard.html">Leaderboard</a><a href="../compare.html">Compare</a></nav></header>
<section class="hero-grid">
  {_metric_card("Runs", str(provider_payload.get("run_count", 0)))}
  {_metric_card("Comparable", str(provider_payload.get("comparable_run_count", 0)))}
  {_metric_card("Kind", str(provider_payload.get("provider_kind", "")))}
  {_metric_card("Adapter", str(provider_payload.get("adapter_name", "historical_or_unspecified")))}
</section>
<section class="split section">
  <div class="panel"><div class="section-kicker">Capabilities</div><h2>Declared surface</h2><p class="mono">{capabilities_text}</p></div>
  <div class="panel"><div class="section-kicker">Runs</div><h2>Artifacts</h2><ul class="list">{model_items}</ul></div>
</section>
<footer>Provider pages are derived from report/data/runs/*/provider.json.</footer></body></html>"""


def _render_protocol_html(protocol_payload: dict[str, Any]) -> str:
    model_items = "".join(
        f"<li>{escape(str(item.get('display_name', '')))}"
        f"<br/><span class='mono'>{escape(str(item.get('artifact_key', '')))}</span></li>"
        for item in protocol_payload.get("models", [])
    )
    machine_text = ", ".join(escape(str(x)) for x in protocol_payload.get("machine_classes", [])) or "unknown"
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{escape(str(protocol_payload.get("protocol_id")))}</title><style>{_shared_css()}</style></head>
<body><header><div class="title-block"><h1>Protocol detail</h1><div class="subtitle">{escape(str(protocol_payload.get("protocol_id")))}</div></div><nav><a href="../index.html">Latest</a><a href="../leaderboard.html">Leaderboard</a><a href="../compare.html">Compare</a></nav></header>
<section class="hero-grid">
  {_metric_card("Runs", str(protocol_payload.get("run_count", 0)))}
  {_metric_card("Suite", str(protocol_payload.get("suite_family", "")))}
  {_metric_card("Prompt set", str(protocol_payload.get("prompt_set_id", "")))}
  {_metric_card("Machine classes", str(len(protocol_payload.get("machine_classes", []))))}
</section>
<section class="split section">
  <div class="panel"><div class="section-kicker">Protocol</div><h2>Run conditions</h2><p class="mono">{machine_text}</p></div>
  <div class="panel"><div class="section-kicker">Runs</div><h2>Artifacts</h2><ul class="list">{model_items}</ul></div>
</section>
<footer>Protocol pages are derived from per-run cases/summary bundle data.</footer></body></html>"""


def _compare_payload(summary_rows: list[dict[str, Any]]) -> dict[str, Any]:
    frontier = [row for row in summary_rows if row.get("lane") == "frontier_27b"]
    pairs: list[dict[str, Any]] = []
    index = {(row.get("display_name"), row.get("thinking_mode")): row for row in frontier}
    wanted = [("on", "thinking_on"), ("off", "thinking_off")]
    for thinking_mode, label in wanted:
        base = index.get(("Qwen3.5 27B Base", thinking_mode))
        distilled = index.get(("Qwen3.5 27B Opus Distilled v2", thinking_mode))
        if not base or not distilled:
            continue
        pairs.append(
            {
                "label": label,
                "structured_json_tok_s_delta": round(
                    float(distilled.get("structured_json_tok_s") or 0.0)
                    - float(base.get("structured_json_tok_s") or 0.0),
                    1,
                ),
                "sustained_tok_s_delta": round(
                    float(distilled.get("sustained_tok_s") or 0.0) - float(base.get("sustained_tok_s") or 0.0),
                    1,
                ),
                "first_answer_ms_delta": round(
                    float(distilled.get("first_answer_ms") or 0.0) - float(base.get("first_answer_ms") or 0.0),
                    1,
                ),
            }
        )
    return {"frontier_pairs": pairs}


def build_report(
    run_dir: Path,
    *,
    repo_root: Path | None = None,
    provider_id: str | None = None,
    provider_id_source: str | None = None,
) -> Path:
    """Write report under ``run_dir/report/``. Returns report directory path."""
    run_dir = run_dir.resolve()
    resolved_provider = provider_id
    resolved_source = provider_id_source
    if resolved_provider is None and resolved_source is None:
        env_pid = provider_id_from_env()
        if env_pid is not None:
            resolved_provider = env_pid
            resolved_source = "env"
    elif resolved_provider is not None and resolved_source is None:
        resolved_source = "cli"

    bundle = build_canonical_data_files(
        run_dir,
        repo_root=repo_root,
        provider_id=resolved_provider,
        provider_id_source=resolved_source,
    )
    report_root = run_dir / "report"
    data_dir = report_root / "data"
    charts_dir = report_root / "charts"
    runs_dir = report_root / "runs"
    machines_dir = report_root / "machines"
    providers_dir = report_root / "providers"
    protocols_dir = report_root / "protocols"
    runs_dir.mkdir(parents=True, exist_ok=True)
    machines_dir.mkdir(parents=True, exist_ok=True)
    providers_dir.mkdir(parents=True, exist_ok=True)
    protocols_dir.mkdir(parents=True, exist_ok=True)

    summary_rows = (bundle.get("summary.json") or {}).get("rows") or []
    if not isinstance(summary_rows, list):
        summary_rows = []
    compare_payload = _compare_payload(summary_rows)
    run_bundles = bundle.get("run_bundles") or []
    provider_index = _provider_index_payload(run_bundles)
    protocol_index = _protocol_index_payload(run_bundles)

    for name, payload in bundle.items():
        if name in {"integrity", "run_bundles"}:
            continue
        _write_json(data_dir / name, payload)

    run_meta_top = bundle.get("run.json") or {}
    leaderboard_payload = {
        "azimuth_bench_schema_version": _schema_version_display(run_meta_top),
        "rows": sorted(summary_rows, key=lambda row: float(row.get("structured_json_tok_s") or 0.0), reverse=True),
    }
    _write_json(data_dir / "leaderboard.json", leaderboard_payload)
    _write_json(data_dir / "compare.json", compare_payload)
    _write_json(data_dir / "latest.json", {"summary": bundle.get("summary.json"), "run": bundle.get("run.json")})
    _write_json(data_dir / "providers" / "index.json", provider_index)
    _write_json(data_dir / "protocols" / "index.json", protocol_index)

    run_index: list[dict[str, Any]] = []
    for run_bundle in run_bundles:
        artifact_key = str((run_bundle.get("run.json") or {}).get("artifact_key") or "unknown")
        run_path = data_dir / "runs" / artifact_key
        for name, payload in run_bundle.items():
            _write_json(run_path / name, payload)
        run_index.append(
            {
                "artifact_key": artifact_key,
                "display_name": (run_bundle.get("model.json") or {}).get("display_name"),
                "path": f"runs/{artifact_key}/run.json",
            }
        )
        (runs_dir / f"{artifact_key}.html").write_text(
            _render_run_detail_html(artifact_key, run_bundle),
            encoding="utf-8",
        )
    _write_json(data_dir / "runs" / "index.json", {"runs": run_index})

    machines_payload = bundle.get("machines.json") or {"machines": {}}
    for machine_key, machine_profile in (machines_payload.get("machines") or {}).items():
        (machines_dir / f"{machine_key}.html").write_text(
            _render_machine_html(machine_key, machine_profile),
            encoding="utf-8",
        )

    for provider_payload in provider_index["providers"]:
        provider_key = str(provider_payload.get("provider_key") or "unknown")
        _write_json(data_dir / "providers" / f"{provider_key}.json", provider_payload)
        (providers_dir / f"{provider_key}.html").write_text(
            _render_provider_html(provider_payload),
            encoding="utf-8",
        )

    for protocol_payload in protocol_index["protocols"]:
        protocol_key = str(protocol_payload.get("protocol_key") or "unknown_protocol")
        protocol_manifest = build_protocol_manifest(
            protocol={
                "protocol_id": protocol_payload.get("protocol_id"),
                "prompt_set_id": protocol_payload.get("prompt_set_id"),
                "machine_class": ", ".join(protocol_payload.get("machine_classes", [])) or None,
            },
            suite_family=str(protocol_payload.get("suite_family") or "unknown"),
        )
        _write_json(
            data_dir / "protocols" / f"{protocol_key}.json",
            {
                **protocol_payload,
                "manifest": protocol_manifest,
            },
        )
        (protocols_dir / f"{protocol_key}.html").write_text(
            _render_protocol_html(protocol_payload),
            encoding="utf-8",
        )

    _chart_bar_svg(
        charts_dir / "throughput_structured.svg",
        summary_rows,
        "structured_json_tok_s",
        "Structured throughput",
        "Structured JSON tok/s",
    )
    _chart_scatter_svg(charts_dir / "latency_tradeoff.svg", summary_rows)
    _chart_frontier_svg(charts_dir / "frontier_compare.svg", summary_rows)

    site_manifest = build_site_manifest(run_dir, bundle)
    _write_json(data_dir / "site_manifest.json", site_manifest)

    (report_root / "summary.md").write_text(
        _render_summary_md(
            summary_rows, integrity_ok=bool((bundle.get("integrity") or {}).get("ok")), site_manifest=site_manifest
        ),
        encoding="utf-8",
    )
    (report_root / "index.html").write_text(_render_index_html(summary_rows, bundle, site_manifest), encoding="utf-8")
    (report_root / "leaderboard.html").write_text(_render_leaderboard_html(summary_rows), encoding="utf-8")
    (report_root / "compare.html").write_text(_render_compare_html(compare_payload), encoding="utf-8")

    return report_root
