import argparse
import json
import os
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from runtime.evaluation.prose_eval_cases import load_prose_evaluation_case  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a prose_evaluation_case_v1 JSON file from explicit inputs."
    )
    parser.add_argument("output", help="Output JSON file path.")
    parser.add_argument("--case-id", required=True, help="Case identifier.")
    parser.add_argument(
        "--task-context",
        required=True,
        help="Path to a JSON file containing task_context.",
    )
    parser.add_argument(
        "--planner-output",
        required=True,
        help="Path to a JSON file containing planner_output.",
    )
    parser.add_argument(
        "--final-prose-text",
        required=True,
        help="Final prose text to include in final_prose_output.text.",
    )
    parser.add_argument(
        "--structural-compliance",
        required=True,
        help="Dimension rating for structural_compliance.",
    )
    parser.add_argument(
        "--semantic-fidelity",
        required=True,
        help="Dimension rating for semantic_fidelity.",
    )
    parser.add_argument(
        "--prose-quality",
        required=True,
        help="Dimension rating for prose_quality.",
    )
    parser.add_argument(
        "--overall-result",
        required=True,
        help="Overall result (acceptable or unacceptable).",
    )
    parser.add_argument(
        "--provenance",
        required=True,
        help="Provenance (model_assisted, human_reviewed, or both).",
    )

    args = parser.parse_args(argv)

    output_path = Path(args.output)

    def _load_json_file(path_str: str, label: str) -> dict:
        path = Path(path_str)
        try:
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"ERROR: {label} file not found: {path}")
            raise SystemExit(1)
        except json.JSONDecodeError as exc:
            print(f"ERROR: {label} file is not valid JSON: {path} ({exc})")
            raise SystemExit(1)

    task_context = _load_json_file(args.task_context, "task_context")
    planner_output = _load_json_file(args.planner_output, "planner_output")

    case = {
        "case_id": args.case_id,
        "scope": "prose_drafting_v1",
        "inputs": {
            "task_context": task_context,
            "planner_output": planner_output,
            "final_prose_output": {"text": args.final_prose_text},
        },
        "evaluation_result": {
            "dimension_ratings": {
                "structural_compliance": args.structural_compliance,
                "semantic_fidelity": args.semantic_fidelity,
                "prose_quality": args.prose_quality,
            },
            "overall_result": args.overall_result,
            "provenance": args.provenance,
        },
    }

    try:
        output_path.write_text(json.dumps(case, indent=2), encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: Could not write output file {output_path}: {exc}")
        return 1

    try:
        load_prose_evaluation_case(output_path)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1

    print(f"OK {output_path.name}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

