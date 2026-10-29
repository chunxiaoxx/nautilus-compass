#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""出题生产 loop · 2026-10-29 正式启动

每轮: 取素材卡→构造题(gate5判定→迭代至达标)→入池→通报
模式: 全自动化·无需人工干预
频率: 30min/轮·每轮产出0-1道候选·连续产出直到14道配额满

 production_queue: runtime/production_loop/queue.json (题池状态)
 results: runtime/production_loop/results/
"""
import json
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parent
QUEUE = BASE / "queue.json"
LOG = BASE / "rounds.log"
STATE = BASE / "state.json"


def load_state():
    if STATE.exists():
        return json.load(open(STATE))
    return {"round": 0, "卡": 0, "题": 0, "门": 0, "items": {}}


def save_state(s):
    STATE.write_text(json.dumps(s, ensure_ascii=False, indent=1))


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG, "a") as f:
        f.write(line + "\n")


def main():
    state = load_state()
    state["round"] += 1
    rn = state["round"]
    log(f"=== 生产轮 R{rn} 开始 · 卡{state['卡']}·题{state['题']}·门{state['门']} ===")

    # 1. 检查在途题的模型读数是否落地
    for iid, info in state.get("items", {}).items():
        if info.get("status") == "JUDGING":
            rdir = BASE.parent / "scratch" / iid / "_s5"
            if rdir.exists():
                reads = list(rdir.glob("*_run*_result.json"))
                log(f"  {iid}: {len(reads)} 读数文件")

    # 2. 取下一张素材卡
    cards = json.load(open(BASE / "material_cards.json"))
    next_card = next((c for c in cards if c["status"] == "PENDING"), None)
    if next_card:
        log(f"  下一卡: #{next_card['card']} {next_card['incident'][:40]} ({next_card['badpattern']})")
        next_card["status"] = "IN_PROGRESS"
        json.dump(cards, open(BASE / "material_cards.json", "w"), ensure_ascii=False, indent=1)
        log(f"  卡#{next_card['card']} 标记 IN_PROGRESS")
    else:
        log("  所有素材卡已分配")

    # 3. 更新状态
    state["素材主线"] = f"卡{state['卡']}·题{state['题']}·门{state['门']}"
    save_state(state)
    log(f"=== 生产轮 R{rn} 结束 · 素材主线: {state['素材主线']} ===")


if __name__ == "__main__":
    main()
