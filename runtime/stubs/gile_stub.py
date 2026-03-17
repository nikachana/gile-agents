from typing import Any, Dict


def gile_client(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Minimal deterministic GILE stub.

    Ignores the payload content and returns a fixed response.
    """
    return {
        "text": "Processed by GILE stub",
    }

