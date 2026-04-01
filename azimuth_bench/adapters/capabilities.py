"""Capability metadata for Azimuth Adapters (comparability and UX)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

DeploymentClass = Literal["local", "remote", "unknown"]


@dataclass(frozen=True, slots=True)
class AdapterCapabilities:
    """What this adapter can do; used to fail closed on unsupported suite options."""

    adapter_name: str
    streaming: bool
    model_listing: bool
    model_selection: bool
    thinking_toggle: bool
    structured_output: bool
    openai_compatible_http: bool
    deployment_class: DeploymentClass
