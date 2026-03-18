import json
import os
import sys
from pathlib import Path

import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from runtime.evaluation.prose_eval_cases import load_prose_evaluation_case


FIXTURE_DIR = Path(__file__).parent / "fixtures"
VALID_CASE_PATH = FIXTURE_DIR / "prose_evaluation_case_valid.json"


def _load_case_dict():
    return json.loads(VALID_CASE_PATH.read_text(encoding="utf-8"))


def _write_tmp(case: dict, tmp_path: Path, name: str) -> Path:
    out = tmp_path / name
    out.write_text(json.dumps(case), encoding="utf-8")
    return out


def test_valid_case_passes():
    case = load_prose_evaluation_case(VALID_CASE_PATH)
    assert case["case_id"] == "case-001"
    assert case["scope"] == "prose_drafting_v1"


@pytest.mark.parametrize("missing_field", ["case_id", "scope", "inputs", "evaluation_result"])
def test_missing_required_top_level_field_fails(missing_field: str, tmp_path: Path):
    case = _load_case_dict()
    case.pop(missing_field)
    tmp = _write_tmp(case, tmp_path, f"tmp_missing_top_{missing_field}.json")

    with pytest.raises(ValueError) as excinfo:
        load_prose_evaluation_case(tmp)
    assert missing_field in str(excinfo.value)


@pytest.mark.parametrize("missing_field", ["task_context", "planner_output", "final_prose_output"])
def test_missing_required_input_field_fails(missing_field: str, tmp_path: Path):
    case = _load_case_dict()
    case["inputs"].pop(missing_field)
    tmp = _write_tmp(case, tmp_path, f"tmp_missing_input_{missing_field}.json")

    with pytest.raises(ValueError) as excinfo:
        load_prose_evaluation_case(tmp)
    assert missing_field in str(excinfo.value)


@pytest.mark.parametrize("missing_field", ["dimension_ratings", "overall_result", "provenance"])
def test_missing_required_evaluation_result_field_fails(missing_field: str, tmp_path: Path):
    case = _load_case_dict()
    case["evaluation_result"].pop(missing_field)
    tmp = _write_tmp(case, tmp_path, f"tmp_missing_eval_{missing_field}.json")

    with pytest.raises(ValueError) as excinfo:
        load_prose_evaluation_case(tmp)
    assert missing_field in str(excinfo.value)


def test_invalid_dimension_rating_fails(tmp_path: Path):
    case = _load_case_dict()
    case["evaluation_result"]["dimension_ratings"]["structural_compliance"] = "not_valid"
    tmp = _write_tmp(case, tmp_path, "tmp_invalid_dimension_rating.json")

    with pytest.raises(ValueError) as excinfo:
        load_prose_evaluation_case(tmp)
    assert "structural_compliance" in str(excinfo.value)


@pytest.mark.parametrize("overall_result", ["ok", "bad", "strong"])
def test_invalid_overall_result_fails(overall_result: str, tmp_path: Path):
    case = _load_case_dict()
    case["evaluation_result"]["overall_result"] = overall_result
    tmp = _write_tmp(case, tmp_path, f"tmp_invalid_overall_{overall_result}.json")

    with pytest.raises(ValueError):
        load_prose_evaluation_case(tmp)


@pytest.mark.parametrize("provenance", ["auto", "manual", "machine_only"])
def test_invalid_provenance_fails(provenance: str, tmp_path: Path):
    case = _load_case_dict()
    case["evaluation_result"]["provenance"] = provenance
    tmp = _write_tmp(case, tmp_path, f"tmp_invalid_prov_{provenance}.json")

    with pytest.raises(ValueError):
        load_prose_evaluation_case(tmp)


def test_metadata_optionality_passes(tmp_path: Path):
    case = _load_case_dict()
    case.pop("metadata", None)
    case["evaluation_result"].pop("metadata", None)
    case["inputs"].pop("metadata", None)
    tmp = _write_tmp(case, tmp_path, "tmp_no_metadata.json")

    loaded = load_prose_evaluation_case(tmp)
    # Should validate and load successfully
    assert loaded["case_id"] == "case-001"

