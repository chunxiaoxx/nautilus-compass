"""Write SWE-bench predictions as JSONL for the official harness.

``swebench.harness.run_evaluation`` reads one JSON object per line with exactly
``instance_id`` / ``model_patch`` / ``model_name_or_path``. An empty ``model_patch``
is a valid unresolved prediction (never dropped — a dropped instance silently
shrinks N, which would misreport the resolve rate).
"""
import json
import os
from typing import Dict, List, Union

KEYS = {"instance_id", "model_patch", "model_name_or_path"}


def write_predictions(
    path: Union[str, "os.PathLike"],
    model_name: str,
    items: List[Dict],
) -> int:
    """Write ``items`` to ``path`` as JSONL; return the number of lines written.

    Each item needs ``instance_id`` and ``model_patch``; an optional per-item
    ``model_name_or_path`` overrides ``model_name`` (e.g. to tag arm1 vs arm3 in a
    shared file). Empty patches are preserved.
    """
    n = 0
    with open(path, "w", encoding="utf-8") as fh:
        for it in items:
            rec = {
                "instance_id": it["instance_id"],
                "model_patch": it.get("model_patch", ""),
                "model_name_or_path": it.get("model_name_or_path", model_name),
            }
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
    return n
