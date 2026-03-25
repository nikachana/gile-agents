import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from scripts import rewrite_ka_institutional as mod  # noqa: E402


def test_system_prompt_exists():
    assert isinstance(mod.SYSTEM_PROMPT, str)
    assert mod.SYSTEM_PROMPT.strip()


def test_user_prompt_template_exists():
    assert isinstance(mod.USER_PROMPT_TEMPLATE, str)
    assert mod.USER_PROMPT_TEMPLATE.strip()


def test_required_instructions_present_in_prompt_text():
    prompt_text = f"{mod.SYSTEM_PROMPT}\n{mod.USER_PROMPT_TEMPLATE}"
    required_phrases = [
        "preserve meaning exactly",
        "improve naturalness and precision",
        "remove unnecessary heaviness",
        "keep formal administrative tone",
        "do not add any new information",
    ]
    for phrase in required_phrases:
        assert phrase in prompt_text


def test_no_runtime_integration_dependency():
    source_path = os.path.join(ROOT_DIR, "scripts", "rewrite_ka_institutional.py")
    source = open(source_path, "r", encoding="utf-8").read()
    banned_markers = [
        "run_orchestrator",
        "runtime.orchestration",
        "contracts/",
        "prose_eval",
    ]
    for marker in banned_markers:
        assert marker not in source
