"""End-to-end test for Agent Engine with MiniMax M2.7."""
import asyncio
import json
import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("e2e_test")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def r(result, key, default=None):
    """Get value from dict or object."""
    if isinstance(result, dict):
        return result.get(key, default)
    return getattr(result, key, default)


async def test_data_labeling():
    """Test data labeling task end-to-end."""
    from core.engine import AgentEngine
    logger.info("=" * 60)
    logger.info("TEST 1: Data Labeling (Text Classification)")
    logger.info("=" * 60)

    engine = AgentEngine(agent_id=1)
    task_data = {
        "task_id": 101,
        "task_type": "DATA_LABELING",
        "description": "Classify each news headline into: technology, sports, politics, entertainment",
        "input_data": json.dumps({
            "labeling_type": "text_classification",
            "labels": ["technology", "sports", "politics", "entertainment"],
            "items": [
                "Apple releases new iPhone with AI chip",
                "Lakers win NBA championship in overtime",
                "Senate passes new climate bill",
                "Marvel announces new Avengers movie",
                "Tesla unveils autonomous robot taxi",
            ]
        }),
    }

    result = await engine.execute_task(task_data)
    error = r(result, "error")
    output = r(result, "result")
    logger.info(f"Status: {'SUCCESS' if not error else 'FAILED'}")
    if output:
        parsed = json.loads(output)
        logger.info(f"Labeled {parsed.get('total_items', 0)} items")
        for item in parsed.get("results", []):
            logger.info(f"  [{item.get('id')}] {item.get('text', '')[:40]}... -> {item.get('label')} ({item.get('confidence', 0):.2f})")
    if error:
        logger.info(f"Error: {error}")
    return not error


async def test_code_generation():
    """Test code generation and execution."""
    from core.engine import AgentEngine
    logger.info("=" * 60)
    logger.info("TEST 2: Code Generation")
    logger.info("=" * 60)

    engine = AgentEngine(agent_id=2)
    task_data = {
        "task_id": 102,
        "task_type": "CODE",
        "description": "Write a Python function that finds prime numbers between 1 and 20, then print them.",
        "input_data": "Find and print all prime numbers between 1 and 20",
        "expected_output": "List of prime numbers between 1 and 20",
    }

    result = await engine.execute_task(task_data)
    error = r(result, "error")
    output = r(result, "result")
    logger.info(f"Status: {'SUCCESS' if not error else 'FAILED'}")
    if output:
        logger.info(f"Output: {output[:300]}")
    if error:
        logger.info(f"Error: {error}")
    return not error


async def test_generic_task():
    """Test generic task execution via LLM."""
    from core.engine import AgentEngine
    logger.info("=" * 60)
    logger.info("TEST 3: Generic Task (LLM Direct)")
    logger.info("=" * 60)

    engine = AgentEngine(agent_id=3)
    task_data = {
        "task_id": 103,
        "task_type": "ANALYSIS",
        "description": "List 3 pros and 3 cons of microservices vs monolith for a startup with 3 developers.",
        "input_data": "Context: Early-stage startup, 3 devs, e-commerce platform",
    }

    result = await engine.execute_task(task_data)
    error = r(result, "error")
    output = r(result, "result")
    logger.info(f"Status: {'SUCCESS' if not error else 'FAILED'}")
    if output:
        logger.info(f"Result preview: {output[:400]}...")
    if error:
        logger.info(f"Error: {error}")
    return not error


async def main():
    logger.info("Starting Agent Engine E2E Tests")
    results = {}
    for name, test_fn in [("data_labeling", test_data_labeling), ("code_generation", test_code_generation), ("generic_task", test_generic_task)]:
        try:
            results[name] = await test_fn()
        except Exception as e:
            logger.error(f"{name} test failed: {e}", exc_info=True)
            results[name] = False

    logger.info("=" * 60)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("=" * 60)
    passed = sum(1 for v in results.values() if v)
    for name, ok in results.items():
        logger.info(f"  {name}: {'PASS' if ok else 'FAIL'}")
    logger.info(f"\n  Total: {passed}/{len(results)} passed")
    return passed == len(results)

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
