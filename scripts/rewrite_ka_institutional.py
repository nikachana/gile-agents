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

REWRITE_SYSTEM_PROMPT = (
    "You rewrite Georgian text into cleaner institutional Georgian.\n\n"
    "First-pass goal:\n"
    "- improve clarity\n"
    "- fix grammar\n"
    "- allow light restructuring\n\n"
    "Hard constraints:\n"
    "- preserve meaning exactly\n"
    "- do not introduce new information\n"
    "- do not change decision status, reason, timeline, conditions, or obligations\n"
    "- do not replace core nouns unless strictly necessary\n"
    "- preserve grammatical voice\n"
    "- do not change verb forms unless certainty is high; if uncertain keep original wording\n"
    "- output only rewritten Georgian text"
)

EDITOR_SYSTEM_PROMPT = (
    "You are an institutional Georgian editor for second-pass cleanup.\n\n"
    "Second-pass goal:\n"
    "- enforce formal institutional tone\n"
    "- remove redundancy\n"
    "- ensure no semantic drift\n"
    "- ensure no grammar errors\n\n"
    "Hard constraints:\n"
    "- preserve meaning exactly\n"
    "- do not introduce new information\n"
    "- do not change decision status, reason, timeline, conditions, or obligations\n"
    "- preserve core nouns, voice, and verb intent; if uncertain keep original wording\n"
    "- output only final Georgian text"
)

# Backward-compatible aggregate prompt constant for prompt-contract tests.
SYSTEM_PROMPT = f"{REWRITE_SYSTEM_PROMPT}\n\n{EDITOR_SYSTEM_PROMPT}"

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

EDITOR_PROMPT_TEMPLATE = """Original text:
{original_text}

First-pass rewrite:
{rewritten_text}

Finalize the first-pass rewrite under the second-pass rules.
Return only the final Georgian text.
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


def _run_two_pass_openai(input_text: str) -> str:
    first_pass = _backend_openai(
        REWRITE_SYSTEM_PROMPT,
        USER_PROMPT_TEMPLATE.format(input_text=input_text),
    )
    second_pass = _backend_openai(
        EDITOR_SYSTEM_PROMPT,
        EDITOR_PROMPT_TEMPLATE.format(
            original_text=input_text,
            rewritten_text=first_pass,
        ),
    )
    return second_pass.strip()


_BACKENDS: dict[str, LLMCallable] = {
    "stub": _backend_stub,
    "openai": lambda _sys, user_prompt: _run_two_pass_openai(
        user_prompt.split("Text:\n", 1)[-1].strip()
    ),
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
        REWRITE_SYSTEM_PROMPT,
        USER_PROMPT_TEMPLATE.format(input_text=input_text),
    )
    sys.stdout.buffer.write((rewritten + "\n").encode("utf-8"))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
