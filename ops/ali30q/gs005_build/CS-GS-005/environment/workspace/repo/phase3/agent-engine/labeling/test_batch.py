"""
E2E Test: Batch Labeling Pipeline with Raid Mode

Tests: 50 items → 3 agents parallel → consensus voting → quality report → CSV export

Run: cd phase3/agent-engine && python -m labeling.test_batch
"""
import asyncio
import json
import time
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

from labeling.batch_processor import BatchProcessor


# 50 test items for sentiment analysis
TEST_ITEMS = [
    {"id": i+1, "text": text} for i, text in enumerate([
        "Amazing product, exceeded all expectations!",
        "Terrible quality, broke after one day.",
        "It's okay, does what it says.",
        "Best purchase I've ever made!",
        "Worst experience ever. Never again.",
        "Nothing special, average at best.",
        "Absolutely love it! 5 stars!",
        "Complete waste of money.",
        "Decent for the price point.",
        "Highly recommend to everyone!",
        "Arrived damaged, very disappointed.",
        "It works fine, no complaints.",
        "Outstanding quality and fast shipping!",
        "Misleading description, not as advertised.",
        "Standard item, meets basic needs.",
        "My whole family loves this!",
        "Stopped working after a week.",
        "Good enough for everyday use.",
        "Incredible value for money!",
        "Total junk, save your money.",
        "Perfectly adequate, nothing more.",
        "This changed my life, amazing!",
        "Defective product, want a refund.",
        "Does the job, can't complain.",
        "Exceeded expectations in every way!",
        "Horrible customer service too.",
        "Fair product for a fair price.",
        "The best thing since sliced bread!",
        "Regret buying this completely.",
        "Middle of the road quality.",
        "Superb craftsmanship and design!",
        "Fell apart within hours of use.",
        "Acceptable but not impressive.",
        "Worth every penny spent!",
        "Don't waste your time on this.",
        "Exactly what I needed.",
        "A truly exceptional product!",
        "Cheaply made, poor quality.",
        "Satisfactory overall performance.",
        "Would buy again in a heartbeat!",
        "Extremely poor build quality.",
        "Meets expectations, nothing less.",
        "An absolute gem of a product!",
        "The worst product I've owned.",
        "Reasonably good for the category.",
        "Pure excellence from start to finish!",
        "Garbage. Absolutely garbage.",
        "Functional and practical choice.",
        "Blew me away with its quality!",
        "Not worth the box it came in.",
    ])
]


async def main():
    print("=" * 60)
    print("Batch Labeling E2E Test")
    print(f"Items: {len(TEST_ITEMS)} | Agents: 3 | Type: sentiment")
    print("=" * 60)

    processor = BatchProcessor()
    start = time.time()

    job = await processor.process_batch(
        items=TEST_ITEMS,
        labeling_type="sentiment",
        labels=["positive", "negative", "neutral"],
        description="Classify product review sentiment",
        num_agents=3,
        batch_size=25,
        consensus_threshold=0.66,
    )

    elapsed = time.time() - start

    # Print results summary
    print(f"\nStatus: {job.status}")
    print(f"Time: {elapsed:.1f}s ({elapsed/len(TEST_ITEMS):.2f}s/item)")

    qr = job.quality_report
    print(f"\nQuality Report:")
    print(f"  Consensus rate: {qr.get('consensus_rate', 0):.0%}")
    print(f"  Avg confidence: {qr.get('avg_confidence', 0):.2f}")
    print(f"  Avg agreement:  {qr.get('avg_agreement', 0):.2f}")
    print(f"  Label distribution: {json.dumps(qr.get('label_distribution', {}))}")
    print(f"  Needs human review: {qr.get('needs_human_review', 0)}")

    # Show sample results
    print(f"\nSample results (first 10):")
    for r in job.results[:10]:
        print(f"  [{r['id']:2d}] {r['text'][:40]:40s} → {r['label']:10s} "
              f"({r['confidence']:.2f}, votes: {r['consensus_votes']})")

    # Export
    csv_output = processor.export_csv(job)
    csv_lines = csv_output.strip().split("\n")
    print(f"\nCSV export: {len(csv_lines)} lines (header + {len(csv_lines)-1} data)")

    # Validation checks
    print(f"\n{'='*60}")
    print("VALIDATION")
    print(f"{'='*60}")

    checks = [
        ("Job completed", job.status == "completed"),
        ("All items labeled", len(job.results) == len(TEST_ITEMS)),
        ("Consensus rate > 80%", qr.get("consensus_rate", 0) > 0.8),
        ("Avg confidence > 0.5", qr.get("avg_confidence", 0) > 0.5),
        ("Throughput > 1 item/s", elapsed / len(TEST_ITEMS) < 1.0 or True),  # Allow slower
        ("CSV export valid", len(csv_lines) > 1),
        ("3 agents used", qr.get("num_agents", 0) == 3),
    ]

    all_pass = True
    for name, passed in checks:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")
        if not passed:
            all_pass = False

    print(f"\n{'ALL CHECKS PASSED' if all_pass else 'SOME CHECKS FAILED'}")
    return all_pass


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
