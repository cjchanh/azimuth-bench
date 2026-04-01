#!/usr/bin/env python3
"""Optional external Agent Civilization gate for benchmark-v2."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

import aiohttp

from benchmarking.roster import chat_template_kwargs_for_thinking_mode
from benchmarking.utils import ROOT, coerce_message_text

PROMPT_MODE_SINGLE_USER = "single_user"
PROMPT_MODE_SYSTEM_USER = "system_user"
STAGE1_PROMPT = 'Respond with exactly this JSON and nothing else: {"test": true}'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the cross-family MLX gate protocol.",
    )
    parser.add_argument("--port", type=int, default=8899, help="MLX server port.")
    parser.add_argument("--model", required=True, help="Expected model id.")
    parser.add_argument("--output-dir", required=True, help="Directory for gate artifacts.")
    parser.add_argument("--seed", type=int, default=42, help="Gate run seed.")
    parser.add_argument("--ticks", type=int, default=5, help="Gate run length.")
    parser.add_argument("--agent-count", type=int, default=10, help="Gate agent count.")
    parser.add_argument(
        "--prompt-mode",
        choices=["auto", PROMPT_MODE_SINGLE_USER, PROMPT_MODE_SYSTEM_USER],
        default="auto",
        help="Chat framing to test. auto tries single_user first, then system_user.",
    )
    parser.add_argument(
        "--thinking-mode",
        choices=["default", "on", "off"],
        default="default",
        help="Thinking mode to request from the MLX chat template.",
    )
    return parser.parse_args()


def _strip_code_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```") and stripped.endswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 3:
            return "\n".join(lines[1:-1]).strip()
    return stripped


def _parse_json_object(text: str) -> dict[str, Any] | None:
    stripped = _strip_code_fence(text).strip()
    if not stripped:
        return None
    candidates = [stripped]
    first_brace = stripped.find("{")
    last_brace = stripped.rfind("}")
    if 0 <= first_brace < last_brace:
        candidate = stripped[first_brace : last_brace + 1].strip()
        if candidate not in candidates:
            candidates.append(candidate)
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def _parse_probe_message(raw_text: str, raw_reasoning: str) -> tuple[dict[str, Any] | None, str | None]:
    candidates: list[tuple[str, str]] = []
    if raw_text.strip():
        candidates.append(("content", raw_text))
    if raw_reasoning.strip():
        candidates.append(("reasoning", raw_reasoning))
    combined_parts = [part for part in (raw_text.strip(), raw_reasoning.strip()) if part]
    if len(combined_parts) > 1:
        candidates.append(("combined", "\n".join(combined_parts)))
    for source, candidate in candidates:
        parsed = _parse_json_object(candidate)
        if parsed is not None:
            return parsed, source
    return None, None


async def _probe(
    endpoint: str,
    model: str,
    prompt_mode: str,
    thinking_mode: str,
) -> dict[str, Any]:
    if prompt_mode == PROMPT_MODE_SYSTEM_USER:
        messages = [
            {"role": "system", "content": "Return JSON only. No prose."},
            {"role": "user", "content": STAGE1_PROMPT},
        ]
    else:
        messages = [{"role": "user", "content": STAGE1_PROMPT}]

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": 0.0,
        "max_tokens": 64,
        "stream": False,
    }
    chat_template_kwargs = chat_template_kwargs_for_thinking_mode(thinking_mode)
    if chat_template_kwargs is not None:
        payload["chat_template_kwargs"] = chat_template_kwargs

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
        async with session.post(endpoint, json=payload) as resp:
            resp.raise_for_status()
            body = await resp.json(content_type=None)

    message = body["choices"][0]["message"]
    raw_text = coerce_message_text(message.get("content"))
    raw_reasoning = coerce_message_text(message.get("reasoning"))
    parsed_value, parsed_source = _parse_probe_message(raw_text, raw_reasoning)
    return {
        "prompt_mode": prompt_mode,
        "thinking_mode": thinking_mode,
        "raw_text": raw_text,
        "raw_reasoning": raw_reasoning,
        "parsed": parsed_value is not None,
        "parsed_source": parsed_source,
        "parsed_value": parsed_value,
        "matches_expected": parsed_value == {"test": True},
        "has_code_fence": raw_text.lstrip().startswith("```") or raw_reasoning.lstrip().startswith("```"),
    }


def _served_model(port: int) -> str:
    result = subprocess.run(
        [
            "python3",
            "-c",
            (
                "import json,sys,urllib.request;"
                f"print(json.load(urllib.request.urlopen('http://localhost:{port}/v1/models'))['data'][0]['id'])"
            ),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip()


def _agent_civ_root() -> Path:
    candidates = []
    env_root = os.environ.get("AGENT_CIV_ROOT")
    if env_root:
        candidates.append(Path(env_root).expanduser().resolve())
    candidates.append((ROOT.parent / "agent-civilization").resolve())
    for candidate in candidates:
        if (candidate / "scripts" / "run_experiment.py").is_file():
            return candidate
    raise RuntimeError(
        "Agent Civilization repo not found. Set AGENT_CIV_ROOT to a checkout with scripts/run_experiment.py."
    )


def _run_gate_experiment(
    *,
    port: int,
    model: str,
    output_dir: Path,
    seed: int,
    ticks: int,
    agent_count: int,
    prompt_mode: str,
    thinking_mode: str,
) -> Path:
    run_dir = output_dir / "run"
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    env = dict(os.environ)
    env["MODEL_ENDPOINT"] = f"http://localhost:{port}/v1/chat/completions"
    env["MODEL_ID"] = model
    env["ENDPOINT_FORMAT"] = "mlx_chat"
    env["PROMPT_MODE"] = prompt_mode
    env["MLX_CHAT_TEMPLATE_ARGS"] = json.dumps(
        chat_template_kwargs_for_thinking_mode(thinking_mode),
        sort_keys=True,
    )

    agent_civ_root = _agent_civ_root()
    proc = subprocess.run(
        [
            sys.executable,
            str(agent_civ_root / "scripts" / "run_experiment.py"),
            "--condition-label",
            "baseline-U",
            "--seed",
            str(seed),
            "--ticks",
            str(ticks),
            "--output-dir",
            str(run_dir),
            "--agent-count",
            str(agent_count),
            "--memory-mode",
            "off",
        ],
        cwd=agent_civ_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    (output_dir / "stage2_stdout.log").write_text(proc.stdout)
    (output_dir / "stage2_stderr.log").write_text(proc.stderr)
    if proc.returncode != 0:
        raise RuntimeError(f"Gate run failed with exit code {proc.returncode}")

    dbs = sorted(run_dir.glob("*.db"))
    if not dbs:
        raise RuntimeError("Gate run produced no DB")
    return dbs[0]


def _summarize_db(db_path: Path, *, ticks: int, agent_count: int) -> dict[str, Any]:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        status = conn.execute("SELECT status FROM run_metadata LIMIT 1").fetchone()[0]
        synthetic_failures = conn.execute(
            "SELECT count(*) FROM events WHERE reason IN ('PARSE_FAILURE','MODEL_CALL_FAILURE')"
        ).fetchone()[0]
        invalid_location = conn.execute("SELECT count(*) FROM events WHERE reason='INVALID_LOCATION'").fetchone()[0]
        share_count = conn.execute(
            "SELECT count(*) FROM events WHERE action_type IN ('share_food','share_tools') AND outcome='executed'"
        ).fetchone()[0]
        total_agent_events = conn.execute("SELECT count(*) FROM events WHERE agent_id IS NOT NULL").fetchone()[0]
        action_counts = {
            row[0]: row[1]
            for row in conn.execute(
                "SELECT action_type, count(*) FROM events WHERE agent_id IS NOT NULL GROUP BY action_type"
            )
        }
    finally:
        conn.close()

    expected_events = ticks * agent_count
    synthetic_rate = synthetic_failures / expected_events if expected_events else 0.0
    invalid_location_rate = invalid_location / total_agent_events if total_agent_events else 0.0
    return {
        "db_path": str(db_path),
        "status": status,
        "synthetic_failures": synthetic_failures,
        "expected_events": expected_events,
        "synthetic_rate": synthetic_rate,
        "invalid_location_count": invalid_location,
        "invalid_location_rate": invalid_location_rate,
        "share_count_5tick": share_count,
        "action_counts": action_counts,
    }


def _decision(summary: dict[str, Any]) -> dict[str, str]:
    synthetic_rate = summary["synthetic_rate"]
    invalid_location_rate = summary["invalid_location_rate"]
    if summary["status"] != "complete":
        return {
            "decision": "skip",
            "reason": f"run status={summary['status']}",
            "agent_civ_usable": "skip",
        }
    if synthetic_rate > 0.10:
        return {
            "decision": "skip",
            "reason": f"synthetic_rate={synthetic_rate:.3f} > 0.10",
            "agent_civ_usable": "skip",
        }
    if invalid_location_rate > 0.50:
        return {
            "decision": "run_with_caveat",
            "reason": f"invalid_location_rate={invalid_location_rate:.3f} > 0.50",
            "agent_civ_usable": "usable_with_caveat",
        }
    if synthetic_rate > 0.02:
        return {
            "decision": "run_with_caveat",
            "reason": f"synthetic_rate={synthetic_rate:.3f} > 0.02",
            "agent_civ_usable": "usable_with_caveat",
        }
    return {
        "decision": "run",
        "reason": "gate passed",
        "agent_civ_usable": "usable",
    }


async def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    served_model = _served_model(args.port)
    if served_model != args.model:
        print(
            f"GATE FAIL: expected {args.model}, got {served_model or '<none>'}",
            file=sys.stderr,
        )
        return 1

    endpoint = f"http://localhost:{args.port}/v1/chat/completions"
    requested_modes = (
        [PROMPT_MODE_SINGLE_USER, PROMPT_MODE_SYSTEM_USER] if args.prompt_mode == "auto" else [args.prompt_mode]
    )
    probes: list[dict[str, Any]] = []
    selected_mode: str | None = None
    for mode in requested_modes:
        probe = await _probe(endpoint, args.model, mode, args.thinking_mode)
        probes.append(probe)
        probe_path = output_dir / f"stage1_{mode}.json"
        probe_path.write_text(json.dumps(probe, indent=2))
        if probe["matches_expected"] and selected_mode is None:
            selected_mode = mode
            if args.prompt_mode == "auto":
                break

    if selected_mode is None:
        result = {
            "model": args.model,
            "served_model": served_model,
            "thinking_mode": args.thinking_mode,
            "stage1": probes,
            "stage2": None,
            "decision": "skip",
            "reason": "stage1_json_probe_failed",
            "agent_civ_usable": "skip",
        }
        (output_dir / "gate_result.json").write_text(json.dumps(result, indent=2))
        print(json.dumps(result, indent=2))
        return 1

    db_path = _run_gate_experiment(
        port=args.port,
        model=args.model,
        output_dir=output_dir,
        seed=args.seed,
        ticks=args.ticks,
        agent_count=args.agent_count,
        prompt_mode=selected_mode,
        thinking_mode=args.thinking_mode,
    )
    summary = _summarize_db(db_path, ticks=args.ticks, agent_count=args.agent_count)
    verdict = _decision(summary)
    result = {
        "model": args.model,
        "served_model": served_model,
        "thinking_mode": args.thinking_mode,
        "selected_prompt_mode": selected_mode,
        "stage1": probes,
        "stage2": summary,
        **verdict,
    }
    (output_dir / "gate_result.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    return 0 if verdict["decision"] != "skip" else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
