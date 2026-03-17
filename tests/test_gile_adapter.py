import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from runtime.stubs.gile_stub import gile_client
from runtime.gile.adapter import (
    GILEConfig as _GILEConfig,
    GILETransport as _GILETransport,
    _create_transport as _create_transport,
    GILEAdapter as _GILEAdapter,
    create_gile_adapter as _create_gile_adapter,
)


def _call(payload: dict) -> dict:
    """Helper to invoke the public GILE client entry point."""
    return gile_client(payload)


def test_gile_translate_dispatch():
    payload = {
        "metadata": {"mode": "translate"},
        "message_text": "Translate this",
        "context": {},
    }

    result = _call(payload)

    assert isinstance(result, dict)
    assert "text" in result
    assert result.get("gile_action") == "translate"
    assert result.get("gile_version") == "stub_v1"


def test_gile_rewrite_dispatch():
    payload = {
        "metadata": {"mode": "rewrite"},
        "message_text": "Rewrite this",
        "context": {},
    }

    result = _call(payload)

    assert isinstance(result, dict)
    assert "text" in result
    assert result.get("gile_action") == "rewrite"
    assert result.get("gile_version") == "stub_v1"


def test_gile_validate_dispatch():
    payload = {
        "metadata": {"mode": "validate"},
        "message_text": "Validate this",
        "context": {},
    }

    result = _call(payload)

    assert isinstance(result, dict)
    assert "text" in result
    assert result.get("gile_action") == "validate"
    assert result.get("gile_version") == "stub_v1"


def test_gile_institutional_rewrite_from_reply_payload():
    # Simulate reply_agent → GILE handoff by providing gile_action explicitly.
    payload = {
        "draft_text": "Some draft text",
        "draft_language": "en",
        "draft_type": "official_letter",
        "requires_gile": True,
        "gile_action": "institutional_rewrite",
        "source_plan": {},
    }

    result = _call(payload)

    assert isinstance(result, dict)
    assert "text" in result
    assert result.get("gile_action") == "institutional_rewrite"
    assert result.get("gile_version") == "stub_v1"


def test_gile_default_config_uses_local_transport_mode():
    # Ensure environment variables do not interfere with default config.
    keys = [
        "GILE_PROVIDER",
        "GILE_MODE",
        "GILE_TRANSPORT_MODE",
        "GILE_BASE_URL",
        "GILE_TIMEOUT_SECONDS",
    ]
    previous = {k: os.environ.get(k) for k in keys}
    try:
        for k in keys:
            os.environ.pop(k, None)

        config = _GILEConfig()

        assert config.transport_mode == "local"
        assert config.mode == "local"
        assert config.provider == "stub"
        assert config.version == "stub_v1"
    finally:
        for k, v in previous.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def test_gile_local_transport_send_shape():
    config = _GILEConfig()
    transport = _create_transport(config)

    request = {
        "action": "translate",
        "payload": {"message_text": "Translate this"},
    }

    raw = transport.send(request)

    assert isinstance(raw, dict)
    assert raw["action"] == "translate"
    assert raw["payload"] == {"message_text": "Translate this"}
    assert raw["transport_version"] == config.version
    assert raw["provider"] == config.provider
    assert raw["mode"] == config.mode
    assert raw["base_url"] == config.base_url
    assert raw["timeout_seconds"] == config.timeout_seconds


def test_gile_remote_transport_placeholder_shape_compatible():
    config = _GILEConfig()
    config.transport_mode = "remote"
    transport = _create_transport(config)

    request = {
        "action": "rewrite",
        "payload": {"message_text": "Rewrite this"},
    }

    raw = transport.send(request)

    # Shape compatibility with local transport
    assert isinstance(raw, dict)
    assert raw["action"] == "rewrite"
    assert raw["payload"] == {"message_text": "Rewrite this"}
    assert raw["transport_version"] == config.version
    assert "provider" in raw
    assert "mode" in raw
    assert "base_url" in raw
    assert "timeout_seconds" in raw
    # Provider should be distinguishable in remote mode but still a string
    assert isinstance(raw["provider"], str)


def test_gile_config_env_overrides_provider_mode_and_base_url():
    keys = [
        "GILE_PROVIDER",
        "GILE_MODE",
        "GILE_TRANSPORT_MODE",
        "GILE_BASE_URL",
        "GILE_TIMEOUT_SECONDS",
    ]
    previous = {k: os.environ.get(k) for k in keys}
    try:
        os.environ["GILE_PROVIDER"] = "env_provider"
        os.environ["GILE_MODE"] = "staging"
        os.environ["GILE_TRANSPORT_MODE"] = "remote"
        os.environ["GILE_BASE_URL"] = "https://gile.example.test/api"
        os.environ["GILE_TIMEOUT_SECONDS"] = "7.5"
        os.environ["GILE_REMOTE_EXECUTION_ENABLED"] = "true"

        config = _GILEConfig()

        assert config.provider == "env_provider"
        assert config.mode == "staging"
        assert config.transport_mode == "remote"
        assert config.base_url == "https://gile.example.test/api"
        assert config.timeout_seconds == 7.5
        assert config.version == "stub_v1"
    finally:
        for k, v in previous.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def test_gile_config_invalid_timeout_falls_back_to_default():
    keys = [
        "GILE_TIMEOUT_SECONDS",
    ]
    previous = {k: os.environ.get(k) for k in keys}
    try:
        os.environ["GILE_TIMEOUT_SECONDS"] = "not-a-number"
        config = _GILEConfig()
        assert config.timeout_seconds == 5.0
    finally:
        for k, v in previous.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def test_gile_remote_execution_disabled_by_default():
    # Ensure no env flag leaks in
    prev = os.environ.get("GILE_REMOTE_EXECUTION_ENABLED")
    try:
        os.environ.pop("GILE_REMOTE_EXECUTION_ENABLED", None)
        config = _GILEConfig()
        assert config.remote_execution_enabled is False
    finally:
        if prev is None:
            os.environ.pop("GILE_REMOTE_EXECUTION_ENABLED", None)
        else:
            os.environ["GILE_REMOTE_EXECUTION_ENABLED"] = prev


def test_gile_remote_execution_flag_can_be_enabled_without_side_effects():
    prev = os.environ.get("GILE_REMOTE_EXECUTION_ENABLED")
    try:
        os.environ["GILE_REMOTE_EXECUTION_ENABLED"] = "true"
        config = _GILEConfig()
        assert config.remote_execution_enabled is True

        # Even when enabled, the remote transport still behaves as a stub and
        # returns the same raw shape (no network side effects).
        config.transport_mode = "remote"
        transport = _create_transport(config)

        adapter = _GILEAdapter()
        payload = {
            "message_text": "Execution gate test",
            "metadata": {"mode": "rewrite"},
            "context": {},
        }
        request = adapter._build_request(payload, action="rewrite")

        raw = transport.send(request)
        assert "outbound_request" in raw
        # Public gile_client behavior should remain unchanged.
        result = _call(payload)
        assert result.get("text") == "Processed by GILE stub"
        assert result.get("gile_action") == "rewrite"
        assert result.get("gile_version") == "stub_v1"
    finally:
        if prev is None:
            os.environ.pop("GILE_REMOTE_EXECUTION_ENABLED", None)
        else:
            os.environ["GILE_REMOTE_EXECUTION_ENABLED"] = prev


def test_gile_client_behavior_unaffected_by_transport_seam():
    # Even if we prepare a payload that could, in future, influence config,
    # the public gile_client contract should remain the same.
    payload = {
        "metadata": {"mode": "translate"},
        "message_text": "Translate this",
        "context": {},
    }

    result = _call(payload)

    assert isinstance(result, dict)
    assert result.get("text") == "Processed by GILE stub"
    assert result.get("gile_action") == "translate"
    assert result.get("gile_version") == "stub_v1"


def test_create_gile_adapter_returns_configured_adapter():
    adapter = _create_gile_adapter()
    assert isinstance(adapter, _GILEAdapter)

    payload = {
        "metadata": {"mode": "translate"},
        "message_text": "Factory helper test",
        "context": {},
    }
    result = adapter.handle(payload)
    assert result.get("text") == "Processed by GILE stub"
    assert result.get("gile_action") == "translate"


def test_gile_adapter_normalize_response_uses_transport_action_echo():
    config = _GILEConfig()
    transport = _create_transport(config)
    adapter = _GILEAdapter()

    request = {
        "action": "validate",
        "endpoint": "/validate",
        "body": "Body",
        "metadata": {},
        "context": {},
        "payload": {},
    }

    # Sanity check: transport echoes the same action we pass in.
    raw = transport.send(request)
    assert raw["action"] == "validate"

    # _normalize_response should reflect the transport's echoed action
    # (which is currently identical to the request action).
    normalized = adapter._normalize_response(request)
    assert normalized["gile_action"] == "validate"


def test_gile_remote_transport_prepares_outbound_request_shape():
    config = _GILEConfig()
    config.transport_mode = "remote"
    transport = _create_transport(config)

    adapter = _GILEAdapter()
    # Build a realistic internal request using the adapter helper
    payload = {
        "message_text": "Remote path test",
        "metadata": {"mode": "rewrite"},
        "context": {"case_id": "CASE-2"},
    }
    request = adapter._build_request(payload, action="rewrite")

    raw = transport.send(request)
    outbound = raw.get("outbound_request")

    assert isinstance(outbound, dict)
    assert outbound["method"] == "POST"
    assert outbound["url"].startswith(config.base_url)
    assert outbound["endpoint"] == "/rewrite"
    assert outbound["body"] == "Remote path test"
    assert outbound["metadata"] == {"mode": "rewrite"}
    assert outbound["context"] == {"case_id": "CASE-2"}

import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from runtime.stubs.gile_stub import GILEAdapter, gile_client


def _call(payload):
    """
    Helper to call the public gile_client entry point.
    """
    return gile_client(payload)


def test_gile_translate_dispatch():
    payload = {
        "metadata": {"mode": "translate"},
        "message_text": "Translate this",
        "context": {},
    }

    result = _call(payload)

    assert isinstance(result, dict)
    assert "text" in result
    assert result.get("gile_action") == "translate"
    assert result.get("gile_version") == "stub_v1"


def test_gile_rewrite_dispatch():
    payload = {
        "metadata": {"mode": "rewrite"},
        "message_text": "Rewrite this",
        "context": {},
    }

    result = _call(payload)

    assert isinstance(result, dict)
    assert "text" in result
    assert result.get("gile_action") == "rewrite"
    assert result.get("gile_version") == "stub_v1"


def test_gile_validate_dispatch():
    payload = {
        "metadata": {"mode": "validate"},
        "message_text": "Validate this",
        "context": {},
    }

    result = _call(payload)

    assert isinstance(result, dict)
    assert "text" in result
    assert result.get("gile_action") == "validate"
    assert result.get("gile_version") == "stub_v1"


def test_gile_unknown_defaults_to_institutional_rewrite():
    # Payload without explicit mode or gile_action should fall back to
    # the safe institutional_rewrite behavior.
    payload = {
        "message_text": "Some text",
        "metadata": {},
        "context": {},
    }

    result = _call(payload)

    assert isinstance(result, dict)
    assert "text" in result
    assert result.get("gile_action") == "institutional_rewrite"
    assert result.get("gile_version") == "stub_v1"


def test_gile_adapter_build_request_router_style_payload():
    adapter = _GILEAdapter()
    payload = {
        "message_text": "Router-style message",
        "metadata": {"mode": "translate", "foo": "bar"},
        "context": {"case_id": "CASE-1"},
    }

    request = adapter._build_request(payload, action="translate")

    assert request["action"] == "translate"
    assert request["endpoint"] == "/translate"
    assert request["body"] == "Router-style message"
    assert request["metadata"] == {"mode": "translate", "foo": "bar"}
    assert request["context"] == {"case_id": "CASE-1"}
    # Legacy payload passthrough preserved
    assert request["payload"] is payload


def test_gile_adapter_build_request_reply_style_payload():
    adapter = _GILEAdapter()
    payload = {
        "draft_text": "Reply draft text",
        "draft_language": "en",
        "draft_type": "official_letter",
        "requires_gile": True,
        "gile_action": "institutional_rewrite",
        "source_plan": {},
    }

    request = adapter._build_request(payload, action="institutional_rewrite")

    assert request["action"] == "institutional_rewrite"
    assert request["endpoint"] == "/institutional_rewrite"
    assert request["body"] == "Reply draft text"
    # No metadata/context in this shape, so they should be empty dicts
    assert request["metadata"] == {}
    assert request["context"] == {}
    assert request["payload"] is payload

