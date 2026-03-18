import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from runtime.stubs.router_stub import router


def _run(message_text: str, mode):
    return router({"message_text": message_text, "metadata": {"mode": mode}, "context": {}})


def test_router_modes_to_task_type_and_route():
    cases = [
        ("Translate this", "translate", "translate", "gile"),
        ("Rewrite this", "rewrite", "rewrite", "gile"),
        ("Validate this", "validate", "validate", "gile"),
        ("Summarize this", "document_summarize", "document_summarize", "gile"),
        ("Plan this", "document_plan", "document_plan", "planner"),
        ("Reply draft", "reply_draft", "reply_draft", "planner"),
        ("Email draft", "email_draft", "email_draft", "planner"),
        ("No explicit mode", None, "document_draft", "planner"),
    ]

    for message_text, mode, expected_task_type, expected_route in cases:
        result = _run(message_text, mode)
        assert result["task_type"] == expected_task_type
        assert result["route_to"] == expected_route


def test_router_needs_clarification_when_message_empty():
    result = _run("   ", None)
    assert result["task_type"] == "needs_clarification"
    assert result["route_to"] == "clarification"

