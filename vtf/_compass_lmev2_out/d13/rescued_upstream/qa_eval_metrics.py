import json
import os
import re
from typing import Any, Callable, Iterable, List, Optional, Sequence, Tuple


DEFAULT_SEPARATORS: Sequence[str] = (",", ";")
_ABSTENTION_JUDGE_SYSTEM_PROMPT = (
    "You are a strict grader for flawed-premise (abstention) questions. "
    "Judge whether a model answer correctly identifies that the question premise is wrong, "
    "consistent with the reference answer. "
    "If the model follows the flawed premise and gives a concrete answer under that premise, "
    "it must be graded 0. "
    "If the model's final answer is just UNKNOWN / cannot determine without identifying the flaw, grade 0. "
    "If the model is contradictory (both rejects premise and also gives a concrete premise-following answer), grade 0. "
    "Paraphrases are allowed when they preserve the same core flaw described by the reference answer."
)
_GOTCHAS_JUDGE_SYSTEM_PROMPT = (
    "You are a strict grader for gotchas-style insight questions. "
    "The reference answer describes the key insight(s). "
    "Grade 1 if the model response includes at least one correct insight point from the reference answer "
    "(paraphrase allowed), and does not contradict any reference point. "
    "If the model's direction is wrong, or it contains contradictions against any reference point, grade 0. "
    "If the model gives multiple points, partial coverage is enough for 1 as long as no contradictions appear."
)
OPENAI_MAX_RETRIES = 10


def normalize_phrase(
    text: str | None,
    *,
    lower: bool = True,
    normalize_hyphen: bool = True,
    strip_punct: bool = True,
) -> str:
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
    if lower:
        text = text.lower()
    if normalize_hyphen:
        text = text.replace("-", " ").replace("_", " ")
    text = re.sub(r"[,;]", " ", text)
    if strip_punct:
        text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def split_phrases(
    text: str | None,
    *,
    separators: Iterable[str] = DEFAULT_SEPARATORS,
    **normalize_kwargs: bool,
) -> List[str]:
    if text is None:
        return []
    separator_list = list(separators)
    if not separator_list:
        normalized = normalize_phrase(text, **normalize_kwargs)
        return [normalized] if normalized else []
    pattern = "|".join(re.escape(sep) for sep in separator_list)
    parts = re.split(pattern, text)
    normalized_parts = [
        normalize_phrase(part, **normalize_kwargs) for part in parts
    ]
    return [part for part in normalized_parts if part]


def norm_phrase_set_match(
    prediction: str | None,
    answer: str | None,
    *,
    separators: Iterable[str] = DEFAULT_SEPARATORS,
    require_non_empty: bool = True,
    **normalize_kwargs: bool,
) -> bool:
    normalized_pred = normalize_phrase(prediction, **normalize_kwargs)
    answer_phrases = split_phrases(answer, separators=separators, **normalize_kwargs)
    if require_non_empty and (not normalized_pred or not answer_phrases):
        return False
    for phrase in set(answer_phrases):
        pattern = r"\b%s\b" % re.escape(phrase)
        if re.search(pattern, normalized_pred) is None:
            return False
    return True


def norm_phrase_set_match_ordered(
    prediction: str | None,
    answer: str | None,
    *,
    separators: Iterable[str] = DEFAULT_SEPARATORS,
    require_non_empty: bool = True,
    **normalize_kwargs: bool,
) -> bool:
    normalized_pred = normalize_phrase(prediction, **normalize_kwargs)
    answer_phrases = split_phrases(answer, separators=separators, **normalize_kwargs)
    if require_non_empty and (not normalized_pred or not answer_phrases):
        return False
    start = 0
    for phrase in answer_phrases:
        pattern = r"\b%s\b" % re.escape(phrase)
        match = re.search(pattern, normalized_pred[start:])
        if match is None:
            return False
        start += match.end()
    return True


def mc_choice_match(
    prediction: str | None,
    answer: str | None,
    *,
    strip_chars: str = ".",
    require_non_empty: bool = True,
    **_: Any,
) -> bool:
    if prediction is None or answer is None:
        return False
    if not isinstance(prediction, str):
        prediction = str(prediction)
    if not isinstance(answer, str):
        answer = str(answer)
    boxed_match = re.search(r"\\boxed\{([^}]*)\}", prediction.lower())
    candidate = boxed_match.group(1) if boxed_match else prediction
    cleaned = re.sub(r"\b(choice|option)\b", "", candidate, flags=re.IGNORECASE)
    for ch in strip_chars:
        cleaned = cleaned.replace(ch, "")
    cleaned = cleaned.strip().upper()
    expected = answer.strip().upper()
    if require_non_empty and (not cleaned or not expected):
        return False
    return cleaned == expected


_MULTI_SELECT_FILLER_WORDS = {
    "AND",
    "ANSWER",
    "ANSWERS",
    "CHOICE",
    "CHOICES",
    "FINAL",
    "LETTER",
    "LETTERS",
    "OPTION",
    "OPTIONS",
}


def _extract_multi_select_letters(text: str | None) -> list[str]:
    if text is None:
        return []
    if not isinstance(text, str):
        text = str(text)
    chunks = re.findall(r"[A-Z]+", text.upper())
    letters: list[str] = []
    for chunk in chunks:
        if chunk in _MULTI_SELECT_FILLER_WORDS:
            continue
        letters.extend(list(chunk))
    return letters


def mc_choice_set_match(
    prediction: str | None,
    answer: str | None,
    *,
    require_non_empty: bool = True,
    **_: Any,
) -> bool:
    pred_letters = _extract_multi_select_letters(prediction)
    answer_letters = _extract_multi_select_letters(answer)
    if require_non_empty and (not pred_letters or not answer_letters):
        return False
    return set(pred_letters) == set(answer_letters)


def extract_boxed_answer(text: str) -> str:
    marker = "\\boxed{"
    idx = text.rfind(marker)
    if idx == -1:
        return text.strip()
    i = idx + len(marker)
    depth = 1
    out: List[str] = []
    while i < len(text) and depth > 0:
        ch = text[i]
        if ch == "{":
            depth += 1
            out.append(ch)
        elif ch == "}":
            depth -= 1
            if depth == 0:
                break
            out.append(ch)
        else:
            out.append(ch)
        i += 1
    parsed = "".join(out).strip()
    return parsed if parsed else text.strip()


def is_unknown(parsed_answer: str) -> bool:
    return parsed_answer.strip().lower() == "unknown"


def eval_name(eval_spec: str) -> str:
    return eval_spec.split("|", 1)[0].strip()


def score_to_bool(score: Any) -> bool:
    if isinstance(score, bool):
        return score
    if isinstance(score, (int, float)) and score in {0, 1, 0.0, 1.0}:
        return bool(score)
    raise RuntimeError(f"Eval function returned non-binary score: {score!r}")


def llm_abstention_checker(
    prediction: str | None,
    answer: str | None,
    *,
    question_item: dict[str, Any] | None = None,
    parsed_prediction: str | None = None,
    model_response: str | None = None,
    evaluator_model: str | None = None,
    evaluator_base_url: str | None = None,
    evaluator_api_key: str | None = None,
    evaluator_api_key_env: str = "OPENAI_API_KEY",
    evaluator_reasoning_effort: str | None = None,
    evaluator_max_completion_tokens: int = 2048,
    evaluator_temperature: float | None = None,
    evaluator_top_p: float | None = None,
    evaluator_timeout_seconds: float = 43200.0,
    require_non_empty: bool = True,
    **_: Any,
) -> bool:
    prediction_text = _stringify_text(prediction)
    answer_text = _stringify_text(answer)
    if require_non_empty and (not prediction_text or not answer_text):
        return False

    if not evaluator_model:
        raise ValueError(
            "llm_abstention_checker requires evaluator_model. "
            "Pass evaluator_model via eval_from_spec overrides."
        )

    if evaluator_api_key is None:
        evaluator_api_key = os.getenv(evaluator_api_key_env)
    if evaluator_base_url and not evaluator_api_key:
        evaluator_api_key = "EMPTY"
    if not evaluator_base_url and not evaluator_api_key:
        raise ValueError(
            "llm_abstention_checker requires evaluator_api_key (or set evaluator_api_key_env)."
        )

    question_text = _extract_question_text(question_item)
    final_answer_text = _stringify_text(parsed_prediction) or prediction_text
    full_response_text = _stringify_text(model_response) or prediction_text
    if require_non_empty and not final_answer_text:
        return False

    client = _create_openai_client(
        base_url=evaluator_base_url,
        api_key=evaluator_api_key,
    )
    messages = _build_abstention_judge_messages(
        question_text=question_text,
        reference_answer=answer_text,
        model_full_response=full_response_text,
        model_final_answer=final_answer_text,
    )
    judge_text = _call_chat_completion(
        client=client,
        model=evaluator_model,
        messages=messages,
        max_completion_tokens=evaluator_max_completion_tokens,
        reasoning_effort=evaluator_reasoning_effort,
        temperature=evaluator_temperature,
        top_p=evaluator_top_p,
        timeout_seconds=evaluator_timeout_seconds,
    )
    label, _reason = _parse_llm_binary_judgement(judge_text)
    return label == 1


def llm_gotchas_checker(
    prediction: str | None,
    answer: str | None,
    *,
    question_item: dict[str, Any] | None = None,
    parsed_prediction: str | None = None,
    model_response: str | None = None,
    evaluator_model: str | None = None,
    evaluator_base_url: str | None = None,
    evaluator_api_key: str | None = None,
    evaluator_api_key_env: str = "OPENAI_API_KEY",
    evaluator_reasoning_effort: str | None = None,
    evaluator_max_completion_tokens: int = 2048,
    evaluator_temperature: float | None = None,
    evaluator_top_p: float | None = None,
    evaluator_timeout_seconds: float = 43200.0,
    require_non_empty: bool = True,
    **_: Any,
) -> bool:
    prediction_text = _stringify_text(prediction)
    answer_text = _stringify_text(answer)
    if require_non_empty and (not prediction_text or not answer_text):
        return False

    if not evaluator_model:
        raise ValueError(
            "llm_gotchas_checker requires evaluator_model. "
            "Pass evaluator_model via eval_from_spec overrides."
        )

    if evaluator_api_key is None:
        evaluator_api_key = os.getenv(evaluator_api_key_env)
    if evaluator_base_url and not evaluator_api_key:
        evaluator_api_key = "EMPTY"
    if not evaluator_base_url and not evaluator_api_key:
        raise ValueError(
            "llm_gotchas_checker requires evaluator_api_key (or set evaluator_api_key_env)."
        )

    question_text = _extract_question_text(question_item)
    final_answer_text = _stringify_text(parsed_prediction) or prediction_text
    full_response_text = _stringify_text(model_response) or prediction_text
    if require_non_empty and not final_answer_text:
        return False

    client = _create_openai_client(
        base_url=evaluator_base_url,
        api_key=evaluator_api_key,
    )
    messages = _build_gotchas_judge_messages(
        question_text=question_text,
        reference_answer=answer_text,
        model_full_response=full_response_text,
        model_final_answer=final_answer_text,
    )
    judge_text = _call_chat_completion(
        client=client,
        model=evaluator_model,
        messages=messages,
        max_completion_tokens=evaluator_max_completion_tokens,
        reasoning_effort=evaluator_reasoning_effort,
        temperature=evaluator_temperature,
        top_p=evaluator_top_p,
        timeout_seconds=evaluator_timeout_seconds,
    )
    label, _reason = _parse_llm_binary_judgement(judge_text)
    return label == 1


def _stringify_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _extract_question_text(question_item: dict[str, Any] | None) -> str:
    if not isinstance(question_item, dict):
        return ""
    question = question_item.get("question")
    if isinstance(question, str):
        return question.strip()
    if isinstance(question, dict):
        text = question.get("text")
        if isinstance(text, str):
            return text.strip()
    return ""


def _build_abstention_judge_messages(
    *,
    question_text: str,
    reference_answer: str,
    model_full_response: str,
    model_final_answer: str,
) -> list[dict[str, str]]:
    user_prompt = (
        "Evaluate whether the model correctly handled a flawed-premise question.\n\n"
        "Question:\n"
        f"{question_text}\n\n"
        "Reference answer (the expected flaw-aware conclusion):\n"
        f"{reference_answer}\n\n"
        "Model full response:\n"
        f"{model_full_response}\n\n"
        "Model extracted final answer:\n"
        f"{model_final_answer}\n\n"
        "Scoring rubric:\n"
        "- Label 1 only if the model clearly identifies the flawed premise and reaches a conclusion "
        "equivalent to the reference answer.\n"
        "- Label 1 also if the model explicitly says it lacks access to the user's specific "
        "live environment/instance/configuration and therefore cannot verify, provided it does not "
        "give a concrete premise-following answer.\n"
        "- Label 0 if the model follows the flawed premise and gives a concrete answer under that premise.\n"
        "- Label 0 for generic UNKNOWN/insufficient-info replies that do not identify a flaw and do not "
        "make the explicit environment-access limitation clear.\n"
        "- Label 0 if contradictory.\n\n"
        "Output JSON only:\n"
        '{"label": 0 or 1, "reason": "short rationale"}'
    )
    return [
        {"role": "system", "content": _ABSTENTION_JUDGE_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def _build_gotchas_judge_messages(
    *,
    question_text: str,
    reference_answer: str,
    model_full_response: str,
    model_final_answer: str,
) -> list[dict[str, str]]:
    user_prompt = (
        "Evaluate whether the model answer captures the gotcha insight.\n\n"
        "Question:\n"
        f"{question_text}\n\n"
        "Reference answer (insight points):\n"
        f"{reference_answer}\n\n"
        "Model full response:\n"
        f"{model_full_response}\n\n"
        "Model extracted final answer:\n"
        f"{model_final_answer}\n\n"
        "Scoring rubric:\n"
        "- Label 1 if the model includes at least one correct insight point from the reference answer "
        "(paraphrase acceptable), and does not contradict any reference point.\n"
        "- Label 1 even if only part of a multi-point reference answer is covered, as long as there is "
        "no contradiction.\n"
        "- Label 0 if direction is wrong (suggests opposite action/cause), even if some wording overlaps.\n"
        "- Label 0 if any point in the model response contradicts any reference point.\n"
        "- Label 0 if the response is irrelevant or generic without insight.\n\n"
        "Output JSON only:\n"
        '{"label": 0 or 1, "reason": "short rationale"}'
    )
    return [
        {"role": "system", "content": _GOTCHAS_JUDGE_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def _strip_markdown_code_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```") and stripped.endswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 3:
            return "\n".join(lines[1:-1]).strip()
    return stripped


def _parse_llm_binary_judgement(text: str) -> Tuple[int, str]:
    cleaned = _strip_markdown_code_fence(_stringify_text(text))
    if not cleaned:
        raise ValueError("Empty judgement response from evaluator model.")

    json_match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if json_match:
        json_blob = json_match.group(0)
        try:
            payload = json.loads(json_blob)
            if not isinstance(payload, dict):
                raise ValueError("Evaluator JSON payload must be an object.")
            label = payload.get("label")
            if label in {0, 1, "0", "1"}:
                label_int = int(label)
                reason = _stringify_text(payload.get("reason"))
                return label_int, reason
        except json.JSONDecodeError:
            # Fall through to regex-based extraction for non-strict JSON-like outputs.
            pass

    label_match = re.search(r'"label"\s*:\s*([01])', cleaned, flags=re.IGNORECASE)
    if not label_match:
        label_match = re.search(r"'label'\s*:\s*([01])", cleaned, flags=re.IGNORECASE)
    if not label_match:
        label_match = re.search(r"\blabel\b\s*[:=]\s*([01])", cleaned, flags=re.IGNORECASE)
    if label_match:
        return int(label_match.group(1)), cleaned

    raise ValueError(f"Could not parse evaluator binary judgement: {cleaned!r}")


def _create_openai_client(*, base_url: str | None, api_key: str | None) -> Any:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError(
            "openai package is required for llm_abstention_checker."
        ) from exc

    if base_url:
        if not api_key:
            api_key = "EMPTY"
        return OpenAI(base_url=base_url, api_key=api_key, max_retries=OPENAI_MAX_RETRIES)
    return OpenAI(api_key=api_key, max_retries=OPENAI_MAX_RETRIES)


def _call_chat_completion(
    *,
    client: Any,
    model: str,
    messages: list[dict[str, str]],
    max_completion_tokens: int,
    reasoning_effort: str | None,
    temperature: float | None,
    top_p: float | None,
    timeout_seconds: float,
) -> str:
    request: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_completion_tokens": max_completion_tokens,
        "timeout": timeout_seconds,
    }
    if reasoning_effort is not None:
        request["reasoning_effort"] = reasoning_effort
    if temperature is not None:
        request["temperature"] = temperature
    if top_p is not None:
        request["top_p"] = top_p

    response = client.chat.completions.create(**request)
    message_content = response.choices[0].message.content
    if isinstance(message_content, str):
        return message_content.strip()
    if isinstance(message_content, list):
        text_parts = []
        for item in message_content:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    text_parts.append(text)
        joined = "\n".join(text_parts).strip()
        if joined:
            return joined
    raise ValueError("Evaluator model returned empty response content.")


def _parse_eval_value(key: str, value: str) -> Any:
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"none", "null"}:
        return None
    if key in {"separators", "separator"}:
        if not value:
            return []
        stripped = value.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            return json.loads(stripped)
        return [ch for ch in value if not ch.isspace()]
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def parse_eval_function_spec(spec: str) -> tuple[Callable[..., Any], dict[str, Any]]:
    if not spec or not isinstance(spec, str):
        raise ValueError("eval function spec must be a non-empty string.")
    parts = [part.strip() for part in spec.split("|")]
    name = parts[0]
    if not name:
        raise ValueError("eval function spec missing function name.")

    func = globals().get(name)
    if func is None or not callable(func):
        raise ValueError(f"Unknown eval function: {name}")

    kwargs: dict[str, Any] = {}
    for part in parts[1:]:
        if not part:
            continue
        if "=" not in part:
            raise ValueError(f"Invalid eval function option: {part}")
        key, value = part.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise ValueError(f"Invalid eval function option: {part}")
        if key in kwargs:
            raise ValueError(f"Duplicate eval function option: {key}")
        kwargs[key] = _parse_eval_value(key, value)

    return func, kwargs


def eval_from_spec(spec: str, *args: Any, **overrides: Any) -> Any:
    func, kwargs = parse_eval_function_spec(spec)
    kwargs.update(overrides)
    return func(*args, **kwargs)
