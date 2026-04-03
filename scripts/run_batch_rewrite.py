import json
import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    input_path = root / "cases_input.json"
    output_path = root / "cases_output.json"

    if not os.environ.get("OPENAI_API_KEY", "").strip():
        print(
            "ERROR: OPENAI_API_KEY is not set. Batch evaluation requires the OpenAI backend.\n"
            "Set OPENAI_API_KEY in your environment and rerun.",
            file=sys.stderr,
        )
        return 1

    batch_env = dict(os.environ)
    batch_env["REWRITE_KA_BACKEND"] = "openai"
    print("BATCH RUNNER backend=openai", file=sys.stderr)

    with input_path.open("r", encoding="utf-8") as f:
        cases = json.load(f)

    results = []
    for item in cases:
        case_id = item.get("case_id", "")
        text = item.get("text", "")

        proc = subprocess.run(
            [sys.executable, "scripts/rewrite_ka_institutional.py", text],
            cwd=str(root),
            env=batch_env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        if proc.returncode == 0:
            results.append(
                {
                    "case_id": case_id,
                    "original_text": text,
                    "output": proc.stdout.rstrip(),
                }
            )
        else:
            results.append(
                {
                    "case_id": case_id,
                    "original_text": text,
                    "output": "ERROR",
                    "error": proc.stderr.rstrip(),
                }
            )

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        f.write("\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
