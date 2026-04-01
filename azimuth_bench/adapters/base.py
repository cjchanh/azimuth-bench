"""Abstract benchmark adapter contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from azimuth_bench.adapters.capabilities import AdapterCapabilities
from azimuth_bench.adapters.identity import ProviderIdSource
from azimuth_bench.core.cases import CaseSpec


class BenchmarkAdapter(ABC):
    """Provider adapter for listing models, loading targets, and running cases."""

    @abstractmethod
    def capabilities(self) -> AdapterCapabilities:
        """Return capability metadata for this adapter."""

    @abstractmethod
    def build_backend_identity(
        self,
        *,
        operator_provider_id: str | None,
        provider_id_source: ProviderIdSource,
    ) -> dict[str, Any]:
        """Return the backend identity envelope for artifacts (no invented verification)."""

    @abstractmethod
    def list_models(self) -> list[str]:
        """Return model ids advertised by the serving endpoint."""

    @abstractmethod
    def healthcheck(self) -> bool:
        """Return True if the serving endpoint responds for discovery."""

    @abstractmethod
    def prepare_target(self, target_model_id: str) -> dict[str, Any]:
        """Ensure the requested model is loaded; return a load receipt dict."""

    @abstractmethod
    def resolve_served_models(self) -> list[str]:
        """Return model ids currently reported by the server."""

    @abstractmethod
    def run_case(self, spec: CaseSpec, *, thinking_mode: str) -> dict[str, Any]:
        """Execute one case; returns measurement row dict."""

    @abstractmethod
    def shutdown(self) -> None:
        """Release ports/processes owned by this adapter."""
