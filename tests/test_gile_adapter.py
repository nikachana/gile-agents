import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from runtime.stubs.gile_stub import gile_client, _GILEConfig, _GILETransport


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
    config = _GILEConfig()

    assert config.transport_mode == "local"
    assert config.mode == "local"
    assert config.provider == "stub"
    assert config.version == "stub_v1"


def test_gile_local_transport_send_shape():
    config = _GILEConfig()
    transport = _GILETransport(config)

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
    transport = _GILETransport(config)

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

