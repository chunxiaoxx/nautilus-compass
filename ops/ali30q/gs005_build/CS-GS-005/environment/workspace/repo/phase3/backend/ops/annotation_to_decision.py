#!/usr/bin/env python3
"""标注→组织决策Schema转换器(NANOJEV_DECISION_SCHEMA_V1·用户批①·2026-09-29)。

输入:人类标注结果(每行: frame_id,label,confidence)
     + 机判基线JSON(frame_id → machine_label)
输出:决策问题jsonl(docs/NANOJEV_DECISION_SCHEMA_V1_20260929.md 格式)

用法:
  python3 ops/annotation_to_decision.py annotations.csv baseline.json -o decisions.jsonl [--split train]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

_LABELS = {"black", "freeze", "blur", "normal"}
_CONF = {"high": 0.9, "mid": 0.6, "low": 0.3}
_CRITERIA = {
    "black": "几乎全黑", "freeze": "与前一帧相同", "blur": "细节发虚", "normal": "无上述问题",
}


def _split_probs(label: str, conf: float) -> dict:
    """软目标:gold 拿 conf,其余均分 1-conf。"""
    rest = round((1 - conf) / 3, 4)
    return {k: (round(conf, 4) if k == label else rest) for k in _LABELS}


def convert(ann_rows: list[tuple[str, str, str]], baseline: dict, split: str,
            source: str = "human_crowd_annotation") -> list[dict]:
    out = []
    for frame_id, label, conf_key in ann_rows:
        if label not in _LABELS:
            raise ValueError(f"bad label {label!r} at {frame_id}")
        conf = _CONF[conf_key]
        machine = baseline.get(frame_id, {}).get("label", "normal")
        out.append({
            "id": f"frameqc:{frame_id}",
            "family_id": "embodied_frame_quality_v1",
            "split": split,
            "state": {
                "frame_id": frame_id,
                "features": baseline.get(frame_id, {}).get("features", {}),
            },
            "questions": {
                "label": {"type": "choice", "instructions": "该帧画面质量属于哪类?",
                          "criteria": dict(_CRITERIA)},
                "is_confident": {"type": "boolean", "instructions": "此判断把握高吗?"},
                "agree_machine": {"type": "boolean",
                                  "instructions": "与机判基线一致吗?"},
            },
            "gold": {"label": label,
                     "is_confident": conf_key == "high",
                     "agree_machine": label == machine},
            "gold_probs": {
                "label": _split_probs(label, conf),
                "is_confident": {"true": conf, "false": round(1 - conf, 4)},
                "agree_machine": {"true": 1.0 if label == machine else 0.0,
                                  "false": 0.0 if label == machine else 1.0},
            },
            "gold_probs_kind": {"label": "annotator_distribution",
                                "is_confident": "deterministic_truth",
                                "agree_machine": "deterministic_truth"},
            "metadata": {
                "source": source, "frame_id": frame_id,
                "qc_machine_baseline": "v0.3",
                "judge_version": "b-human-001-judge-v1",
                "integrity": hashlib.sha256(
                    f"{frame_id}|{label}|{conf_key}".encode()).hexdigest()[:16],
            },
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("annotations")
    ap.add_argument("baseline")
    ap.add_argument("-o", "--output", default="decisions.jsonl")
    ap.add_argument("--split", default="train")
    a = ap.parse_args()

    rows = []
    for line in Path(a.annotations).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.lower().startswith(("frame", "#")):
            continue
        parts = [p.strip().rstrip(",") for p in line.replace(",", " ").split()[:3]] \
            if "," not in line else [p.strip() for p in line.split(",")[:3]]
        rows.append((parts[0], parts[1].lower(), parts[2].lower()))

    baseline = json.loads(Path(a.baseline).read_text(encoding="utf-8"))
    recs = convert(rows, baseline, a.split)
    with open(a.output, "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"converted {len(recs)} rows -> {a.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
