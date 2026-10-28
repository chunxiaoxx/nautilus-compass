#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""硬介入登记(M0·U28 20260930 晚用户拍)——用户每做一次拍板/动手,记一行。

口径(U28):硬介入=用户拍板或动手(软/被动不计入 PC-004)。
台账: docs/evidence/org-os/pilot/intervention_log.jsonl
消费方: frame_snapshot.py PC-004 断奶仪表节(每日 09:07)——手工恒 0 而函化石高
=登记纪律失守,快照自动亮牌(文档不是肌肉,登记纪律也要被对账)。

用法(phase3/backend/ 下):
  python ops/log_intervention.py --category 拍板 --summary "批M0/M1开工" --host 断奶工程
  python ops/log_intervention.py --category 外发 --summary "知乎发布BC1" --could-delegate n
"""
import argparse
import json
from datetime import datetime
from pathlib import Path

LEDGER = (Path(__file__).resolve().parents[1]
          / "docs" / "evidence" / "org-os" / "pilot" / "intervention_log.jsonl")

CATEGORIES = ["拍板", "外发", "会话", "其他"]  # 介入四分类(U28 转移矩阵)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--category", required=True, choices=CATEGORIES)
    ap.add_argument("--summary", required=True, help="一句话:用户做了什么")
    ap.add_argument("--could-delegate", default="y", choices=["y", "n"],
                    help="y=可移交平台模块/agent;n=用户产权不可移交")
    ap.add_argument("--host", default="", help="可移交时的承接宿主(模块/机制名)")
    a = ap.parse_args()
    rec = {"ts": datetime.now().isoformat(timespec="seconds"),
           "category": a.category, "summary": a.summary,
           "could_delegate": a.could_delegate, "host": a.host, "source": "session"}
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"logged -> {LEDGER.name}: [{a.category}] {a.summary}")


if __name__ == "__main__":
    main()
