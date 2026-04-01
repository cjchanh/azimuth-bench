"""Backend identity envelope for artifacts and reports (operator vs verified)."""

from __future__ import annotations

from typing import Any, Literal

from azimuth_bench.adapters.capabilities import AdapterCapabilities

ProviderIdSource = Literal["cli", "env", "default", "artifact", "inferred"]


def build_backend_identity(
    *,
    provider_id: str,
    provider_kind: str,
    adapter_name: str,
    provider_id_source: ProviderIdSource,
    capabilities: AdapterCapabilities,
    verified: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a JSON-serializable identity envelope.

    Args:
        provider_id: Stable label for the serving stack (operator-supplied or default).
        provider_kind: Coarse class, e.g. ``mlx_lm``, ``ollama``, ``openai_compatible``.
        adapter_name: Concrete adapter implementation name.
        provider_id_source: Where ``provider_id`` came from (``cli``, ``env``, ``default``, ``artifact``).
        capabilities: Capability snapshot for this adapter.
        verified: Optional machine-verified fields (never invent; omit if unknown).

    Returns:
        Dict suitable for embedding in benchmark JSON.
    """
    envelope: dict[str, Any] = {
        "provider_id": provider_id,
        "provider_kind": provider_kind,
        "adapter_name": adapter_name,
        "provider_id_source": provider_id_source,
        "capabilities": {
            "streaming": capabilities.streaming,
            "model_listing": capabilities.model_listing,
            "model_selection": capabilities.model_selection,
            "thinking_toggle": capabilities.thinking_toggle,
            "structured_output": capabilities.structured_output,
            "openai_compatible_http": capabilities.openai_compatible_http,
            "deployment_class": capabilities.deployment_class,
        },
    }
    if verified:
        envelope["verified"] = verified
    return envelope
