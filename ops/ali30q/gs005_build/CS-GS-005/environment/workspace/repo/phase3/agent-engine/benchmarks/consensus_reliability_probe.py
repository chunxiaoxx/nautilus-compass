"""Consensus reliability probe.

Compares single-LLM baseline accuracy against RAID consensus accuracy on a
bug-detection classification dataset, to test whether multi-agent consensus
is more reliable than a single LLM (external benchmark ground truth as fitness).

Phase 1 binding-DONE = single accuracy vs consensus accuracy + delta.
"""
import json
import os
import re
import sys
from collections import Counter
from typing import Callable, Dict, List, Optional

# Allow `from llm.client import ...` when run as a script (sys.path[0] = benchmarks/).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def build_bug_detection_prompt(item: dict, valid_labels: List[str]) -> str:
    """Frame a bug-detection item as a prompt that ends with a parseable verdict.

    The trailing ``VERDICT: <label>`` line is what `parse_label` keys on, so
    both the single baseline and the RAID consensus path emit comparable output.
    """
    labels = " or ".join(valid_labels)
    return (
        "You are a code reviewer. Determine whether the function below contains "
        "a bug (incorrect behaviour on some input) or is correct.\n\n"
        f"```\n{item['text']}\n```\n\n"
        "Reason step by step about correctness, then on the FINAL line write "
        "your verdict exactly as one of:\n"
        f"VERDICT: {valid_labels[0]}\n"
        f"VERDICT: {valid_labels[-1]}\n"
        f"It must be exactly one of: {labels}."
    )


def build_judge_prompt(item: dict, samples: List[str], valid_labels: List[str]) -> str:
    """Judge-based consensus (RAID-3 style): a judge weighs N independent
    analyses of the same code and decides the final verdict. Unlike majority
    vote, the judge can recognise a thorough bug-finding analysis as more
    correct than several superficial 'clean' ones.
    """
    labels = " or ".join(valid_labels)
    blocks = "\n\n".join(
        f"--- Reviewer {i + 1} ---\n{s}" for i, s in enumerate(samples)
    )
    return (
        f"{len(samples)} reviewers independently judged whether the function "
        "below contains a bug. Weigh their analyses (a single reviewer who finds "
        "a concrete bug usually outweighs several who simply say it looks fine), "
        "then decide the correct final verdict.\n\n"
        f"```\n{item['text']}\n```\n\n"
        f"{blocks}\n\n"
        "On the FINAL line write exactly one of:\n"
        f"VERDICT: {valid_labels[0]}\n"
        f"VERDICT: {valid_labels[-1]}\n"
        f"It must be exactly one of: {labels}."
    )


def parse_label(text: str, valid_labels: List[str]) -> Optional[str]:
    """Extract a discrete label from free-form LLM / RAID output.

    Returns the matched label (as it appears in valid_labels) or None when the
    output is ambiguous or contains no valid label.
    """
    lowered = text.lower()
    for label in valid_labels:
        if re.search(r"verdict:\s*" + re.escape(label.lower()), lowered):
            return label
    # Fallback: exactly one valid label appears as a whole word.
    present = [
        label for label in valid_labels
        if re.search(r"\b" + re.escape(label.lower()) + r"\b", lowered)
    ]
    if len(present) == 1:
        return present[0]
    return None


def majority_vote_label(outputs: List[str], valid_labels: List[str]) -> Optional[str]:
    """Self-consistency consensus: parse each sample's label, return the strict
    majority among parseable votes. A tie (no single winner) or no parseable
    vote returns None (counts as incorrect downstream — no guessing)."""
    votes = [parse_label(o, valid_labels) for o in outputs]
    votes = [v for v in votes if v is not None]
    if not votes:
        return None
    counts = Counter(votes)
    top_label, top_n = counts.most_common(1)[0]
    if list(counts.values()).count(top_n) > 1:  # tie at the top
        return None
    return top_label


def run_probe(
    items: List[dict],
    single_labeler: Callable[[dict], str],
    consensus_labeler: Callable[[dict], str],
    valid_labels: List[str],
) -> Dict:
    """Score single-LLM vs consensus labelers over a ground-truth dataset.

    `single_labeler` / `consensus_labeler` each map an item to a raw output
    string; labels are extracted with `parse_label`. An unparseable output
    (None) counts as incorrect. Returns accuracies, counts, delta and the
    per-item breakdown (for the variance / honesty audit).
    """
    per_item = []
    single_correct = 0
    consensus_correct = 0

    for item in items:
        gt = str(item["ground_truth"]).lower().strip()
        single_pred = parse_label(single_labeler(item), valid_labels)
        consensus_pred = parse_label(consensus_labeler(item), valid_labels)
        single_ok = (single_pred or "").lower().strip() == gt
        consensus_ok = (consensus_pred or "").lower().strip() == gt
        single_correct += int(single_ok)
        consensus_correct += int(consensus_ok)
        per_item.append({
            "id": item.get("id"),
            "ground_truth": gt,
            "single_pred": single_pred,
            "single_ok": single_ok,
            "consensus_pred": consensus_pred,
            "consensus_ok": consensus_ok,
        })

    total = len(items)
    single_accuracy = single_correct / total if total else 0.0
    consensus_accuracy = consensus_correct / total if total else 0.0

    return {
        "total": total,
        "single_correct": single_correct,
        "consensus_correct": consensus_correct,
        "single_accuracy": single_accuracy,
        "consensus_accuracy": consensus_accuracy,
        "delta": consensus_accuracy - single_accuracy,
        "per_item": per_item,
    }


# --- Integration glue (real LLM; verified by the cloud run, not offline tests) ---

def load_dataset(path: str) -> tuple:
    """Load a bug-detection dataset. Returns (items, valid_labels).

    Schema: {"valid_labels": [...], "items": [{"id", "text", "ground_truth"}]}.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["items"], data["valid_labels"]


def make_single_labeler(llm, valid_labels: List[str], temperature: float = 0.0):
    """Single-LLM baseline: one greedy call per item."""
    def label(item: dict) -> str:
        return llm.chat(
            prompt=build_bug_detection_prompt(item, valid_labels),
            system="You are a meticulous code reviewer.",
            temperature=temperature,
            max_tokens=8000,
        )
    return label


def make_consensus_labeler(
    llm, valid_labels: List[str], n_samples: int = 3, temperature: float = 0.7,
):
    """Self-consistency consensus: n sampled calls per item, majority vote.

    Returns a synthetic 'VERDICT: <label>' string so the same parse/score path
    applies; a tie/no-majority yields a non-label string (scored incorrect).
    """
    def label(item: dict) -> str:
        prompt = build_bug_detection_prompt(item, valid_labels)
        samples = [
            llm.chat(prompt=prompt, system="You are a meticulous code reviewer.",
                     temperature=temperature, max_tokens=8000)
            for _ in range(n_samples)
        ]
        voted = majority_vote_label(samples, valid_labels)
        return f"VERDICT: {voted}" if voted else "VERDICT: no-consensus"
    return label


def make_judge_labeler(
    llm, valid_labels: List[str], n_samples: int = 3, sample_temp: float = 0.7,
):
    """Judge-based consensus (RAID-3 style): n sampled analyses, then a judge
    LLM adjudicates the final verdict. Output is the judge's raw text (parsed
    by the same parse_label path)."""
    def label(item: dict) -> str:
        prompt = build_bug_detection_prompt(item, valid_labels)
        samples = [
            llm.chat(prompt=prompt, system="You are a meticulous code reviewer.",
                     temperature=sample_temp, max_tokens=8000)
            for _ in range(n_samples)
        ]
        return llm.chat(
            prompt=build_judge_prompt(item, samples, valid_labels),
            system="You are a senior reviewer adjudicating a panel.",
            temperature=0.0,
            max_tokens=8000,
        )
    return label


def main(argv: Optional[List[str]] = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    dataset_path = argv[0] if argv else os.path.join(
        os.path.dirname(__file__), "bug_detection_dataset.json")
    n_samples = int(argv[1]) if len(argv) > 1 else 3
    max_workers = int(argv[2]) if len(argv) > 2 else 8
    mode = argv[3] if len(argv) > 3 else "vote"  # "vote" | "judge"

    items, valid_labels = load_dataset(dataset_path)
    print(f"Loaded {len(items)} items | labels={valid_labels} | mode={mode} | dataset={dataset_path}")

    from concurrent.futures import ThreadPoolExecutor
    from llm.client import get_llm_client
    llm = get_llm_client()

    single = make_single_labeler(llm, valid_labels, temperature=0.0)
    if mode == "judge":
        consensus = make_judge_labeler(llm, valid_labels, n_samples=n_samples)
    else:
        consensus = make_consensus_labeler(llm, valid_labels, n_samples=n_samples, temperature=0.7)

    # LLM calls are I/O-bound; run items concurrently, then score with the pure
    # (tested) aggregator. Pre-computing outputs keeps run_probe deterministic.
    print(f"Labeling {len(items)} items (single) with {max_workers} workers...")
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        single_outs = list(ex.map(single, items))
    print(f"Labeling {len(items)} items (consensus={mode} n={n_samples})...")
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        consensus_outs = list(ex.map(consensus, items))

    single_by_id = {it["id"]: o for it, o in zip(items, single_outs)}
    consensus_by_id = {it["id"]: o for it, o in zip(items, consensus_outs)}
    result = run_probe(
        items,
        lambda it: single_by_id[it["id"]],
        lambda it: consensus_by_id[it["id"]],
        valid_labels,
    )
    # Attach raw single-output tails + algorithm names for honest per-item audit.
    algo_by_id = {it["id"]: it.get("algorithm") for it in items}
    for row in result["per_item"]:
        row["algorithm"] = algo_by_id.get(row["id"])
        row["single_raw_tail"] = single_by_id[row["id"]][-120:]
        row["consensus_raw_tail"] = consensus_by_id[row["id"]][-120:]

    # Persist data FIRST so a console-encoding hiccup can't lose the result.
    out_path = os.path.join(os.path.dirname(__file__), f"consensus_probe_result_{mode}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print(f"  Single baseline   : {result['single_accuracy']:.1%} "
          f"({result['single_correct']}/{result['total']})")
    print(f"  Consensus (n={n_samples}) : {result['consensus_accuracy']:.1%} "
          f"({result['consensus_correct']}/{result['total']})")
    print(f"  DELTA             : {result['delta']:+.1%}")
    print("=" * 60)

    # Headroom verdict (Phase-0 lesson: a near-perfect single makes delta uninformative)
    if result["single_accuracy"] >= 0.85:
        print("  [WARN] NO HEADROOM: single baseline near-ceiling. Delta is not a "
              "fair test of consensus — swap in a harder dataset before concluding.")
    else:
        print("  [OK] Headroom present: delta is a meaningful single-vs-consensus signal.")
    print(f"\nPer-item breakdown written to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
