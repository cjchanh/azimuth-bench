"""Environment-driven configuration (no secrets; operator-visible only)."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

# Preferred public env var names (Azimuth Bench).
ENV_PROVIDER_ID = "AZIMUTH_BENCH_PROVIDER_ID"
ENV_MLX_SERVER_LOG = "AZIMUTH_BENCH_MLX_SERVER_LOG"
ENV_FLEET_GUARD_PATH = "AZIMUTH_BENCH_FLEET_GUARD_PATH"
ENV_OPENAI_BASE_URL = "AZIMUTH_BENCH_OPENAI_BASE_URL"
ENV_OPENAI_API_KEY = "AZIMUTH_BENCH_API_KEY"

# Legacy aliases (honored for non-breaking upgrades).
LEGACY_ENV_PROVIDER_ID = "SIGNALBENCH_PROVIDER_ID"
LEGACY_ENV_MLX_SERVER_LOG = "SIGNALBENCH_MLX_SERVER_LOG"
LEGACY_ENV_FLEET_GUARD_PATH = "SIGNALBENCH_FLEET_GUARD_PATH"
LEGACY_OPENAI_BASE_URL = "OPENAI_BASE_URL"
LEGACY_OPENAI_API_KEY = "OPENAI_API_KEY"


def default_temp_dir() -> Path:
    """Prefer ``TMPDIR`` / ``TEMP`` / system temp (POSIX-friendly, no hardcoded paths)."""
    for key in ("TMPDIR", "TEMP", "TMP"):
        value = os.environ.get(key)
        if value:
            return Path(value)
    return Path(tempfile.gettempdir())


def default_mlx_server_log_path() -> Path:
    """Default MLX LM server log path under the effective temp directory."""
    for key in (ENV_MLX_SERVER_LOG, LEGACY_ENV_MLX_SERVER_LOG):
        base = os.environ.get(key)
        if base:
            return Path(base)
    return default_temp_dir() / "azimuth_bench_mlx_bench_server.log"


def default_fleet_guard_path() -> Path:
    """Default fleet guard JSON path under the effective temp directory."""
    for key in (ENV_FLEET_GUARD_PATH, LEGACY_ENV_FLEET_GUARD_PATH):
        base = os.environ.get(key)
        if base:
            return Path(base)
    return default_temp_dir() / "azimuth_bench_fleet_guard.json"


def provider_id_from_env() -> str | None:
    """Return stripped provider id from env, or ``None`` if unset/empty."""
    for key in (ENV_PROVIDER_ID, LEGACY_ENV_PROVIDER_ID):
        raw = os.environ.get(key)
        if raw is None:
            continue
        stripped = raw.strip()
        if stripped:
            return stripped
    return None


def openai_compatible_base_url(cli_value: str | None) -> str | None:
    """Resolve OpenAI-compatible base URL: CLI wins, then Azimuth, then generic OpenAI env."""
    if cli_value and cli_value.strip():
        return cli_value.strip().rstrip("/")
    for key in (ENV_OPENAI_BASE_URL, LEGACY_OPENAI_BASE_URL):
        raw = os.environ.get(key)
        if raw and raw.strip():
            return raw.strip().rstrip("/")
    return None


def openai_compatible_api_key() -> str | None:
    """Optional API key for OpenAI-compatible endpoints (never logged or embedded in artifacts)."""
    for key in (ENV_OPENAI_API_KEY, LEGACY_OPENAI_API_KEY):
        raw = os.environ.get(key)
        if raw and raw.strip():
            return raw.strip()
    return None
