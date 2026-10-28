"""Build a balanced bug-detection dataset from QuixBugs (external ground truth).

QuixBugs (https://github.com/jkoppel/QuixBugs) ships each classic algorithm in
two versions: a one-line-buggy variant (python_programs/) and the corrected
reference (correct_python_programs/). We emit each as a {buggy|clean} item so
single-vs-consensus accuracy can be measured against an external, published
ground truth (no self-authored labels).

Docstrings/comments are stripped from BOTH versions so the only signal that
distinguishes buggy from clean is the actual bug — not a docstring asymmetry.

Usage:
    python build_quixbugs_dataset.py <quixbugs_dir> <n_algorithms> <out.json>
"""
import json
import os
import re
import sys


def strip_docstrings(src: str) -> str:
    src = re.sub(r'""".*?"""', "", src, flags=re.DOTALL)
    src = re.sub(r"'''.*?'''", "", src, flags=re.DOTALL)
    lines = [ln for ln in src.splitlines() if not ln.strip().startswith("#")]
    return "\n".join(lines).strip()


def build(quixbugs_dir: str, n_algorithms: int, out_path: str) -> None:
    buggy_dir = os.path.join(quixbugs_dir, "python_programs")
    clean_dir = os.path.join(quixbugs_dir, "correct_python_programs")

    names = sorted(
        f[:-3] for f in os.listdir(buggy_dir)
        if f.endswith(".py") and not f.endswith("_test.py") and f != "node.py"
    )
    # Keep only algorithms that have a corrected counterpart.
    names = [n for n in names if os.path.exists(os.path.join(clean_dir, n + ".py"))]
    names = names[:n_algorithms]

    items = []
    item_id = 1
    for name in names:
        with open(os.path.join(buggy_dir, name + ".py"), encoding="utf-8") as f:
            buggy = strip_docstrings(f.read())
        with open(os.path.join(clean_dir, name + ".py"), encoding="utf-8") as f:
            clean = strip_docstrings(f.read())
        items.append({"id": item_id, "algorithm": name, "text": buggy, "ground_truth": "buggy"})
        item_id += 1
        items.append({"id": item_id, "algorithm": name, "text": clean, "ground_truth": "clean"})
        item_id += 1

    dataset = {
        "source": "QuixBugs (jkoppel/QuixBugs) python_programs vs correct_python_programs",
        "valid_labels": ["buggy", "clean"],
        "items": items,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(items)} items ({len(names)} algorithms) to {out_path}")


if __name__ == "__main__":
    build(sys.argv[1], int(sys.argv[2]), sys.argv[3])
