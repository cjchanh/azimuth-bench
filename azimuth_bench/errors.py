"""Explicit errors for Azimuth Bench (fail closed; no silent fallback)."""

from __future__ import annotations


class AzimuthBenchError(Exception):
    """Base class for Azimuth Bench failures."""

    pass


class UnsupportedAdapterFeatureError(AzimuthBenchError):
    """Raised when a suite requests a capability the adapter does not support."""

    pass


class BackendIdentityError(AzimuthBenchError):
    """Raised when provider identity cannot be established without ambiguity."""

    pass


class AdapterConfigurationError(AzimuthBenchError):
    """Raised when adapter construction or env configuration is invalid."""

    pass


class MergeCollisionError(AzimuthBenchError):
    """Raised when merged run sources contain duplicate or ambiguous identity."""

    pass


class MergeInputError(AzimuthBenchError):
    """Raised when a merge source is invalid or merge preconditions fail."""

    pass
