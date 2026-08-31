#!/usr/bin/env python3
import argparse
import asyncio
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
import contextlib
import json
import mimetypes
import os
import random
import signal
import shutil
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from openai import AsyncOpenAI, BadRequestError
from tqdm import tqdm

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from memory_modules.memory import (  # noqa: E402
    Memory,
    MemoryContextItem,
    build_memory,
    load_memory,
    load_memory_config,
    save_memory,
)
from evaluation.qa_eval_metrics import (  # noqa: E402
    eval_from_spec,
    eval_name,
    extract_boxed_answer,
    is_unknown,
    score_to_bool,
)


CATEGORY_MAP = {
    "static-environment": "static",
    "static-environment-abs": "static-abs",
    "dynamic-environment": "dynamic",
    "dynamic-environment-abs": "dynamic-abs",
    "procedure": "procedure",
    "procedure-abs": "procedure-abs",
    "errors-gotchas": "gotchas",
}
NON_ABSTENTION_CATEGORIES = ["static", "dynamic", "procedure", "gotchas"]
ABSTENTION_CATEGORIES = ["static-abs", "dynamic-abs", "procedure-abs"]
COMBINED_ABSTENTION_CATEGORY_PAIRS = {
    "static": ("static", "static-abs"),
    "dynamic": ("dynamic", "dynamic-abs"),
    "procedure": ("procedure", "procedure-abs"),
}
LLM_EVAL_FUNCTIONS = {"llm_abstention_checker", "llm_gotchas_checker"}
OPENAI_MAX_RETRIES = 10
MEMORY_CONTEXT_PROCESSOR_LOCAL = threading.local()
NONSHARED_PARALLEL_MEMORY_TYPES = {
    "codex",
    "agentrunbook_c",
    "agentrunbook_c_v2",
    "agentrunbook_r",
    "rag",
}
DOMAIN_SYSTEM_PROMPTS = {
    "web": (
        "You are an experienced colleague in a web browsing environment that has "
        "a customized magento-based shopping website, a customized magento-based "
        "shopping admin cms website, as well as a customized forum website based "
        "on reddit/postmill. Answer based on your memory of the environment. "
        "If you do not know the answer, output exactly \\boxed{UNKNOWN}. "
        "Do not guess. Never attempt to guess an answer if you are not sure. "
        "If you believe the question's construction/premise is wrong, provide an "
        "explanation in \boxed{} explaining why the question is flawed."
    ),
    "enterprise": (
        "You are an experienced colleague working in a customized ServiceNow "
        "environment. Answer based on your memory of the environment. "
        "If you do not know the answer, output exactly \\boxed{UNKNOWN}. "
        "Do not guess. Never attempt to guess an answer if you are not sure. "
        "If you believe the question's construction/premise is wrong, provide an "
        "explanation in \boxed{} explaining why the question is flawed."
    ),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


@contextlib.contextmanager
def prompt_build_interrupt_context(cancel_event: threading.Event) -> Any:
    signals_to_patch: list[int] = []
    if threading.current_thread() is threading.main_thread():
        signals_to_patch.extend([signal.SIGINT, signal.SIGTERM])
        if hasattr(signal, "SIGHUP"):
            signals_to_patch.append(signal.SIGHUP)
    previous_handlers: dict[int, Any] = {}

    def _handle_interrupt(signum: int, _frame: Any) -> None:
        cancel_event.set()
        raise KeyboardInterrupt(f"Received signal {signum}")

    try:
        for sig in signals_to_patch:
            previous_handlers[sig] = signal.getsignal(sig)
            signal.signal(sig, _handle_interrupt)
        yield
    finally:
        for sig, handler in previous_handlers.items():
            signal.signal(sig, handler)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LongMemEval-V2 evaluation harness.")
    parser.add_argument("--domain", choices=["web", "enterprise"], required=True)
    parser.add_argument("--questions-path", required=True, help="Path to JSON file containing evaluation questions")
    parser.add_argument("--haystack-path", required=True, help="Path to JSON file mapping question id to list of trajectory ids in its haystack")
    parser.add_argument("--trajectories-path", required=True, help="Path to JSON file containing trajectory data")
    parser.add_argument(
        "--memory-config-path",
        default=None,
        help=(
            "Path to JSON file containing memory configuration. When used with "
            "--load-memory-dir, the memory class validates and reconciles the "
            "requested config against the saved memory config."
        ),
    )
    parser.add_argument("--output-dir", required=True, help="Directory to save evaluation results")
    parser.add_argument(
        "--save-memory",
        action="store_true",
        help="Save the shared memory state to output_dir/memory_state after indexing",
    )
    parser.add_argument(
        "--skip-evaluation",
        action="store_true",
        help="Build and save shared memory, then exit before prompt construction",
    )
    parser.add_argument(
        "--load-memory-dir",
        default=None,
        help="Path to a saved memory_state directory to load instead of rebuilding from trajectories",
    )

    # Reader model parameters
    parser.add_argument("--model", default=None)
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--api-key-env", default="OPENAI_API_KEY")
    parser.add_argument("--api-key-file", default=None)
    parser.add_argument("--max-completion-tokens", type=int, default=20000)
    parser.add_argument("--memory-context-max-tokens", type=int, default=200000)
    parser.add_argument("--prompt-build-max-workers", type=int, default=1)
    parser.add_argument(
        "--shuffle-questions-seed",
        type=int,
        default=None,
        help="Shuffle question streaming order with this fixed seed before prompt construction",
    )
    parser.add_argument("--reader-max-concurrent-requests", type=int, default=500)
    parser.add_argument("--timeout-seconds", type=float, default=43200.0)
    parser.add_argument("--reasoning-effort", choices=["low", "medium", "high"], default=None)
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--top-p", type=float, default=None)
    parser.add_argument("--presence-penalty", type=float, default=None)
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--repetition-penalty", type=float, default=None)
    reader_thinking_group = parser.add_mutually_exclusive_group()
    reader_thinking_group.add_argument(
        "--reader-enable-thinking",
        dest="reader_enable_thinking",
        action="store_true",
    )
    reader_thinking_group.add_argument(
        "--reader-disable-thinking",
        dest="reader_enable_thinking",
        action="store_false",
    )
    parser.set_defaults(reader_enable_thinking=True)

    # Evaluator model parameters (for eval functions that use LLMs)
    parser.add_argument("--evaluator-model", default=None)
    parser.add_argument("--evaluator-base-url", default=None)
    parser.add_argument("--evaluator-api-key-env", default="OPENAI_API_KEY")
    parser.add_argument("--evaluator-api-key-file", default=None)
    parser.add_argument(
        "--evaluator-reasoning-effort",
        choices=["low", "medium", "high"],
        default="medium",
    )
    parser.add_argument("--evaluator-max-completion-tokens", type=int, default=4096)
    parser.add_argument("--evaluator-timeout-seconds", type=float, default=43200.0)
    return parser.parse_args()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def load_json_list(path_str: str) -> list[dict[str, Any]]:
    path = Path(path_str)
    require(path.exists(), f"Missing JSON file: {path}")
    if path.suffix == ".jsonl":
        data = [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    else:
        data = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(data, list), f"Expected list in {path}")
    return data


def load_questions(path_str: str) -> list[dict[str, Any]]:
    return load_json_list(path_str)


def get_system_prompt(domain: str) -> str:
    require(domain in DOMAIN_SYSTEM_PROMPTS, f"Unsupported domain: {domain}")
    return DOMAIN_SYSTEM_PROMPTS[domain]


def load_trajectories(path_str: str) -> dict[str, dict[str, Any]]:
    trajectories = load_json_list(path_str)
    out: dict[str, dict[str, Any]] = {}
    for idx, traj in enumerate(trajectories):
        traj_id = traj.get("id")
        require(isinstance(traj_id, str) and traj_id, f"Invalid trajectory id at index {idx}")
        require(traj_id not in out, f"Duplicate trajectory id: {traj_id}")
        out[traj_id] = traj
    return out


def load_haystack_mapping(path_str: str) -> dict[str, list[str]]:
    path = Path(path_str)
    require(path.exists(), f"Missing haystack file: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(data, dict), "Haystack JSON must be an object mapping question id to list")
    out: dict[str, list[str]] = {}
    for key, value in data.items():
        require(isinstance(key, str) and key, "Haystack question ids must be non-empty strings")
        require(isinstance(value, list), f"Haystack entry for {key} must be a list")
        require(all(isinstance(item, str) and item for item in value), f"Haystack entry for {key} must contain non-empty string ids")
        out[key] = list(value)
    return out


def inject_runtime_memory_params(
    memory_config: dict[str, Any],
    *,
    workspace_dir: Path,
    trajectories_path: str,
    reader_temperature: float | None = None,
    reader_top_p: float | None = None,
    query_trace_dir: Path | None = None,
) -> dict[str, Any]:
    runtime_config = {
        "memory_type": memory_config["memory_type"],
        "memory_params": dict(memory_config["memory_params"]),
    }
    if runtime_config["memory_type"] not in {
        "rag",
        "agentrunbook_r",
        "codex",
        "agentrunbook_c",
        "agentrunbook_c_v2",
    }:
        return runtime_config

    runtime_config["memory_params"]["workspace_dir"] = str(workspace_dir.resolve())
    runtime_config["memory_params"]["trajectories_root_dir"] = str(
        Path(trajectories_path).resolve().parent
    )
    if runtime_config["memory_type"] in {"codex", "agentrunbook_c", "agentrunbook_c_v2"} and query_trace_dir is not None:
        runtime_config["memory_params"]["query_trace_dir"] = str(query_trace_dir.resolve())
    if runtime_config["memory_type"] == "agent_runbook":
        generation_params_obj = runtime_config["memory_params"].get("generation_params", {})
        require(
            isinstance(generation_params_obj, dict),
            "agent_runbook generation_params must be an object",
        )
        generation_params = dict(generation_params_obj)
        if reader_temperature is not None:
            generation_params["temperature"] = reader_temperature
        if reader_top_p is not None:
            generation_params["top_p"] = reader_top_p
        runtime_config["memory_params"]["generation_params"] = generation_params
        if query_trace_dir is not None:
            runtime_config["memory_params"]["query_trace_dir"] = str(query_trace_dir.resolve())
    return runtime_config


def validate_memory_context_items(
    memory_context: Any,
    *,
    question_id: str,
) -> list[MemoryContextItem]:
    require(isinstance(memory_context, list), f"memory.query must return a list for {question_id}")
    validated: list[MemoryContextItem] = []
    for idx, item in enumerate(memory_context):
        require(
            isinstance(item, dict),
            f"memory.query item {idx} must be an object for {question_id}",
        )
        item_type = item.get("type")
        value = item.get("value")
        require(
            item_type in {"text", "image"},
            f"memory.query item {idx} has invalid type {item_type!r} for {question_id}",
        )
        require(
            isinstance(value, str) and value.strip(),
            f"memory.query item {idx} has invalid value for {question_id}",
        )
        if item_type == "image":
            require(Path(value).exists(), f"memory.query image path does not exist for {question_id}: {value}")
        validated.append({"type": item_type, "value": value})
    return validated


def supports_nonshared_parallel_prompt_build(memory_type: str) -> bool:
    return memory_type in NONSHARED_PARALLEL_MEMORY_TYPES


def memory_config_enables_online_learning(memory_config: dict[str, Any] | None) -> bool:
    if memory_config is None or memory_config.get("memory_type") != "agentrunbook_c_v2":
        return False
    memory_params = memory_config.get("memory_params")
    if not isinstance(memory_params, dict):
        return False
    online_learning_params = memory_params.get("online_learning_params")
    return (
        isinstance(online_learning_params, dict)
        and online_learning_params.get("enabled") is True
    )


def get_memory_context_processor() -> Any:
    from transformers import AutoProcessor

    processor = getattr(MEMORY_CONTEXT_PROCESSOR_LOCAL, "processor", None)
    if processor is None:
        processor = AutoProcessor.from_pretrained("Qwen/Qwen3.5-9B")
        MEMORY_CONTEXT_PROCESSOR_LOCAL.processor = processor
    return processor


def load_memory_context_images(memory_context: list[MemoryContextItem]) -> list[Any | None]:
    from PIL import Image

    loaded_images: list[Any | None] = []
    for item in memory_context:
        if item["type"] != "image":
            loaded_images.append(None)
            continue
        with Image.open(item["value"]) as image:
            loaded_images.append(image.convert("RGB"))
    return loaded_images


def count_memory_context_tokens(
    memory_context: list[MemoryContextItem],
    loaded_images: list[Any | None],
) -> int:
    require(
        len(memory_context) == len(loaded_images),
        "memory_context and loaded_images must have the same length",
    )
    if not memory_context:
        return 0

    processor = get_memory_context_processor()
    content_parts: list[dict[str, str]] = []
    images: list[Any] = []
    for item, loaded_image in zip(memory_context, loaded_images):
        if item["type"] == "text":
            content_parts.append({"type": "text", "text": item["value"]})
            continue
        require(loaded_image is not None, "Missing loaded image for memory context item")
        content_parts.append({"type": "image"})
        images.append(loaded_image)

    prompt_text = processor.apply_chat_template(
        [{"role": "user", "content": content_parts}],
        tokenize=False,
        add_generation_prompt=False,
    )
    encoded = processor(
        text=prompt_text,
        images=images or None,
        return_tensors="pt",
    )
    return int(encoded["input_ids"].shape[-1])


def truncate_memory_context(
    memory_context: list[MemoryContextItem],
    *,
    max_tokens: int,
    question_id: str,
) -> tuple[list[MemoryContextItem], int, int]:
    require(max_tokens > 0, "memory_context_max_tokens must be positive")
    loaded_images = load_memory_context_images(memory_context)
    prefix_token_counts: dict[int, int] = {0: 0}

    def prefix_token_count(prefix_length: int) -> int:
        require(
            0 <= prefix_length <= len(memory_context),
            f"Invalid memory context prefix length {prefix_length} for {question_id}",
        )
        if prefix_length not in prefix_token_counts:
            prefix_token_counts[prefix_length] = count_memory_context_tokens(
                memory_context[:prefix_length],
                loaded_images[:prefix_length],
            )
        return prefix_token_counts[prefix_length]

    original_token_count = prefix_token_count(len(memory_context))
    if original_token_count <= max_tokens:
        return memory_context, original_token_count, original_token_count

    lo = 0
    hi = len(memory_context)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if prefix_token_count(mid) <= max_tokens:
            lo = mid
        else:
            hi = mid - 1

    truncated_items = memory_context[:lo]
    truncated_token_count = prefix_token_count(lo)
    print(
        f"Truncated memory context for {question_id}: "
        f"original_tokens={original_token_count} "
        f"truncated_tokens={truncated_token_count} "
        f"original_items={len(memory_context)} "
        f"truncated_items={len(truncated_items)}"
    )
    return truncated_items, original_token_count, truncated_token_count


def all_haystacks_shared(question_ids: list[str], haystack_mapping: dict[str, list[str]]) -> bool:
    if not question_ids:
        return False
    first = haystack_mapping[question_ids[0]]
    return all(haystack_mapping[qid] == first for qid in question_ids[1:])


def validate_question_and_haystack_ids(
    question_ids: list[str],
    haystack_mapping: dict[str, list[str]],
) -> None:
    question_id_set = set(question_ids)
    haystack_id_set = set(haystack_mapping)
    require(
        question_id_set == haystack_id_set,
        "Question ids and haystack question ids must match exactly. "
        f"missing_in_haystack={sorted(question_id_set - haystack_id_set)} "
        f"extra_in_haystack={sorted(haystack_id_set - question_id_set)}",
    )


def load_api_key(api_key_env: str, api_key_file: str | None) -> str | None:
    env_value = os.getenv(api_key_env)
    if env_value:
        return env_value
    if api_key_file is None:
        return None
    path = Path(api_key_file)
    require(path.exists(), f"Missing API key file: {path}")
    value = path.read_text(encoding="utf-8").strip()
    require(value, f"Empty API key file: {path}")
    return value


def create_async_client(base_url: str | None, api_key_env: str, api_key_file: str | None) -> AsyncOpenAI:
    api_key = load_api_key(api_key_env, api_key_file)
    if base_url:
        return AsyncOpenAI(base_url=base_url, api_key=api_key or "EMPTY", max_retries=OPENAI_MAX_RETRIES)
    require(api_key is not None, f"Missing API key via env {api_key_env} or key file")
    return AsyncOpenAI(api_key=api_key, max_retries=OPENAI_MAX_RETRIES)


def get_question_components(question_field: Any) -> Tuple[str, Optional[str]]:
    if isinstance(question_field, str):
        return question_field, None
    require(isinstance(question_field, dict), "question must be str or dict")
    text = question_field.get("text")
    image = question_field.get("image")
    require(isinstance(text, str) and text.strip(), "question.text must be non-empty")
    require(isinstance(image, str) and image.strip(), "question.image must be non-empty")
    return text, image


def to_data_url(image_path: str) -> str:
    path = Path(image_path)
    require(path.exists(), f"Missing image file: {path}")
    mime, _ = mimetypes.guess_type(str(path))
    raw = path.read_bytes()
    encoded = base64.b64encode(raw).decode("ascii")
    return f"data:{mime or 'image/png'};base64,{encoded}"


def build_messages(
    system_prompt: str,
    question_text: str,
    image_path: str | None,
    memory_context: list[MemoryContextItem],
) -> Tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    intro_text = "### Memory context:\n"
    if not memory_context:
        intro_text += "(empty)"
    content_parts: list[dict[str, Any]] = [{"type": "text", "text": intro_text}]
    log_parts: list[dict[str, Any]] = [{"type": "text", "text": intro_text}]
    for item in memory_context:
        if item["type"] == "text":
            content_parts.append({"type": "text", "text": item["value"]})
            log_parts.append({"type": "text", "text": item["value"]})
        else:
            content_parts.append({"type": "image_url", "image_url": {"url": to_data_url(item["value"])}})
            log_parts.append({"type": "image_path", "image_path": item["value"]})
    question_block = f"\n\n### Question to answer:\n{question_text}"
    content_parts.append({"type": "text", "text": question_block})
    log_parts.append({"type": "text", "text": question_block})
    if image_path is not None:
        content_parts.append({"type": "image_url", "image_url": {"url": to_data_url(image_path)}})
        log_parts.append({"type": "image_path", "image_path": image_path})
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": content_parts},
    ]
    messages_for_log = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": log_parts},
    ]
    return messages, messages_for_log


def build_prompt_row(
    item: dict[str, Any],
    *,
    haystack_ids: list[str],
    memory: Memory,
    system_prompt: str,
    memory_context_max_tokens: int,
) -> dict[str, Any]:
    qid = item["question_id"]
    memory.set_query_context(
        query_invocation_id=item["query_invocation_id"],
    )
    try:
        query_started_at = time.perf_counter()
        memory_context = validate_memory_context_items(
            memory.query(
                item["question_text"],
                query_image=item["question_image"],
            ),
            question_id=qid,
        )
        memory_query_duration_seconds = time.perf_counter() - query_started_at
        post_query_started_at = time.perf_counter()
        memory_post_query_metadata = memory.post_query_hook(
            query=item["question_text"],
            query_image=item["question_image"],
            memory_context=memory_context,
        )
        memory_post_query_duration_seconds = time.perf_counter() - post_query_started_at
    finally:
        memory.clear_query_context()
    memory_context, original_memory_token_count, truncated_memory_token_count = truncate_memory_context(
        memory_context,
        max_tokens=memory_context_max_tokens,
        question_id=qid,
    )
    messages, messages_for_log = build_messages(
        system_prompt=system_prompt,
        question_text=item["question_text"],
        image_path=item["question_image"],
        memory_context=memory_context,
    )
    return {
        **item,
        "haystack_ids": haystack_ids,
        "memory_context": memory_context,
        "memory_query_duration_seconds": memory_query_duration_seconds,
        "memory_post_query_duration_seconds": memory_post_query_duration_seconds,
        "memory_post_query_metadata": memory_post_query_metadata,
        "memory_context_original_token_count": original_memory_token_count,
        "memory_context_token_count": truncated_memory_token_count,
        "memory_context_was_truncated": original_memory_token_count > truncated_memory_token_count,
        "messages": messages,
        "prompt_messages": messages_for_log,
        "is_abstention_problem": item["eval_name"] == "llm_abstention_checker",
    }


def _latest_query_attempt_summary_path(
    query_trace_dir: Path,
    query_invocation_id: str,
) -> Path | None:
    invocation_trace_dir = query_trace_dir / query_invocation_id
    if not invocation_trace_dir.exists():
        return None
    attempt_dirs = sorted(
        path
        for path in invocation_trace_dir.iterdir()
        if path.is_dir() and path.name.startswith("attempt_")
    )
    for attempt_dir in reversed(attempt_dirs):
        summary_path = attempt_dir / "summary.json"
        if summary_path.exists():
            return summary_path
    return None


def _selected_trajectory_ids_from_query_summary(summary_payload: dict[str, Any]) -> list[str]:
    spans = summary_payload.get("trajectory_spans_valid")
    if not isinstance(spans, list):
        return []
    selected: list[str] = []
    seen: set[str] = set()
    for idx, span in enumerate(spans):
        if not isinstance(span, dict):
            continue
        trajectory_id = span.get("trajectory_id")
        if not isinstance(trajectory_id, str) or not trajectory_id.strip():
            continue
        if trajectory_id in seen:
            continue
        seen.add(trajectory_id)
        selected.append(trajectory_id)
    return selected


def _rewrite_compacted_workspace_metadata(workspace_dir: Path, kept_trajectory_ids: list[str]) -> None:
    index_path = workspace_dir / "index.json"
    haystack_manifest_path = workspace_dir / "haystack_manifest.json"

    ordered_ids = list(kept_trajectory_ids)
    memory_type = "unknown"
    if index_path.exists():
        index_payload = json.loads(index_path.read_text(encoding="utf-8"))
        require(isinstance(index_payload, dict), f"index.json must contain an object: {index_path}")
        existing_ids = index_payload.get("inserted_trajectory_ids")
        if isinstance(existing_ids, list) and all(isinstance(item, str) for item in existing_ids):
            keep_set = set(kept_trajectory_ids)
            ordered_ids = [traj_id for traj_id in existing_ids if traj_id in keep_set]
            for traj_id in kept_trajectory_ids:
                if traj_id not in ordered_ids:
                    ordered_ids.append(traj_id)
        memory_type_value = index_payload.get("memory_type")
        if isinstance(memory_type_value, str) and memory_type_value.strip():
            memory_type = memory_type_value

    save_json(
        index_path,
        {
            "memory_type": memory_type,
            "updated_at_utc": utc_now_iso(),
            "trajectory_count": len(ordered_ids),
            "inserted_trajectory_ids": ordered_ids,
        },
    )

    haystack_id = "compacted_memory_workspace"
    haystack_variant = "current_memory_workspace_compacted"
    haystack_metadata: dict[str, Any] = {}
    if haystack_manifest_path.exists():
        haystack_payload = json.loads(haystack_manifest_path.read_text(encoding="utf-8"))
        require(
            isinstance(haystack_payload, dict),
            f"haystack_manifest.json must contain an object: {haystack_manifest_path}",
        )
        haystack_id_value = haystack_payload.get("id")
        if isinstance(haystack_id_value, str) and haystack_id_value.strip():
            haystack_id = haystack_id_value
        haystack_variant_value = haystack_payload.get("variant")
        if isinstance(haystack_variant_value, str) and haystack_variant_value.strip():
            haystack_variant = haystack_variant_value
        metadata_value = haystack_payload.get("metadata")
        if isinstance(metadata_value, dict):
            haystack_metadata = dict(metadata_value)

    haystack_metadata["generated_at_utc"] = utc_now_iso()
    haystack_metadata["trajectory_count"] = len(ordered_ids)
    if memory_type != "unknown":
        haystack_metadata["memory_type"] = memory_type

    save_json(
        haystack_manifest_path,
        {
            "id": haystack_id,
            "variant": haystack_variant,
            "trajectory_ids": ordered_ids,
            "metadata": haystack_metadata,
        },
    )


def compact_nonshared_memory_workspace(
    *,
    workspace_dir: Path,
    query_trace_dir: Path,
    query_invocation_id: str,
) -> None:
    summary_path = _latest_query_attempt_summary_path(
        query_trace_dir,
        query_invocation_id,
    )
    if summary_path is None:
        return None
    summary_payload = json.loads(summary_path.read_text(encoding="utf-8"))
    require(isinstance(summary_payload, dict), f"summary.json must contain an object: {summary_path}")
    if summary_payload.get("status_after") != "finished":
        return None

    kept_trajectory_ids = _selected_trajectory_ids_from_query_summary(summary_payload)
    trajectories_dir = workspace_dir / "trajectories"
    if not trajectories_dir.exists():
        return None

    keep_set = set(kept_trajectory_ids)
    for path in trajectories_dir.iterdir():
        if path.name.endswith(".md"):
            continue
        if path.name in keep_set:
            continue
        if path.is_symlink():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)
    _rewrite_compacted_workspace_metadata(workspace_dir, kept_trajectory_ids)
    return None


def build_prompt_row_with_per_question_memory(
    item: dict[str, Any],
    *,
    haystack_ids: list[str],
    memory_config: dict[str, Any],
    trajectories: dict[str, dict[str, Any]],
    trajectories_path: str,
    workspace_dir: Path,
    query_trace_dir: Path,
    system_prompt: str,
    memory_context_max_tokens: int,
    reader_temperature: float | None,
    reader_top_p: float | None,
    cancel_event: threading.Event | None,
) -> dict[str, Any]:
    question_id = item["question_id"]
    total_trajectories = len(haystack_ids)
    insert_log_interval = max(1, total_trajectories // 4)
    worker_started_at = time.perf_counter()
    insert_started_at = worker_started_at
    print(
        f"[prompt-build][{question_id}] start: building per-question memory from "
        f"{total_trajectories} trajectories",
        flush=True,
    )
    memory = build_memory(
        inject_runtime_memory_params(
            memory_config,
            workspace_dir=workspace_dir,
            trajectories_path=trajectories_path,
            reader_temperature=reader_temperature,
            reader_top_p=reader_top_p,
            query_trace_dir=query_trace_dir,
        )
    )
    memory.configure_runtime(
        query_trace_dir=query_trace_dir,
        generation_temperature=reader_temperature,
        generation_top_p=reader_top_p,
        cancel_event=cancel_event,
    )
    for insert_index, traj_id in enumerate(haystack_ids, start=1):
        require(traj_id in trajectories, f"Missing trajectory id in trajectories data: {traj_id}")
        memory.insert(trajectories[traj_id])
        if insert_index % insert_log_interval == 0 or insert_index == total_trajectories:
            insert_elapsed = time.perf_counter() - insert_started_at
            print(
                f"[prompt-build][{question_id}] inserted {insert_index}/{total_trajectories} "
                f"trajectories in {insert_elapsed:.1f}s",
                flush=True,
            )
    insert_elapsed = time.perf_counter() - insert_started_at
    print(
        f"[prompt-build][{question_id}] memory ready in {insert_elapsed:.1f}s; starting query",
        flush=True,
    )
    prompt_row = build_prompt_row(
        item,
        haystack_ids=haystack_ids,
        memory=memory,
        system_prompt=system_prompt,
        memory_context_max_tokens=memory_context_max_tokens,
    )
    if supports_nonshared_parallel_prompt_build(memory_config["memory_type"]):
        compact_nonshared_memory_workspace(
            workspace_dir=workspace_dir,
            query_trace_dir=query_trace_dir,
            query_invocation_id=item["query_invocation_id"],
        )
    total_elapsed = time.perf_counter() - worker_started_at
    print(
        f"[prompt-build][{question_id}] prompt ready in {total_elapsed:.1f}s "
        f"(memory_query={prompt_row['memory_query_duration_seconds']:.1f}s)",
        flush=True,
    )
    return prompt_row


def extract_text_from_response_message(message: Any) -> str:
    content = getattr(message, "content", None)
    if isinstance(content, str) and content.strip():
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text_val = item.get("text")
                if isinstance(text_val, str) and text_val.strip():
                    parts.append(text_val.strip())
            else:
                text_val = getattr(item, "text", None)
                if isinstance(text_val, str) and text_val.strip():
                    parts.append(text_val.strip())
        joined = "\n".join(parts).strip()
        if joined:
            return joined
    reasoning = getattr(message, "reasoning", None)
    if isinstance(reasoning, str) and reasoning.strip():
        return reasoning.strip()
    return ""


def build_extra_body(args: argparse.Namespace) -> dict[str, Any] | None:
    extra_body: dict[str, Any] = {}
    if args.top_k is not None:
        extra_body["top_k"] = args.top_k
    if args.repetition_penalty is not None:
        extra_body["repetition_penalty"] = args.repetition_penalty
    if args.base_url and args.model == "Qwen/Qwen3.5-9B" and not args.reader_enable_thinking:
        extra_body["chat_template_kwargs"] = {"enable_thinking": False}
    return extra_body or None


def build_reader_request(
    args: argparse.Namespace,
    messages: list[dict[str, Any]],
) -> dict[str, Any]:
    req: dict[str, Any] = {
        "model": args.model,
        "messages": messages,
        "timeout": args.timeout_seconds,
    }
    if args.base_url:
        req["max_tokens"] = args.max_completion_tokens
    else:
        req["max_completion_tokens"] = args.max_completion_tokens
    if args.reasoning_effort is not None:
        req["reasoning_effort"] = args.reasoning_effort
    if args.temperature is not None:
        req["temperature"] = args.temperature
    if args.top_p is not None:
        req["top_p"] = args.top_p
    if args.presence_penalty is not None:
        req["presence_penalty"] = args.presence_penalty
    extra_body = build_extra_body(args)
    if extra_body is not None:
        req["extra_body"] = extra_body
    return req


def extract_usage_dict(response: Any) -> dict[str, int]:
    usage = getattr(response, "usage", None)
    return {
        "prompt_tokens": int(getattr(usage, "prompt_tokens", 0) or 0),
        "completion_tokens": int(getattr(usage, "completion_tokens", 0) or 0),
        "total_tokens": int(getattr(usage, "total_tokens", 0) or 0),
    }


async def call_reader_model_async(
    client: AsyncOpenAI,
    args: argparse.Namespace,
    messages: list[dict[str, Any]],
) -> tuple[str, dict[str, int]]:
    response = await client.chat.completions.create(**build_reader_request(args, messages))
    text = extract_text_from_response_message(response.choices[0].message)
    require(text != "", "Model returned empty text")
    return text, extract_usage_dict(response)


async def generate_all_reader_outputs(
    args: argparse.Namespace,
    prompt_rows: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    require(
        args.reader_max_concurrent_requests > 0,
        "reader_max_concurrent_requests must be positive",
    )
    client = create_async_client(args.base_url, args.api_key_env, args.api_key_file)
    semaphore = asyncio.Semaphore(args.reader_max_concurrent_requests)

    async def run_one(row: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        async with semaphore:
            try:
                response_raw, usage = await call_reader_model_async(client, args, row["messages"])
            except BadRequestError as exc:
                print(
                    f"Reader request failed for question_id={row['question_id']}: {exc}. "
                    "Using empty response and continuing.",
                    file=sys.stderr,
                    flush=True,
                )
                response_raw = ""
                usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        parsed_answer = extract_boxed_answer(response_raw)
        return row["question_id"], {
            "response_raw": response_raw,
            "response_parsed_boxed": parsed_answer,
            "is_unknown": is_unknown(parsed_answer),
            "usage": usage,
        }

    tasks = [asyncio.create_task(run_one(row)) for row in prompt_rows]
    outputs: dict[str, dict[str, Any]] = {}
    with tqdm(total=len(tasks), desc="Generating", unit="q") as progress:
        for task in asyncio.as_completed(tasks):
            question_id, output = await task
            outputs[question_id] = output
            progress.update(1)

    await client.close()
    return outputs


def category_from_question_type(question_type: str) -> str:
    require(question_type in CATEGORY_MAP, f"Unexpected question_type: {question_type}")
    return CATEGORY_MAP[question_type]


def aggregate_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    require(records, "No records to aggregate")

    non_abst = [r for r in records if not r["is_abstention_problem"]]
    abst = [r for r in records if r["is_abstention_problem"]]

    def mean_score(rows: list[dict[str, Any]]) -> float | None:
        if not rows:
            return None
        return sum(float(r["score"]) for r in rows) / len(rows)

    def breakdown(rows: list[dict[str, Any]]) -> dict[str, Any]:
        n = len(rows)
        if n == 0:
            return {
                "count": 0,
                "pct_correct": None,
                "pct_answered_wrong": None,
                "pct_unknown": None,
            }
        unknown_count = sum(1 for r in rows if r["is_unknown"])
        correct_count = sum(1 for r in rows if r["score_bool"] and not r["is_unknown"])
        wrong_count = n - correct_count - unknown_count
        return {
            "count": n,
            "pct_correct": correct_count / n,
            "pct_answered_wrong": wrong_count / n,
            "pct_unknown": unknown_count / n,
        }

    overall = {
        "overall_full_set": mean_score(records),
        "overall_non_abstention_only": mean_score(non_abst),
        "overall_abstention_only": mean_score(abst),
        "count_all_questions": len(records),
        "count_non_abstention": len(non_abst),
        "count_abstention": len(abst),
    }

    non_abstention_by_category: dict[str, Any] = {}
    for cat in NON_ABSTENTION_CATEGORIES:
        rows = [r for r in non_abst if r["category"] == cat]
        non_abstention_by_category[cat] = breakdown(rows)

    abstention_by_category: dict[str, Any] = {}
    for cat in ABSTENTION_CATEGORIES:
        rows = [r for r in abst if r["category"] == cat]
        abstention_by_category[cat] = breakdown(rows)

    combined_abstention_by_category: dict[str, Any] = {}
    for cat, pair in COMBINED_ABSTENTION_CATEGORY_PAIRS.items():
        rows = [r for r in records if r["category"] in pair]
        combined_abstention_by_category[cat] = breakdown(rows)

    return {
        "overall": overall,
        "non_abstention_by_category": non_abstention_by_category,
        "abstention_by_category": abstention_by_category,
        "combined_abstention_by_category": combined_abstention_by_category,
        "abstention_overall": breakdown(abst),
    }


def make_eval_config(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "evaluator_model": args.evaluator_model,
        "evaluator_base_url": args.evaluator_base_url,
        "evaluator_api_key": load_api_key(args.evaluator_api_key_env, args.evaluator_api_key_file),
        "evaluator_reasoning_effort": args.evaluator_reasoning_effort,
        "evaluator_max_completion_tokens": args.evaluator_max_completion_tokens,
        "evaluator_timeout_seconds": args.evaluator_timeout_seconds,
    }


def score_prediction(
    row: dict[str, Any],
    eval_config: dict[str, Any],
) -> tuple[bool, str, bool]:
    q_eval_name = row["eval_name"]
    eval_kwargs: dict[str, Any] = {}
    if q_eval_name in LLM_EVAL_FUNCTIONS:
        eval_kwargs.update(eval_config)
        eval_kwargs["question_item"] = row["question_item"]
        eval_kwargs["parsed_prediction"] = row["response_parsed_boxed"]
        eval_kwargs["model_response"] = row["response_raw"]

    prediction_for_eval = row["response_parsed_boxed"]
    if q_eval_name in LLM_EVAL_FUNCTIONS:
        prediction_for_eval = row["response_raw"]

    score_raw = eval_from_spec(
        row["eval_function"],
        prediction_for_eval,
        row["answer_gold"],
        **eval_kwargs,
    )
    score_bool = score_to_bool(score_raw)
    if row["is_unknown"]:
        score_bool = False
    return score_bool, q_eval_name, row["is_unknown"]


def main() -> None:
    args = parse_args()
    require(args.prompt_build_max_workers > 0, "--prompt-build-max-workers must be positive")
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    memory_state_dir = output_dir / "memory_state"
    memory_workspace_root = output_dir / "memory_workspace"

    require(not args.skip_evaluation or args.save_memory, "--skip-evaluation requires --save-memory")
    require(not args.load_memory_dir or not args.save_memory, "--load-memory-dir cannot be combined with --save-memory")
    require(
        args.load_memory_dir or args.memory_config_path is not None,
        "--memory-config-path is required unless --load-memory-dir is used",
    )
    require(
        args.skip_evaluation or (isinstance(args.model, str) and args.model.strip()),
        "--model is required unless --skip-evaluation is set",
    )
    memory_config_template: dict[str, Any] | None = None
    if args.memory_config_path is not None:
        memory_config_template = load_memory_config(args.memory_config_path)
    parallel_guard_memory_config = memory_config_template
    if parallel_guard_memory_config is None and args.load_memory_dir is not None:
        parallel_guard_memory_config = load_memory_config(
            Path(args.load_memory_dir) / "memory_config.json"
        )
    require(
        not (
            args.prompt_build_max_workers > 1
            and memory_config_enables_online_learning(parallel_guard_memory_config)
        ),
        "--prompt-build-max-workers > 1 is not supported when online learning is enabled",
    )
    if args.load_memory_dir is None:
        if memory_config_template["memory_type"] in {
            "rag",
            "agentrunbook_r",
            "codex",
            "agentrunbook_c",
            "agentrunbook_c_v2",
        }:
            require(
                not memory_workspace_root.exists(),
                f"Refusing to overwrite existing memory workspace: {memory_workspace_root}",
            )
    if args.save_memory:
        require(
            not memory_state_dir.exists(),
            f"Refusing to overwrite existing memory state: {memory_state_dir}",
        )

    save_json(output_dir / "run_args.json", {**vars(args), "started_at_utc": utc_now_iso()})

    questions = load_questions(args.questions_path)
    haystack_mapping = load_haystack_mapping(args.haystack_path)

    # Loading and validating questions
    prepared_questions: list[dict[str, Any]] = []
    question_ids: list[str] = []
    seen_question_ids: set[str] = set()
    for idx, question_item in enumerate(questions):
        qid = question_item.get("id")
        qtype = question_item.get("question_type")
        q_eval_spec = question_item.get("eval_function")
        answer = question_item.get("answer")
        require(isinstance(qid, str) and qid, f"Invalid id at question index {idx}")
        require(isinstance(qtype, str) and qtype, f"Invalid question_type for {qid}")
        require(isinstance(q_eval_spec, str) and q_eval_spec, f"Invalid eval_function for {qid}")
        require(isinstance(answer, str), f"Invalid answer for {qid}")
        require(qid not in seen_question_ids, f"Duplicate question id: {qid}")
        seen_question_ids.add(qid)
        require(qid in haystack_mapping, f"Missing haystack entry for question {qid}")
        q_eval_name = eval_name(q_eval_spec)
        if q_eval_name == "llm_abstention_checker":
            require(
                "-abs" in qtype,
                f"llm_abstention_checker question must use an -abs question_type (qid={qid}, question_type={qtype})",
            )
        question_text, image_path = get_question_components(question_item.get("question"))
        prepared_questions.append(
            {
                "index": idx,
                "question_item": question_item,
                "question_id": qid,
                "query_invocation_id": uuid.uuid4().hex,
                "question_type": qtype,
                "category": category_from_question_type(qtype),
                "eval_function": q_eval_spec,
                "eval_name": q_eval_name,
                "question_text": question_text,
                "question_image": image_path,
                "answer_gold": answer,
            }
        )
        question_ids.append(qid)

    validate_question_and_haystack_ids(question_ids, haystack_mapping)
    original_question_ids = list(question_ids)
    if args.shuffle_questions_seed is not None:
        rng = random.Random(args.shuffle_questions_seed)
        rng.shuffle(prepared_questions)
        print(
            f"Shuffled question stream with seed {args.shuffle_questions_seed}.",
            flush=True,
        )
    for stream_index, item in enumerate(prepared_questions):
        item["stream_index"] = stream_index
    question_ids = [item["question_id"] for item in prepared_questions]

    # If all questions share the same haystack, build memory once and reuse it for all questions.
    shared_haystack = all_haystacks_shared(question_ids, haystack_mapping)
    shared_memory = None
    shared_haystack_ids: list[str] | None = None
    trajectories: dict[str, dict[str, Any]] | None = None
    memory_config: dict[str, Any] | None = memory_config_template
    prompt_build_cancel_event = threading.Event()
    supports_nonshared_parallel = (
        memory_config is not None
        and supports_nonshared_parallel_prompt_build(memory_config["memory_type"])
    )
    if shared_haystack:
        shared_haystack_ids = haystack_mapping[question_ids[0]]
        if args.load_memory_dir is not None:
            print("All questions share the same haystack, loading shared memory once for all questions.")
            shared_memory = load_memory(args.load_memory_dir, requested_config=memory_config_template)
            shared_memory.configure_runtime(
                query_trace_dir=output_dir / "query_traces",
                generation_temperature=args.temperature,
                generation_top_p=args.top_p,
                cancel_event=prompt_build_cancel_event,
            )
        else:
            print("All questions share the same haystack, building shared memory once for all questions.")
            require(memory_config is not None, "Missing memory config for shared memory construction")
            trajectories = load_trajectories(args.trajectories_path)
            shared_memory = build_memory(
                inject_runtime_memory_params(
                    memory_config,
                    workspace_dir=memory_workspace_root / "shared",
                    trajectories_path=args.trajectories_path,
                    reader_temperature=args.temperature,
                    reader_top_p=args.top_p,
                    query_trace_dir=output_dir / "query_traces",
                )
            )
            shared_memory.configure_runtime(
                query_trace_dir=output_dir / "query_traces",
                generation_temperature=args.temperature,
                generation_top_p=args.top_p,
                cancel_event=prompt_build_cancel_event,
            )
            for traj_id in tqdm(shared_haystack_ids, desc="Building memory", unit="traj"):
                require(traj_id in trajectories, f"Missing trajectory id in trajectories data: {traj_id}")
                shared_memory.insert(trajectories[traj_id])
            if args.save_memory:
                save_memory(shared_memory, memory_state_dir)
        if args.skip_evaluation:
            print(f"Saved shared memory to {memory_state_dir} and skipping evaluation.")
            return
    else:
        if args.prompt_build_max_workers > 1:
            require(
                supports_nonshared_parallel,
                (
                    "--prompt-build-max-workers > 1 with non-shared haystacks is only "
                    "supported for rag, agentrunbook_r, codex, agentrunbook_c, and agentrunbook_c_v2"
                ),
            )
        require(not args.save_memory, "--save-memory is only supported when all questions share the same ordered haystack")
        require(not args.skip_evaluation, "--skip-evaluation is only supported when all questions share the same ordered haystack")
        require(args.load_memory_dir is None, "--load-memory-dir is only supported when all questions share the same ordered haystack")
        print("Questions have different haystacks, building memory separately for each question.")
        trajectories = load_trajectories(args.trajectories_path)
        require(memory_config is not None, "Missing memory config for per-question memory construction")

    prompt_rows: list[dict[str, Any]] = []
    system_prompt = get_system_prompt(args.domain)

    # pass 1: build prompts for all questions
    with prompt_build_interrupt_context(prompt_build_cancel_event):
        if shared_memory is not None and args.prompt_build_max_workers > 1:
            print(
                "Building prompts in parallel across shared memory with "
                f"{args.prompt_build_max_workers} workers."
            )
            with ThreadPoolExecutor(max_workers=args.prompt_build_max_workers) as executor:
                try:
                    future_to_item = {
                        executor.submit(
                            build_prompt_row,
                            item,
                            haystack_ids=haystack_mapping[item["question_id"]],
                            memory=shared_memory,
                            system_prompt=system_prompt,
                            memory_context_max_tokens=args.memory_context_max_tokens,
                        ): item
                        for item in prepared_questions
                    }
                    for future in tqdm(as_completed(future_to_item), total=len(future_to_item), desc="Building prompts", unit="q"):
                        item = future_to_item[future]
                        try:
                            prompt_rows.append(future.result())
                        except KeyboardInterrupt:
                            prompt_build_cancel_event.set()
                            raise
                        except Exception as exc:
                            raise RuntimeError(
                                f"Prompt building failed for question {item['question_id']}"
                            ) from exc
                except KeyboardInterrupt:
                    prompt_build_cancel_event.set()
                    raise
            prompt_rows.sort(key=lambda row: row["stream_index"])
        elif (
            shared_memory is None
            and args.prompt_build_max_workers > 1
            and supports_nonshared_parallel
        ):
            require(memory_config is not None, "Missing memory config for per-question memory construction")
            require(trajectories is not None, "Missing trajectories for per-question memory construction")
            print(
                "Building prompts in parallel across non-shared per-question memory with "
                f"{args.prompt_build_max_workers} workers."
            )
            query_trace_dir = output_dir / "query_traces"
            with ThreadPoolExecutor(max_workers=args.prompt_build_max_workers) as executor:
                try:
                    future_to_item = {
                        executor.submit(
                            build_prompt_row_with_per_question_memory,
                            item,
                            haystack_ids=haystack_mapping[item["question_id"]],
                            memory_config=memory_config,
                            trajectories=trajectories,
                            trajectories_path=args.trajectories_path,
                            workspace_dir=memory_workspace_root / item["query_invocation_id"],
                            query_trace_dir=query_trace_dir,
                            system_prompt=system_prompt,
                            memory_context_max_tokens=args.memory_context_max_tokens,
                            reader_temperature=args.temperature,
                            reader_top_p=args.top_p,
                            cancel_event=prompt_build_cancel_event,
                        ): item
                        for item in prepared_questions
                    }
                    for future in tqdm(
                        as_completed(future_to_item),
                        total=len(future_to_item),
                        desc="Building prompts",
                        unit="q",
                    ):
                        item = future_to_item[future]
                        try:
                            prompt_rows.append(future.result())
                        except KeyboardInterrupt:
                            prompt_build_cancel_event.set()
                            raise
                        except Exception as exc:
                            raise RuntimeError(
                                f"Prompt building failed for question {item['question_id']}"
                            ) from exc
                except KeyboardInterrupt:
                    prompt_build_cancel_event.set()
                    raise
            prompt_rows.sort(key=lambda row: row["stream_index"])
        else:
            for item in tqdm(prepared_questions, desc="Building prompts", unit="q"):
                qid = item["question_id"]
                haystack_ids = haystack_mapping[qid]
                if shared_memory is None:
                    require(memory_config is not None, "Missing memory config for per-question memory construction")
                    require(trajectories is not None, "Missing trajectories for per-question memory construction")
                    prompt_rows.append(
                        build_prompt_row_with_per_question_memory(
                            item,
                            haystack_ids=haystack_ids,
                            memory_config=memory_config,
                            trajectories=trajectories,
                            trajectories_path=args.trajectories_path,
                            workspace_dir=memory_workspace_root / item["query_invocation_id"],
                            query_trace_dir=output_dir / "query_traces",
                            system_prompt=system_prompt,
                            memory_context_max_tokens=args.memory_context_max_tokens,
                            reader_temperature=args.temperature,
                            reader_top_p=args.top_p,
                            cancel_event=prompt_build_cancel_event,
                        )
                    )
                else:
                    memory = shared_memory

                if shared_memory is not None:
                    prompt_rows.append(
                        build_prompt_row(
                            item,
                            haystack_ids=haystack_ids,
                            memory=memory,
                            system_prompt=system_prompt,
                            memory_context_max_tokens=args.memory_context_max_tokens,
                        )
                    )

    # pass 2: get outputs for all prompts
    with (output_dir / "prompt_rows.jsonl").open("w", encoding="utf-8") as fp:
        for row in prompt_rows:
            fp.write(json.dumps(row, ensure_ascii=True) + "\n")
    save_json(
        output_dir / "prompt_build_summary.json",
        {
            "completed_at_utc": utc_now_iso(),
            "prompt_row_count": len(prompt_rows),
            "question_ids": [row["question_id"] for row in prompt_rows],
            "original_question_ids": original_question_ids,
            "shuffle_questions_seed": args.shuffle_questions_seed,
        },
    )

    outputs_by_question_id = asyncio.run(generate_all_reader_outputs(args, prompt_rows))

    per_question_path = output_dir / "per_question.jsonl"
    records: list[dict[str, Any]] = []
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_memory_context_tokens = 0
    total_memory_context_original_tokens = 0
    total_memory_query_duration_seconds = 0.0
    total_memory_post_query_duration_seconds = 0.0
    truncated_sequence_count = 0
    eval_config = make_eval_config(args)
    memory_query_durations: list[float] = []
    memory_post_query_durations: list[float] = []

    # pass 3: score outputs sequentially
    with per_question_path.open("w", encoding="utf-8") as fp:
        for row in tqdm(prompt_rows, desc="Scoring", unit="q"):
            qid = row["question_id"]
            output = outputs_by_question_id[qid]
            row = {
                **row,
                "response_raw": output["response_raw"],
                "response_parsed_boxed": output["response_parsed_boxed"],
                "is_unknown": output["is_unknown"],
                "usage": output["usage"],
            }
            score_bool, _, _ = score_prediction(row, eval_config)

            record = {
                "index": row["index"],
                "stream_index": row["stream_index"],
                "question_id": qid,
                "question_type": row["question_type"],
                "category": row["category"],
                "is_abstention_problem": row["is_abstention_problem"],
                "eval_function": row["eval_function"],
                "question_text": row["question_text"],
                "question_image": row["question_image"],
                "haystack_ids": row["haystack_ids"],
                "memory_context": row["memory_context"],
                "memory_query_duration_seconds": row["memory_query_duration_seconds"],
                "memory_post_query_duration_seconds": row["memory_post_query_duration_seconds"],
                "memory_post_query_metadata": row["memory_post_query_metadata"],
                "memory_context_original_token_count": row["memory_context_original_token_count"],
                "memory_context_token_count": row["memory_context_token_count"],
                "memory_context_was_truncated": row["memory_context_was_truncated"],
                "prompt_messages": row["prompt_messages"],
                "answer_gold": row["answer_gold"],
                "response_raw": row["response_raw"],
                "response_parsed_boxed": row["response_parsed_boxed"],
                "is_unknown": row["is_unknown"],
                "score": 1.0 if score_bool else 0.0,
                "score_bool": score_bool,
                "usage": row["usage"],
                "timestamp_utc": utc_now_iso(),
            }
            fp.write(json.dumps(record, ensure_ascii=True) + "\n")
            fp.flush()
            records.append(record)
            total_prompt_tokens += row["usage"]["prompt_tokens"]
            total_completion_tokens += row["usage"]["completion_tokens"]
            total_memory_context_tokens += row["memory_context_token_count"]
            total_memory_context_original_tokens += row["memory_context_original_token_count"]
            total_memory_query_duration_seconds += row["memory_query_duration_seconds"]
            total_memory_post_query_duration_seconds += row["memory_post_query_duration_seconds"]
            memory_query_durations.append(float(row["memory_query_duration_seconds"]))
            memory_post_query_durations.append(float(row["memory_post_query_duration_seconds"]))
            truncated_sequence_count += int(row["memory_context_was_truncated"])

    aggregated = aggregate_metrics(records)
    aggregated["tokens"] = {
        "prompt_tokens": total_prompt_tokens,
        "completion_tokens": total_completion_tokens,
        "total_tokens": total_prompt_tokens + total_completion_tokens,
        "avg_prompt_tokens": total_prompt_tokens / len(records) if records else None,
        "avg_completion_tokens": (
            total_completion_tokens / len(records) if records else None
        ),
        "avg_total_tokens": (
            (total_prompt_tokens + total_completion_tokens) / len(records)
            if records
            else None
        ),
    }
    aggregated["memory_context"] = {
        "avg_original_tokens": (
            total_memory_context_original_tokens / len(records) if records else None
        ),
        "avg_final_tokens": (
            total_memory_context_tokens / len(records) if records else None
        ),
        "num_truncated_sequences": truncated_sequence_count,
    }
    sorted_memory_query_durations = sorted(memory_query_durations)
    aggregated["memory_query"] = {
        "avg_seconds": (
            total_memory_query_duration_seconds / len(memory_query_durations)
            if memory_query_durations
            else None
        ),
        "p50_seconds": (
            sorted_memory_query_durations[len(sorted_memory_query_durations) // 2]
            if sorted_memory_query_durations
            else None
        ),
        "p95_seconds": (
            sorted_memory_query_durations[min(len(sorted_memory_query_durations) - 1, int(0.95 * len(sorted_memory_query_durations)))]
            if sorted_memory_query_durations
            else None
        ),
        "max_seconds": (
            sorted_memory_query_durations[-1] if sorted_memory_query_durations else None
        ),
        "total_seconds": total_memory_query_duration_seconds,
    }
    sorted_memory_post_query_durations = sorted(memory_post_query_durations)
    aggregated["memory_post_query"] = {
        "avg_seconds": (
            total_memory_post_query_duration_seconds / len(memory_post_query_durations)
            if memory_post_query_durations
            else None
        ),
        "p50_seconds": (
            sorted_memory_post_query_durations[len(sorted_memory_post_query_durations) // 2]
            if sorted_memory_post_query_durations
            else None
        ),
        "p95_seconds": (
            sorted_memory_post_query_durations[
                min(
                    len(sorted_memory_post_query_durations) - 1,
                    int(0.95 * len(sorted_memory_post_query_durations)),
                )
            ]
            if sorted_memory_post_query_durations
            else None
        ),
        "max_seconds": (
            sorted_memory_post_query_durations[-1]
            if sorted_memory_post_query_durations
            else None
        ),
        "total_seconds": total_memory_post_query_duration_seconds,
    }
    aggregated["completed_at_utc"] = utc_now_iso()
    aggregated["shared_haystack"] = shared_haystack
    if shared_haystack_ids is not None:
        aggregated["shared_haystack_ids"] = shared_haystack_ids
    save_json(output_dir / "aggregated_metrics.json", aggregated)


if __name__ == "__main__":
    main()
