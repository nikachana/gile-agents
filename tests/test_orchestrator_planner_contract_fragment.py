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


def _make_minimal_valid_planner_output(source_payload: dict) -> dict:
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


def _make_valid_reply_output() -> dict:
    return {
        "draft_text": "Here is the draft response.",
        "draft_language": "en",
        "draft_type": "email",
        "requires_gile": False,
        "gile_action": "rewrite",
        "source_plan": {"plan_id": "p-1"},
    }


def test_valid_minimal_planner_fragment_allows_reply_boundary_progression():
    request = _make_request()
    router_output = _make_router_output()
    planner_output = _make_minimal_valid_planner_output(router_output["handoff_payload"])
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
        return deepcopy(_make_valid_reply_output())

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


@pytest.mark.parametrize("missing_field", ["intent", "sections", "draft_instructions"])
def test_invalid_planner_output_missing_required_top_level_field(missing_field):
    request = _make_request()
    router_output = _make_router_output()
    planner_output = _make_minimal_valid_planner_output(router_output["handoff_payload"])
    planner_output.pop(missing_field)
    counters = {
        "planner_calls": 0,
        "reply_calls": 0,
        "gile_calls": 0,
    }

    def fake_router(_request):
        return deepcopy(router_output)

    def fake_planner(handoff_payload):
        counters["planner_calls"] += 1
        return deepcopy(planner_output)

    def fake_reply_agent(*args, **kwargs):
        counters["reply_calls"] += 1
        return deepcopy(_make_valid_reply_output())

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
    assert result["error"]["code"] == "invalid_planner_output"
    assert result["workflow"]["route"] == "planner_reply_flow"
    assert counters["planner_calls"] == 1
    assert counters["reply_calls"] == 0
    assert counters["gile_calls"] == 0


@pytest.mark.parametrize("missing_field", ["id", "title", "purpose", "required"])
def test_invalid_planner_output_invalid_section_item_shape(missing_field):
    request = _make_request()
    router_output = _make_router_output()
    planner_output = _make_minimal_valid_planner_output(router_output["handoff_payload"])
    planner_output["sections"][0].pop(missing_field)
    counters = {
        "planner_calls": 0,
        "reply_calls": 0,
        "gile_calls": 0,
    }

    def fake_router(_request):
        return deepcopy(router_output)

    def fake_planner(handoff_payload):
        counters["planner_calls"] += 1
        return deepcopy(planner_output)

    def fake_reply_agent(*args, **kwargs):
        counters["reply_calls"] += 1
        return deepcopy(_make_valid_reply_output())

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
    assert result["error"]["code"] == "invalid_planner_output"
    assert result["workflow"]["route"] == "planner_reply_flow"
    assert counters["planner_calls"] == 1
    assert counters["reply_calls"] == 0
    assert counters["gile_calls"] == 0


@pytest.mark.parametrize("missing_field", ["language", "tone", "constraints"])
def test_invalid_planner_output_invalid_draft_instructions_shape(missing_field):
    request = _make_request()
    router_output = _make_router_output()
    planner_output = _make_minimal_valid_planner_output(router_output["handoff_payload"])
    planner_output["draft_instructions"].pop(missing_field)
    counters = {
        "planner_calls": 0,
        "reply_calls": 0,
        "gile_calls": 0,
    }

    def fake_router(_request):
        return deepcopy(router_output)

    def fake_planner(handoff_payload):
        counters["planner_calls"] += 1
        return deepcopy(planner_output)

    def fake_reply_agent(*args, **kwargs):
        counters["reply_calls"] += 1
        return deepcopy(_make_valid_reply_output())

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
    assert result["error"]["code"] == "invalid_planner_output"
    assert result["workflow"]["route"] == "planner_reply_flow"
    assert counters["planner_calls"] == 1
    assert counters["reply_calls"] == 0
    assert counters["gile_calls"] == 0


def test_valid_planner_output_with_tolerated_extra_top_level_fields_still_passes():
    request = _make_request()
    router_output = _make_router_output()
    planner_output = _make_minimal_valid_planner_output(router_output["handoff_payload"])
    planner_output.update(
        {
            "document_format": "email",
            "format_variant": "stub_default",
            "confidence": 0.98,
            "reasoning_summary": "This extra metadata should be tolerated.",
            "risk_flags": [],
        }
    )
    counters = {
        "planner_calls": 0,
        "reply_calls": 0,
        "gile_calls": 0,
    }

    def fake_router(_request):
        return deepcopy(router_output)

    def fake_planner(handoff_payload):
        counters["planner_calls"] += 1
        return deepcopy(planner_output)

    def fake_reply_agent(*args, **kwargs):
        counters["reply_calls"] += 1
        return deepcopy(_make_valid_reply_output())

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

