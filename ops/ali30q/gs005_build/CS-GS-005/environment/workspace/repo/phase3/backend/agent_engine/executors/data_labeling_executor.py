"""
Data Labeling Executor - Executes data labeling tasks using LLM.

Supports:
- Text classification
- Sentiment analysis
- Entity extraction
- Intent recognition
"""
import json
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class DataLabelingExecutor:
    """
    Execute data labeling tasks using MiniMax M2.7.

    Designed for the Nautilus data labeling vertical market.
    """

    def __init__(self):
        self._llm = None
        logger.info("DataLabelingExecutor initialized")

    @property
    def llm(self):
        if self._llm is None:
            from llm.client import get_llm_client
            self._llm = get_llm_client()
        return self._llm

    async def execute(self, state) -> str:
        """
        Execute data labeling task.

        Expects state.input_data as JSON with structure:
        {
            "labeling_type": "text_classification" | "sentiment" | "entity_extraction" | "intent",
            "labels": ["label1", "label2", ...],  // for classification/sentiment
            "items": ["text1", "text2", ...] | [{"id": 1, "text": "..."}, ...]
        }

        Returns JSON with labeled results.
        """
        logger.info(f"Executing data labeling task {state.task_id}")

        try:
            config = json.loads(state.input_data)
        except (json.JSONDecodeError, TypeError) as e:
            raise ValueError(f"Invalid input data: {e}. Expected JSON with labeling_type, labels, items.")

        # Support both formats:
        # 1. {"labeling_type": ..., "labels": [...], "items": [...]}
        # 2. [{"id": 1, "text": "..."}, ...] (raw items array)
        if isinstance(config, list):
            # Raw items array - infer type from task description
            items = config
            labeling_type = _infer_labeling_type(state.description)
            labels = _infer_labels(state.description, labeling_type)
        else:
            labeling_type = config.get("labeling_type", "text_classification")
            labels = config.get("labels", [])
            items = config.get("items", [])

        if not items:
            raise ValueError("No items provided for labeling")

        # Normalize items to list of dicts
        normalized = _normalize_items(items)

        # Process in batches for efficiency
        batch_size = 20
        all_results = []

        for i in range(0, len(normalized), batch_size):
            batch = normalized[i:i + batch_size]
            batch_results = await self._label_batch(
                batch, labeling_type, labels, state.description
            )
            all_results.extend(batch_results)
            logger.info(f"Labeled batch {i // batch_size + 1}: {len(batch_results)} items")

        result = {
            "labeling_type": labeling_type,
            "total_items": len(all_results),
            "labels_used": labels,
            "results": all_results,
        }

        return json.dumps(result, indent=2, ensure_ascii=False)

    async def _label_batch(
        self,
        items: List[Dict],
        labeling_type: str,
        labels: List[str],
        task_description: str,
    ) -> List[Dict]:
        """Label a batch of items using LLM."""

        items_text = "\n".join(
            f"[{item['id']}] {item['text']}" for item in items
        )

        if labeling_type == "text_classification":
            prompt = self._build_classification_prompt(items_text, labels, task_description)
        elif labeling_type == "sentiment":
            prompt = self._build_sentiment_prompt(items_text, task_description)
        elif labeling_type == "entity_extraction":
            prompt = self._build_entity_prompt(items_text, task_description)
        elif labeling_type == "intent":
            prompt = self._build_intent_prompt(items_text, labels, task_description)
        else:
            prompt = self._build_classification_prompt(items_text, labels, task_description)

        response = self.llm.chat(
            prompt=prompt,
            system="You are a precise data labeling AI. Label each item accurately. Always respond in valid JSON.",
            temperature=0.1,
            max_tokens=4096,
        )

        try:
            parsed = _extract_json_from_response(response)
            results = parsed if isinstance(parsed, list) else parsed.get("results", [])

            # Ensure each result has the required fields
            for i, result in enumerate(results):
                if "id" not in result and i < len(items):
                    result["id"] = items[i]["id"]

            return results

        except Exception as e:
            logger.error(f"Failed to parse labeling response: {e}")
            # Return items with "error" label
            return [
                {"id": item["id"], "text": item["text"], "label": "ERROR", "confidence": 0.0}
                for item in items
            ]

    def _build_classification_prompt(self, items_text: str, labels: list, description: str) -> str:
        labels_str = ", ".join(f'"{l}"' for l in labels)
        return f"""Classify each text item into one of these categories: [{labels_str}]

Task context: {description}

Items to classify:
{items_text}

Respond as a JSON array:
[{{"id": <id>, "text": "<original text>", "label": "<chosen label>", "confidence": <0.0-1.0>}}, ...]"""

    def _build_sentiment_prompt(self, items_text: str, description: str) -> str:
        return f"""Analyze the sentiment of each text item.

Task context: {description}

Items to analyze:
{items_text}

Respond as a JSON array:
[{{"id": <id>, "text": "<original text>", "label": "positive"|"negative"|"neutral", "confidence": <0.0-1.0>, "score": <-1.0 to 1.0>}}, ...]"""

    def _build_entity_prompt(self, items_text: str, description: str) -> str:
        return f"""Extract named entities from each text item.

Task context: {description}

Items to process:
{items_text}

Respond as a JSON array:
[{{"id": <id>, "text": "<original text>", "entities": [{{"text": "<entity>", "type": "<PERSON|ORG|LOC|DATE|MONEY|OTHER>", "start": <char_offset>, "end": <char_offset>}}]}}, ...]"""

    def _build_intent_prompt(self, items_text: str, labels: list, description: str) -> str:
        labels_str = ", ".join(f'"{l}"' for l in labels)
        return f"""Classify the intent of each text item into one of: [{labels_str}]

Task context: {description}

Items to classify:
{items_text}

Respond as a JSON array:
[{{"id": <id>, "text": "<original text>", "label": "<intent>", "confidence": <0.0-1.0>}}, ...]"""


def _normalize_items(items: list) -> List[Dict]:
    """Normalize items to list of dicts with id and text."""
    normalized = []
    for i, item in enumerate(items):
        if isinstance(item, str):
            normalized.append({"id": i + 1, "text": item})
        elif isinstance(item, dict):
            normalized.append({
                "id": item.get("id", i + 1),
                "text": item.get("text", str(item)),
            })
        else:
            normalized.append({"id": i + 1, "text": str(item)})
    return normalized


def _infer_labeling_type(description: str) -> str:
    """Infer labeling type from task description."""
    desc_lower = description.lower()
    if any(w in desc_lower for w in ["sentiment", "positive", "negative"]):
        return "sentiment"
    if any(w in desc_lower for w in ["entity", "ner", "named entity", "extract"]):
        return "entity_extraction"
    if any(w in desc_lower for w in ["intent", "purpose", "goal"]):
        return "intent"
    return "text_classification"


def _infer_labels(description: str, labeling_type: str) -> list:
    """Infer labels from task description."""
    # Labels will be determined by LLM from context; return empty to let LLM decide
    return []


def _extract_json_from_response(text: str):
    """Extract JSON array or object from LLM response."""
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    if "```json" in text:
        start = text.index("```json") + 7
        end = text.index("```", start)
        return json.loads(text[start:end].strip())

    if "```" in text:
        start = text.index("```") + 3
        end = text.index("```", start)
        return json.loads(text[start:end].strip())

    # Find array or object
    for char, end_char in [("[", "]"), ("{", "}")]:
        start_idx = text.find(char)
        end_idx = text.rfind(end_char) + 1
        if start_idx >= 0 and end_idx > start_idx:
            try:
                return json.loads(text[start_idx:end_idx])
            except json.JSONDecodeError:
                continue

    raise ValueError(f"Could not extract JSON from response: {text[:200]}")
