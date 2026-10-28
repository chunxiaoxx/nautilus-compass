"""
E2E Test: API Execute Endpoint → Agent Engine → Result

Tests the full pipeline:
1. Agent Engine receives task via API bridge
2. MiniMax M2.7 evaluates, plans, executes, verifies
3. Result returned to caller

Run: cd phase3/agent-engine && python test_api_execute.py
"""
import asyncio
import json
import time
import sys
import os

# Add parent dirs to path
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Load .env from agent-engine directory
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from core.engine import AgentEngine, AgentState


async def test_execute_via_engine():
    """Test direct engine execution (simulates what API endpoint calls)."""
    print("=" * 60)
    print("E2E Test: API Execute → Agent Engine")
    print("=" * 60)

    engine = AgentEngine(agent_id=1, max_concurrent_tasks=3)
    results = []

    # 10 diverse test tasks
    tasks = [
        {
            "task_id": 1,
            "task_type": "DATA_LABELING",
            "description": "Classify the sentiment of these product reviews",
            "input_data": json.dumps([
                {"id": 1, "text": "Amazing product, exceeded expectations!"},
                {"id": 2, "text": "Terrible quality, broke after one day"},
                {"id": 3, "text": "It's okay, nothing special"}
            ]),
            "expected_output": "JSON with sentiment labels"
        },
        {
            "task_id": 2,
            "task_type": "DATA_LABELING",
            "description": "Extract named entities (PERSON, ORG, LOCATION) from texts",
            "input_data": json.dumps([
                {"id": 1, "text": "Elon Musk announced Tesla will open a new factory in Shanghai"},
                {"id": 2, "text": "Google CEO Sundar Pichai visited MIT in Boston"}
            ]),
            "expected_output": "JSON with entity labels"
        },
        {
            "task_id": 3,
            "task_type": "DATA_LABELING",
            "description": "Classify the intent of customer support messages",
            "input_data": json.dumps([
                {"id": 1, "text": "I want to return my order #12345"},
                {"id": 2, "text": "What are your business hours?"},
                {"id": 3, "text": "My package hasn't arrived yet"}
            ]),
            "expected_output": "JSON with intent labels"
        },
        {
            "task_id": 4,
            "task_type": "DATA_LABELING",
            "description": "Classify news articles into categories: TECH, FINANCE, SPORTS, POLITICS",
            "input_data": json.dumps([
                {"id": 1, "text": "Apple unveils new M4 chip with revolutionary AI capabilities"},
                {"id": 2, "text": "Federal Reserve holds interest rates steady at 5.25%"},
                {"id": 3, "text": "Lakers defeat Celtics 112-108 in overtime thriller"}
            ]),
            "expected_output": "JSON with category labels"
        },
        {
            "task_id": 5,
            "task_type": "CODE",
            "description": "Write a Python function that finds the longest palindromic substring in a string",
            "input_data": "Test with: 'babad' should return 'bab' or 'aba'",
        },
        {
            "task_id": 6,
            "task_type": "DATA",
            "description": "Calculate basic statistics for this dataset",
            "input_data": json.dumps({"values": [23, 45, 67, 89, 12, 34, 56, 78, 90, 11]}),
            "expected_output": "JSON with mean, median, min, max, std"
        },
        {
            "task_id": 7,
            "task_type": "DATA_LABELING",
            "description": "Rate the toxicity level of these comments: LOW, MEDIUM, HIGH",
            "input_data": json.dumps([
                {"id": 1, "text": "Great article, very informative!"},
                {"id": 2, "text": "This is the worst thing I've ever read"},
                {"id": 3, "text": "You're an absolute idiot for writing this garbage"}
            ]),
        },
        {
            "task_id": 8,
            "task_type": "COMPUTE",
            "description": "Calculate the result of this expression",
            "input_data": "(2**10 + 3**5) * 7 - 100",
            "expected_output": "Numeric result"
        },
        {
            "task_id": 9,
            "task_type": "DATA_LABELING",
            "description": "Classify these emails as SPAM or HAM (not spam)",
            "input_data": json.dumps([
                {"id": 1, "text": "Congratulations! You've won $1,000,000! Click here now!"},
                {"id": 2, "text": "Hi team, the meeting is rescheduled to 3pm tomorrow"},
                {"id": 3, "text": "URGENT: Your account will be suspended unless you verify NOW"}
            ]),
        },
        {
            "task_id": 10,
            "task_type": "DATA_LABELING",
            "description": "Identify the language of these texts: EN, ZH, ES, FR, DE, JA",
            "input_data": json.dumps([
                {"id": 1, "text": "Hello, how are you today?"},
                {"id": 2, "text": "Je suis tres content de vous voir"},
                {"id": 3, "text": "Hola, como estas?"},
                {"id": 4, "text": "Dies ist ein Test"},
            ]),
        },
    ]

    total_start = time.time()
    passed = 0
    failed = 0

    for task_data in tasks:
        tid = task_data["task_id"]
        ttype = task_data["task_type"]
        print(f"\n--- Task {tid}: {ttype} ---")
        print(f"  Description: {task_data['description'][:60]}...")

        start = time.time()
        try:
            final_state = await engine.execute_task(task_data)
            elapsed = time.time() - start

            if final_state.error:
                print(f"  FAILED: {final_state.error}")
                failed += 1
                results.append({"task_id": tid, "status": "FAILED", "error": final_state.error})
            else:
                result_preview = (final_state.result or "")[:200]
                print(f"  PASSED ({elapsed:.1f}s)")
                print(f"  Result: {result_preview}...")
                passed += 1
                results.append({"task_id": tid, "status": "PASSED", "time": elapsed})

        except Exception as e:
            elapsed = time.time() - start
            print(f"  ERROR ({elapsed:.1f}s): {e}")
            failed += 1
            results.append({"task_id": tid, "status": "ERROR", "error": str(e)})

    total_elapsed = time.time() - total_start

    # Summary
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print(f"Total tasks: {len(tasks)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success rate: {passed/len(tasks)*100:.0f}%")
    print(f"Total time: {total_elapsed:.1f}s")
    print(f"Avg time per task: {total_elapsed/len(tasks):.1f}s")
    print()

    # Pass/fail criteria
    success_rate = passed / len(tasks)
    avg_time = total_elapsed / len(tasks)

    checks = []
    checks.append(("Success rate >= 80%", success_rate >= 0.8))
    checks.append(("Avg time < 30s per task", avg_time < 30))
    checks.append(("At least 8/10 tasks passed", passed >= 8))

    all_pass = True
    for check_name, check_result in checks:
        status_str = "PASS" if check_result else "FAIL"
        print(f"  [{status_str}] {check_name}")
        if not check_result:
            all_pass = False

    print()
    if all_pass:
        print("E2E TEST: ALL CHECKS PASSED")
    else:
        print("E2E TEST: SOME CHECKS FAILED")

    return all_pass


if __name__ == "__main__":
    success = asyncio.run(test_execute_via_engine())
    sys.exit(0 if success else 1)
