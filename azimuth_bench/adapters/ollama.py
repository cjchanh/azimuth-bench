"""Ollama local/remote HTTP adapter (``/api/tags``, ``/api/chat``)."""

from __future__ import annotations

import asyncio
import json
import urllib.error
import urllib.request
from typing import Any

import aiohttp

from azimuth_bench.adapters.base import BenchmarkAdapter
from azimuth_bench.adapters.capabilities import AdapterCapabilities
from azimuth_bench.adapters.identity import ProviderIdSource, build_backend_identity
from azimuth_bench.adapters.ollama_http import measure_ollama_chat_metrics
from azimuth_bench.core.cases import CaseSpec
from azimuth_bench.core.runtime import resolve_target_model


def _normalize_base_url(base_url: str) -> str:
    stripped = base_url.strip().rstrip("/")
    if not stripped:
        raise ValueError("base_url must be non-empty")
    return stripped


def _tags_model_names(base_url: str, *, timeout_s: float = 5.0) -> list[str]:
    req = urllib.request.Request(
        f"{base_url}/api/tags",
        headers={"Accept": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"failed to fetch models from {base_url}/api/tags: {exc}") from exc
    if not isinstance(payload, dict):
        return []
    models = payload.get("models")
    if not isinstance(models, list):
        return []
    names: list[str] = []
    for item in models:
        if isinstance(item, dict):
            name = item.get("name")
            if isinstance(name, str) and name:
                names.append(name)
    return names


class OllamaAdapter(BenchmarkAdapter):
    """Ollama HTTP API; no OpenAI ``/v1`` paths — uses adapter mediation only."""

    def __init__(
        self,
        *,
        base_url: str,
        timeout_s: float = 300.0,
    ) -> None:
        self._base_url = _normalize_base_url(base_url)
        self._timeout_s = timeout_s
        self._active_target_model_id: str | None = None

    def capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            adapter_name="OllamaAdapter",
            streaming=True,
            model_listing=True,
            model_selection=True,
            thinking_toggle=False,
            structured_output=False,
            openai_compatible_http=False,
            deployment_class="local",
        )

    def build_backend_identity(
        self,
        *,
        operator_provider_id: str | None,
        provider_id_source: ProviderIdSource,
    ) -> dict[str, Any]:
        caps = self.capabilities()
        pid = (operator_provider_id or "").strip() or "ollama"
        return build_backend_identity(
            provider_id=pid,
            provider_kind="ollama",
            adapter_name=caps.adapter_name,
            provider_id_source=provider_id_source,
            capabilities=caps,
            verified={"endpoint_configured": True},
        )

    def list_models(self) -> list[str]:
        return _tags_model_names(self._base_url)

    def healthcheck(self) -> bool:
        try:
            _tags_model_names(self._base_url, timeout_s=3.0)
            return True
        except RuntimeError:
            return False

    def prepare_target(self, target_model_id: str) -> dict[str, Any]:
        names = _tags_model_names(self._base_url)
        if target_model_id not in names:
            raise ValueError(
                f"target model {target_model_id!r} not listed in Ollama /api/tags; "
                "pull the model locally or fix --model-id (no silent fallback).",
            )
        self._active_target_model_id = target_model_id
        return {
            "served_model": target_model_id,
            "expected_model": target_model_id,
            "served_model_ids": names,
            "base_url": self._base_url,
            "load_seconds": 0.0,
        }

    def resolve_served_models(self) -> list[str]:
        return self.list_models()

    def run_case(self, spec: CaseSpec, *, thinking_mode: str) -> dict[str, Any]:
        return asyncio.run(self._run_case_async(spec, thinking_mode=thinking_mode))

    async def _run_case_async(self, spec: CaseSpec, *, thinking_mode: str) -> dict[str, Any]:
        del thinking_mode  # Ollama path does not map MLX-style thinking toggles.
        target_model_id: str | None = self._active_target_model_id
        if target_model_id is None:
            meta_target = spec.metadata.get("target_model_id")
            if isinstance(meta_target, str) and meta_target:
                target_model_id = meta_target
        if target_model_id is None:
            raise ValueError("run_case requires prepare_target() or spec.metadata['target_model_id']")

        names = self.list_models()
        model_id = resolve_target_model(names, target_model_id=target_model_id)
        chat_url = f"{self._base_url}/api/chat"
        timeout = aiohttp.ClientTimeout(total=self._timeout_s)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            return await measure_ollama_chat_metrics(
                session,
                chat_url=chat_url,
                model_id=model_id,
                user_prompt=spec.prompt,
                max_tokens=spec.max_tokens,
            )

    def shutdown(self) -> None:
        self._active_target_model_id = None
