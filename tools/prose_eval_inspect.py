import argparse
import os
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from runtime.evaluation.prose_eval_cases import load_prose_evaluation_case  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect a prose_drafting_v1 evaluation case."
    )
    parser.add_argument(
        "path",
        help="Path to a prose_evaluation_case_v1 JSON file.",
    )
    args = parser.parse_args(argv)

    case_path = Path(args.path)

    try:
        case = load_prose_evaluation_case(case_path)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1

    evaluation_result = case.get("evaluation_result", {})
    dimension_ratings = evaluation_result.get("dimension_ratings", {})

    print(f"case_id: {case.get('case_id')}")
    print(f"scope: {case.get('scope')}")
    print(f"dimension_ratings: {dimension_ratings}")
    print(f"overall_result: {evaluation_result.get('overall_result')}")
    print(f"provenance: {evaluation_result.get('provenance')}")

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

