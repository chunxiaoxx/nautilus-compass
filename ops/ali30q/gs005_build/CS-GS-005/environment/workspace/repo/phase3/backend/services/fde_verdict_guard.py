"""齿轮③ verdict 语义守卫(2026-06-22)· compass 实测语义混的 ingest 侧治本。

compass 7 齿轮③:两套口径混用同一 `overall_pass` → bvh_001 类 bug(solver 解错 score=0
却 pass=true)。根因 = 没显式标 verdict 口径。

守卫(ingest 持久化前应用·纯函数):
- `verdict_kind == "solver_correctness"`(解对 pass):**score=0 强制 overall_pass=false**。
- `verdict_kind == "stump_gate"`(难倒门 pass):score=0 + pass=true 合法(doubao 全败=最难倒·
  买方 stump 验收)·不动。
- 无 `verdict_kind`(历史 verdict):不臆断·不动(向后兼容)。

闲聊/占位守卫 = 已部署 `services/fde_scorer_poll.py` 的 `is_substantive_output`(scorer 侧·非此处)。
"""
from __future__ import annotations


def apply_verdict_kind_guard(body: dict) -> dict:
    """按 verdict_kind 口径校正 overall_pass(就地改 body·返回同 dict)。"""
    kind = body.get("verdict_kind")
    if kind == "solver_correctness":
        try:
            score = float(body.get("score") or 0.0)
        except (TypeError, ValueError):
            score = 0.0
        if score == 0.0:
            # 解对 pass 路径:解错(score=0)绝不能 pass=true(bvh_001 类)
            body["overall_pass"] = False
    return body
