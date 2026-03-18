import os
import sys
from typing import Any, Dict, Tuple

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from runtime.orchestration.orchestrator import run_orchestrator


BASE_REQUEST: Dict[str, Any] = {
    "message_text": "Test message",
    "metadata": {},
    "context": {},
}


def _make_reply_spy(reply_output: Dict[str, Any]):
    calls = {"count": 0}

    def _reply_agent(planner_output: Dict[str, Any]) -> Dict[str, Any]:
        calls["count"] += 1
        return dict(reply_output, source_plan=planner_output)

    return _reply_agent, calls


def _make_gile_spy() -> Tuple[Any, Dict[str, Any]]:
    calls = {"count": 0, "last_payload": None}

    def _gile_client(payload: Dict[str, Any]) -> Dict[str, Any]:
        calls["count"] += 1
        calls["last_payload"] = payload
        return {"text": "spy"}

    return _gile_client, calls


def _document_draft_router(_request: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "task_type": "document_draft",
        "route_to": "planner",
        "confidence": 1.0,
        "reasoning_summary": "forced document_draft for planner->reply tests",
        "handoff_payload": {
            "message_text": "Draft this document",
            "metadata": {},
            "context": {},
        },
    }


def _email_draft_router(_request: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "task_type": "email_draft",
        "route_to": "planner",
        "confidence": 1.0,
        "reasoning_summary": "forced email_draft for planner->reply tests",
        "handoff_payload": {
            "message_text": "Draft this email",
            "metadata": {},
            "context": {},
        },
    }


def _valid_planner_output(source_payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "intent": "draft_document",
        "document_format": "official_letter",
        "confidence": 1.0,
        "reasoning_summary": "minimal valid planner output",
        "sections": [
            {
                "id": "s1",
                "title": "Body",
                "purpose": "Provide the main content.",
                "required": True,
            }
        ],
        "draft_instructions": {
            "tone": "formal_professional",
            "language": "en",
            "constraints": [],
        },
        "source_payload": dict(source_payload),
    }


def test_document_draft_planner_valid_calls_reply_agent_and_not_gile():
    gile_client, gile_calls = _make_gile_spy()

    def planner(router_payload: Dict[str, Any]) -> Dict[str, Any]:
        return _valid_planner_output(router_payload)

    reply_agent, reply_calls = _make_reply_spy(
        {
            "draft_text": "draft",
            "draft_language": "en",
            "draft_type": "generic",
            "requires_gile": False,
            "gile_action": "none",
            "source_plan": {},
        }
    )

    result = run_orchestrator(
        request=BASE_REQUEST,
        router=_document_draft_router,
        planner=planner,
        reply_agent=reply_agent,
        gile_client=gile_client,
    )

    assert result["status"] == "ok"
    assert result["workflow"]["task_type"] == "document_draft"
    assert result["workflow"]["route"] == "planner_reply"
    assert reply_calls["count"] == 1
    assert gile_calls["count"] == 0

    trace = result.get("trace")
    assert isinstance(trace, list)
    assert "planner_called" in trace
    assert "validate_planner_output" in trace
    assert "reply_agent_called" in trace
    assert "validate_reply_output" in trace
    assert "gile_called" not in trace


def test_document_draft_invalid_planner_missing_sections_blocks_reply_and_gile():
    gile_client, gile_calls = _make_gile_spy()
    reply_agent, reply_calls = _make_reply_spy(
        {
            "draft_text": "draft",
            "draft_language": "en",
            "draft_type": "generic",
            "requires_gile": True,
            "gile_action": "institutional_rewrite",
            "source_plan": {},
        }
    )

    def bad_planner(router_payload: Dict[str, Any]) -> Dict[str, Any]:
        out = _valid_planner_output(router_payload)
        out.pop("sections", None)
        return out

    result = run_orchestrator(
        request=BASE_REQUEST,
        router=_document_draft_router,
        planner=bad_planner,
        reply_agent=reply_agent,
        gile_client=gile_client,
    )

    assert result["status"] == "error"
    assert result["error"]["code"] == "invalid_planner_output"
    assert result["workflow"]["task_type"] == "document_draft"
    assert result["workflow"]["route"] == "planner_reply_flow"
    assert reply_calls["count"] == 0
    assert gile_calls["count"] == 0

    trace = result.get("trace")
    assert isinstance(trace, list)
    assert "planner_called" in trace
    assert "validate_planner_output" in trace
    assert "validation_failed_planner" in trace


def test_document_draft_invalid_planner_missing_draft_instructions_blocks_reply_and_gile():
    gile_client, gile_calls = _make_gile_spy()
    reply_agent, reply_calls = _make_reply_spy(
        {
            "draft_text": "draft",
            "draft_language": "en",
            "draft_type": "generic",
            "requires_gile": True,
            "gile_action": "institutional_rewrite",
            "source_plan": {},
        }
    )

    def bad_planner(router_payload: Dict[str, Any]) -> Dict[str, Any]:
        out = _valid_planner_output(router_payload)
        out.pop("draft_instructions", None)
        return out

    result = run_orchestrator(
        request=BASE_REQUEST,
        router=_document_draft_router,
        planner=bad_planner,
        reply_agent=reply_agent,
        gile_client=gile_client,
    )

    assert result["status"] == "error"
    assert result["error"]["code"] == "invalid_planner_output"
    assert result["workflow"]["task_type"] == "document_draft"
    assert result["workflow"]["route"] == "planner_reply_flow"
    assert reply_calls["count"] == 0
    assert gile_calls["count"] == 0

    trace = result.get("trace")
    assert isinstance(trace, list)
    assert "planner_called" in trace
    assert "validate_planner_output" in trace
    assert "validation_failed_planner" in trace


def test_document_draft_planner_valid_reply_requires_gile_calls_gile():
    gile_client, gile_calls = _make_gile_spy()

    def planner(router_payload: Dict[str, Any]) -> Dict[str, Any]:
        return _valid_planner_output(router_payload)

    reply_agent, reply_calls = _make_reply_spy(
        {
            "draft_text": "draft",
            "draft_language": "en",
            "draft_type": "generic",
            "requires_gile": True,
            "gile_action": "institutional_rewrite",
            "source_plan": {},
        }
    )

    result = run_orchestrator(
        request=BASE_REQUEST,
        router=_document_draft_router,
        planner=planner,
        reply_agent=reply_agent,
        gile_client=gile_client,
    )

    assert result["status"] == "ok"
    assert result["workflow"]["task_type"] == "document_draft"
    assert result["workflow"]["route"] == "planner_reply_gile"
    assert reply_calls["count"] == 1
    assert gile_calls["count"] == 1

    trace = result.get("trace")
    assert isinstance(trace, list)
    assert "planner_called" in trace
    assert "validate_planner_output" in trace
    assert "reply_agent_called" in trace
    assert "validate_reply_output" in trace
    assert "planner_reply_gile_path" in trace
    assert "gile_called" in trace


def test_email_draft_planner_valid_calls_reply_agent_and_not_gile():
    gile_client, gile_calls = _make_gile_spy()

    def planner(router_payload: Dict[str, Any]) -> Dict[str, Any]:
        return _valid_planner_output(router_payload)

    reply_agent, reply_calls = _make_reply_spy(
        {
            "draft_text": "draft",
            "draft_language": "en",
            "draft_type": "generic",
            "requires_gile": False,
            "gile_action": "none",
            "source_plan": {},
        }
    )

    result = run_orchestrator(
        request=BASE_REQUEST,
        router=_email_draft_router,
        planner=planner,
        reply_agent=reply_agent,
        gile_client=gile_client,
    )

    assert result["status"] == "ok"
    assert result["workflow"]["task_type"] == "email_draft"
    assert result["workflow"]["route"] == "planner_reply"
    assert reply_calls["count"] == 1
    assert gile_calls["count"] == 0

    trace = result.get("trace")
    assert isinstance(trace, list)
    assert "planner_called" in trace
    assert "validate_planner_output" in trace
    assert "reply_agent_called" in trace
    assert "validate_reply_output" in trace
    assert "gile_called" not in trace


def test_email_draft_planner_valid_reply_requires_gile_calls_gile():
    gile_client, gile_calls = _make_gile_spy()

    def planner(router_payload: Dict[str, Any]) -> Dict[str, Any]:
        return _valid_planner_output(router_payload)

    reply_agent, reply_calls = _make_reply_spy(
        {
            "draft_text": "draft",
            "draft_language": "en",
            "draft_type": "generic",
            "requires_gile": True,
            "gile_action": "institutional_rewrite",
            "source_plan": {},
        }
    )

    result = run_orchestrator(
        request=BASE_REQUEST,
        router=_email_draft_router,
        planner=planner,
        reply_agent=reply_agent,
        gile_client=gile_client,
    )

    assert result["status"] == "ok"
    assert result["workflow"]["task_type"] == "email_draft"
    assert result["workflow"]["route"] == "planner_reply_gile"
    assert reply_calls["count"] == 1
    assert gile_calls["count"] == 1

    trace = result.get("trace")
    assert isinstance(trace, list)
    assert "planner_called" in trace
    assert "validate_planner_output" in trace
    assert "reply_agent_called" in trace
    assert "validate_reply_output" in trace
    assert "planner_reply_gile_path" in trace
    assert "gile_called" in trace


def test_email_draft_invalid_planner_missing_sections_blocks_reply_and_gile():
    gile_client, gile_calls = _make_gile_spy()
    reply_agent, reply_calls = _make_reply_spy(
        {
            "draft_text": "draft",
            "draft_language": "en",
            "draft_type": "generic",
            "requires_gile": True,
            "gile_action": "institutional_rewrite",
            "source_plan": {},
        }
    )

    def bad_planner(router_payload: Dict[str, Any]) -> Dict[str, Any]:
        out = _valid_planner_output(router_payload)
        out.pop("sections", None)
        return out

    result = run_orchestrator(
        request=BASE_REQUEST,
        router=_email_draft_router,
        planner=bad_planner,
        reply_agent=reply_agent,
        gile_client=gile_client,
    )

    assert result["status"] == "error"
    assert result["error"]["code"] == "invalid_planner_output"
    assert result["workflow"]["task_type"] == "email_draft"
    assert result["workflow"]["route"] == "planner_reply_flow"
    assert reply_calls["count"] == 0
    assert gile_calls["count"] == 0

    trace = result.get("trace")
    assert isinstance(trace, list)
    assert "planner_called" in trace
    assert "validate_planner_output" in trace
    assert "validation_failed_planner" in trace


def test_email_draft_invalid_reply_missing_draft_text_blocks_gile():
    gile_client, gile_calls = _make_gile_spy()

    def planner(router_payload: Dict[str, Any]) -> Dict[str, Any]:
        return _valid_planner_output(router_payload)

    def bad_reply_agent(planner_output: Dict[str, Any]):
        # Missing draft_text triggers reply validation failure.
        return {
            "draft_language": "en",
            "draft_type": "generic",
            "requires_gile": True,
            "gile_action": "institutional_rewrite",
            "source_plan": planner_output,
        }

    result = run_orchestrator(
        request=BASE_REQUEST,
        router=_email_draft_router,
        planner=planner,
        reply_agent=bad_reply_agent,
        gile_client=gile_client,
    )

    assert result["status"] == "error"
    assert result["error"]["code"] == "invalid_reply_output"
    assert result["workflow"]["task_type"] == "email_draft"
    assert result["workflow"]["route"] == "planner_reply_flow"
    assert gile_calls["count"] == 0

    trace = result.get("trace")
    assert isinstance(trace, list)
    assert "validation_failed_reply" in trace

