import os
import sys
from copy import deepcopy

import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from runtime.orchestration.orchestrator import run_orchestrator


def _make_request(mode: str) -> dict:
    return {
        "message_text": f"{mode} this",
        "metadata": {"mode": mode},
        "context": {"source": "unit_test"},
    }


@pytest.mark.parametrize("mode", ["translate", "rewrite", "validate"])
def test_direct_gile_flow_passes_router_handoff_payload_verbatim(mode: str):
    request = _make_request(mode)

    handoff_payload = {
        "message_text": "payload message",
        "metadata": {"mode": mode, "extra": {"k": "v"}},
        "context": {"ctx": 1},
    }
    router_output = {
        "task_type": mode,
        "route_to": "gile",
        "confidence": 1.0,
        "reasoning_summary": "direct gile test router",
        "handoff_payload": handoff_payload,
    }

    calls = {"gile_calls": 0, "last_payload": None}

    def fake_router(_request: dict) -> dict:
        assert _request == request
        return router_output

    def fake_planner(_payload: dict) -> dict:  # pragma: no cover
        raise AssertionError("planner should not be called in direct GILE flow")

    def fake_reply_agent(_planner_output: dict) -> dict:  # pragma: no cover
        raise AssertionError("reply_agent should not be called in direct GILE flow")

    def fake_gile_client(payload: dict) -> dict:
        calls["gile_calls"] += 1
        calls["last_payload"] = payload
        return {"text": "ok"}

    result = run_orchestrator(
        request=request,
        router=fake_router,
        planner=fake_planner,
        reply_agent=fake_reply_agent,
        gile_client=fake_gile_client,
    )

    assert result["status"] == "ok"
    assert result["workflow"]["task_type"] == mode
    assert result["workflow"]["route"] == "direct_gile"
    assert calls["gile_calls"] == 1

    # Verbatim: same object reference and same content.
    assert calls["last_payload"] is handoff_payload
    assert calls["last_payload"] == handoff_payload


def test_document_draft_requires_gile_passes_reply_output_verbatim():
    request = _make_request("document_draft")

    router_output = {
        "task_type": "document_draft",
        "route_to": "planner",
        "confidence": 1.0,
        "reasoning_summary": "planner route",
        "handoff_payload": {
            "message_text": "draft this",
            "metadata": {"mode": "document_draft"},
            "context": {},
        },
    }

    planner_output = {
        # Minimal frozen planner fragment + tolerated extra fields.
        "intent": "communication",
        "sections": [
            {
                "id": "s1",
                "title": "Body",
                "purpose": "Main content",
                "required": True,
            }
        ],
        "draft_instructions": {
            "language": "en",
            "tone": "formal",
            "constraints": [],
        },
        "document_format": "official_letter",
        "confidence": 1.0,
        "reasoning_summary": "extra tolerated fields",
        "source_payload": deepcopy(router_output["handoff_payload"]),
    }

    reply_output = {
        "draft_text": "Here is a draft.",
        "draft_language": "en",
        "draft_type": "email",
        "requires_gile": True,
        "gile_action": "institutional_rewrite",
        "source_plan": {"plan_id": "p-1"},
        "extra_reply_field": {"k": "v"},
    }

    calls = {"reply_calls": 0, "gile_calls": 0, "last_payload": None}

    def fake_router(_request: dict) -> dict:
        assert _request == request
        return deepcopy(router_output)

    def fake_planner(handoff_payload: dict) -> dict:
        assert handoff_payload == router_output["handoff_payload"]
        return deepcopy(planner_output)

    def fake_reply_agent(_planner_output: dict) -> dict:
        calls["reply_calls"] += 1
        return reply_output

    def fake_gile_client(payload: dict) -> dict:
        calls["gile_calls"] += 1
        calls["last_payload"] = payload
        return {"text": "ok"}

    result = run_orchestrator(
        request=request,
        router=fake_router,
        planner=fake_planner,
        reply_agent=fake_reply_agent,
        gile_client=fake_gile_client,
    )

    assert result["status"] == "ok"
    assert result["workflow"]["task_type"] == "document_draft"
    assert result["workflow"]["route"] == "planner_reply_gile"
    assert calls["reply_calls"] == 1
    assert calls["gile_calls"] == 1

    # Verbatim: same object reference and same content.
    assert calls["last_payload"] is reply_output
    assert calls["last_payload"] == reply_output

