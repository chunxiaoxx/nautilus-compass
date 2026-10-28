# -*- coding: utf-8 -*-
"""阿里 CodeSense 30 题·bounty 批量发单器(调度正本 V1 §六 配套)。

用法:
    python ops/ali30q_post_bounties.py --batch B --dry-run   # 预演,只打印
    python ops/ali30q_post_bounties.py --batch B             # 实发

题族清单来源:org_mailbox 函 v5 确认件(trace ali-30q-batchB-topic-draft-*)
确认前禁止实发(脚本内置 gate:清单文件不存在即退出)。
幂等:bounty_id NOT EXISTS 挡重发。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://nautilus_user:nautilus2024@127.0.0.1:15432/nautilus_production",
)

# 工序定义(正本 §二):代号→(名称,默认承接,交付判据)
STAGES = {
    "S1": ("出题", "v5", "零方法论文档(泄题红线);题族不与已发qid重(判重门)"),
    "S2": ("五件套打包", "v5", "Harbor五件套manifest完整+zip sha16入函"),
    "S3": ("校准四门变体", "compass", "deficient/guessed脚本化可复跑+校准四件套齐"),
    "S4": ("质检判重+泄题扫描", "compass", "判重门通过+扫描零命中"),
    "S5": ("五模型x4判分", "kairos", "连跑3次一致+G1-G7矩阵入证据包"),
}

BATCH_DEADLINES = {
    "B": ("2026-10-30 18:00", "B批5题·首发试点"),
    "C": ("2026-11-14 18:00", "C批21题·全速批"),
}
REWARD_NAU = {"S1": 20, "S2": 10, "S3": 15, "S4": 10, "S5": 25}

# 清单文件:每行 = 题号|题族|深浅|业务贴|区分度假说 (v5 确认后落盘)
MANIFEST = os.path.join(os.path.dirname(__file__), "ali30q_topics_{batch}.tsv")


def load_topics(batch: str) -> list[dict]:
    path = MANIFEST.format(batch=batch)
    if not os.path.exists(path):
        print(f"GATE: 题族清单 {path} 不存在——v5 确认函未落盘,禁止发单")
        sys.exit(2)
    rows = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) != 5:
            raise ValueError(f"清单行格式须5段: {line}")
        rows.append(
            dict(qid=parts[0], family=parts[1], depth=parts[2], story=parts[3], hypothesis=parts[4])
        )
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", required=True, choices=BATCH_DEADLINES)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    topics = load_topics(args.batch)
    dl_str, batch_note = BATCH_DEADLINES[args.batch]
    deadline = datetime.fromisoformat(dl_str)

    if args.dry_run:
        for t in topics:
            for stage, (sname, owner, criteria) in STAGES.items():
                print(f"[dry] ali30q-{t['qid']}-{stage.lower()} | {t['family']}·{sname} "
                      f"| {owner} | reward {REWARD_NAU[stage]} | 死线 {dl_str}")
        print(f"批次 {args.batch}({batch_note}) 题 {len(topics)} 道 x 工序 {len(STAGES)} = "
              f"{len(topics) * len(STAGES)} 单(dry-run,未落库)")
        return

    # 实发才需要 DB 依赖(系统 python 也能跑 dry-run/gate)
    from sqlalchemy import create_engine, text

    engine = create_engine(DATABASE_URL)
    posted, skipped = 0, 0
    with engine.begin() as conn:
        for t in topics:
            for stage, (sname, owner, criteria) in STAGES.items():
                bid = f"ali30q-{t['qid']}-{stage.lower()}"
                exists = conn.execute(
                    text("SELECT 1 FROM platform_bounties WHERE bounty_id=:b"), {"b": bid}
                ).fetchone()
                if exists:
                    skipped += 1
                    continue
                meta = {
                    "program": "ali-codesense-30q",
                    "qid": t["qid"], "family": t["family"], "depth": t["depth"],
                    "stage": stage, "criteria_prereg": criteria,
                    "hypoth": t["hypothesis"], "dispatch_doc": "docs/ALI_CODESENSE_30Q_DISPATCH_V1_20261024.md",
                }
                conn.execute(
                    text("""INSERT INTO platform_bounties
                        (bounty_id, title, description, reward_nau, difficulty, task_type,
                         status, posted_by, assigned_to, deadline, metadata, channel)
                        VALUES (:b, :title, :desc, :nau, :diff, 'codesense_eval',
                         'open', 'platform', :owner, :dl, CAST(:meta AS jsonb), 'org_dispatch')"""),
                    {"b": bid,
                     "title": f"[阿里30q] {t['qid']} {t['family']}·{sname}",
                     "desc": f"{t['story']} | 判据: {criteria} | 区分度假说: {t['hypothesis']}",
                     "nau": REWARD_NAU[stage],
                     "diff": {"深": "hard", "中": "medium", "浅": "easy"}[t["depth"]],
                     "owner": owner, "dl": deadline,
                     "meta": json.dumps(meta, ensure_ascii=False)},
                )
                posted += 1
    print(f"完成: 发单 {posted} 跳过(已存在) {skipped};dry_run={args.dry_run}")


if __name__ == "__main__":
    main()
