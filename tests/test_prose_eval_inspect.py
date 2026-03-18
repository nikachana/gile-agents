import os
import sys
from pathlib import Path

import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from tools.prose_eval_inspect import main  # noqa: E402


FIXTURE_DIR = Path(__file__).parent / "fixtures"
VALID_CASE_PATH = FIXTURE_DIR / "prose_evaluation_case_valid.json"


def test_prose_eval_inspect_valid_case_prints_summary(capsys):
    exit_code = main([str(VALID_CASE_PATH)])
    captured = capsys.readouterr()

    assert exit_code == 0
    out = captured.out.strip()
    assert "case_id: case-001" in out
    assert "scope: prose_drafting_v1" in out
    assert "dimension_ratings:" in out
    assert "overall_result:" in out
    assert "provenance:" in out


def test_prose_eval_inspect_invalid_case_prints_error(tmp_path: Path, capsys):
    # Start from valid case and break a required field.
    invalid_case_path = tmp_path / "invalid_case.json"
    invalid_case_path.write_text("{}", encoding="utf-8")

    exit_code = main([str(invalid_case_path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "ERROR:" in captured.out

