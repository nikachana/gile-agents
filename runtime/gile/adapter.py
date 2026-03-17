import os
from typing import Any, Dict


class GILEConfig:
    """
    Internal configuration source for the GILE transport layer.

    In this version the configuration is fully static and deterministic,
    providing a clear place to hang provider/mode/base_url/timeout settings
    once real network integration is introduced.
    """

    def __init__(self) -> None:
        # Provider name (e.g. stub, internal_http, external_saas)
        self.provider: str = os.getenv("GILE_PROVIDER", "stub")

        # High-level environment or deployment mode (e.g. local, staging, prod).
        self.mode: str = os.getenv("GILE_MODE", "local")

        # Transport mode controls whether calls are handled locally or via
        # a real remote transport. Defaults to local when unset.
        self.transport_mode: str = os.getenv("GILE_TRANSPORT_MODE", "local")

        # Base URL placeholder for future HTTP integration.
        self.base_url: str = os.getenv("GILE_BASE_URL", "http://gile.local/stub")

        # Timeout placeholder; falls back to a safe default on invalid values.
        timeout_env = os.getenv("GILE_TIMEOUT_SECONDS")
        if timeout_env is not None:
            try:
                self.timeout_seconds = float(timeout_env)
            except ValueError:
                self.timeout_seconds = 5.0
        else:
            self.timeout_seconds = 5.0

        # Adapter/transport version identifier.
        self.version: str = "stub_v1"

        # Gate for future real remote execution. Defaults to disabled so that
        # the remote transport only prepares outbound requests without
        # executing them.
        self.remote_execution_enabled: bool = (
            os.getenv("GILE_REMOTE_EXECUTION_ENABLED", "false").lower()
            in ("1", "true", "yes")
        )


class GILETransport:
    """
    Abstract transport interface for GILE.

    Concrete implementations are provided by the internal transport factory
    based on configuration (e.g. local vs remote).
    """

    def send(self, request: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError


class _LocalGILETransport(GILETransport):
    """
    Internal transport skeleton for GILE.

    Local, fully deterministic transport used in tests and default runtime
    mode. Performs no network I/O.
    """

    def __init__(self, config: GILEConfig) -> None:
        self._config = config

    def send(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Local, fully deterministic transport path used in tests and default
        runtime mode.
        """
        return {
            "action": request.get("action"),
            "payload": request.get("payload"),
            "transport_version": self._config.version,
            "provider": self._config.provider,
            "mode": self._config.mode,
            "base_url": self._config.base_url,
            "timeout_seconds": self._config.timeout_seconds,
        }


class _RemoteGILETransport(GILETransport):
    """
    Placeholder for a future real remote transport path.

    This implementation intentionally does not perform any network calls yet.
    It returns a shape compatible with the local transport so that adapter
    behavior remains stable while allowing the transport mode to be switched
    in a controlled way later.
    """

    def __init__(self, config: GILEConfig) -> None:
        self._config = config

    def send(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remote placeholder path; shape-compatible with the local transport.

        Prepares an explicit outbound HTTP-style request shape but does not
        actually perform any network call.
        """
        endpoint = request.get("endpoint") or "/institutional_rewrite"
        outbound_request = {
            "method": "POST",
            "url": f"{self._config.base_url}{endpoint}",
            "timeout_seconds": self._config.timeout_seconds,
            "endpoint": endpoint,
            "body": request.get("body"),
            "metadata": request.get("metadata") or {},
            "context": request.get("context") or {},
        }

        # Execution gate: in the current stub implementation we never execute
        # the outbound request. When remote_execution_enabled is true in a
        # future version, this is where real network I/O would be invoked.
        if self._config.remote_execution_enabled:
            self._execute(outbound_request)

        return {
            "action": request.get("action"),
            "payload": request.get("payload"),
            "transport_version": self._config.version,
            "provider": f"{self._config.provider}-remote",
            "mode": self._config.mode,
            "base_url": self._config.base_url,
            "timeout_seconds": self._config.timeout_seconds,
            "outbound_request": outbound_request,
        }

    def _execute(self, outbound_request: Dict[str, Any]) -> None:
        """
        Future hook for performing real remote execution.

        This method intentionally performs no network I/O in the current stub.
        It prepares an internal execution contract describing the future HTTP
        call shape and then discards it, serving purely as a structural seam.
        """
        execution_contract = {
            "method": outbound_request.get("method", "POST"),
            "url": outbound_request.get("url"),
            "timeout_seconds": outbound_request.get("timeout_seconds"),
            "headers": {},
            "body": outbound_request.get("body"),
        }
        # The execution_contract is not used further in the stub implementation.
        _ = execution_contract
        return None


def _create_transport(config: GILEConfig) -> GILETransport:
    """
    Internal transport factory used by the adapter.

    Selects the appropriate concrete transport based on configuration while
    keeping the selection logic out of individual transport implementations.
    """
    if config.transport_mode == "remote":
        return _RemoteGILETransport(config)
    return _LocalGILETransport(config)


class GILEAdapter:
    """
    Thin, deterministic adapter skeleton for the GILE service.

    This class acts as the runtime-facing abstraction over the future real
    GILE API. In this initial version it does not perform any network calls
    or LLM logic and instead returns a fixed, contract-aligned response.
    """

    def __init__(self) -> None:
        # Future configuration (base URL, auth, client, etc.) can live here.
        self._config = GILEConfig()
        self._version = self._config.version
        self._transport = _create_transport(self._config)

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
        endpoint = self._endpoint_for_action(action)

        # Normalize a simple source/body field from known payload shapes.
        if "draft_text" in payload:
            body = payload.get("draft_text") or ""
        elif "message_text" in payload:
            body = payload.get("message_text") or ""
        else:
            body = payload.get("text") or ""

        # Pass through metadata/context when present; otherwise use empty dicts.
        metadata = payload.get("metadata") or {}
        context = payload.get("context") or {}

        return {
            "action": action,
            "endpoint": endpoint,
            "body": body,
            "metadata": metadata,
            "context": context,
            # Preserve the original payload structure for backward-compatible
            # transport behavior and any consumers that rely on it.
            "payload": payload,
        }

    def _endpoint_for_action(self, action: str) -> str:
        """
        Map high-level GILE actions to logical endpoint/operation names.
        """
        if action == "translate":
            return "/translate"
        if action == "rewrite":
            return "/rewrite"
        if action == "validate":
            return "/validate"
        # institutional_rewrite and any unknown actions fall back to a
        # generic refinement endpoint.
        return "/institutional_rewrite"

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

        The internal transport is invoked here so that all per-action handlers
        share the same normalization flow. The returned raw response is not
        yet used to shape the public contract, keeping behavior identical to
        the previous stub.
        """
        raw_response = self._transport.send(request)

        # Prefer the action echoed back by the transport (if any), otherwise
        # fall back to the adapter's internal request action. This keeps the
        # current behavior identical while ensuring the raw transport result
        # is actually consulted.
        action = raw_response.get("action") or request.get("action", "institutional_rewrite")
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
    adapter = create_gile_adapter()
    return adapter.handle(payload)


def create_gile_adapter() -> GILEAdapter:
    """
    Public helper for constructing a GILEAdapter instance.

    This provides a single, controlled seam for adapter instantiation while
    allowing tests and integration code to obtain a configured adapter
    without duplicating construction details.
    """
    return GILEAdapter()

