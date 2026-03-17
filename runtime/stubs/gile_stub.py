from typing import Any, Dict


class GILEAdapter:
    """
    Thin, deterministic adapter skeleton for the GILE service.

    This class acts as the runtime-facing abstraction over the future real
    GILE API. In this initial version it does not perform any network calls
    or LLM logic and instead returns a fixed, contract-aligned response.
    """

    def __init__(self) -> None:
        # Future configuration (base URL, auth, client, etc.) can live here.
        self._version = "stub_v1"

    def handle(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Entry point for all GILE refinement requests.

        The payload is expected to originate from:
          - router handoff payloads (for translate / rewrite / validate), or
          - reply_agent outputs (for institutional_rewrite flows).
        """
        action = self._infer_action(payload)
        request = self._build_request(payload, action)
        return self._dispatch(request)

    # ---------- Dispatch & action inference ----------

    def _infer_action(self, payload: Dict[str, Any]) -> str:
        """
        Infer the GILE action from the incoming payload.

        For reply_agent → GILE handoffs, we expect a gile_action field.
        For direct router → GILE handoffs, we infer from metadata.mode.
        """
        gile_action = payload.get("gile_action")
        if isinstance(gile_action, str) and gile_action:
            return gile_action

        metadata = payload.get("metadata") or {}
        mode = metadata.get("mode")
        if mode in {"translate", "rewrite", "validate"}:
            return mode

        return "institutional_rewrite"

    def _build_request(self, payload: Dict[str, Any], action: str) -> Dict[str, Any]:
        """
        Build an internal request representation for the adapter.

        This is where future transformations from orchestrator payloads into
        concrete HTTP or RPC requests can be centralized.
        """
        return {
            "action": action,
            "payload": payload,
        }

    def _dispatch(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dispatch the internal request to the appropriate handler.
        """
        action = request.get("action")

        if action == "translate":
            return self._handle_translate(request)
        if action == "rewrite":
            return self._handle_rewrite(request)
        if action == "validate":
            return self._handle_validate(request)
        if action == "institutional_rewrite":
            return self._handle_institutional_rewrite(request)

        # Fallback for any unknown action – treated as institutional_rewrite.
        return self._handle_institutional_rewrite(
            {"action": "institutional_rewrite", "payload": request.get("payload", {})}
        )

    # ---------- Per-action handlers ----------

    def _handle_translate(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Placeholder for future /translate behavior.
        """
        return self._normalize_response(request)

    def _handle_rewrite(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Placeholder for future /rewrite behavior.
        """
        return self._normalize_response(request)

    def _handle_validate(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Placeholder for future /validate behavior.
        """
        return self._normalize_response(request)

    def _handle_institutional_rewrite(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Placeholder for future /institutional_rewrite behavior.
        """
        return self._normalize_response(request)

    # ---------- Response normalization ----------

    def _normalize_response(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize the (future) raw GILE response into the adapter's public
        output shape.

        Current runtime behavior and tests only require that a dict with a
        'text' field is returned; we also expose gile_action and gile_version
        as stable metadata for adapter tests.
        """
        action = request.get("action", "institutional_rewrite")
        return {
            "text": "Processed by GILE stub",
            "gile_action": action,
            "gile_version": self._version,
        }


def gile_client(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Public callable used by the orchestrator.

    This keeps the same interface as the original stub (gile_client(payload)
    -> dict) while delegating to the adapter skeleton, so all existing
    runtime behavior and tests are preserved.
    """
    adapter = GILEAdapter()
    return adapter.handle(payload)

