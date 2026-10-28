"""
Batch Processor - Core pipeline for batch data labeling.

Handles: upload → split → parallel label → consensus → report → export
"""
import json
import csv
import io
import time
import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class BatchStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class LabelingType(str, Enum):
    SENTIMENT = "sentiment"
    CLASSIFICATION = "text_classification"
    ENTITY = "entity_extraction"
    INTENT = "intent"
    SPAM = "spam_detection"
    TOXICITY = "toxicity"
    LANGUAGE = "language_detection"
    CUSTOM = "custom"


@dataclass
class BatchJob:
    """A batch labeling job."""
    job_id: str
    labeling_type: str
    labels: List[str]
    description: str
    total_items: int
    status: str = BatchStatus.PENDING
    created_at: str = ""
    completed_at: str = ""
    # Config
    num_agents: int = 3         # For consensus voting
    batch_size: int = 20        # Items per LLM call
    consensus_threshold: float = 0.66  # 2/3 agreement needed
    # Results
    results: List[Dict] = field(default_factory=list)
    quality_report: Dict = field(default_factory=dict)
    # Timing
    processing_time_s: float = 0.0

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()


class BatchProcessor:
    """
    Production batch labeling pipeline.

    Usage:
        processor = BatchProcessor()
        job = await processor.process_batch(
            items=[{"id": 1, "text": "..."}],
            labeling_type="sentiment",
            num_agents=3,
        )
        csv_output = processor.export_csv(job)
    """

    def __init__(self):
        self._llm = None

    @property
    def llm(self):
        if self._llm is None:
            from llm.client import get_llm_client
            self._llm = get_llm_client()
        return self._llm

    async def process_batch(
        self,
        items: List[Dict],
        labeling_type: str = "sentiment",
        labels: List[str] = None,
        description: str = "",
        num_agents: int = 3,
        batch_size: int = 20,
        consensus_threshold: float = 0.66,
        job_id: str = None,
    ) -> BatchJob:
        """
        Process a batch of items through the labeling pipeline.

        Args:
            items: List of {"id": ..., "text": "..."} dicts
            labeling_type: Type of labeling
            labels: Allowed labels (optional, LLM infers if empty)
            description: Task description for context
            num_agents: Number of parallel labeling passes for consensus
            batch_size: Items per LLM call
            consensus_threshold: Agreement ratio needed (0.5-1.0)
            job_id: Optional job ID

        Returns:
            BatchJob with results and quality report
        """
        job = BatchJob(
            job_id=job_id or f"batch_{int(time.time())}",
            labeling_type=labeling_type,
            labels=labels or [],
            description=description or f"Label items as {labeling_type}",
            total_items=len(items),
            num_agents=num_agents,
            batch_size=batch_size,
            consensus_threshold=consensus_threshold,
        )
        job.status = BatchStatus.PROCESSING
        start_time = time.time()

        logger.info(f"Starting batch job {job.job_id}: {len(items)} items, "
                     f"{num_agents} agents, type={labeling_type}")

        try:
            # Step 1: Split into batches
            batches = _split_batches(items, batch_size)
            logger.info(f"Split into {len(batches)} batches of up to {batch_size} items")

            # Step 2: Run N agents in parallel (Raid mode)
            all_agent_results = await self._raid_label(
                batches, num_agents, labeling_type, labels, description
            )

            # Step 3: Consensus voting
            consensus_results = _consensus_vote(
                all_agent_results, items, consensus_threshold
            )

            # Step 4: Generate quality report
            quality_report = _generate_quality_report(
                consensus_results, num_agents, labeling_type
            )

            job.results = consensus_results
            job.quality_report = quality_report
            job.status = BatchStatus.COMPLETED
            job.completed_at = datetime.utcnow().isoformat()
            job.processing_time_s = time.time() - start_time

            logger.info(f"Batch job {job.job_id} completed: "
                        f"{quality_report.get('consensus_rate', 0):.0%} consensus, "
                        f"{job.processing_time_s:.1f}s")

        except Exception as e:
            logger.error(f"Batch job {job.job_id} failed: {e}")
            job.status = BatchStatus.FAILED
            job.quality_report = {"error": str(e)}
            job.processing_time_s = time.time() - start_time

        return job

    async def _raid_label(
        self,
        batches: List[List[Dict]],
        num_agents: int,
        labeling_type: str,
        labels: List[str],
        description: str,
    ) -> List[List[Dict]]:
        """
        Raid mode: run multiple agents in parallel on the same data.

        Returns list of results per agent (num_agents lists).
        """
        async def run_single_agent(agent_idx: int) -> List[Dict]:
            """One agent labels all batches sequentially."""
            agent_results = []
            for batch_idx, batch in enumerate(batches):
                result = await self._label_batch(
                    batch, labeling_type, labels, description,
                    agent_idx=agent_idx, variation=agent_idx * 0.05,
                )
                agent_results.extend(result)
                logger.info(f"Agent {agent_idx}: batch {batch_idx+1}/{len(batches)} done")
            return agent_results

        # Run all agents concurrently
        tasks = [run_single_agent(i) for i in range(num_agents)]
        all_results = await asyncio.gather(*tasks)

        return list(all_results)

    async def _label_batch(
        self,
        items: List[Dict],
        labeling_type: str,
        labels: List[str],
        description: str,
        agent_idx: int = 0,
        variation: float = 0.0,
    ) -> List[Dict]:
        """Label a single batch using LLM."""
        items_text = "\n".join(f"[{it['id']}] {it['text']}" for it in items)

        labels_str = ", ".join(f'"{l}"' for l in labels) if labels else "appropriate labels"

        prompt = f"""Label each text item for {labeling_type}.
Task: {description}
Allowed labels: [{labels_str}]

Items:
{items_text}

Respond as a JSON array:
[{{"id": <id>, "label": "<label>", "confidence": <0.0-1.0>}}, ...]"""

        try:
            response = self.llm.chat(
                prompt=prompt,
                system="You are a precise data labeling AI. Respond ONLY with a JSON array. No explanations.",
                temperature=0.1 + variation,
                max_tokens=4096,
            )

            parsed = _parse_json_response(response)
            results = parsed if isinstance(parsed, list) else parsed.get("results", [parsed])

            # Ensure all items have IDs
            for i, r in enumerate(results):
                if "id" not in r and i < len(items):
                    r["id"] = items[i]["id"]

            return results

        except Exception as e:
            logger.error(f"Agent {agent_idx} batch labeling failed: {e}")
            return [{"id": it["id"], "label": "ERROR", "confidence": 0.0} for it in items]

    def export_csv(self, job: BatchJob) -> str:
        """Export results as CSV string."""
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(["id", "text", "label", "confidence", "consensus_votes", "agreement_rate"])

        for item in job.results:
            writer.writerow([
                item.get("id", ""),
                item.get("text", "")[:200],
                item.get("label", ""),
                f"{item.get('confidence', 0):.2f}",
                item.get("consensus_votes", ""),
                f"{item.get('agreement_rate', 0):.2f}",
            ])

        return output.getvalue()

    def export_jsonl(self, job: BatchJob) -> str:
        """Export results as JSONL string."""
        lines = []
        for item in job.results:
            lines.append(json.dumps(item, ensure_ascii=False))
        return "\n".join(lines)

    def export_json(self, job: BatchJob) -> str:
        """Export full job as JSON."""
        return json.dumps(asdict(job), indent=2, ensure_ascii=False)


def _split_batches(items: List[Dict], batch_size: int) -> List[List[Dict]]:
    """Split items into batches."""
    return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]


def _consensus_vote(
    all_agent_results: List[List[Dict]],
    original_items: List[Dict],
    threshold: float,
) -> List[Dict]:
    """
    Consensus voting: multiple agents label the same items,
    the majority label wins if agreement >= threshold.
    """
    num_agents = len(all_agent_results)
    item_lookup = {it["id"]: it for it in original_items}

    # Build vote map: item_id -> {label: count}
    vote_map: Dict[Any, Dict[str, int]] = {}
    confidence_map: Dict[Any, List[float]] = {}

    for agent_results in all_agent_results:
        for r in agent_results:
            item_id = r.get("id")
            label = r.get("label", "UNKNOWN")
            conf = r.get("confidence", 0.5)

            if item_id not in vote_map:
                vote_map[item_id] = {}
                confidence_map[item_id] = []

            vote_map[item_id][label] = vote_map[item_id].get(label, 0) + 1
            confidence_map[item_id].append(conf)

    # Determine consensus
    results = []
    for item_id, votes in vote_map.items():
        # Find winning label
        winner = max(votes, key=votes.get)
        winner_count = votes[winner]
        agreement = winner_count / num_agents

        original = item_lookup.get(item_id, {})
        avg_confidence = sum(confidence_map.get(item_id, [0])) / max(len(confidence_map.get(item_id, [1])), 1)

        results.append({
            "id": item_id,
            "text": original.get("text", ""),
            "label": winner,
            "confidence": round(avg_confidence, 3),
            "consensus_votes": f"{winner_count}/{num_agents}",
            "agreement_rate": round(agreement, 3),
            "consensus_met": agreement >= threshold,
            "all_votes": votes,
        })

    # Sort by ID
    results.sort(key=lambda x: x.get("id", 0))
    return results


def _generate_quality_report(
    results: List[Dict],
    num_agents: int,
    labeling_type: str,
) -> Dict:
    """Generate quality metrics report."""
    total = len(results)
    if total == 0:
        return {"error": "No results"}

    consensus_met = sum(1 for r in results if r.get("consensus_met", False))
    avg_confidence = sum(r.get("confidence", 0) for r in results) / total
    avg_agreement = sum(r.get("agreement_rate", 0) for r in results) / total

    # Label distribution
    label_dist = {}
    for r in results:
        label = r.get("label", "UNKNOWN")
        label_dist[label] = label_dist.get(label, 0) + 1

    # Low confidence items
    low_conf = [r for r in results if r.get("confidence", 1) < 0.5]
    disagreements = [r for r in results if not r.get("consensus_met", True)]

    return {
        "total_items": total,
        "num_agents": num_agents,
        "labeling_type": labeling_type,
        "consensus_rate": consensus_met / total,
        "avg_confidence": round(avg_confidence, 3),
        "avg_agreement": round(avg_agreement, 3),
        "label_distribution": label_dist,
        "low_confidence_count": len(low_conf),
        "disagreement_count": len(disagreements),
        "needs_human_review": len(low_conf) + len(disagreements),
    }


def _parse_json_response(text: str):
    """Parse JSON from LLM response."""
    import re
    text = re.sub(r'ThinkingBlock\([^)]*(?:\([^)]*\)[^)]*)*\)', '', text, flags=re.DOTALL).strip()

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

    for c, e in [("[", "]"), ("{", "}")]:
        s = text.find(c)
        ei = text.rfind(e) + 1
        if s >= 0 and ei > s:
            try:
                return json.loads(text[s:ei])
            except json.JSONDecodeError:
                continue

    raise ValueError(f"Could not parse JSON: {text[:200]}")
