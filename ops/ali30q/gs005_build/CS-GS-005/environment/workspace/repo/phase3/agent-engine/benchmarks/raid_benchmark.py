"""
Raid Mode Benchmark - Tests multi-agent parallel labeling with accuracy & throughput metrics.

Usage:
    MINIMAX_API_KEY=your_key python benchmarks/raid_benchmark.py
"""
import asyncio
import json
import os
import sys
import time
import logging
from typing import Dict, List, Any
from dataclasses import dataclass, field

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("raid_benchmark")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@dataclass
class BenchmarkResult:
    task_name: str
    total_items: int
    correct: int
    accuracy: float
    duration_seconds: float
    items_per_minute: float
    mode: str  # "single" or "raid"
    agent_count: int = 1
    errors: List[str] = field(default_factory=list)


def load_dataset() -> dict:
    dataset_path = os.path.join(os.path.dirname(__file__), "labeling_dataset.json")
    with open(dataset_path, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate_classification(results: list, ground_truth: list) -> tuple:
    """Compare labels against ground truth. Returns (correct_count, errors)."""
    correct = 0
    errors = []
    gt_map = {item["id"]: item["ground_truth"] for item in ground_truth}

    for result in results:
        rid = result.get("id")
        predicted = result.get("label", "").lower().strip()
        expected = str(gt_map.get(rid, "")).lower().strip()

        if predicted == expected:
            correct += 1
        else:
            errors.append(f"Item {rid}: expected '{expected}', got '{predicted}'")

    return correct, errors


def evaluate_entity_extraction(results: list, ground_truth: list) -> tuple:
    """Evaluate entity extraction by checking if key entities are found."""
    correct = 0
    errors = []
    gt_map = {item["id"]: item["ground_truth"] for item in ground_truth}

    for result in results:
        rid = result.get("id")
        expected = gt_map.get(rid, {})
        entities = result.get("entities", [])

        # Check if key entities are present
        found_entities = {e.get("text", "") for e in entities}
        expected_entities = set()
        for entity_list in expected.values():
            expected_entities.update(entity_list)

        if not expected_entities:
            correct += 1
            continue

        overlap = len(found_entities & expected_entities) / len(expected_entities)
        if overlap >= 0.5:  # At least 50% of entities found
            correct += 1
        else:
            errors.append(f"Item {rid}: expected {expected_entities}, found {found_entities}")

    return correct, errors


async def run_single_agent(task: dict) -> BenchmarkResult:
    """Run a labeling task with a single agent."""
    from core.engine import AgentEngine

    engine = AgentEngine(agent_id=1)
    items = task["items"]

    input_data = {
        "labeling_type": task["type"],
        "items": [{"id": item["id"], "text": item["text"]} for item in items],
    }
    if "labels" in task:
        input_data["labels"] = task["labels"]

    task_data = {
        "task_id": task["id"] * 1000,
        "task_type": "DATA_LABELING",
        "description": task["description"],
        "input_data": json.dumps(input_data, ensure_ascii=False),
    }

    start = time.time()
    result = await engine.execute_task(task_data)
    duration = time.time() - start

    output = result.get("result") if isinstance(result, dict) else getattr(result, "result", None)
    error = result.get("error") if isinstance(result, dict) else getattr(result, "error", None)

    if error or not output:
        return BenchmarkResult(
            task_name=f"Task {task['id']}: {task['type']}",
            total_items=len(items), correct=0, accuracy=0.0,
            duration_seconds=duration, items_per_minute=0.0,
            mode="single", errors=[str(error or "No output")]
        )

    parsed = json.loads(output)
    results_list = parsed.get("results", [])

    if task["type"] == "entity_extraction":
        correct, errors = evaluate_entity_extraction(results_list, items)
    else:
        correct, errors = evaluate_classification(results_list, items)

    accuracy = correct / len(items) if items else 0
    items_per_min = (len(items) / duration) * 60 if duration > 0 else 0

    return BenchmarkResult(
        task_name=f"Task {task['id']}: {task['type']}",
        total_items=len(items), correct=correct, accuracy=accuracy,
        duration_seconds=duration, items_per_minute=items_per_min,
        mode="single", errors=errors
    )


async def run_raid_mode(task: dict, num_agents: int = 3) -> BenchmarkResult:
    """Run a labeling task with multiple agents in parallel (Raid mode)."""
    from core.engine import AgentEngine

    items = task["items"]

    # Split items across agents
    chunk_size = max(1, len(items) // num_agents)
    chunks = []
    for i in range(0, len(items), chunk_size):
        chunks.append(items[i:i + chunk_size])

    # Ensure we don't have more chunks than agents
    while len(chunks) > num_agents:
        chunks[-2].extend(chunks[-1])
        chunks.pop()

    async def agent_work(agent_id: int, agent_items: list) -> dict:
        engine = AgentEngine(agent_id=agent_id)
        input_data = {
            "labeling_type": task["type"],
            "items": [{"id": item["id"], "text": item["text"]} for item in agent_items],
        }
        if "labels" in task:
            input_data["labels"] = task["labels"]

        task_data = {
            "task_id": task["id"] * 1000 + agent_id,
            "task_type": "DATA_LABELING",
            "description": task["description"],
            "input_data": json.dumps(input_data, ensure_ascii=False),
        }

        result = await engine.execute_task(task_data)
        output = result.get("result") if isinstance(result, dict) else getattr(result, "result", None)
        if output:
            return json.loads(output)
        return {"results": []}

    start = time.time()
    agent_results = await asyncio.gather(*[
        agent_work(i + 10, chunk) for i, chunk in enumerate(chunks)
    ])
    duration = time.time() - start

    # Merge results from all agents
    all_results = []
    for ar in agent_results:
        all_results.extend(ar.get("results", []))

    if task["type"] == "entity_extraction":
        correct, errors = evaluate_entity_extraction(all_results, items)
    else:
        correct, errors = evaluate_classification(all_results, items)

    accuracy = correct / len(items) if items else 0
    items_per_min = (len(items) / duration) * 60 if duration > 0 else 0

    return BenchmarkResult(
        task_name=f"Task {task['id']}: {task['type']}",
        total_items=len(items), correct=correct, accuracy=accuracy,
        duration_seconds=duration, items_per_minute=items_per_min,
        mode="raid", agent_count=num_agents, errors=errors
    )


async def main():
    dataset = load_dataset()
    tasks = dataset["tasks"]

    logger.info(f"Loaded {len(tasks)} benchmark tasks with {sum(len(t['items']) for t in tasks)} total items")

    single_results = []
    raid_results = []

    # Run single agent benchmarks
    logger.info("\n" + "=" * 70)
    logger.info("SINGLE AGENT MODE")
    logger.info("=" * 70)

    for task in tasks:
        logger.info(f"\nRunning: {task['type']} ({len(task['items'])} items)...")
        result = await run_single_agent(task)
        single_results.append(result)
        logger.info(f"  Accuracy: {result.accuracy:.1%} ({result.correct}/{result.total_items})")
        logger.info(f"  Duration: {result.duration_seconds:.1f}s | Speed: {result.items_per_minute:.1f} items/min")
        if result.errors:
            for e in result.errors[:3]:
                logger.info(f"  Error: {e}")

    # Run raid mode benchmarks (3 agents)
    logger.info("\n" + "=" * 70)
    logger.info("RAID MODE (3 AGENTS)")
    logger.info("=" * 70)

    for task in tasks:
        if len(task["items"]) < 3:
            continue
        logger.info(f"\nRunning: {task['type']} ({len(task['items'])} items, 3 agents)...")
        result = await run_raid_mode(task, num_agents=3)
        raid_results.append(result)
        logger.info(f"  Accuracy: {result.accuracy:.1%} ({result.correct}/{result.total_items})")
        logger.info(f"  Duration: {result.duration_seconds:.1f}s | Speed: {result.items_per_minute:.1f} items/min")

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("BENCHMARK SUMMARY")
    logger.info("=" * 70)

    total_single_correct = sum(r.correct for r in single_results)
    total_single_items = sum(r.total_items for r in single_results)
    total_single_time = sum(r.duration_seconds for r in single_results)
    avg_single_accuracy = total_single_correct / total_single_items if total_single_items else 0

    logger.info(f"\nSingle Agent:")
    logger.info(f"  Overall Accuracy: {avg_single_accuracy:.1%} ({total_single_correct}/{total_single_items})")
    logger.info(f"  Total Time: {total_single_time:.1f}s")
    logger.info(f"  Throughput: {(total_single_items / total_single_time * 60):.1f} items/min")

    if raid_results:
        total_raid_correct = sum(r.correct for r in raid_results)
        total_raid_items = sum(r.total_items for r in raid_results)
        total_raid_time = sum(r.duration_seconds for r in raid_results)
        avg_raid_accuracy = total_raid_correct / total_raid_items if total_raid_items else 0

        logger.info(f"\nRaid Mode (3 agents):")
        logger.info(f"  Overall Accuracy: {avg_raid_accuracy:.1%} ({total_raid_correct}/{total_raid_items})")
        logger.info(f"  Total Time: {total_raid_time:.1f}s")
        logger.info(f"  Throughput: {(total_raid_items / total_raid_time * 60):.1f} items/min")

        speedup = total_single_time / total_raid_time if total_raid_time > 0 else 0
        logger.info(f"\n  Speedup: {speedup:.1f}x faster with Raid mode")

    # Cost estimate
    est_cost_per_1000 = 0.5  # rough estimate based on MiniMax pricing
    human_cost_per_1000 = 25.0  # average human labeling cost

    logger.info(f"\nCost Analysis (estimated):")
    logger.info(f"  AI Agent: ~${est_cost_per_1000:.2f} per 1000 labels")
    logger.info(f"  Human:    ~${human_cost_per_1000:.2f} per 1000 labels")
    logger.info(f"  Savings:  {(1 - est_cost_per_1000/human_cost_per_1000):.0%}")

    # Human throughput comparison
    human_items_per_min = 3.0  # average human labeling speed
    ai_throughput = total_single_items / total_single_time * 60 if total_single_time > 0 else 0
    logger.info(f"\nSpeed Comparison:")
    logger.info(f"  AI Agent: {ai_throughput:.1f} items/min")
    logger.info(f"  Human:    ~{human_items_per_min:.1f} items/min")
    logger.info(f"  AI is {ai_throughput/human_items_per_min:.0f}x faster")

    return avg_single_accuracy >= 0.8


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
