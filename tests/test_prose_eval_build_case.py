import json
import os
import sys
from pathlib import Path

import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from tools.prose_eval_build_case import main  # noqa: E402


def _write_json(path: Path, data: dict) -> Path:
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_prose_eval_build_case_success(tmp_path: Path, capsys):
    task_context_path = _write_json(
        tmp_path / "task_context.json",
        {"instructions": "Draft an email."},
    )
    planner_output_path = _write_json(
        tmp_path / "planner_output.json",
        {"intent": "communication", "sections": ["intro", "body", "closing"]},
    )
    output_path = tmp_path / "case.json"

    argv = [
        str(output_path),
        "--case-id",
        "case-123",
        "--task-context",
        str(task_context_path),
        "--planner-output",
        str(planner_output_path),
        "--final-prose-text",
        "Hello, world.",
        "--structural-compliance",
        "strong",
        "--semantic-fidelity",
        "acceptable",
        "--prose-quality",
        "weak",
        "--overall-result",
        "acceptable",
        "--provenance",
        "human_reviewed",
    ]

    exit_code = main(argv)
    captured = capsys.readouterr()

    assert exit_code == 0
    assert output_path.exists()
    assert f"OK {output_path.name}" in captured.out


def test_prose_eval_build_case_invalid_enum_returns_error(tmp_path: Path, capsys):
    task_context_path = _write_json(
        tmp_path / "task_context.json",
        {"instructions": "Draft an email."},
    )
    planner_output_path = _write_json(
        tmp_path / "planner_output.json",
        {"intent": "communication", "sections": ["intro", "body", "closing"]},
    )
    output_path = tmp_path / "case_invalid_enum.json"

    argv = [
        str(output_path),
        "--case-id",
        "case-123",
        "--task-context",
        str(task_context_path),
        "--planner-output",
        str(planner_output_path),
        "--final-prose-text",
        "Hello, world.",
        "--structural-compliance",
        "not_valid",  # invalid rating
        "--semantic-fidelity",
        "acceptable",
        "--prose-quality",
        "weak",
        "--overall-result",
        "acceptable",
        "--provenance",
        "human_reviewed",
    ]

    exit_code = main(argv)
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "ERROR:" in captured.out


def test_prose_eval_build_case_missing_input_file_returns_error(tmp_path: Path, capsys):
    # Do not create task_context.json to trigger file-not-found handling.
    planner_output_path = _write_json(
        tmp_path / "planner_output.json",
        {"intent": "communication", "sections": ["intro", "body", "closing"]},
    )
    output_path = tmp_path / "case_missing_input.json"

    argv = [
        str(output_path),
        "--case-id",
        "case-123",
        "--task-context",
        str(tmp_path / "missing_task_context.json"),
        "--planner-output",
        str(planner_output_path),
        "--final-prose-text",
        "Hello, world.",
        "--structural-compliance",
        "strong",
        "--semantic-fidelity",
        "acceptable",
        "--prose-quality",
        "weak",
        "--overall-result",
        "acceptable",
        "--provenance",
        "human_reviewed",
    ]

    with pytest.raises(SystemExit) as excinfo:
        main(argv)
    captured = capsys.readouterr()

    assert excinfo.value.code == 1
    assert "ERROR: task_context file not found" in captured.out

