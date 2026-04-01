"""Construct adapters for CLI and runners (explicit configuration; fail closed)."""

from __future__ import annotations

import os
from pathlib import Path

from azimuth_bench.adapters.base import BenchmarkAdapter
from azimuth_bench.adapters.identity import ProviderIdSource
from azimuth_bench.adapters.mlx import MLXLmServerAdapter
from azimuth_bench.adapters.ollama import OllamaAdapter
from azimuth_bench.adapters.openai_compatible import OpenAICompatibleAdapter
from azimuth_bench.core.env import default_mlx_server_log_path, openai_compatible_api_key, openai_compatible_base_url
from azimuth_bench.errors import AdapterConfigurationError


def resolve_ollama_base_url(explicit: str | None) -> str:
    """Return Ollama base URL (explicit CLI wins, then env, else local default)."""
    if explicit and explicit.strip():
        return explicit.strip().rstrip("/")
    env = os.environ.get("AZIMUTH_BENCH_OLLAMA_BASE_URL") or os.environ.get("OLLAMA_HOST")
    if env and str(env).strip():
        raw = str(env).strip().rstrip("/")
        if raw.startswith("http://") or raw.startswith("https://"):
            return raw
        return f"http://{raw}"
    return "http://127.0.0.1:11434"


def build_throughput_adapter(
    *,
    adapter_name: str,
    repo_root: Path,
    bench_port: int,
    base_url: str | None,
    max_tokens_default: int,
) -> BenchmarkAdapter:
    """Build a throughput-suite adapter by name (``mlx`` | ``openai_compatible`` | ``ollama``)."""
    key = adapter_name.strip().lower()
    if key == "mlx":
        return MLXLmServerAdapter(
            repo_root=repo_root,
            bench_port=bench_port,
            server_log_path=default_mlx_server_log_path(),
            max_tokens_default=max_tokens_default,
        )
    if key == "openai_compatible":
        resolved = openai_compatible_base_url(base_url)
        if not resolved:
            raise AdapterConfigurationError(
                "openai_compatible adapter requires --base-url or AZIMUTH_BENCH_OPENAI_BASE_URL / OPENAI_BASE_URL",
            )
        return OpenAICompatibleAdapter(
            base_url=resolved,
            api_key=openai_compatible_api_key(),
        )
    if key == "ollama":
        return OllamaAdapter(base_url=resolve_ollama_base_url(base_url))
    raise AdapterConfigurationError(f"unknown adapter {adapter_name!r}")


def resolve_provider_fields(
    *,
    cli_provider_id: str | None,
) -> tuple[str | None, ProviderIdSource]:
    """Resolve operator provider id: CLI overrides environment."""
    from azimuth_bench.core.env import provider_id_from_env

    if cli_provider_id and cli_provider_id.strip():
        return cli_provider_id.strip(), "cli"
    env_id = provider_id_from_env()
    if env_id:
        return env_id, "env"
    return None, "default"


def default_machine_class_for_adapter(adapter_name: str) -> str:
    """Default protocol machine_class label (no silent MLX assumption for non-mlx)."""
    key = adapter_name.strip().lower()
    if key == "mlx":
        return "Apple Silicon M5 Max local MLX lane"
    return "unspecified_host"
