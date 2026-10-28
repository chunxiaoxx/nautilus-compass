"""
Metrics Evaluator - Measures prompt performance against eval datasets.

Like autoresearch's val_bpb metric: a single number that says
whether a change made things better or worse.
"""
import json
import time
import logging
from typing import Dict, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EvalResult:
    """Result of evaluating a prompt against a dataset."""
    accuracy: float          # 0.0 - 1.0
    avg_latency_s: float     # seconds per item
    total_cost_estimate: float  # rough USD estimate
    correct: int
    total: int
    errors: int
    details: List[Dict]      # per-item results

    @property
    def score(self) -> float:
        """Composite score (higher is better). Weights: accuracy 70%, speed 20%, cost 10%."""
        speed_score = max(0, 1.0 - self.avg_latency_s / 10.0)  # 10s = 0 score
        cost_score = max(0, 1.0 - self.total_cost_estimate / 1.0)  # $1 = 0 score
        return self.accuracy * 0.7 + speed_score * 0.2 + cost_score * 0.1


def evaluate_labeling_prompt(
    llm_client,
    system_prompt: str,
    task_prompt_template: str,
    eval_items: List[Dict],
    labeling_type: str = "sentiment",
    max_items: int = 0,
) -> EvalResult:
    """
    Evaluate a labeling prompt against ground-truth data.

    Args:
        llm_client: LLM client instance
        system_prompt: System prompt to test
        task_prompt_template: Task prompt template (must contain {items_text})
        eval_items: Items with ground truth labels
        labeling_type: Type of labeling task
        max_items: Limit items (0 = all)

    Returns:
        EvalResult with accuracy, latency, and per-item details
    """
    if max_items > 0:
        eval_items = eval_items[:max_items]

    # Format items for prompt
    items_text = "\n".join(
        f"[{item['id']}] {item['text']}" for item in eval_items
    )

    prompt = task_prompt_template.replace("{items_text}", items_text)

    start = time.time()
    try:
        response = llm_client.chat(
            prompt=prompt,
            system=system_prompt,
            temperature=0.1,
            max_tokens=4096,
        )
    except Exception as e:
        logger.error(f"LLM call failed during evaluation: {e}")
        return EvalResult(
            accuracy=0.0, avg_latency_s=0.0, total_cost_estimate=0.0,
            correct=0, total=len(eval_items), errors=len(eval_items), details=[]
        )

    elapsed = time.time() - start

    # Parse response
    try:
        results = _parse_labeling_response(response)
    except Exception as e:
        logger.error(f"Failed to parse eval response: {e}")
        return EvalResult(
            accuracy=0.0, avg_latency_s=elapsed / len(eval_items),
            total_cost_estimate=_estimate_cost(len(prompt) + len(response)),
            correct=0, total=len(eval_items), errors=len(eval_items), details=[]
        )

    # Compare with ground truth
    correct = 0
    details = []
    for item in eval_items:
        predicted = _find_prediction(results, item["id"])
        is_correct = _labels_match(predicted, item["label"])
        if is_correct:
            correct += 1
        details.append({
            "id": item["id"],
            "text": item["text"][:50],
            "expected": item["label"],
            "predicted": predicted,
            "correct": is_correct,
        })

    accuracy = correct / len(eval_items) if eval_items else 0.0
    avg_latency = elapsed / len(eval_items) if eval_items else 0.0
    cost_estimate = _estimate_cost(len(prompt) + len(response))

    return EvalResult(
        accuracy=accuracy,
        avg_latency_s=avg_latency,
        total_cost_estimate=cost_estimate,
        correct=correct,
        total=len(eval_items),
        errors=len(eval_items) - correct,
        details=details,
    )


def _parse_labeling_response(text: str) -> List[Dict]:
    """Parse JSON array from LLM response."""
    import re
    text = re.sub(r'ThinkingBlock\([^)]*(?:\([^)]*\)[^)]*)*\)', '', text, flags=re.DOTALL).strip()

    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, list) else parsed.get("results", [parsed])
    except json.JSONDecodeError:
        pass

    for start_char, end_char in [("[", "]"), ("{", "}")]:
        s = text.find(start_char)
        e = text.rfind(end_char) + 1
        if s >= 0 and e > s:
            try:
                parsed = json.loads(text[s:e])
                return parsed if isinstance(parsed, list) else [parsed]
            except json.JSONDecodeError:
                continue

    return []


def _find_prediction(results: List[Dict], item_id: int) -> str:
    """Find the predicted label for an item by ID."""
    for r in results:
        if r.get("id") == item_id:
            return r.get("label", "UNKNOWN")
    return "MISSING"


def _labels_match(predicted: str, expected: str) -> bool:
    """Fuzzy label matching."""
    if not predicted or predicted in ("UNKNOWN", "MISSING"):
        return False
    return predicted.lower().strip() == expected.lower().strip()


def _estimate_cost(total_chars: int) -> float:
    """Rough cost estimate based on character count."""
    # MiniMax M2.7: ~$0.001 per 1K tokens, ~4 chars per token
    tokens = total_chars / 4
    return tokens * 0.001 / 1000
