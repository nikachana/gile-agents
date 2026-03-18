from copy import deepcopy

import pytest

from runtime.orchestration.orchestrator import run_orchestrator


def _make_request() -> dict:
    return {
        "message_text": "Draft a response",
        "metadata": {},
        "context": {},
    }


def _make_router_output(task_type: str = "document_draft") -> dict:
    return {
        "task_type": task_type,
        "route_to": "planner",
        "confidence": 0.99,
        "reasoning_summary": "Planner route.",
        "handoff_payload": {
            "message_text": "Please draft a formal response.",
            "metadata": {"language": "en"},
            "context": {"source": "unit_test"},
        },
    }


def _make_valid_planner_output(source_payload: dict) -> dict:
    return {
        "intent": "communication",
        "sections": [
            {
                "id": "intro",
                "title": "Introduction",
                "purpose": "Open the draft.",
                "required": True,
            }
        ],
        "draft_instructions": {
            "language": "en",
            "tone": "formal",
            "constraints": [],
        },
        "source_payload": deepcopy(source_payload),
    }


def test_reply_output_requires_gile_false_does_not_call_gile():
    request = _make_request()
    router_output = _make_router_output()
    planner_output = _make_valid_planner_output(router_output["handoff_payload"])
    reply_output = {
        "requires_gile": False,
    }
    counters = {
        "planner_calls": 0,
        "reply_calls": 0,
        "gile_calls": 0,
    }

    def fake_router(_request):
        return deepcopy(router_output)

    def fake_planner(handoff_payload):
        counters["planner_calls"] += 1
        assert handoff_payload == router_output["handoff_payload"]
        return deepcopy(planner_output)

    def fake_reply_agent(*args, **kwargs):
        counters["reply_calls"] += 1
        return deepcopy(reply_output)

    def fake_gile_client(payload):
        counters["gile_calls"] += 1
        return {"status": "ok", "content": "handled by gile"}

    result = run_orchestrator(
        request=request,
        router=fake_router,
        planner=fake_planner,
        reply_agent=fake_reply_agent,
        gile_client=fake_gile_client,
    )

    assert result["status"] == "ok"
    assert result["workflow"]["route"] == "planner_reply"
    assert counters["planner_calls"] == 1
    assert counters["reply_calls"] == 1
    assert counters["gile_calls"] == 0


def test_reply_output_requires_gile_true_valid_handoff_calls_gile_verbatim():
    request = _make_request()
    router_output = _make_router_output()
    planner_output = _make_valid_planner_output(router_output["handoff_payload"])
    reply_output = {
        "requires_gile": True,
        "draft_text": "Draft body for GILE post-processing.",
        "draft_language": "en",
        "draft_type": "official_letter",
        "gile_action": "rewrite",
        "source_plan": {
            "plan_id": "plan-001",
            "sections": ["intro"],
        },
    }
    counters = {
        "planner_calls": 0,
        "reply_calls": 0,
        "gile_calls": 0,
    }
    captured = {}

    def fake_router(_request):
        return deepcopy(router_output)

    def fake_planner(handoff_payload):
        counters["planner_calls"] += 1
        assert handoff_payload == router_output["handoff_payload"]
        return deepcopy(planner_output)

    def fake_reply_agent(*args, **kwargs):
        counters["reply_calls"] += 1
        return reply_output

    def fake_gile_client(payload):
        counters["gile_calls"] += 1
        captured["payload"] = payload
        return {"status": "ok", "content": "handled by gile"}

    result = run_orchestrator(
        request=request,
        router=fake_router,
        planner=fake_planner,
        reply_agent=fake_reply_agent,
        gile_client=fake_gile_client,
    )

    assert result["status"] == "ok"
    assert result["workflow"]["route"] == "planner_reply_gile"
    assert counters["planner_calls"] == 1
    assert counters["reply_calls"] == 1
    assert counters["gile_calls"] == 1
    assert captured["payload"] is reply_output
    assert captured["payload"] == reply_output


@pytest.mark.parametrize("missing_field", ["draft_text", "draft_language", "draft_type", "gile_action"])
def test_reply_output_requires_gile_true_invalid_handoff_does_not_call_gile(missing_field):
    request = _make_request()
    router_output = _make_router_output()
    planner_output = _make_valid_planner_output(router_output["handoff_payload"])
    reply_output = {
        "requires_gile": True,
        "draft_text": "Draft body for GILE post-processing.",
        "draft_language": "en",
        "draft_type": "official_letter",
        "gile_action": "rewrite",
    }
    reply_output.pop(missing_field)
    counters = {
        "planner_calls": 0,
        "reply_calls": 0,
        "gile_calls": 0,
    }

    def fake_router(_request):
        return deepcopy(router_output)

    def fake_planner(handoff_payload):
        counters["planner_calls"] += 1
        assert handoff_payload == router_output["handoff_payload"]
        return deepcopy(planner_output)

    def fake_reply_agent(*args, **kwargs):
        counters["reply_calls"] += 1
        return deepcopy(reply_output)

    def fake_gile_client(payload):
        counters["gile_calls"] += 1
        return {"status": "ok", "content": "handled by gile"}

    result = run_orchestrator(
        request=request,
        router=fake_router,
        planner=fake_planner,
        reply_agent=fake_reply_agent,
        gile_client=fake_gile_client,
    )

    assert result["status"] == "error"
    assert result["error"]["code"] == "invalid_reply_output"
    assert result["workflow"]["route"] == "planner_reply_flow"
    assert counters["planner_calls"] == 1
    assert counters["reply_calls"] == 1
    assert counters["gile_calls"] == 0


def test_reply_output_missing_requires_gile_is_invalid():
    request = _make_request()
    router_output = _make_router_output()
    planner_output = _make_valid_planner_output(router_output["handoff_payload"])
    reply_output = {}
    counters = {
        "planner_calls": 0,
        "reply_calls": 0,
        "gile_calls": 0,
    }

    def fake_router(_request):
        return deepcopy(router_output)

    def fake_planner(handoff_payload):
        counters["planner_calls"] += 1
        assert handoff_payload == router_output["handoff_payload"]
        return deepcopy(planner_output)

    def fake_reply_agent(*args, **kwargs):
        counters["reply_calls"] += 1
        return deepcopy(reply_output)

    def fake_gile_client(payload):
        counters["gile_calls"] += 1
        return {"status": "ok", "content": "handled by gile"}

    result = run_orchestrator(
        request=request,
        router=fake_router,
        planner=fake_planner,
        reply_agent=fake_reply_agent,
        gile_client=fake_gile_client,
    )

    assert result["status"] == "error"
    assert result["error"]["code"] == "invalid_reply_output"
    assert result["workflow"]["route"] == "planner_reply_flow"
    assert counters["planner_calls"] == 1
    assert counters["reply_calls"] == 1
    assert counters["gile_calls"] == 0


def test_reply_output_requires_gile_must_be_boolean():
    request = _make_request()
    router_output = _make_router_output()
    planner_output = _make_valid_planner_output(router_output["handoff_payload"])
    reply_output = {
        "requires_gile": "yes",
    }
    counters = {
        "planner_calls": 0,
        "reply_calls": 0,
        "gile_calls": 0,
    }

    def fake_router(_request):
        return deepcopy(router_output)

    def fake_planner(handoff_payload):
        counters["planner_calls"] += 1
        assert handoff_payload == router_output["handoff_payload"]
        return deepcopy(planner_output)

    def fake_reply_agent(*args, **kwargs):
        counters["reply_calls"] += 1
        return deepcopy(reply_output)

    def fake_gile_client(payload):
        counters["gile_calls"] += 1
        return {"status": "ok", "content": "handled by gile"}

    result = run_orchestrator(
        request=request,
        router=fake_router,
        planner=fake_planner,
        reply_agent=fake_reply_agent,
        gile_client=fake_gile_client,
    )

    assert result["status"] == "error"
    assert result["error"]["code"] == "invalid_reply_output"
    assert result["workflow"]["route"] == "planner_reply_flow"
    assert counters["planner_calls"] == 1
    assert counters["reply_calls"] == 1
    assert counters["gile_calls"] == 0

