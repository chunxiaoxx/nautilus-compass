"""compass · FDE expert-review packet generator (出复核包).

Assembles one expert-facing markdown review packet per FDE task: the task prompt,
every checklist item with the soul 一审 pass/fail marked (so the human reviewer
can CHALLENGE the AI judge), veto items flagged, the deliverable list (or a LOST
flag), and the structured 专家复核表单. The filled form becomes the
source='expert' external verdict — the first non-self-referential PoI fuel
(anchor #3). compass owns 出复核包; the review then runs on 飞书多维表格.

Format designed + user-approved via the data_004 worked example. Reuses
load_fde_tasks (DRY) for latest-verdict selection + filename fallback. NO LLM.

Run:
  python ops/fde_review_packet_build.py            # write packets for all tasks
  python ops/fde_review_packet_build.py --out DIR --deliverable-root VTF_DIR
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
from ops.fde_avoidance_corpus_build import load_fde_tasks  # noqa: E402  (DRY loader)

# RUBRIC §10 dimensions the expert scores (the 分项分 row)
_SCORE_DIMS = ("引用准确性", "覆盖完整性", "防编造(幻觉)", "附件运用",
               "计算/定量", "产物格式可用", "行业体例", "时效性")


def _soul_marks(verdict: dict) -> dict:
    """{item_id: '✅'|'❌'} from the soul verdict items (join by id)."""
    return {v.get("id"): ("✅" if v.get("pass") else "❌")
            for v in (verdict.get("items") or [])}


def _deliverable_block(deliverable) -> str:
    if deliverable:
        lines = "\n".join(f"- {name}" for name in deliverable)
        return ("**AI 交付物**(本地留存 · 专家据此验收):\n" + lines)
    return ("**AI 交付物**:⚠️ **已丢失**(生产侧未持久化 model_output + 本地无 _out 目录)。\n"
            "→ 本题只复核 **题目 + 打分标准**,**不复核交付物**(无产物可验收)。")


def build_packet(task_id, checklist, verdict, deliverable=None) -> str:
    """Render the markdown review packet for one task. `deliverable` = list of
    artifact filenames (present) or None/[] (lost → flagged)."""
    marks = _soul_marks(verdict)
    items = checklist.get("items") or []
    level = checklist.get("level", "")
    task = checklist.get("task", "")
    passed = verdict.get("passed", sum(1 for m in marks.values() if m == "✅"))
    total = verdict.get("total", len(items))

    rows = []
    for it in items:
        cid = it.get("id", "")
        veto = "**否决**" if it.get("veto") else ""
        point = str(it.get("point", "")).replace("|", "/").replace("\n", " ")
        mark = marks.get(cid, "—")
        rows.append(f"| {cid} | {veto} | {point} | {mark} | ☐达标 ☐不达标 | |")
    table = "\n".join(rows)

    score_row = "  ".join(f"{d} ___" for d in _SCORE_DIMS)

    return f"""# 专家复核包 · {task_id}（{level}）

> compass 自动组装。专家对照交付物逐项判 → 填末尾「专家复核表单」。
> 你的判断 = `source='expert'` 外部 verdict = 整条链上**第一个不是 AI 自评的真信号**。

## 0. 复核员须知（3 分钟）
- 我们给买方(字节)做「行业高难题目」:一道题 = 真实业务场景 + 附件 + 要交付的产物。AI 先做题、AI 再打一次分(soul 一审)。**AI 给 AI 打分 = 自说自话**,所以需要你这位真人专家判一次。
- **你判**:①题目够不够格 ②打分标准对不对 ③交付物买方会不会收。不需要懂 AI。
- **耗时**:约 30–45 分钟。

## 1. 题目
{task}

## 2. 交付物
{_deliverable_block(deliverable)}

## 3. 打分项 · 你逐项判（✅/❌ 是 soul AI 一审,放这给你**挑战**）
> soul 一审:{passed}/{total} 通过。否决项一旦真不达标 = 整题打回。

| 项 | 否决 | 考点 | soul一审 | **你的判断** | 理由 |
|---|---|---|---|---|---|
{table}

## 4. 专家复核表单（填这个 → source='expert' verdict）
```
题目: {task_id}    复核人: ____    日期: ____    你的领域: ____

【A. 题目质量】够格当买方付费题?
  ☐够格  ☐勉强  ☐不够格    理由: __________

【B. 打分标准】这些项对不对?有没有漏判?
  ☐都合理  ☐有问题(列 c几+为什么): __________
  漏判的关键点: __________

【C. 交付物验收】买方会收吗?
  总判定:  ☐ 通过   ☐ 打回
  分项分(0-10): {score_row}
  与 soul 一审({passed}/{total})最大分歧在哪几项 + 为什么: __________
  打回的话致命问题: __________

【D. 一句话结论】（最有复用价值 → 进避坑语料）
  这类题做好/砸的关键: __________
```
"""


def _detect_deliverable(deliverable_root, task_id):
    """Find a task's local deliverable artifacts. dir = `_<taskid no underscore>_out`
    (data_002 → _data002_out). Returns sorted filenames excluding internal scratch
    (`_`-prefixed, e.g. _model_output.txt), or None when the dir is absent (lost)."""
    if not deliverable_root:
        return None
    dirname = "_" + task_id.replace("_", "") + "_out"
    d = Path(deliverable_root) / dirname
    if not d.is_dir():
        return None
    files = sorted(p.name for p in d.iterdir()
                   if p.is_file() and not p.name.startswith("_"))
    return files or None


def build_all(checklist_dir, verdict_dir, out_dir, deliverable_root=None,
              task_ids=None) -> list:
    """Build a packet per loaded task into out_dir. Returns the written paths."""
    tasks = load_fde_tasks(verdict_dir, checklist_dir, task_ids=task_ids)
    os.makedirs(out_dir, exist_ok=True)
    written = []
    for t in tasks:
        deliverable = _detect_deliverable(deliverable_root, t["task_id"])
        md = build_packet(t["task_id"], t["checklist"], t["verdict"], deliverable)
        path = Path(out_dir) / f"复核包_{t['task_id']}.md"
        path.write_text(md, encoding="utf-8")
        written.append(str(path))
    return written


def main(argv=None):
    ap = argparse.ArgumentParser(description="Generate FDE expert-review packets.")
    ap.add_argument("--verdict-dir", help="dir with _v5_*_real_verdict_*.json")
    ap.add_argument("--checklist-dir", help="dir with <uid>_checklist.json")
    ap.add_argument("--deliverable-root", help="dir holding the _<task>_out/ artifact dirs")
    ap.add_argument("--out", default="复核包_out", help="output dir for packets")
    args = ap.parse_args(argv)

    vtf = args.deliverable_root or os.environ.get("COMPASS_VTF_ROOT")
    verdict_dir = args.verdict_dir or vtf
    checklist_dir = args.checklist_dir or vtf
    if not (verdict_dir and checklist_dir):
        raise SystemExit("[packet] set --verdict-dir/--checklist-dir or --deliverable-root/COMPASS_VTF_ROOT")

    written = build_all(checklist_dir, verdict_dir, args.out,
                        deliverable_root=vtf)
    print(f"[packet] wrote {len(written)} packets → {args.out}")
    for p in written:
        print(f"  · {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
