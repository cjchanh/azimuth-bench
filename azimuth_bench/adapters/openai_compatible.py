"""OpenAI-compatible HTTP adapter (no local server lifecycle; explicit base URL)."""

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
from azimuth_bench.adapters.openai_http import measure_chat_completion_metrics
from azimuth_bench.core.cases import CaseSpec
from azimuth_bench.core.runtime import (
    chat_template_kwargs_for_thinking_mode,
    model_ids_from_payload,
    resolve_model_id,
)


def _normalize_base_url(base_url: str) -> str:
    stripped = base_url.strip().rstrip("/")
    if not stripped:
        raise ValueError("base_url must be non-empty")
    return stripped


def _models_payload(base_url: str, *, api_key: str | None, timeout_s: float = 5.0) -> dict[str, Any]:
    req = urllib.request.Request(
        f"{base_url}/v1/models",
        headers={"Accept": "application/json", **({"Authorization": f"Bearer {api_key}"} if api_key else {})},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            raw = resp.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"failed to fetch models from {base_url}/v1/models: {exc}") from exc
    return json.loads(raw)


class OpenAICompatibleAdapter(BenchmarkAdapter):
    """Any server exposing OpenAI-compatible ``/v1/models`` and ``/v1/chat/completions``."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str | None = None,
        timeout_s: float = 300.0,
    ) -> None:
        self._base_url = _normalize_base_url(base_url)
        self._api_key = api_key
        self._timeout_s = timeout_s
        self._active_target_model_id: str | None = None

    def capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            adapter_name="OpenAICompatibleAdapter",
            streaming=True,
            model_listing=True,
            model_selection=True,
            thinking_toggle=False,
            structured_output=True,
            openai_compatible_http=True,
            deployment_class="remote",
        )

    def build_backend_identity(
        self,
        *,
        operator_provider_id: str | None,
        provider_id_source: ProviderIdSource,
    ) -> dict[str, Any]:
        caps = self.capabilities()
        pid = (operator_provider_id or "").strip() or "openai_compatible"
        return build_backend_identity(
            provider_id=pid,
            provider_kind="openai_compatible",
            adapter_name=caps.adapter_name,
            provider_id_source=provider_id_source,
            capabilities=caps,
            verified={"endpoint_configured": True, "api_key_set": bool(self._api_key)},
        )

    def list_models(self) -> list[str]:
        payload = _models_payload(self._base_url, api_key=self._api_key)
        return model_ids_from_payload(payload)

    def healthcheck(self) -> bool:
        try:
            _models_payload(self._base_url, api_key=self._api_key, timeout_s=3.0)
            return True
        except (RuntimeError, json.JSONDecodeError, ValueError):
            return False

    def prepare_target(self, target_model_id: str) -> dict[str, Any]:
        payload = _models_payload(self._base_url, api_key=self._api_key)
        model_ids = model_ids_from_payload(payload)
        if target_model_id not in model_ids:
            raise ValueError(
                f"target model {target_model_id!r} not in /v1/models for {self._base_url}; "
                "refusing silent fallback to another model",
            )
        self._active_target_model_id = target_model_id
        return {
            "served_model": target_model_id,
            "expected_model": target_model_id,
            "served_model_ids": model_ids,
            "base_url": self._base_url,
            "load_seconds": 0.0,
        }

    def resolve_served_models(self) -> list[str]:
        return self.list_models()

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

        chat_url = f"{self._base_url}/v1/chat/completions"
        models_url = f"{self._base_url}/v1/models"
        chat_template_kwargs = chat_template_kwargs_for_thinking_mode(thinking_mode)
        headers: dict[str, str] = {}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        timeout = aiohttp.ClientTimeout(total=self._timeout_s)
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
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
        self._active_target_model_id = None
