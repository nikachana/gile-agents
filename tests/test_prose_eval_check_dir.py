import json
import os
import sys
from pathlib import Path

import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from tools.prose_eval_check_dir import main  # noqa: E402


FIXTURE_DIR = Path(__file__).parent / "fixtures"
VALID_CASE_PATH = FIXTURE_DIR / "prose_evaluation_case_valid.json"


def _write_case(tmp_dir: Path, name: str, data: dict) -> Path:
    path = tmp_dir / name
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_prose_eval_check_dir_all_valid(tmp_path: Path, capsys):
    # Copy valid case into directory
    valid_data = json.loads(VALID_CASE_PATH.read_text(encoding="utf-8"))
    _write_case(tmp_path, "case1.json", valid_data)
    _write_case(tmp_path, "case2.json", valid_data)

    exit_code = main([str(tmp_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    out = captured.out.strip().splitlines()
    # Two OK lines plus summary
    assert any(line.startswith("OK case1.json") for line in out)
    assert any(line.startswith("OK case2.json") for line in out)
    assert "total: 2" in out[-3:]
    assert "valid: 2" in out[-2:]
    assert "invalid: 0" in out[-1:]


def test_prose_eval_check_dir_mixed_valid_and_invalid(tmp_path: Path, capsys):
    valid_data = json.loads(VALID_CASE_PATH.read_text(encoding="utf-8"))
    _write_case(tmp_path, "valid.json", valid_data)

    invalid_data = {"case_id": "broken"}  # missing required fields
    _write_case(tmp_path, "invalid.json", invalid_data)

    exit_code = main([str(tmp_path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    out = captured.out.strip().splitlines()
    assert any(line.startswith("OK valid.json") for line in out)
    assert any("ERROR invalid.json:" in line for line in out)
    assert "total: 2" in out[-3:]
    assert "valid: 1" in out[-2:]
    assert "invalid: 1" in out[-1:]


def test_prose_eval_check_dir_empty_directory(tmp_path: Path, capsys):
    exit_code = main([str(tmp_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    out = captured.out.strip().splitlines()
    # No OK/ERROR lines, only summary
    assert "total: 0" in out[-3:]
    assert "valid: 0" in out[-2:]
    assert "invalid: 0" in out[-1:]

