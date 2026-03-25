"""
Standalone prototype — rewrites Georgian text into formal institutional Georgian.

Usage
-----
  python scripts/rewrite_ka_institutional.py "ტექსტი"
  echo "ტექსტი" | python scripts/rewrite_ka_institutional.py

Environment variables
---------------------
REWRITE_KA_BACKEND   "openai" | "stub"  (default: "stub")
OPENAI_API_KEY       required when backend is "openai"
OPENAI_MODEL         model name          (default: "gpt-4o")
OPENAI_MAX_TOKENS    max tokens          (default: 1024)
OPENAI_TEMPERATURE   temperature         (default: 0.2)
"""

import argparse
import os
import sys
from typing import Callable

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You rewrite Georgian text into clean, natural, formal institutional Georgian.\n\n"
    "Your job is to improve wording, clarity, tone, and administrative naturalness "
    "while preserving meaning exactly.\n\n"
    "STRICT MODE — apply minimal edits only, but actively perform low-risk improvements.\n"
    "- Strongly prefer word-order cleanup, punctuation fixes, and obvious "
    "redundancy removal before any lexical substitution.\n"
    "- Do not replace core nouns unless the original is clearly wrong.\n"
    "- Do not change grammatical voice (active must stay active, passive must stay passive).\n"
    "- Do not modify verb forms unless you are fully certain the new form is correct; "
    "when uncertain, keep the original verb form exactly.\n"
    "- Do not replace distinct state words "
    "(e.g. 'გადაიდო' (postponed) must not become 'შეჩერდა' (paused)).\n"
    "- Do not add facts, conditions, timelines, or obligations not present in the input.\n"
    "- If the text can be improved safely, improve it with minimal edits.\n"
    "- If uncertain, keep the original wording.\n"
    "- If the text is already clean and correct, return it unchanged.\n"
    "- Output only the rewritten Georgian text.\n\n"
    "Example A:\n"
    "  Input: 'როგორც მთხოვეთ, მოთხოვნა გავაგზავნე ფოსტით და ადრესატი "
    "დოკუმენტებს ერთ კვირაში მიიღებს.'\n"
    "  Preferred rewrite: 'როგორც მთხოვეთ, მოთხოვნა ფოსტით გავაგზავნე და "
    "ადრესატი დოკუმენტებს ერთ კვირაში მიიღებს.'\n\n"
    "Example B:\n"
    "  Input: 'როგორც ტელეფონით შევთანხმდით ამ წერილით გიგზავნით 2025 წლის "
    "ანგარიშს და აუდიტის დასკვნას.'\n"
    "  Preferred rewrite: 'როგორც ტელეფონით შევთანხმდით, გიგზავნით 2025 წლის "
    "ანგარიშსა და აუდიტის დასკვნას.'\n\n"
    "Bad rewrite: changing 'მოთხოვნა' to 'დოკუმენტები', or writing "
    "'გავგზავნე' instead of 'გავაგზავნე'."
)

USER_PROMPT_TEMPLATE = """Rewrite the following text into stronger institutional Georgian.

Requirements:
- preserve meaning exactly
- improve naturalness and precision
- remove unnecessary heaviness
- keep formal administrative tone
- do not add any new information

Text:
{input_text}
"""

# ---------------------------------------------------------------------------
# Backends
# ---------------------------------------------------------------------------

LLMCallable = Callable[[str, str], str]


def _backend_stub(prompt_system: str, prompt_user: str) -> str:
    marker = "Text:\n"
    idx = prompt_user.find(marker)
    if idx != -1:
        return prompt_user[idx + len(marker):].strip()
    return prompt_user.strip()


def _backend_openai(prompt_system: str, prompt_user: str) -> str:
    try:
        import openai
    except ImportError as exc:
        raise SystemExit(
            "ERROR: openai package not installed. Run: pip install openai"
        ) from exc

    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise SystemExit("ERROR: OPENAI_API_KEY is not set.")

    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        messages=[
            {"role": "system", "content": prompt_system},
            {"role": "user", "content": prompt_user},
        ],
        max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "1024")),
        temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.2")),
    )
    return response.choices[0].message.content.strip()


_BACKENDS: dict[str, LLMCallable] = {
    "stub": _backend_stub,
    "openai": _backend_openai,
}


def get_backend(name: str | None = None) -> LLMCallable:
    resolved = name or os.getenv("REWRITE_KA_BACKEND", "stub")
    if resolved not in _BACKENDS:
        raise SystemExit(
            f"ERROR: unknown backend '{resolved}'. "
            f"Choose from: {', '.join(_BACKENDS)}"
        )
    return _BACKENDS[resolved]

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Rewrite Georgian text into formal institutional Georgian."
    )
    parser.add_argument(
        "text",
        nargs="?",
        help="Input text. If omitted, read from stdin.",
    )
    args = parser.parse_args(argv)

    if args.text is not None:
        input_text = args.text
    else:
        raw = sys.stdin.buffer.read()
        input_text = raw.decode(sys.stdin.encoding or "utf-8", errors="replace").strip()
    if not input_text:
        return 0

    rewritten = get_backend()(
        SYSTEM_PROMPT,
        USER_PROMPT_TEMPLATE.format(input_text=input_text),
    )
    sys.stdout.buffer.write((rewritten + "\n").encode("utf-8"))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
