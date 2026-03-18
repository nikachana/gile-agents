import json
from pathlib import Path
from typing import Any, Dict

from jsonschema import ValidationError, validate


ProseEvaluationCase = Dict[str, Any]


def _load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as exc:
        raise ValueError(f"File not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in file: {path}") from exc


def load_prose_evaluation_case(case_path: str | Path) -> ProseEvaluationCase:
    """
    Load and structurally validate a prose_drafting_v1 evaluation case.

    - Load JSON from file
    - Validate against contracts/prose_evaluation_case_v1.schema.json
    - Return parsed object on success
    - Raise ValueError with a clear message on failure
    """
    case_path = Path(case_path)
    repo_root = Path(__file__).resolve().parents[2]
    schema_path = repo_root / "contracts" / "prose_evaluation_case_v1.schema.json"

    case = _load_json(case_path)
    schema = _load_json(schema_path)

    try:
        validate(instance=case, schema=schema)
    except ValidationError as exc:
        location = ".".join(str(p) for p in exc.path) or "$"
        raise ValueError(f"Schema validation failed at {location}: {exc.message}") from exc

    return case

