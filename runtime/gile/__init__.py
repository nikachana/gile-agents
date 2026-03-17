"""
Public export surface for GILE runtime integration.

This module exposes the stable adapter and helper interfaces used by the
runtime layer and tests. It intentionally re-exports only the integration-
facing symbols from `runtime.gile.adapter`.
"""

from .adapter import (  # noqa: F401
    GILEAdapter,
    GILEConfig,
    create_gile_adapter,
    gile_client,
)

__all__ = [
    "GILEAdapter",
    "GILEConfig",
    "create_gile_adapter",
    "gile_client",
]

