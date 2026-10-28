"""薛美雪题验证器:Q4 连续劳务稽核(劳务报酬预扣 + 跨期 + 完税凭证)。

真值独立重算:
- 劳务报酬预扣(按月合并):收入>4000 减 20%,否则减 800;预扣率 ≤2万 20%/0,2-5万 30%/2000,>5万 40%/7000。
- 跨期 = 服务月份 ≠ 付款月份(含未付款);缺凭证 = 数据行完税凭证号为空。
"""
from __future__ import annotations
import pandas as pd
from pathlib import Path

BASE = Path(r"C:/Users/chunx/AppData/Local/Temp/claude/C--Users-chunx-Projects-nautilus-core/efea1144-0b71-4702-8732-646859f091b0/scratchpad/batch1/titi/大模型训练师-题目/连续劳务/薛美雪")

def svc_tax(x: float) -> float:
    ded = x * 0.2 if x > 4000 else 800.0
    t = x - ded
    if t <= 20000: return round(t * 0.20, 2)
    if t <= 50000: return round(t * 0.30 - 2000, 2)
    return round(t * 0.40 - 7000, 2)

def load():
    pay = pd.read_excel(BASE / "附件2_Q4劳务费用支付明细表.xlsx", header=2)
    pay = pay[pd.to_numeric(pay["序号"], errors="coerce").notna()].copy()
    pay["序号"] = pay["序号"].astype(int)
    led = pd.read_excel(BASE / "附件3_个税预扣预缴台账.xlsx", header=2)
    led = led[pd.to_numeric(led["序号"], errors="coerce").notna()].copy()
    inv = pd.read_excel(BASE / "附件4_发票记录表.xlsx", header=2)
    inv = inv[pd.to_numeric(inv["序号"], errors="coerce").notna()].copy()
    return pay, led, inv

def ground_truth():
    pay, led, inv = load()
    # 付款月(取得时点)合并口径;未付款行不产生 Q4 预扣义务
    pay["付款月"] = pay["付款日期"].astype(str).str[:7]
    paid = pay[pay["付款日期"].astype(str).str.contains("2025")]
    month_map = {"2025-10": "10月", "2025-11": "11月", "2025-12": "12月"}
    grp = paid.groupby(["劳务提供者", "付款月"])["金额(价税合计)"].sum().reset_index()
    correct = {}
    for _, r in grp.iterrows():
        correct[(r["劳务提供者"], month_map[r["付款月"]])] = svc_tax(float(r["金额(价税合计)"]))
    # 台账按(人,月)聚合已预扣
    led2 = led[led["劳务提供者"].notna() & (led["劳务提供者"] != "—")]
    booked = led2.groupby(["劳务提供者", "月份"])["已预扣税额"].sum().to_dict()
    fixes = {}
    for k, v in correct.items():
        b = float(booked.get(k, 0.0))
        if abs(v - b) > 0.5:
            fixes[k] = v
    cross = set(int(r["序号"]) for _, r in pay.iterrows()
                if str(r["服务月份"])[:7] != (str(r["付款日期"])[:7] if "2025" in str(r["付款日期"]) else "未付"))
    miss = set(int(r["序号"]) for _, r in inv.iterrows()
               if str(r["完税凭证号"]).strip() in ("—", "-", "", "nan", "None"))
    return fixes, cross, miss

def verify(candidate: dict, tol: float = 1.0):
    """candidate: {"个税更正":[{"人":..,"月":..,"正确税额":..}], "跨期序号":[...], "缺完税凭证发票序号":[...]}"""
    fixes, cross, miss = ground_truth()
    findings = []
    cand_fix = {(str(d.get("人", d.get("劳务提供者", ""))).strip(), str(d.get("月", d.get("月份", ""))).strip()):
                float(d.get("正确税额", -1)) for d in candidate.get("个税更正", [])}
    for k, v in fixes.items():
        if k not in cand_fix: findings.append(("漏更正", k, v))
        elif abs(cand_fix[k] - v) > tol: findings.append(("更正值错", k, cand_fix[k], v))
    for k in cand_fix:
        if k not in fixes: findings.append(("误更正", k, cand_fix[k]))
    cc = set(int(x) for x in candidate.get("跨期序号", []) if str(x).strip().isdigit())
    if cc != cross: findings.append(("跨期集不符", sorted(cc), sorted(cross)))
    mm = set(int(x) for x in candidate.get("缺完税凭证发票序号", candidate.get("缺完税凭证发票号", [])) if str(x).strip().isdigit())
    if mm != miss: findings.append(("缺凭证集不符", sorted(mm), sorted(miss)))
    return (not findings), findings

if __name__ == "__main__":
    fixes, cross, miss = ground_truth()
    print("个税更正真值(人,月)→正确税额:")
    for k, v in sorted(fixes.items()): print("  ", k, "→", v)
    print("跨期序号:", sorted(cross))
    print("缺凭证发票表序号:", sorted(miss))
