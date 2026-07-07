"""compass · 收敛执法日报生成器(一键)· 把今天零散的 3 条探针合成一个命令。

背景(2026-07-07):收敛执法日报此前靠手摇 3 个脚本 + 临时 SQL。本模块把它们合成
`python ops/convergence_report.py`,一键出「5 记分牌 + FDE 4 表 + 合约状态」的 grounded 快照。
复用不另造(anchor #5):
- 经济探针 = `economy_liveness_probe`(income / engine_cycle / income_ground_truth)。
- 记分牌 DB 查询(verdict 分层 / autonomous 铸币 / settle 路由)= 本模块直接 SELECT(同 compass_sub 只读连接)。
- FDE 4 表行数 = `feishu_read_via_cloud`(经 cloud 白名单 IP · 治 99991401)。
- 合约状态 = `contract.scan_sessions_for_contracts`。

**只读**:全 SELECT + HTTP GET · 不写任何生产表/飞书。degrade gracefully:某段读失败标 GAP 不崩。

用法:
    python ops/convergence_report.py            # 文本日报
    python ops/convergence_report.py --json     # JSON(给 cron/看板)
    python ops/convergence_report.py --no-feishu # 跳过飞书(离线/无 cloud 时)
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent

# v06 培训链 4 表(与 reference_feishu 一致)
V06_TABLES = [
    ("学员(行业专家)", "tblQChALfBACGLYB"),
    ("派活★", "tblfPoDrZzKHpU36"),
    ("交付总表", "tblwz7PQZrZW3UzO"),
    ("审计日志", "tblqX49MQooUZjKH"),
]
PRODUCER_AGENT_ID = 9000009


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    # 注册 sys.modules 后再 exec:否则 dataclass asdict/deepcopy 在未注册模块上崩
    # ('NoneType' object has no attribute '__dict__')。
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _scoreboard_db(conn) -> dict:
    """5 记分牌里需额外 SQL 的部分:verdict 分层 + autonomous 铸币 + settle 路由。"""
    cur = conn.cursor()
    out = {}
    # verdict 分层
    cur.execute("SELECT COUNT(*), COUNT(*) FILTER (WHERE external_verified), "
                "COUNT(*) FILTER (WHERE external_verified AND overall_pass) FROM fde_verdicts")
    total, ext, mint = cur.fetchone()
    out["verdict"] = {"total": total, "external_verified": ext, "minting": mint}
    # autonomous 铸币(自治率分子)
    cur.execute("SELECT COUNT(*) FROM fde_verdicts WHERE external_verified AND overall_pass "
                "AND (artifacts->>'autonomous')::text = 'true'")
    out["autonomous_mints"] = cur.fetchone()[0]
    # settle a2a 路由(0 settled 的根因证据)
    cur.execute("SELECT tool_name, COUNT(*), COUNT(*) FILTER (WHERE success) "
                "FROM agent_tool_calls WHERE ts > now()-interval '48 hours' "
                "AND tool_name IN ('send_to_agent','nautilus__nautilus_claim_bounty') "
                "GROUP BY tool_name ORDER BY 2 DESC")
    out["settle_routes"] = [{"tool": r[0], "n": r[1], "ok": r[2]} for r in cur.fetchall()]
    # producer 活性
    cur.execute("SELECT COUNT(*), COUNT(*) FILTER (WHERE success), MAX(ts) "
                "FROM agent_tool_calls WHERE ts > now()-interval '24 hours' "
                "AND agent_id = 'nautilus-prime-001'")
    n, ok, last = cur.fetchone()
    out["producer_prime001_24h"] = {"calls": n, "ok": ok, "last": str(last)}
    return out


def gather(use_feishu: bool = True) -> dict:
    elp = _load("economy_liveness_probe", _HERE / "economy_liveness_probe.py")
    report: dict = {"probes": None, "scoreboard_db": None, "feishu": None, "contracts": None}

    # 1. 经济探针 + 补充 DB 记分牌(同一连接)
    try:
        with elp.open_live_conn() as conn:
            report["probes"] = elp.run_all(conn, PRODUCER_AGENT_ID)
            report["scoreboard_db"] = _scoreboard_db(conn)
    except Exception as e:  # noqa: BLE001
        report["probes"] = {"_error": f"DB read fail: {str(e)[:160]}"}

    # 2. FDE 4 表(经 cloud · 可选)
    if use_feishu:
        try:
            fr = _load("feishu_read_via_cloud", _HERE / "feishu_read_via_cloud.py")
            report["feishu"] = {label: fr.table_row_count(tid) for label, tid in V06_TABLES}
        except Exception as e:  # noqa: BLE001
            report["feishu"] = {"_error": f"feishu read fail (需 cloud): {str(e)[:160]}"}
    else:
        report["feishu"] = {"_skipped": True}

    # 3. 合约状态
    try:
        contract = _load("contract", _REPO / "contract.py")
        roots = contract._default_memory_roots()
        scan = contract.scan_sessions_for_contracts(roots, within_hours=720.0)
        report["contracts"] = {"outstanding": len(scan["outstanding"]),
                               "consumed": len(scan["consumed"]),
                               "expired": len(scan["expired"]),
                               "outstanding_ids": [c.id for c in scan["outstanding"]]}
    except Exception as e:  # noqa: BLE001
        report["contracts"] = {"_error": f"contract scan fail: {str(e)[:160]}"}

    return report


def render_text(r: dict) -> str:
    L = ["🧭 compass 收敛执法日报(convergence_report · grounded 探针快照)", "=" * 60]
    p = r.get("probes") or {}
    sdb = r.get("scoreboard_db") or {}
    inc = p.get("verified_income", {})
    gt = p.get("income_ground_truth", {})
    cyc = p.get("engine_cycle", {})
    L.append("[记分牌]")
    L.append(f"  income        : agent_survival={gt.get('total_income','?')} · "
             f"verdict-derived={inc.get('derived_income','?')}({inc.get('minting_count','?')} 铸币)")
    L.append(f"  自治率        : autonomous 铸币 {sdb.get('autonomous_mints','?')} 条")
    sr = sdb.get("settle_routes") or []
    sr_s = " · ".join(f"{x['tool'].split('__')[-1]} {x['ok']}/{x['n']}ok" for x in sr) or "n/a"
    L.append(f"  settle(a2a)   : {sr_s}  (0 ok = 路由 404)")
    L.append(f"  verdict       : external_verified={sdb.get('verdict',{}).get('external_verified','?')} · "
             f"minting={sdb.get('verdict',{}).get('minting','?')}")
    prod = sdb.get("producer_prime001_24h", {})
    L.append(f"  engine_cycle  : [{cyc.get('status','?')}] {cyc.get('detail','')[:60]}")
    L.append(f"  producer      : prime-001 24h calls={prod.get('calls','?')}/ok={prod.get('ok','?')} last={prod.get('last','?')[:19]}")
    L.append("")
    L.append("[FDE 培训链 4 表]")
    fs = r.get("feishu") or {}
    if fs.get("_error"):
        L.append(f"  GAP · {fs['_error']}")
    elif fs.get("_skipped"):
        L.append("  (--no-feishu 跳过)")
    else:
        for label, _ in V06_TABLES:
            L.append(f"  {label:16}: {fs.get(label,'?')} 行")
    L.append("")
    c = r.get("contracts") or {}
    L.append(f"[合约] outstanding={c.get('outstanding','?')} consumed={c.get('consumed','?')} "
             f"expired={c.get('expired','?')}")
    for cid in (c.get("outstanding_ids") or [])[:8]:
        L.append(f"  · OUT {cid}")
    return "\n".join(L)


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass
    ap = argparse.ArgumentParser(description="compass 收敛执法日报(一键 grounded 快照)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-feishu", action="store_true", help="跳过飞书读(离线/无 cloud)")
    a = ap.parse_args(argv)
    r = gather(use_feishu=not a.no_feishu)
    if a.json:
        print(json.dumps(r, indent=2, ensure_ascii=False, default=str))
    else:
        print(render_text(r))
    return 0


if __name__ == "__main__":
    sys.exit(main())
