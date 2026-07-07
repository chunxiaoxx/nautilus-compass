"""compass · economy liveness probe · 读**生产 DB 真值**验闭环(替换 liveness_audit 的"瞎")。

背景(SSOT 7/7 v3 · compass ① 第一优先):旧 ops/liveness_audit.py 三探针全查
**本地文件**(PoI snapshot mtime / patch marker),验不了 income 98/188 真假、验不了
agent 的 "1233 actions / 0 settled" 是否真 —— 独立裁判缺口。本模块是那个独立裁判:
走已验证的 compass_sub ssh-tunnel 只读连接(复用 cross_agent_outcome_poller ·
anchor #5 不另造),直接 SELECT 生产表,**不信任何自报**。

三探针(对应 SSOT binding-DONE 判据):
- probe_verified_income:fde_verdicts 里 external_verified ∧ overall_pass 的
  sum(round(score)) = **独立复现的 income**(不读 agent_survival 也能佐证 188)+
  latest external_verified_at 新鲜度。judge:income 是否由真外部验证的 verdict 撑起。
- probe_engine_cycle_liveness:engine_cycle_outcomes last cycle 时效 + 24h 计数 =
  独立验"cron 220+ cycle 0 执行 / 引擎停摆一个月"剧场(诚实 surface,不藏)。
- probe_income_ground_truth:试读 agent_survival.total_income 真值;compass_sub 无
  GRANT → 诚实报 GAP(附需要的 GRANT + 回退到 verdict-derived),**绝不 fake-GREEN**。

connection 注入设计 → 纯探针函数吃一个 DB-API conn · 可用 fake cursor 单测(不依赖网络)。
CLI 用 open_live_conn() 走真连接。

用法:
  python ops/economy_liveness_probe.py            # live · 跑全部
  python ops/economy_liveness_probe.py --json     # JSON(给 cron/监控)
  python ops/economy_liveness_probe.py --probe verified_income
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path

_HERE = Path(__file__).resolve().parent

# 生产 producer agent(9000009 = cloud-genopt-runner · SSOT 活 producer)
PRODUCER_AGENT_ID = int(os.environ.get("COMPASS_PRODUCER_AGENT_ID", "9000009"))
# engine cycle 新鲜阈值:> 此小时数无新 cycle → STALE(引擎自循环停摆)
CYCLE_STALE_HOURS = float(os.environ.get("COMPASS_CYCLE_STALE_HOURS", "48.0"))
# external_verified 新鲜阈值:> 此小时数无新外部验证 → income 链停滞
VERIFY_STALE_HOURS = float(os.environ.get("COMPASS_VERIFY_STALE_HOURS", "168.0"))

# 状态词汇 · 诚实分级(不把"读不到"或"引擎死了"粉饰成 GREEN)
GREEN = "GREEN"    # 可读 + 健康
STALE = "STALE"    # 可读,但所测的东西停滞(引擎循环死 / 验证链停)—— 真实诊断,非健康
GAP = "GAP"        # 因缺 GRANT 读不到 —— 诚实的能力缺口
RED = "RED"        # 读错误 / 意外

PROBE_INCOME = "verified_income"
PROBE_CYCLE = "engine_cycle"
PROBE_GROUND_TRUTH = "income_ground_truth"
ALL_PROBES = [PROBE_INCOME, PROBE_CYCLE, PROBE_GROUND_TRUTH]


def _is_permission_denied(exc: Exception) -> bool:
    """驱动无关地识别 postgres permission-denied(不 import psycopg2 · 保持可测)。"""
    return "permission denied" in str(exc).lower()


def probe_verified_income(conn) -> dict:
    """fde_verdicts 独立复现 income:external_verified ∧ overall_pass 的
    sum(round(score))。这是**不信 agent_survival 自报**的 income 佐证。

    GREEN:至少 1 条铸币 verdict(income 由真外部验证撑起)。
    STALE:有历史铸币但 latest external_verified_at 超 VERIFY_STALE_HOURS(链停滞)。
    RED:读失败。
    """
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT COALESCE(SUM(ROUND(score)::int), 0), COUNT(*), "
            "MAX(external_verified_at) "
            "FROM fde_verdicts WHERE external_verified AND overall_pass"
        )
        derived_income, minting_count, latest = cur.fetchone()
        derived_income = int(derived_income or 0)
        minting_count = int(minting_count or 0)
    except Exception as e:  # noqa: BLE001 — 分类上报,不吞
        return {"status": RED, "detail": f"fde_verdicts read fail: {str(e)[:160]}"}

    if minting_count < 1:
        return {"status": STALE,
                "detail": "no external_verified∧overall_pass verdict · income 0",
                "derived_income": 0, "minting_count": 0}

    age_h = _age_hours(latest)
    stale = age_h is not None and age_h > VERIFY_STALE_HOURS
    status = STALE if stale else GREEN
    detail = (f"derived_income={derived_income} from {minting_count} minting "
              f"verdict(s) · latest_verify_age={_fmt_age(age_h)}")
    return {"status": status, "detail": detail,
            "derived_income": derived_income, "minting_count": minting_count,
            "latest_verified_at": str(latest) if latest else None}


def probe_engine_cycle_liveness(conn) -> dict:
    """engine_cycle_outcomes 独立验引擎自循环是否真在跑(治"信剧场")。

    GREEN:近 24h 有 cycle(引擎活)。
    STALE:可读但最新 cycle 超 CYCLE_STALE_HOURS(引擎自循环停摆 —— 诚实 surface)。
    RED:读失败。
    """
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT MAX(created_at), COUNT(*), "
            "COUNT(*) FILTER (WHERE created_at > now() - interval '24 hours') "
            "FROM engine_cycle_outcomes"
        )
        last, total, last_24h = cur.fetchone()
        total = int(total or 0)
        last_24h = int(last_24h or 0)
    except Exception as e:  # noqa: BLE001
        return {"status": RED, "detail": f"engine_cycle_outcomes read fail: {str(e)[:160]}"}

    age_h = _age_hours(last)
    alive = last_24h > 0 and (age_h is not None and age_h <= CYCLE_STALE_HOURS)
    status = GREEN if alive else STALE
    detail = (f"last_cycle_age={_fmt_age(age_h)} · cycles_24h={last_24h} · "
              f"total={total}" + ("" if alive else " · 引擎自循环停摆(非健康)"))
    return {"status": status, "detail": detail,
            "cycles_24h": last_24h, "total_cycles": total,
            "last_cycle_at": str(last) if last else None}


def probe_income_ground_truth(conn, producer_agent_id: int = PRODUCER_AGENT_ID) -> dict:
    """试读 agent_survival.total_income 真值(income 总额权威源)。

    GREEN:读到真值。
    GAP:compass_sub 无 GRANT → 诚实报缺口 + 需要的 GRANT(不 fake-GREEN)。
    RED:其它读错误。
    """
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT total_income, survival_level, status FROM agent_survival "
            "WHERE agent_id = %s", (producer_agent_id,))
        row = cur.fetchone()
    except Exception as e:  # noqa: BLE001
        if _is_permission_denied(e):
            return {"status": GAP,
                    "detail": ("agent_survival 无 SELECT grant · income 总额读不到 · "
                               "需 platform: GRANT SELECT ON agent_survival TO compass_sub · "
                               "回退用 probe_verified_income 的 verdict-derived income"),
                    "needs_grant": "GRANT SELECT ON agent_survival TO compass_sub"}
        return {"status": RED, "detail": f"agent_survival read fail: {str(e)[:160]}"}

    if row is None:
        return {"status": STALE,
                "detail": f"agent {producer_agent_id} not in agent_survival"}
    total_income, level, status_val = row
    return {"status": GREEN,
            "detail": f"agent {producer_agent_id} total_income={total_income} "
                      f"level={level} status={status_val}",
            "total_income": total_income}


# ------------------------------------------------------------------ helpers
def _age_hours(ts) -> float | None:
    """timestamptz → 距今小时数(now 用 DB 侧 · 这里近似用本地 now 仅供展示阈值判断)。"""
    if ts is None:
        return None
    try:
        from datetime import datetime, timezone
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - ts).total_seconds() / 3600.0
    except Exception:  # noqa: BLE001
        return None


def _fmt_age(age_h) -> str:
    if age_h is None:
        return "n/a"
    if age_h < 48:
        return f"{age_h:.1f}h"
    return f"{age_h / 24:.1f}d"


# ------------------------------------------------------------------ runner
def run_all(conn, producer_agent_id: int = PRODUCER_AGENT_ID) -> dict:
    return {
        PROBE_INCOME: probe_verified_income(conn),
        PROBE_CYCLE: probe_engine_cycle_liveness(conn),
        PROBE_GROUND_TRUTH: probe_income_ground_truth(conn, producer_agent_id),
    }


@contextmanager
def open_live_conn():
    """复用 cross_agent_outcome_poller 的 ssh-tunnel + compass_sub 只读连接
    (anchor #5 不另造连接层)。"""
    spec = importlib.util.spec_from_file_location(
        "cross_agent_outcome_poller", _HERE / "cross_agent_outcome_poller.py")
    poller = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(poller)
    cfg = poller.parse_secret(poller.SECRET_FILE)
    with poller.db_connection(cfg, readonly=True) as conn:
        yield conn


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="compass economy liveness probe · 读生产 DB 真值验闭环")
    ap.add_argument("--probe", choices=ALL_PROBES, help="单探针(默认全部)")
    ap.add_argument("--producer", type=int, default=PRODUCER_AGENT_ID)
    ap.add_argument("--json", action="store_true", help="JSON 输出(给 cron/监控)")
    args = ap.parse_args(argv)

    try:
        with open_live_conn() as conn:
            if args.probe == PROBE_INCOME:
                result = {PROBE_INCOME: probe_verified_income(conn)}
            elif args.probe == PROBE_CYCLE:
                result = {PROBE_CYCLE: probe_engine_cycle_liveness(conn)}
            elif args.probe == PROBE_GROUND_TRUTH:
                result = {PROBE_GROUND_TRUTH: probe_income_ground_truth(conn, args.producer)}
            else:
                result = run_all(conn, args.producer)
    except Exception as e:  # noqa: BLE001 — 连接失败也要诚实报(不静默)
        result = {"_connect": {"status": RED, "detail": f"db connect fail: {str(e)[:200]}"}}

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    else:
        for name, r in result.items():
            print(f"[{r['status']}] {name}: {r['detail']}")

    # 全 GREEN → 0 · 任一非 GREEN(含 STALE/GAP/RED)→ 1(给 cron 告警 · 诚实)
    return 0 if all(r["status"] == GREEN for r in result.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
