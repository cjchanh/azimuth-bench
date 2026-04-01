#!/usr/bin/env python3
"""All-model benchmark-v2 runner with token-first and optional gate planes."""
from __future__ import annotations

import argparse
import json
import os
import platform
import signal
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from benchmarking.roster import DEFAULT_ROSTER, artifact_key, filter_roster, hf_cache_dir, load_roster
from benchmarking.utils import DEFAULT_BENCHMARKS_DIR, ROOT

EXPERIMENT_PORT = 8899
SERVER_LOG_PATH = Path("/tmp/mlx_bench_server.log")
FLEET_GUARD_PATH = Path("/tmp/benchmark_fleet_guard.json")


class Logger:
    """Timestamped logger that optionally mirrors to a file."""

    def __init__(self, path: Path | None) -> None:
        self.path = path

    def log(self, message: str = "") -> None:
        line = f"{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')} {message}"
        print(line)
        if self.path is not None:
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(f"{line}\n")

    def emit_block(self, text: str) -> None:
        if not text:
            return
        for line in text.rstrip().splitlines():
            self.log(line)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Benchmark-v2 MLX sweep with token benchmark primary and optional gate validation."
    )
    parser.add_argument("--lane", choices=["all", "core", "frontier_27b"], default="all")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--with-gate", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--benchmarks-dir",
        type=Path,
        default=Path(os.environ.get("BENCHMARKS_DIR", str(DEFAULT_BENCHMARKS_DIR))),
    )
    parser.add_argument(
        "--bench-port",
        type=int,
        default=int(os.environ.get("BENCH_PORT", "9700")),
    )
    parser.add_argument(
        "--benchmark-gpu-mb",
        type=int,
        default=int(os.environ.get("BENCHMARK_GPU_MB", "22000")),
    )
    parser.add_argument("--roster", type=Path, default=DEFAULT_ROSTER)
    return parser.parse_args(argv)


def _pages_free() -> str:
    result = subprocess.run(["vm_stat"], capture_output=True, text=True, check=False)
    for line in result.stdout.splitlines():
        if "Pages free" in line:
            return line.split(":", 1)[1].replace(".", "").strip()
    return "unknown"


def _port_pids(port: int) -> list[int]:
    result = subprocess.run(
        ["lsof", "-i", f":{port}", "-t"],
        capture_output=True,
        text=True,
        check=False,
    )
    pids: list[int] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.isdigit():
            pids.append(int(line))
    return pids


def _kill_port_holders(port: int) -> None:
    for pid in _port_pids(port):
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            continue


def _served_model(port: int) -> str:
    try:
        with urllib.request.urlopen(f"http://localhost:{port}/v1/models", timeout=2) as resp:
            payload = json.load(resp)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return ""
    try:
        return str(payload["data"][0]["id"])
    except (KeyError, IndexError, TypeError):
        return ""


def _command_text(cmd: list[str]) -> str | None:
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    text = (result.stdout or result.stderr).strip()
    return text or None


def _write_receipt(receipt_dir: Path, name: str, payload: dict[str, Any]) -> Path:
    receipt_dir.mkdir(parents=True, exist_ok=True)
    path = receipt_dir / f"{name}.json"
    path.write_text(json.dumps(payload, indent=2))
    return path


def _machine_receipt(*, model_id: str, lane: str, thinking_mode: str, bench_port: int) -> dict[str, Any]:
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "hostname": platform.node(),
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "bench_port": bench_port,
        "lane": lane,
        "model_id": model_id,
        "thinking_mode": thinking_mode,
        "loadavg": [round(value, 2) for value in os.getloadavg()],
        "vm_pages_free": _pages_free(),
        "cpu_brand": _command_text(["sysctl", "-n", "machdep.cpu.brand_string"]),
        "hardware_model": _command_text(["sysctl", "-n", "hw.model"]),
        "memsize": _command_text(["sysctl", "-n", "hw.memsize"]),
        "battery_or_power": _command_text(["pmset", "-g", "batt"]),
        "continuous_monitoring": "disabled_by_protocol",
    }


def _merge_artifact_receipts(
    artifact_json: Path,
    *,
    receipt_payloads: dict[str, dict[str, Any]],
    receipt_paths: dict[str, Path],
) -> None:
    payload = json.loads(artifact_json.read_text())
    receipts = payload.setdefault("receipts", {})
    receipts.update(receipt_payloads)
    payload["receipt_paths"] = {
        name: str(path) for name, path in sorted(receipt_paths.items())
    }
    artifact_json.write_text(json.dumps(payload, indent=2))


def _artifact_completeness_receipt(artifact_json: Path) -> dict[str, Any]:
    payload = json.loads(artifact_json.read_text())
    required_keys = ["protocol", "summary", "validity", "comparability", "receipts"]
    missing_keys = [key for key in required_keys if key not in payload]
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_path": str(artifact_json),
        "required_keys": required_keys,
        "missing_keys": missing_keys,
        "valid_run": bool(payload.get("validity", {}).get("valid_run")),
        "comparable": bool(payload.get("comparability", {}).get("comparable")),
        "complete": not missing_keys,
    }


def _swap_model(target: str, port: int, logger: Logger) -> dict[str, Any]:
    load_started_at = datetime.now(timezone.utc).isoformat()
    wall_start = time.perf_counter()
    _kill_port_holders(port)
    time.sleep(3)

    mem_before = _pages_free()
    with SERVER_LOG_PATH.open("w", encoding="utf-8") as handle:
        subprocess.Popen(
            [
                sys.executable,
                "-m",
                "mlx_lm",
                "server",
                "--model",
                target,
                "--port",
                str(port),
                "--max-tokens",
                "512",
            ],
            stdout=handle,
            stderr=subprocess.STDOUT,
            cwd=ROOT,
        )

    for attempt in range(1, 121):
        served_model = _served_model(port)
        if served_model == target:
            mem_after = _pages_free()
            logger.log(
                f"  Loaded {target} in {attempt}s (pages_free: {mem_before} -> {mem_after})"
            )
            return {
                "started_at_utc": load_started_at,
                "finished_at_utc": datetime.now(timezone.utc).isoformat(),
                "load_seconds": round(time.perf_counter() - wall_start, 2),
                "served_model": served_model,
                "expected_model": target,
                "pages_free_before": mem_before,
                "pages_free_after": mem_after,
                "port": port,
            }
        if served_model and served_model != target:
            _kill_port_holders(port)
            time.sleep(2)
            with SERVER_LOG_PATH.open("w", encoding="utf-8") as handle:
                subprocess.Popen(
                    [
                        sys.executable,
                        "-m",
                        "mlx_lm",
                        "server",
                        "--model",
                        target,
                        "--port",
                        str(port),
                        "--max-tokens",
                        "512",
                    ],
                    stdout=handle,
                    stderr=subprocess.STDOUT,
                    cwd=ROOT,
                )
        time.sleep(1)

    raise RuntimeError(f"failed to load {target} on :{port}")


def _experiment_server_active(port: int) -> bool:
    result = subprocess.run(
        ["lsof", "-i", f":{port}", "-sTCP:LISTEN"],
        capture_output=True,
        text=True,
        check=False,
    )
    return bool(result.stdout.strip())


def _run_subprocess(cmd: list[str], *, cwd: Path, logger: Logger, fail_message: str, stdout_to: Path | None = None) -> None:
    if stdout_to is None:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
        logger.emit_block(result.stdout)
        logger.emit_block(result.stderr)
        if result.returncode != 0:
            raise RuntimeError(fail_message)
        return

    stdout_to.parent.mkdir(parents=True, exist_ok=True)
    with stdout_to.open("w", encoding="utf-8") as handle:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            stdout=handle,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
    logger.log(f"  Wrote log: {stdout_to}")
    if result.returncode != 0:
        raise RuntimeError(fail_message)


def _fleet_guard(repo_root: Path, bench_port: int, benchmark_gpu_mb: int, logger: Logger) -> None:
    fleet_path = shutil.which("fleet")
    if fleet_path is None:
        logger.log("Fleet guard unavailable; proceeding on explicit local assumption.")
        return
    result = subprocess.run(
        [
            fleet_path,
            "guard",
            "--repo",
            str(repo_root),
            "--port",
            str(bench_port),
            "--gpu",
            str(benchmark_gpu_mb),
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    FLEET_GUARD_PATH.write_text(result.stdout or result.stderr)
    if result.returncode != 0:
        raise RuntimeError(
            f"fleet guard denied repo/port/gpu claim; see {FLEET_GUARD_PATH}"
        )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    log_path: Path | None = None
    if not args.dry_run:
        args.benchmarks_dir.mkdir(parents=True, exist_ok=True)
        log_path = args.benchmarks_dir / "benchmark_all.log"
        log_path.write_text("")
    logger = Logger(log_path)

    logger.log("=== BENCHMARK-V2 MLX SWEEP ===")
    logger.log(f"Lane: {args.lane}")
    logger.log(f"Bench port: {args.bench_port}")
    logger.log(f"Gate lane: {'enabled' if args.with_gate else 'disabled'}")
    logger.log(f"Mode: {'dry-run' if args.dry_run else 'execute'}")
    logger.log()

    if not args.dry_run:
        if _experiment_server_active(EXPERIMENT_PORT):
            raise RuntimeError(
                f"experiment server is active on :{EXPERIMENT_PORT}. Benchmark lane is offline-only."
            )
        _fleet_guard(ROOT, args.bench_port, args.benchmark_gpu_mb, logger)

    entries = filter_roster(load_roster(args.roster), args.lane)
    if not entries:
        raise RuntimeError(f"no roster entries resolved for lane={args.lane}")

    logger.log(f"Roster entries: {len(entries)}")
    logger.log()

    for entry in entries:
        model_id = str(entry["model_id"])
        display_name = str(entry["display_name"])
        lane = str(entry["lane"])
        thinking_mode = str(entry["thinking_mode"])
        source_label = str(entry["source_label"])
        source_badge = str(entry["source_badge"])
        artifact = artifact_key(entry)
        artifact_json = args.benchmarks_dir / f"{artifact}.json"
        gate_dir = args.benchmarks_dir / f"gate_{artifact}"
        gate_result = gate_dir / "gate_result.json"
        receipt_dir = args.benchmarks_dir / "receipts" / artifact
        need_benchmark = True
        need_gate = args.with_gate

        logger.log(f"[{artifact}] {display_name} | lane={lane} | thinking={thinking_mode}")
        receipt_payloads: dict[str, dict[str, Any]] = {}
        receipt_paths: dict[str, Path] = {}

        try:
            cache_dir = hf_cache_dir(model_id)
            if not cache_dir.exists():
                if entry.get("required_cache"):
                    raise RuntimeError(f"required cache missing for {model_id} ({cache_dir})")
                logger.log(f"[{artifact}] Cache missing; optional entry skipped")
                logger.log()
                continue

            if args.dry_run:
                if args.with_gate:
                    logger.log(
                        f"[{artifact}] DRY RUN cache=present artifact_json={artifact_json} gate_dir={gate_dir}"
                    )
                else:
                    logger.log(f"[{artifact}] DRY RUN cache=present artifact_json={artifact_json}")
                logger.log()
                continue

            if not args.force:
                if artifact_json.exists():
                    need_benchmark = False
                if args.with_gate and gate_result.exists():
                    need_gate = False
                if not need_benchmark and not need_gate:
                    logger.log(f"[{artifact}] Existing requested artifacts found; skipping")
                    logger.log()
                    continue

            machine_receipt = _machine_receipt(
                model_id=model_id,
                lane=lane,
                thinking_mode=thinking_mode,
                bench_port=args.bench_port,
            )
            receipt_payloads["machine_pre_run"] = machine_receipt
            receipt_paths["machine_pre_run"] = _write_receipt(
                receipt_dir, "machine_pre_run", machine_receipt
            )

            model_load_receipt = _swap_model(model_id, args.bench_port, logger)
            receipt_payloads["model_load"] = model_load_receipt
            receipt_paths["model_load"] = _write_receipt(
                receipt_dir, "model_load", model_load_receipt
            )

            if need_benchmark:
                logger.log(f"[{artifact}] Running token benchmark...")
                token_run_start = {
                    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                    "artifact_key": artifact,
                    "artifact_path": str(artifact_json),
                    "model_id": model_id,
                    "thinking_mode": thinking_mode,
                    "lane": lane,
                }
                receipt_payloads["token_run_start"] = token_run_start
                receipt_paths["token_run_start"] = _write_receipt(
                    receipt_dir, "token_run_start", token_run_start
                )
                _run_subprocess(
                    [
                        sys.executable,
                        "-m",
                        "benchmarking.token",
                        "--port",
                        str(args.bench_port),
                        "--output",
                        str(artifact_json),
                        "--display-name",
                        display_name,
                        "--lane",
                        lane,
                        "--thinking-mode",
                        thinking_mode,
                        "--source-label",
                        source_label,
                        "--source-badge",
                        source_badge,
                        "--artifact-key",
                        artifact,
                    ],
                    cwd=ROOT,
                    logger=logger,
                    fail_message=f"token benchmark failed for {artifact}",
                )
                token_run_finish = {
                    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                    "artifact_path": str(artifact_json),
                    "status": "complete",
                }
                receipt_payloads["token_run_finish"] = token_run_finish
                receipt_paths["token_run_finish"] = _write_receipt(
                    receipt_dir, "token_run_finish", token_run_finish
                )
                completeness = _artifact_completeness_receipt(artifact_json)
                receipt_payloads["artifact_complete"] = completeness
                receipt_paths["artifact_complete"] = _write_receipt(
                    receipt_dir, "artifact_complete", completeness
                )
                _merge_artifact_receipts(
                    artifact_json,
                    receipt_payloads=receipt_payloads,
                    receipt_paths=receipt_paths,
                )
            else:
                logger.log(f"[{artifact}] Token benchmark artifact already present; skipping")

            if need_gate:
                logger.log(f"[{artifact}] Running optional 5-tick Agent Civilization gate...")
                if gate_dir.exists():
                    shutil.rmtree(gate_dir)
                _run_subprocess(
                    [
                        sys.executable,
                        "-m",
                        "benchmarking.gate",
                        "--port",
                        str(args.bench_port),
                        "--model",
                        model_id,
                        "--output-dir",
                        str(gate_dir),
                        "--thinking-mode",
                        thinking_mode,
                    ],
                    cwd=ROOT,
                    logger=logger,
                    fail_message=f"gate failed for {artifact}",
                    stdout_to=gate_dir / "gate.log",
                )
                gate_payload = json.loads(gate_result.read_text())
                logger.log(
                    f"[{artifact}] Gate: decision={gate_payload['decision']} usable={gate_payload['agent_civ_usable']}"
                )
            logger.log()
        except Exception as exc:
            if not args.dry_run:
                failure_receipt = {
                    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                    "artifact_key": artifact,
                    "model_id": model_id,
                    "thinking_mode": thinking_mode,
                    "lane": lane,
                    "error": str(exc),
                }
                _write_receipt(receipt_dir, "failure", failure_receipt)
            raise

    if args.dry_run:
        logger.log(
            "DRY RUN COMPLETE: roster, cache, and artifact paths validated; no repo artifacts were written."
        )
        return 0

    summary_cmd = [
        sys.executable,
        "-m",
        "benchmarking.summary",
        "--benchmarks-dir",
        str(args.benchmarks_dir),
        "--lane",
        args.lane,
    ]
    if args.with_gate:
        summary_cmd.append("--write-gate")
    _run_subprocess(
        summary_cmd,
        cwd=ROOT,
        logger=logger,
        fail_message="benchmark summary compilation failed",
    )

    logger.log("=== BENCHMARK-V2 COMPLETE ===")
    logger.log(f"Token summary: {args.benchmarks_dir / 'benchmark_v2_token_summary.json'}")
    if args.with_gate:
        logger.log(f"Gate summary: {args.benchmarks_dir / 'benchmark_v2_gate_summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
