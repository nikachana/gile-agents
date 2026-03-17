import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from runtime.orchestration.orchestrator import run_orchestrator
from runtime.stubs.router_stub import router
from runtime.stubs.planner_stub import planner
from runtime.stubs.reply_agent_stub import reply_agent
from runtime.stubs.gile_stub import gile_client


def _run(request: dict) -> dict:
    return run_orchestrator(
        request=request,
        router=router,
        planner=planner,
        reply_agent=reply_agent,
        gile_client=gile_client,
    )


def test_translate_direct_gile():
    result = _run(
        {
            "message_text": "Translate this",
            "metadata": {"mode": "translate"},
            "context": {},
        }
    )

    assert result["status"] == "ok"
    assert result["workflow"]["task_type"] == "translate"
    assert result["workflow"]["route"] == "direct_gile"

    artifacts = result["artifacts"]
    assert artifacts["router_output"] is not None
    assert artifacts["planner_output"] is None
    assert artifacts["reply_output"] is None

    final_output = result["final_output"]
    assert isinstance(final_output, dict)
    assert "text" in final_output


def test_document_plan_planner_only():
    result = _run(
        {
            "message_text": "Plan this document",
            "metadata": {"mode": "document_plan"},
            "context": {},
        }
    )

    assert result["status"] == "ok"
    assert result["workflow"]["task_type"] == "document_plan"
    assert result["workflow"]["route"] == "planner_only"

    artifacts = result["artifacts"]
    assert artifacts["router_output"] is not None
    assert artifacts["planner_output"] is not None
    assert artifacts["reply_output"] is None

    final_output = result["final_output"]
    assert isinstance(final_output, dict)
    # planner_only returns the plan artifact as final_output
    assert "sections" in final_output
    assert "draft_instructions" in final_output


def test_document_draft_planner_reply_gile():
    result = _run(
        {
            "message_text": "Draft this document",
            "metadata": {},
            "context": {},
        }
    )

    assert result["status"] == "ok"
    assert result["workflow"]["task_type"] == "document_draft"
    assert result["workflow"]["route"] == "planner_reply_gile"

    artifacts = result["artifacts"]
    assert artifacts["router_output"] is not None
    assert artifacts["planner_output"] is not None
    assert artifacts["reply_output"] is not None

    final_output = result["final_output"]
    # For document_draft with requires_gile=True, final_output comes from gile_client
    assert isinstance(final_output, dict)
    assert final_output.get("text") == "Processed by GILE stub"


def test_reply_draft_planner_reply():
    result = _run(
        {
            "message_text": "Reply to this message",
            "metadata": {"mode": "reply_draft"},
            "context": {},
        }
    )

    assert result["status"] == "ok"
    assert result["workflow"]["task_type"] == "reply_draft"
    assert result["workflow"]["route"] == "planner_reply"

    artifacts = result["artifacts"]
    assert artifacts["router_output"] is not None
    assert artifacts["planner_output"] is not None
    assert artifacts["reply_output"] is not None

    final_output = result["final_output"]
    # For reply_draft with requires_gile=False, final_output is the reply artifact
    assert isinstance(final_output, dict)
    assert final_output.get("draft_text", "").startswith("[official_letter]")
    assert final_output.get("requires_gile") is False


def test_needs_clarification_clarification_route():
    result = _run(
        {
            "message_text": "   ",
            "metadata": {},
            "context": {},
        }
    )

    assert result["status"] == "clarification_required"
    assert result["workflow"]["task_type"] == "needs_clarification"
    assert result["workflow"]["route"] == "clarification"

    artifacts = result["artifacts"]
    assert artifacts["router_output"] is not None
    assert artifacts["planner_output"] is None
    assert artifacts["reply_output"] is None

    final_output = result["final_output"]
    # Clarification final_output is the router_output clarification artifact
    assert isinstance(final_output, dict)
    assert final_output.get("task_type") == "needs_clarification"
    assert "handoff_payload" in final_output

