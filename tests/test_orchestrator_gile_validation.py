import os
import sys
from typing import Any, Dict

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from runtime.orchestration.orchestrator import run_orchestrator
from runtime.stubs.router_stub import router as default_router
from runtime.stubs.planner_stub import planner as default_planner


BASE_REQUEST: Dict[str, Any] = {
    "message_text": "Test message",
    "metadata": {},
    "context": {},
}


def _make_gile_spy():
    calls = {"count": 0, "last_payload": None}

    def _gile_client(payload: Dict[str, Any]) -> Dict[str, Any]:
        calls["count"] += 1
        calls["last_payload"] = payload
        return {"text": "spy"}

    return _gile_client, calls


# --- Direct GILE flow: invalid router handoff payloads ---


def _run_with_router(router_fn, gile_client, *, mode: str = "translate"):
    return run_orchestrator(
        request={**BASE_REQUEST, "metadata": {"mode": mode}},
        router=router_fn,
        planner=default_planner,
        reply_agent=lambda po: po,  # not used in direct flow
        gile_client=gile_client,
    )


def test_direct_gile_invalid_handoff_not_dict():
    def bad_router(_request: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "task_type": "translate",
            "route_to": "gile",
            "confidence": 1.0,
            "reasoning_summary": "bad handoff payload (not dict)",
            "handoff_payload": "not a dict",
        }

    gile_client, calls = _make_gile_spy()
    result = _run_with_router(bad_router, gile_client)

    assert result["status"] == "error"
    assert result["error"]["code"] == "invalid_router_output"
    workflow = result["workflow"]
    assert workflow["task_type"] == "translate"
    assert workflow["route"] is None
    trace = result.get("trace")
    assert isinstance(trace, list)
    assert "validation_failed_router" in trace
    assert calls["count"] == 0


def test_direct_gile_invalid_handoff_missing_message_text():
    def bad_router(_request: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "task_type": "translate",
            "route_to": "gile",
            "confidence": 1.0,
            "reasoning_summary": "missing message_text",
            "handoff_payload": {
                # "message_text" intentionally omitted
                "metadata": {},
                "context": {},
            },
        }

    gile_client, calls = _make_gile_spy()
    result = _run_with_router(bad_router, gile_client)

    assert result["status"] == "error"
    assert result["error"]["code"] == "invalid_router_output"
    workflow = result["workflow"]
    assert workflow["task_type"] == "translate"
    assert workflow["route"] is None
    trace = result.get("trace")
    assert isinstance(trace, list)
    assert "validation_failed_router" in trace
    assert calls["count"] == 0


def test_direct_gile_invalid_handoff_missing_metadata():
    def bad_router(_request: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "task_type": "translate",
            "route_to": "gile",
            "confidence": 1.0,
            "reasoning_summary": "missing metadata",
            "handoff_payload": {
                "message_text": "ok",
                # "metadata" intentionally omitted
                "context": {},
            },
        }

    gile_client, calls = _make_gile_spy()
    result = _run_with_router(bad_router, gile_client)

    assert result["status"] == "error"
    assert result["error"]["code"] == "invalid_router_output"
    workflow = result["workflow"]
    assert workflow["task_type"] == "translate"
    assert workflow["route"] is None
    trace = result.get("trace")
    assert isinstance(trace, list)
    assert "validation_failed_router" in trace
    assert calls["count"] == 0


def test_direct_gile_invalid_handoff_missing_context():
    def bad_router(_request: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "task_type": "translate",
            "route_to": "gile",
            "confidence": 1.0,
            "reasoning_summary": "missing context",
            "handoff_payload": {
                "message_text": "ok",
                "metadata": {},
                # "context" intentionally omitted
            },
        }

    gile_client, calls = _make_gile_spy()
    result = _run_with_router(bad_router, gile_client)


def test_document_summarize_invalid_handoff_missing_message_text():
    def bad_router(_request: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "task_type": "document_summarize",
            "route_to": "gile",
            "confidence": 1.0,
            "reasoning_summary": "missing message_text for summarize",
            "handoff_payload": {
                # "message_text" intentionally omitted
                "metadata": {},
                "context": {},
            },
        }

    gile_client, calls = _make_gile_spy()
    result = _run_with_router(bad_router, gile_client, mode="document_summarize")

    assert result["status"] == "error"
    assert result["error"]["code"] == "invalid_router_output"
    workflow = result["workflow"]
    assert workflow["task_type"] == "document_summarize"
    assert workflow["route"] is None
    trace = result.get("trace")
    assert isinstance(trace, list)
    assert "validation_failed_router" in trace
    assert calls["count"] == 0


# --- Reply-driven flow: invalid reply outputs when requires_gile is True ---


def _run_document_draft(router_fn, reply_agent_fn, gile_client):
    return run_orchestrator(
        request=BASE_REQUEST,
        router=router_fn,
        planner=default_planner,
        reply_agent=reply_agent_fn,
        gile_client=gile_client,
    )


def _document_draft_router(request: Dict[str, Any]) -> Dict[str, Any]:
    # Reuse the default router behavior but force document_draft mode.
    forced = dict(request)
    forced.setdefault("metadata", {})
    forced["metadata"]["mode"] = None  # ensures router chooses document_draft
    return default_router(forced)


def test_reply_gile_invalid_reply_not_dict():
    def bad_reply_agent(_planner_output: Dict[str, Any]):
        # Not a dict, so reply validation should fail before any GILE call.
        return "not a dict"

    gile_client, calls = _make_gile_spy()
    result = _run_document_draft(_document_draft_router, bad_reply_agent, gile_client)

    assert result["status"] == "error"
    assert result["error"]["code"] == "invalid_reply_output"
    workflow = result["workflow"]
    assert workflow["task_type"] == "document_draft"
    assert workflow["route"] == "planner_reply_flow"
    trace = result.get("trace")
    assert isinstance(trace, list)
    assert "validation_failed_reply" in trace
    assert calls["count"] == 0


def test_reply_gile_invalid_reply_missing_draft_text():
    def bad_reply_agent(planner_output: Dict[str, Any]):
        reply = {
            # "draft_text" intentionally omitted
            "draft_language": "en",
            "draft_type": "generic",
            "requires_gile": True,
            "gile_action": "institutional_rewrite",
            "source_plan": planner_output,
        }
        return reply

    gile_client, calls = _make_gile_spy()
    result = _run_document_draft(_document_draft_router, bad_reply_agent, gile_client)

    assert result["status"] == "error"
    assert result["error"]["code"] == "invalid_reply_output"
    workflow = result["workflow"]
    assert workflow["task_type"] == "document_draft"
    assert workflow["route"] == "planner_reply_flow"
    trace = result.get("trace")
    assert isinstance(trace, list)
    assert "validation_failed_reply" in trace
    assert calls["count"] == 0


def test_reply_gile_invalid_reply_missing_draft_language():
    def bad_reply_agent(planner_output: Dict[str, Any]):
        reply = {
            "draft_text": "text",
            # "draft_language" intentionally omitted
            "draft_type": "generic",
            "requires_gile": True,
            "gile_action": "institutional_rewrite",
            "source_plan": planner_output,
        }
        return reply

    gile_client, calls = _make_gile_spy()
    result = _run_document_draft(_document_draft_router, bad_reply_agent, gile_client)

    assert result["status"] == "error"
    assert result["error"]["code"] == "invalid_reply_output"
    workflow = result["workflow"]
    assert workflow["task_type"] == "document_draft"
    assert workflow["route"] == "planner_reply_flow"
    trace = result.get("trace")
    assert isinstance(trace, list)
    assert "validation_failed_reply" in trace
    assert calls["count"] == 0


def test_reply_gile_invalid_reply_missing_draft_type():
    def bad_reply_agent(planner_output: Dict[str, Any]):
        reply = {
            "draft_text": "text",
            "draft_language": "en",
            # "draft_type" intentionally omitted
            "requires_gile": True,
            "gile_action": "institutional_rewrite",
            "source_plan": planner_output,
        }
        return reply

    gile_client, calls = _make_gile_spy()
    result = _run_document_draft(_document_draft_router, bad_reply_agent, gile_client)

    assert result["status"] == "error"
    assert result["error"]["code"] == "invalid_reply_output"
    workflow = result["workflow"]
    assert workflow["task_type"] == "document_draft"
    assert workflow["route"] == "planner_reply_flow"
    trace = result.get("trace")
    assert isinstance(trace, list)
    assert "validation_failed_reply" in trace
    assert calls["count"] == 0


def test_reply_gile_invalid_reply_missing_gile_action():
    def bad_reply_agent(planner_output: Dict[str, Any]):
        reply = {
            "draft_text": "text",
            "draft_language": "en",
            "draft_type": "generic",
            "requires_gile": True,
            # "gile_action" intentionally omitted
            "source_plan": planner_output,
        }
        return reply

    gile_client, calls = _make_gile_spy()
    result = _run_document_draft(_document_draft_router, bad_reply_agent, gile_client)

    assert result["status"] == "error"
    assert result["error"]["code"] == "invalid_reply_output"
    workflow = result["workflow"]
    assert workflow["task_type"] == "document_draft"
    assert workflow["route"] == "planner_reply_flow"
    trace = result.get("trace")
    assert isinstance(trace, list)
    assert "validation_failed_reply" in trace
    assert calls["count"] == 0

