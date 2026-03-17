from typing import Any, Dict

from runtime.gile.adapter import GILEAdapter, GILEConfig, GILETransport


def gile_client(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Public callable used by the orchestrator.

    This keeps the same interface as the original stub (gile_client(payload)
    -> dict) while delegating to the real GILE adapter in the runtime layer.
    """
    adapter = GILEAdapter()
    return adapter.handle(payload)

