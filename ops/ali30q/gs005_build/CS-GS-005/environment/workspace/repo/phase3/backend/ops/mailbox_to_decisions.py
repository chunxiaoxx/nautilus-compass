#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""org_mailbox → 决策 Schema 转换首跑(纲领主线一兑现·U32 治一过性)。

把组织函件流(用户输入+agent 输出+过程判断)转为统一决策数据集——
"吸收"的物理载体:下一次的判断可以查上一次的判断。
输出: docs/evidence/org-os/decision_dataset.jsonl(追加幂等,按函 id 去重)

用法(phase3/backend/ 下):
  python ops/mailbox_to_decisions.py            # 全量增量转换
  python ops/mailbox_to_decisions.py --stats    # 只看统计
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from sqlalchemy import text

import sys as _sys
from pathlib import Path as _P
_sys.path.insert(0, str(_P(__file__).resolve().parents[1]))  # backend/ 入 path(云端无cwd巧合)
from utils.database import SessionLocal

OUT = Path(__file__).resolve().parents[1] / "docs" / "evidence" / "org-os" / "decision_dataset.jsonl"

# 决策语义识别:函件标题/正文中的裁决信号(轻规则,首版;后续可换判分器)
RULING = re.compile(r"\[(?:裁决|拍板|裁定|REJECT|批准|照准|驳回|终裁)|口径预注册|预授权|通牒", re.I)
INPUT_MARK = re.compile(r"用户(拍|批|令|定调|裁|纠|更正)", re.I)


def to_row(m: dict) -> dict:
    """函件 → 决策 Schema 行(v1 五字段)。"""
    kind = "input" if INPUT_MARK.search(m["title"] or "") else (
        "ruling" if RULING.search((m["title"] or "") + (m["body"] or "")[:200]) else "exchange")
    return {
        "id": f"mb-{m['id']}",
        "ts": str(m["created_at"]),
        "from": m["from_agent"],
        "to": m["to_agent"],
        "kind": kind,  # input=用户判断 / ruling=组织裁决 / exchange=过程轨迹
        "title": (m["title"] or "")[:120],
        "digest": (m["body"] or "")[:280],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stats", action="store_true")
    a = ap.parse_args()
    done: set[str] = set()
    if OUT.exists():
        for ln in OUT.read_text(encoding="utf-8").splitlines():
            try:
                done.add(json.loads(ln)["id"])
            except Exception:  # noqa: BLE001
                pass
    s = SessionLocal()
    rows = s.execute(text(
        "SELECT id, from_agent, to_agent, title, body, created_at FROM org_mailbox ORDER BY id"
    )).mappings().all()
    s.close()
    fresh = [to_row(dict(r)) for r in rows if f"mb-{r['id']}" not in done]
    if a.stats:
        kinds: dict[str, int] = {}
        for r in rows:
            kinds[to_row(dict(r))["kind"]] = kinds.get(to_row(dict(r))["kind"], 0) + 1
        print(f"mailbox_total={len(rows)} dataset_done={len(done)} "
              f"kind_dist={kinds}")
        return 0
    with OUT.open("a", encoding="utf-8") as fh:
        for r in fresh:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"converted +{len(fresh)} (total {len(done) + len(fresh)}) -> {OUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
