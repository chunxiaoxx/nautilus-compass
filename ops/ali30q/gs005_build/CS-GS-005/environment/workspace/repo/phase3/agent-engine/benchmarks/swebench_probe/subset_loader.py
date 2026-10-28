"""Load the locked SWE-bench-Lite core subset (N=110, gold patch >=2 hunks).

The subset ids live in ``benchmarks/swebench_lite_core_subset.json`` (committed
8c563554d). This joins those ids with the HF dataset rows to surface the fields
the solver and the official ``swebench`` harness need. The dataset is injectable
so unit tests run with no network/Docker.
"""
import json
import os
from typing import Dict, List, Optional, Sequence, Union

_HERE = os.path.dirname(os.path.abspath(__file__))
_SUBSET_JSON = os.path.join(os.path.dirname(_HERE), "swebench_lite_core_subset.json")

SubsetItem = Union[str, Dict]


def _instance_id(item: SubsetItem) -> str:
    return item if isinstance(item, str) else item["instance_id"]


def load_subset_ids(path: str = _SUBSET_JSON) -> List[str]:
    """Read the locked subset ids from the artifact JSON, preserving order."""
    with open(path, encoding="utf-8") as fh:
        return [row["instance_id"] for row in json.load(fh)]


def _default_dataset():
    from datasets import load_dataset
    return load_dataset("princeton-nlp/SWE-bench_Lite", split="test")


def load_subset_instances(
    subset: Optional[Sequence[SubsetItem]] = None,
    dataset=None,
) -> List[Dict]:
    """Return full instance rows for the subset, in subset order.

    ``subset`` items may be bare instance-id strings or dicts with an
    ``instance_id`` key; defaults to the locked artifact. ``dataset`` is any
    iterable of dict rows (HF dataset or a list); defaults to SWE-bench-Lite test.
    Raises ``KeyError`` if a subset id is absent from the dataset.
    """
    ids = [_instance_id(it) for it in subset] if subset is not None else load_subset_ids()
    rows = dataset if dataset is not None else _default_dataset()
    by_id = {r["instance_id"]: r for r in rows}
    out = []
    for iid in ids:
        if iid not in by_id:
            raise KeyError(f"instance_id not in dataset: {iid}")
        out.append(dict(by_id[iid]))
    return out
