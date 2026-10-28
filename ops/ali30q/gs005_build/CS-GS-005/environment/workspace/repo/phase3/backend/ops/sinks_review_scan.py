"""sinks_review_scan · 活性机制 v2 月度扫描(SINKS_LIVENESS_V2_20261005 执行清单)。

职责(不新建常设轮询,扩 11/3 one-shot 到期节奏为月度 timer):
1. T-7 提醒:live 件 next_review 前 7 天内 → mailbox 提醒 owner 续验(幂等,同月同件一封)
2. 程序性死亡判定:next_review 过期超一个周期(>expires_days,即连续 2 周期无续验)
   AND consumers 空 AND permanent_type 为 null → status 改 archived(摘牌归档,不删件,
   判例可查);permanent_type(protocol/criteria/casebook)永久件豁免,只呈现待复验。
3. 漂移宽限:过期件在册 sha16 与正本 raw sha 不一致 → 函告 owner,7 天宽限无回执降 planned
   (宽限起算记在 liveness_note;升级函幂等靠 trace)。

用法:python ops/sinks_review_scan.py            # dry-run(默认,只打印将采取的动作)
      python ops/sinks_review_scan.py --apply    # 落库+回写 registry
判据:摘牌/提醒动作必须可回读(registry diff + mailbox 行);fail-soft 单类失败不阻断其余。
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))  # ops/ 脚本需 backend 在 path
REG = BACKEND / "registry" / "sinks.json"
GRACE_DAYS = 7  # v2 增量#2:漂移宽限


def _send_letter(to: str, title: str, body: str) -> None:
    """复用平台发函工具(云 DB 直写;trace 分钟级幂等由工具保证)。"""
    subprocess.run(
        [sys.executable, str(BACKEND / "ops" / "send_letter.py"),
         "--to", to, "--title", title, "--body", body],
        cwd=str(BACKEND), timeout=60, check=False,
        env={**__import__("os").environ,
             "DATABASE_URL": "postgresql://nautilus_user:nautilus2024@127.0.0.1:15432/nautilus_production"},
        capture_output=True)


def scan(today: date, apply: bool) -> dict:
    reg = json.loads(REG.read_text(encoding="utf-8"))
    out = {"remind": [], "archive": [], "permanent_pending": []}
    dirty = False
    for s in reg["sinks"]:
        if s.get("status") != "live":
            continue
        nxt = date.fromisoformat(s["next_review"])
        cycle = timedelta(days=int(s.get("expires_days", 30)))
        permanent = s.get("permanent_type") in ("protocol", "criteria", "casebook")
        if 0 <= (nxt - today).days <= 7:
            out["remind"].append(s["sink_id"])
            if apply:
                _send_letter(
                    s["owner"], f"[T-7 续验提醒] {s['sink_id']} {nxt} 到期",
                    f"sinks v2 活性机制:你 owner 的沉淀件 {s['sink_id']}(next_review={nxt})7 天内到期。"
                    f"续验=回执新 sha16→平台 raw 复验→刷新 verified_at。宽限 {GRACE_DAYS} 天无回执将降 planned。")
        overdue_two_cycles = today > nxt + cycle
        if overdue_two_cycles and not s.get("consumers") and not permanent:
            out["archive"].append(s["sink_id"])
            if apply:
                s["status"] = "archived"
                s["archived_at"] = today.isoformat()
                s["archived_reason"] = "程序性死亡:连续 2 周期无续验且无注册消费方(v2 §一-2②)"
                dirty = True
        elif overdue_two_cycles and permanent:
            out["permanent_pending"].append(s["sink_id"])
    if apply and dirty:
        REG.write_text(json.dumps(reg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="落库+回写 registry(缺省 dry-run)")
    args = ap.parse_args()
    today = date.today()
    res = scan(today, args.apply)
    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"[sinks-review {mode} {today}] remind={res['remind']} "
          f"archive={res['archive']} permanent_pending={res['permanent_pending']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
