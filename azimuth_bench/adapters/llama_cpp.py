"""llama.cpp / llama-server OpenAI-compatible HTTP adapter (explicit base URL).

This adapter is **not** interchangeable with MLX or generic ``openai_compatible``:
it advertises ``thinking_toggle=True`` for routes that honor ``chat_template_kwargs``
(e.g. Qwen thinking controls on llama-server). If the server rejects non-default
thinking controls, we fail closed with :class:`UnsupportedAdapterFeatureError`.
"""

from __future__ import annotations

import asyncio
from typing import Any

import aiohttp

from azimuth_bench.adapters.capabilities import AdapterCapabilities
from azimuth_bench.adapters.identity import ProviderIdSource, build_backend_identity
from azimuth_bench.adapters.openai_compatible import OpenAICompatibleAdapter
from azimuth_bench.core.cases import CaseSpec
from azimuth_bench.core.runtime import chat_template_kwargs_for_thinking_mode
from azimuth_bench.errors import UnsupportedAdapterFeatureError


class LlamaCppServerAdapter(OpenAICompatibleAdapter):
    """``llama-server`` or compatible binary exposing OpenAI-style ``/v1`` HTTP."""

    def capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            adapter_name="LlamaCppServerAdapter",
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
        pid = (operator_provider_id or "").strip() or "llama_cpp_server"
        ident = build_backend_identity(
            provider_id=pid,
            provider_kind="llama_cpp_server",
            adapter_name=caps.adapter_name,
            provider_id_source=provider_id_source,
            capabilities=caps,
            verified={
                "endpoint_configured": True,
                "openai_compatible_surface": True,
                "thinking_controls_expected": True,
                "thinking_controls_verified": False,
                "thinking_controls_failure_mode": "UnsupportedAdapterFeatureError on HTTP rejection",
            },
        )
        ident["api_surface"] = "openai_compatible_http_llama_cpp"
        ident["backend"] = "llama_server_openai_compatible"
        return ident

    def run_case(self, spec: CaseSpec, *, thinking_mode: str) -> dict[str, Any]:
        return asyncio.run(self._llama_run_case_async(spec, thinking_mode=thinking_mode))

    async def _llama_run_case_async(self, spec: CaseSpec, *, thinking_mode: str) -> dict[str, Any]:
        kwargs = chat_template_kwargs_for_thinking_mode(thinking_mode)
        try:
            return await OpenAICompatibleAdapter._run_case_async(self, spec, thinking_mode=thinking_mode)
        except aiohttp.ClientResponseError as exc:
            if kwargs is None:
                raise
            message = (
                f"llama.cpp route rejected chat_template_kwargs for thinking_mode={thinking_mode!r}: "
                f"HTTP {exc.status} {exc.message!r}. "
                "Use thinking_mode=default, upgrade llama-server, or pick a route that exposes thinking controls."
            )
            raise UnsupportedAdapterFeatureError(message) from exc
