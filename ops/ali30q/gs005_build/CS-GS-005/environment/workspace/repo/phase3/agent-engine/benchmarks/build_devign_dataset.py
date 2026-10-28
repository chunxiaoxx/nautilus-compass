"""Build a balanced bug/vulnerability-detection dataset from Devign (CodeXGLUE).

Devign (google/code_x_glue_cc_defect_detection) is a real-world C function-level
defect-detection benchmark with external, published labels (target 1 = defective,
0 = clean). Single LLMs are documented at ~55-65% accuracy here, so it should
have the headroom QuixBugs lacked. We keep only short functions to bound the
thinking-model latency/cost, balance the two classes, and emit our schema.

Usage:
    python build_devign_dataset.py <n_per_class> <max_chars> <out.json>
"""
import json
import sys


def build(n_per_class: int, max_chars: int, out_path: str) -> None:
    from datasets import load_dataset

    ds = load_dataset(
        "google/code_x_glue_cc_defect_detection", split="train", streaming=True,
    )

    buggy, clean = [], []
    for ex in ds:
        func = ex["func"]
        if not func or len(func) > max_chars or func.count("\n") > 45:
            continue
        target = int(ex["target"])
        bucket = buggy if target == 1 else clean
        if len(bucket) < n_per_class:
            bucket.append(func)
        if len(buggy) >= n_per_class and len(clean) >= n_per_class:
            break

    items = []
    item_id = 1
    for func in buggy:
        items.append({"id": item_id, "algorithm": "devign", "text": func, "ground_truth": "buggy"})
        item_id += 1
    for func in clean:
        items.append({"id": item_id, "algorithm": "devign", "text": func, "ground_truth": "clean"})
        item_id += 1

    dataset = {
        "source": "Devign / CodeXGLUE (google/code_x_glue_cc_defect_detection), short funcs only",
        "valid_labels": ["buggy", "clean"],
        "items": items,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(items)} items ({len(buggy)} buggy + {len(clean)} clean) to {out_path}")


if __name__ == "__main__":
    build(int(sys.argv[1]), int(sys.argv[2]), sys.argv[3])
