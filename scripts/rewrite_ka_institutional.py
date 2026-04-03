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
import difflib
import re
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
    "You SHOULD fix (SAFE and required when present):\n"
    "- missing punctuation (commas, spacing)\n"
    "- unnatural word order\n"
    "- obvious redundancy (e.g. 'ამ წერილით')\n"
    "- obvious spelling mistakes and broken word forms (e.g. 'გიგგზანით', 'მოთოხოვნის')\n"
    "- These changes are considered SAFE and should be applied.\n\n"
    "If text contains clear errors (typos, broken words), you must fix them "
    "even if no other improvements are made.\n\n"
    "If the input contains obvious grammatical or lexical corruption, do not preserve it literally.\n"
    "Repair it into the closest clear institutional Georgian form without adding new information.\n\n"
    "Style preference (without changing meaning):\n"
    "- prefer clearer, more standard institutional Georgian over heavier administrative phrasing\n"
    "- if two versions preserve meaning equally, choose the simpler and more natural one\n"
    "- prioritize correct Georgian inflection and morphology\n"
    "- ensure noun/adjective case agreement is correct\n"
    "- prefer natural administrative phrasing over literal or awkward constructions\n"
    "- discourage vague bureaucratic fillers unless truly necessary, including:\n"
    "  - 'აღნიშნულთან დაკავშირებით'\n"
    "  - 'წინამდებარე'\n"
    "  - 'უქონლობის გამო' when a clearer equivalent preserves meaning\n"
    "  - similar heavy filler constructions\n\n"
    "Hard constraints:\n"
    "- preserve meaning exactly\n"
    "- do not introduce new information\n"
    "- do not change decision status, reason, timeline, conditions, or obligations\n"
    "- preserve grammatical voice (active/passive)\n"
    "- do not convert active constructions into passive or document-based forms\n"
    "- You MUST correct clearly incorrect grammatical forms (including verb forms, "
    "agreement, and case) when the correct form is unambiguous.\n"
    "- This is considered a SAFE transformation.\n"
    "- Do NOT change grammatically correct structures.\n"
    "- Only fix clearly incorrect forms.\n"
    "- output only rewritten Georgian text\n\n"
    "Examples:\n"
    "  Input: 'სააგენტომ ოპერაციულ გარემოში დანერგვა პლატფორმა'\n"
    "  Preferred: 'სააგენტომ ოპერაციულ გარემოში დანერგა პლატფორმა'\n\n"
    "  Input: 'ინფორმაციული უსართხოების'\n"
    "  Preferred: 'ინფორმაციული უსაფრთხოების'\n\n"
    "  Input: 'გიგგზანით კრებსითი ანგარიშს თქვენი მოთოხოვნის შესაბამისად.'\n"
    "  Preferred: 'გიგზავნით კრებსით ანგარიშს თქვენი მოთხოვნის შესაბამისად.'\n\n"
    "  Input: 'აღნიშნულთან დაკავშირებით გთხოვთ წარმოადგინოთ დამატებითი ინფორმაცია...'\n"
    "  Preferred: 'გთხოვთ, წარმოადგინოთ დამატებითი ინფორმაცია...'\n\n"
    "  Input: 'საქმის განხილვა შეჩერებულია საჭირო ინფორმაციის არარსებობის გამო'\n"
    "  Preferred: stay close to this form; avoid shifting to heavier synonyms.\n\n"
    "  Input: 'გაცნობთ რომ თქვეს საქმეს განხილვის პროცესი დაწყებულია. "
    "გთხოვთ უმოკლეს დროში წარმოადგინოთ დამატებით საბუთები.'\n"
    "  Preferred: 'გაცნობებთ, რომ თქვენი საქმის განხილვის პროცესი დაწყებულია. "
    "გთხოვთ, უმოკლეს დროში წარმოადგინოთ დამატებითი საბუთები.'\n\n"
    "  Input: 'როგორც ტელეფონით შევთანხმდით ამ წერილით გიგზავნით 2025 წლის "
    "ანგარიშს და აუდიტის დასკვნას'\n"
    "  Preferred: 'როგორც ტელეფონით შევთანხმდით, გიგზავნით 2025 წლის "
    "ანგარიშსა და აუდიტის დასკვნას'"
)

REWRITE_SYSTEM_PROMPT_MINIMAL = (
    "You rewrite Georgian institutional/legal text in SENSITIVE MINIMAL CORRECTION mode.\n\n"
    "You MUST apply these safe corrections when present:\n"
    "- obvious spelling mistakes\n"
    "- punctuation errors (commas, spacing)\n"
    "- obvious grammatical errors\n"
    "- broken inflection/case forms\n\n"
    "You MUST NOT:\n"
    "- split sentences under any condition, even if the sentence is long or poorly structured\n"
    "- add explanatory insertions\n"
    "- simplify terminology\n"
    "- replace role/term descriptions\n"
    "- rewrite for readability\n\n"
    "You MAY apply minimal clarity improvements only if they do not alter meaning, sentence boundaries, terminology, or structure.\n\n"
    "Required behavior:\n"
    "- preserve structure and meaning\n"
    "- preserve legal/procedural precision\n"
    "- preserve original terminology and role descriptions exactly\n"
    "- if text contains clear errors, fix them (do not return unchanged text)\n"
    "- if input contains obvious grammatical or lexical corruption, do not preserve it literally\n"
    "- repair to the closest clear institutional Georgian form without adding new information\n"
    "- do not add any new sentence\n\n"
    "Example (sensitive legal text):\n"
    "Input:\n"
    "საქართველოს მთავრობიას 2015 წლის 20 აპრილი №169 დადგენილებით დამტკიცებული "
    "„C ჰეპატიტის მართვის სახელმწიფო პროგრამის“ ფარგლებში, 2022 წლის 29 აგვისტოს "
    "იგეგმბა ჯანმრთელობის დაცვის სახელმწიფო პროგრამების ორგანიზაციული უზრუნველყოფის, "
    "მონიტორინგის, სამკურნალო და სამედიცინო საშუალებების ადმინისტრირების დეპარტამენტის, "
    "სამკურნალო და სამედიცინო საშუალებების ადმინისტრირების ხელშეკრულებით დასაქმებული პირის "
    "ლელა ვაშაყმაძის მივლინება ,,C” გეპატიტის მკურნალობაში ჩართული პაციენტებისათვის "
    "განკუთვნებულ მედიკამენტების ტრანსპორტირების მიზნით ქ. გორში, ქ. ხაშურში, ქ. ქუთაისში, "
    "ქ. სენაკში, ქ. ზუგდიდში და ქ. ბათუმში.\n\n"
    "გთხოვთ, დაავალოდებულოთ ადმინისტრაციულ დეპარტამენტს მივლინების გააფორმოს და "
    "ტრანსპორტირებით უზრუნველყოფა.\n\n"
    "Preferred behavior:\n"
    "- fix only clearly broken forms\n"
    "- preserve the long sentence structure\n"
    "- preserve 'ხელშეკრულებით დასაქმებული პირი'\n"
    "- do not add any new sentence\n\n"
    "Additional correction example:\n"
    "Input:\n"
    "გაცნობთ რომ თქვეს საქმეს განხილვის პროცესი დაწყებულია. "
    "გთხოვთ უმოკლეს დროში წარმოადგინოთ დამატებით საბუთები.\n\n"
    "Preferred:\n"
    "გაცნობებთ, რომ თქვენი საქმის განხილვის პროცესი დაწყებულია. "
    "გთხოვთ, უმოკლეს დროში წარმოადგინოთ დამატებითი საბუთები.\n\n"
    "Output only rewritten Georgian text."
)

EDITOR_SYSTEM_PROMPT = (
    "You are an institutional Georgian editor for second-pass cleanup.\n\n"
    "Second-pass goal:\n"
    "- enforce formal institutional tone\n"
    "- remove redundancy\n"
    "- ensure no semantic drift\n"
    "- ensure no grammar errors\n\n"
    "Style preference (without changing meaning):\n"
    "- prefer clearer, more standard institutional Georgian over heavier administrative phrasing\n"
    "- if two versions preserve meaning equally, choose the simpler and more natural one\n"
    "- prioritize correct Georgian inflection and morphology\n"
    "- ensure noun/adjective case agreement is correct\n"
    "- prefer natural administrative phrasing over literal or awkward constructions\n"
    "- discourage vague bureaucratic fillers unless truly necessary, including:\n"
    "  - 'აღნიშნულთან დაკავშირებით'\n"
    "  - 'წინამდებარე'\n"
    "  - 'უქონლობის გამო' when a clearer equivalent preserves meaning\n"
    "  - similar heavy filler constructions\n\n"
    "Hard constraints:\n"
    "- preserve meaning exactly\n"
    "- do not introduce new information\n"
    "- do not change decision status, reason, timeline, conditions, or obligations\n"
    "- preserve legal terminology, role definitions, employment types, and procedural descriptors\n"
    "- do not simplify or generalize legal or institutional terms\n"
    "- do not remove reference qualifiers or attribution phrases such as "
    "'თქვენს მიერ აღნიშნული', 'მითითებული', 'ზემოაღნიშნული', and similar "
    "context-defining elements unless clearly redundant and meaning is unchanged\n"
    "- avoid restructuring sentences that contain legal or procedural content\n"
    "- never remove information\n"
    "- preserve grammatical voice (active/passive)\n"
    "- do not convert active constructions into passive or document-based forms\n"
    "- preserve core nouns, voice, and verb intent; if uncertain keep original wording\n"
    "- You MUST correct clearly incorrect grammatical forms (including verb forms, "
    "agreement, and case) when the correct form is unambiguous.\n"
    "- This is considered a SAFE transformation.\n"
    "- Do NOT change grammatically correct structures.\n"
    "- Only fix clearly incorrect forms.\n"
    "- You must apply safe improvements such as:\n"
    "  - punctuation fixes\n"
    "  - natural word order adjustments\n"
    "  - removal of obvious redundancy\n"
    "- Do not return unchanged text if such improvements exist.\n"
    "- If there is any risk of changing meaning, keep the original wording.\n"
    "- output only final Georgian text\n\n"
    "Examples:\n"
    "  Input: 'სააგენტომ ოპერაციულ გარემოში დანერგვა პლატფორმა'\n"
    "  Preferred: 'სააგენტომ ოპერაციულ გარემოში დანერგა პლატფორმა'\n\n"
    "  Input: 'ინფორმაციული უსართხოების'\n"
    "  Preferred: 'ინფორმაციული უსაფრთხოების'\n\n"
    "  Input: 'გიგგზანით კრებსითი ანგარიშს თქვენი მოთოხოვნის შესაბამისად.'\n"
    "  Preferred: 'გიგზავნით კრებსით ანგარიშს თქვენი მოთხოვნის შესაბამისად.'\n\n"
    "  Input: 'აღნიშნულთან დაკავშირებით გთხოვთ წარმოადგინოთ დამატებითი ინფორმაცია...'\n"
    "  Preferred: 'გთხოვთ, წარმოადგინოთ დამატებითი ინფორმაცია...'\n\n"
    "  Input: 'საქმის განხილვა შეჩერებულია საჭირო ინფორმაციის არარსებობის გამო'\n"
    "  Preferred: stay close to this form; avoid shifting to heavier synonyms."
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
DEBUG = False


def _dprint(message: str) -> None:
    if DEBUG:
        print(message, file=sys.stderr)


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

    model = os.getenv("OPENAI_MODEL", "gpt-4o")
    temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.2"))
    max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "1024"))

    _dprint("DEBUG: backend=openai")
    _dprint(f"DEBUG: model={model}")
    _dprint(f"DEBUG: temperature={temperature}")
    _dprint("DEBUG: SYSTEM PROMPT START")
    _dprint(prompt_system)
    _dprint("DEBUG: SYSTEM PROMPT END")
    _dprint("DEBUG: USER PROMPT START")
    _dprint(prompt_user)
    _dprint("DEBUG: USER PROMPT END")

    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt_system},
            {"role": "user", "content": prompt_user},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()


def _extract_numbers(text: str) -> list[str]:
    return re.findall(r"\d+", text)


def _extract_date_like_tokens(text: str) -> list[str]:
    patterns = [
        r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b",
        r"\b\d{4}\b",
    ]
    out = []
    for p in patterns:
        out.extend(re.findall(p, text))
    return out


def _tokens(text: str) -> set[str]:
    # Basic word extraction for overlap heuristics.
    return {t for t in re.findall(r"[A-Za-z0-9\u10A0-\u10FF]+", text.lower()) if len(t) > 2}


def _normalize_for_typo_compare(text: str) -> str:
    # Keep letters/digits/spaces, normalize punctuation away, lowercase, and collapse spaces.
    cleaned = re.sub(r"[^\w\u10A0-\u10FF\s]", " ", text.lower())
    return re.sub(r"\s+", " ", cleaned).strip()


def _words_for_typo_compare(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9\u10A0-\u10FF]+", _normalize_for_typo_compare(text))


def _is_typo_tolerant_close(original: str, candidate: str) -> bool:
    """
    Return True when candidate is very close to original and likely differs mainly
    by spelling/orthographic corrections (not semantic rewrites).
    """
    o_norm = _normalize_for_typo_compare(original)
    c_norm = _normalize_for_typo_compare(candidate)
    if not o_norm or not c_norm:
        return False

    # Whole-text closeness.
    text_ratio = difflib.SequenceMatcher(None, o_norm, c_norm).ratio()
    if text_ratio < 0.82:
        return False

    o_words = _words_for_typo_compare(original)
    c_words = _words_for_typo_compare(candidate)
    if not o_words or not c_words:
        return False
    if abs(len(o_words) - len(c_words)) > 2:
        return False

    # Word-level closeness (same position, allowing minor character edits).
    paired = zip(o_words, c_words)
    close_pairs = 0
    total = min(len(o_words), len(c_words))
    for ow, cw in paired:
        if ow == cw:
            close_pairs += 1
            continue
        wr = difflib.SequenceMatcher(None, ow, cw).ratio()
        if wr >= 0.72:
            close_pairs += 1

    if total == 0:
        return False
    return (close_pairs / total) >= 0.75


def _safe_pass2_output(original: str, candidate: str) -> bool:
    # 1) Numbers preserved
    if _extract_numbers(original) != _extract_numbers(candidate):
        return False

    # 2) Date-like tokens preserved
    orig_dates = sorted(_extract_date_like_tokens(original))
    cand_dates = sorted(_extract_date_like_tokens(candidate))
    if orig_dates != cand_dates:
        return False

    # 3) Basic noun/key-word overlap heuristic
    orig_tokens = _tokens(original)
    cand_tokens = _tokens(candidate)
    if orig_tokens:
        overlap_ratio = len(orig_tokens & cand_tokens) / max(1, len(orig_tokens))
        typo_close = _is_typo_tolerant_close(original, candidate)
        if overlap_ratio < 0.55 and not typo_close:
            return False

    # 4) No major shortening
    orig_len = len(original.strip())
    cand_len = len(candidate.strip())
    if orig_len > 0 and cand_len < int(orig_len * 0.65):
        return False

    # 5) No obvious new entities introduced (capitalized latin words as rough proxy)
    orig_entities = set(re.findall(r"\b[A-Z][A-Za-z0-9_-]*\b", original))
    cand_entities = set(re.findall(r"\b[A-Z][A-Za-z0-9_-]*\b", candidate))
    if not cand_entities.issubset(orig_entities):
        return False

    return True


def is_sensitive_institutional_text(text: str) -> bool:
    markers = [
        "საქართველოს",
        "მუხლი",
        "დადგენილებით",
        "ბრძანების",
        "შესაბამისად",
        "ხელშეკრულებით დასაქმებული პირი",
    ]
    if any(m in text for m in markers):
        return True

    # Simple heuristic for long legal/administrative noun chains.
    if len(text) > 350 and text.count(",") >= 5:
        return True

    return False


def _violates_institutional_constraints(original: str, candidate: str) -> bool:
    original_norm = re.sub(r"\s+", " ", original).strip()
    candidate_norm = re.sub(r"\s+", " ", candidate).strip()

    # Required deterministic checks
    if "ხელშეკრულებით დასაქმებული პირი" in original_norm and "ხელშეკრულებით დასაქმებული პირი" not in candidate_norm:
        _dprint("PASS2 rejected: critical term loss")
        return True
    if "მისი მიზანია" in candidate_norm and "მისი მიზანია" not in original_norm:
        _dprint("PASS2 rejected: forbidden phrase insertion")
        return True

    # A) Forbidden explanatory phrase inserted
    forbidden_insertions = [
        "მისი მიზანია",
        "ამ პროცესის მიზანია",
    ]
    for phrase in forbidden_insertions:
        if phrase in candidate_norm and phrase not in original_norm:
            if phrase == "მისი მიზანია":
                _dprint("PASS2 rejected: forbidden phrase insertion")
            return True

    # B) Critical term loss
    critical_terms = [
        "ხელშეკრულებით დასაქმებული პირი",
        "შრომითი ხელშეკრულებით დასაქმებული პირი",
        "უტყუარობა",
        "თქვენს მიერ აღნიშნული",
        "მითითებული",
        "ზემოაღნიშნული",
    ]
    for term in critical_terms:
        if term in original_norm and term not in candidate_norm:
            if term == "ხელშეკრულებით დასაქმებული პირი":
                _dprint("PASS2 rejected: critical term loss")
            return True

    # C) Sentence count expansion on legal/procedural text
    legal_markers = [
        "საქართველოს",
        "მუხლი",
        "დადგენილებით",
        "ბრძანების",
        "შესაბამისად",
    ]
    if any(marker in original_norm for marker in legal_markers):
        orig_count = len(re.findall(r"[.!?]", original))
        cand_count = len(re.findall(r"[.!?]", candidate))
        if cand_count > orig_count:
            return True

    return False


def _run_two_pass_openai(input_text: str) -> str:
    _dprint("DEBUG: running PASS1")
    sensitive = is_sensitive_institutional_text(input_text)
    pass1_prompt = REWRITE_SYSTEM_PROMPT_MINIMAL if sensitive else REWRITE_SYSTEM_PROMPT
    if sensitive:
        _dprint("DEBUG: sensitive text detected")
        _dprint("DEBUG: PASS1 using MINIMAL CORRECTION mode")
    first_pass = _backend_openai(
        pass1_prompt,
        USER_PROMPT_TEMPLATE.format(input_text=input_text),
    )
    _dprint("DEBUG: PASS1 OUTPUT START")
    _dprint(first_pass)
    _dprint("DEBUG: PASS1 OUTPUT END")

    if sensitive:
        _dprint("DEBUG: skipping PASS2 for sensitive text")
        return first_pass.strip()

    _dprint("DEBUG: running PASS2")
    second_pass = _backend_openai(
        EDITOR_SYSTEM_PROMPT,
        EDITOR_PROMPT_TEMPLATE.format(
            original_text=input_text,
            rewritten_text=first_pass,
        ),
    )
    _dprint("DEBUG: PASS2 OUTPUT START")
    _dprint(second_pass)
    _dprint("DEBUG: PASS2 OUTPUT END")

    second_pass = second_pass.strip()
    pass2_safe = _safe_pass2_output(input_text, second_pass)
    pass2_violates = _violates_institutional_constraints(input_text, second_pass)
    if pass2_safe and not pass2_violates:
        return second_pass
    if pass2_violates:
        _dprint("DEBUG: PASS2 rejected by institutional guardrail; falling back to PASS1")
    if _safe_pass2_output(input_text, first_pass.strip()):
        return first_pass.strip()
    return input_text.strip()


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


def _rewrite_text(input_text: str) -> str:
    return get_backend()(
        REWRITE_SYSTEM_PROMPT,
        USER_PROMPT_TEMPLATE.format(input_text=input_text),
    )


def _rewrite_batch_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()
    if not content:
        return ""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", content) if p.strip()]
    rewritten = [_rewrite_text(p) for p in paragraphs]
    return "\n\n".join(rewritten)

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
        help="Input text for single mode. If omitted, read from stdin.",
    )
    parser.add_argument(
        "--mode",
        choices=["single", "batch"],
        default="single",
        help="Processing mode: single (default) or batch.",
    )
    parser.add_argument(
        "--input",
        help="Path to input .txt file for batch mode.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Show debug trace including pass1/pass2 prompts and outputs.",
    )
    args = parser.parse_args(argv)
    global DEBUG
    DEBUG = args.debug

    backend_name = os.getenv("REWRITE_KA_BACKEND", "stub")
    _dprint(f"DEBUG: selected backend={backend_name}")
    if backend_name == "openai":
        _dprint(f"DEBUG: selected model={os.getenv('OPENAI_MODEL', 'gpt-4o')}")
        _dprint(
            f"DEBUG: selected temperature={float(os.getenv('OPENAI_TEMPERATURE', '0.2'))}"
        )
    else:
        _dprint("DEBUG: selected model=n/a (stub backend)")
        _dprint("DEBUG: selected temperature=n/a (stub backend)")

    if args.mode == "batch":
        if not args.input:
            raise SystemExit("ERROR: --input is required for --mode batch.")
        output_text = _rewrite_batch_file(args.input)
    else:
        if args.text is not None:
            input_text = args.text
        else:
            raw = sys.stdin.buffer.read()
            input_text = raw.decode(sys.stdin.encoding or "utf-8", errors="replace").strip()
        if not input_text:
            return 0
        output_text = _rewrite_text(input_text)

    sys.stdout.buffer.write((output_text + "\n").encode("utf-8"))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
