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
        description="Validate all prose_evaluation_case_v1 JSON files in a directory."
    )
    parser.add_argument(
        "directory",
        help="Path to a directory containing prose_evaluation_case_v1 JSON files.",
    )
    args = parser.parse_args(argv)

    directory = Path(args.directory)
    if not directory.is_dir():
        print(f"ERROR: {directory} is not a directory")
        return 1

    json_files = sorted(p for p in directory.iterdir() if p.suffix == ".json")

    total = 0
    valid = 0
    invalid = 0

    for path in json_files:
        total += 1
        try:
            load_prose_evaluation_case(path)
        except ValueError as exc:
            invalid += 1
            print(f"ERROR {path.name}: {exc}")
        else:
            valid += 1
            print(f"OK {path.name}")

    print(f"total: {total}")
    print(f"valid: {valid}")
    print(f"invalid: {invalid}")

    return 0 if invalid == 0 else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

