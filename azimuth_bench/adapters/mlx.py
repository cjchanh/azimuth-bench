"""MLX LM OpenAI-compatible server adapter."""

from __future__ import annotations

import asyncio
import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiohttp

from azimuth_bench.adapters.base import BenchmarkAdapter
from azimuth_bench.adapters.capabilities import AdapterCapabilities
from azimuth_bench.adapters.identity import ProviderIdSource, build_backend_identity
from azimuth_bench.adapters.openai_http import measure_chat_completion_metrics
from azimuth_bench.core.cases import CaseSpec
from azimuth_bench.core.runtime import (
    chat_template_kwargs_for_thinking_mode,
    model_ids_from_payload,
    resolve_model_id,
)


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


def _pages_free() -> str:
    result = subprocess.run(["vm_stat"], capture_output=True, text=True, check=False)
    for line in result.stdout.splitlines():
        if "Pages free" in line:
            return line.split(":", 1)[1].replace(".", "").strip()
    return "unknown"


def _served_model_ids(port: int) -> list[str]:
    try:
        with urllib.request.urlopen(f"http://localhost:{port}/v1/models", timeout=2) as resp:
            payload = json.load(resp)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return []
    return model_ids_from_payload(payload)


class MLXLmServerAdapter(BenchmarkAdapter):
    """MLX LM `python -m mlx_lm server` lifecycle and OpenAI-compatible calls."""

    def __init__(
        self,
        *,
        repo_root: Path,
        bench_port: int,
        server_log_path: Path,
        max_tokens_default: int = 512,
    ) -> None:
        self._repo_root = repo_root
        self._bench_port = bench_port
        self._server_log_path = server_log_path
        self._max_tokens_default = max_tokens_default
        self._active_target_model_id: str | None = None

    def capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            adapter_name="MLXLmServerAdapter",
            streaming=True,
            model_listing=True,
            model_selection=True,
            thinking_toggle=True,
            structured_output=True,
            openai_compatible_http=True,
            deployment_class="local",
        )

    def build_backend_identity(
        self,
        *,
        operator_provider_id: str | None,
        provider_id_source: ProviderIdSource,
    ) -> dict[str, Any]:
        caps = self.capabilities()
        pid = (operator_provider_id or "").strip() or "mlx_lm"
        return build_backend_identity(
            provider_id=pid,
            provider_kind="mlx_lm",
            adapter_name=caps.adapter_name,
            provider_id_source=provider_id_source,
            capabilities=caps,
            verified={"bench_port": self._bench_port, "launcher": "mlx_lm_server"},
        )

    def list_models(self) -> list[str]:
        return _served_model_ids(self._bench_port)

    def healthcheck(self) -> bool:
        try:
            with urllib.request.urlopen(f"http://localhost:{self._bench_port}/v1/models", timeout=2) as resp:
                return resp.status == 200
        except (urllib.error.URLError, TimeoutError):
            return False

    def prepare_target(self, target_model_id: str) -> dict[str, Any]:
        load_started_at = datetime.now(timezone.utc).isoformat()
        wall_start = time.perf_counter()
        _kill_port_holders(self._bench_port)
        time.sleep(3)

        mem_before = _pages_free()
        self._server_log_path.parent.mkdir(parents=True, exist_ok=True)
        with self._server_log_path.open("w", encoding="utf-8") as handle:
            subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "mlx_lm",
                    "server",
                    "--model",
                    target_model_id,
                    "--port",
                    str(self._bench_port),
                    "--max-tokens",
                    str(self._max_tokens_default),
                ],
                stdout=handle,
                stderr=subprocess.STDOUT,
                cwd=self._repo_root,
            )

        for _attempt in range(1, 121):
            served_model_ids = _served_model_ids(self._bench_port)
            if target_model_id in served_model_ids:
                mem_after = _pages_free()
                self._active_target_model_id = target_model_id
                return {
                    "started_at_utc": load_started_at,
                    "finished_at_utc": datetime.now(timezone.utc).isoformat(),
                    "load_seconds": round(time.perf_counter() - wall_start, 2),
                    "served_model": target_model_id,
                    "expected_model": target_model_id,
                    "served_model_ids": served_model_ids,
                    "pages_free_before": mem_before,
                    "pages_free_after": mem_after,
                    "port": self._bench_port,
                }
            time.sleep(1)

        raise RuntimeError(f"failed to load {target_model_id} on :{self._bench_port}")

    def resolve_served_models(self) -> list[str]:
        return _served_model_ids(self._bench_port)

    def run_case(self, spec: CaseSpec, *, thinking_mode: str) -> dict[str, Any]:
        return asyncio.run(self._run_case_async(spec, thinking_mode=thinking_mode))

    async def _run_case_async(self, spec: CaseSpec, *, thinking_mode: str) -> dict[str, Any]:
        target_model_id: str | None = self._active_target_model_id
        if target_model_id is None:
            meta_target = spec.metadata.get("target_model_id")
            if isinstance(meta_target, str) and meta_target:
                target_model_id = meta_target
        if target_model_id is None:
            raise ValueError("run_case requires prepare_target() or spec.metadata['target_model_id']")

        chat_url = f"http://localhost:{self._bench_port}/v1/chat/completions"
        models_url = f"http://localhost:{self._bench_port}/v1/models"
        chat_template_kwargs = chat_template_kwargs_for_thinking_mode(thinking_mode)

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=300)) as session:
            async with session.get(models_url) as resp:
                resp.raise_for_status()
                models = await resp.json(content_type=None)
            model_id = resolve_model_id(models, target_model_id=target_model_id)
            return await measure_chat_completion_metrics(
                session,
                chat_completions_url=chat_url,
                model_id=model_id,
                user_prompt=spec.prompt,
                max_tokens=spec.max_tokens,
                temperature=float(spec.metadata.get("temperature", 0.3)),
                chat_template_kwargs=chat_template_kwargs,
            )

    def shutdown(self) -> None:
        _kill_port_holders(self._bench_port)
