"""张欢题验证器:个税累计预扣预缴(2026 口径,居民工资薪金)。

确定性契约:同输入同输出。两用:
1) calibrate(): 独立重算 vs 附件中专家已算值 → 验证器自校准;
2) verify(candidate): 模型输出(姓名→个税金额) vs 专家值 → pass/fail + 逐人证据。
"""
from __future__ import annotations
import pandas as pd
from pathlib import Path

BRACKETS = [  # (累计应纳税所得额上限, 税率, 速算扣除数)
    (36000, 0.03, 0), (144000, 0.10, 2520), (300000, 0.20, 16920),
    (420000, 0.25, 31920), (660000, 0.30, 52920), (960000, 0.35, 85920),
    (float("inf"), 0.45, 181920),
]

def cum_tax(base: float) -> float:
    if base <= 0: return 0.0
    for cap, rate, quick in BRACKETS:
        if base <= cap:
            return round(base * rate - quick, 2)
    raise AssertionError

def load_expert(xlsx: str) -> pd.DataFrame:
    df = pd.read_excel(xlsx, sheet_name="工资", header=None, skiprows=3)
    out = pd.DataFrame({
        "姓名": df[1], "应税工资": df[14], "上期累计应税": df[27],
        "专项附加合计": df[[28,29,30,31,32,33]].fillna(0).sum(axis=1),
        "本期累计应税": df[34], "累计免征额": df[35],
        "本期累计个税_专家": df[36], "上期已缴": df[49],
        "个税金额_专家": df[50], "实发_专家": df[52],
    })
    out = out[out["姓名"].notna() & out["应税工资"].notna()].reset_index(drop=True)
    for c in out.columns[1:]:
        out[c] = pd.to_numeric(out[c], errors="coerce").fillna(0.0)
    return out

def recompute(row) -> tuple[float, float]:
    cum_taxable = row["上期累计应税"] + row["应税工资"]
    base = cum_taxable - row["累计免征额"] - row["专项附加合计"]
    t_cum = cum_tax(base)
    t_now = round(max(0.0, t_cum - row["上期已缴"]), 2)
    return t_cum, t_now

def calibrate(xlsx: str, tol: float = 0.05):
    df = load_expert(xlsx)
    bad = []
    for _, r in df.iterrows():
        _, t_now = recompute(r)
        if abs(t_now - r["个税金额_专家"]) > tol:
            bad.append((r["姓名"], t_now, r["个税金额_专家"]))
    return len(df), bad

def verify(xlsx: str, candidate: dict[str, float], tol: float = 0.05):
    """candidate: {姓名: 本期个税金额}。返回 (ok, 逐人偏差清单, 覆盖率)。"""
    df = load_expert(xlsx)
    findings, hit = [], 0
    for _, r in df.iterrows():
        name = str(r["姓名"]).strip()
        if name not in candidate:
            findings.append((name, "缺失", r["个税金额_专家"])); continue
        hit += 1
        got = float(candidate[name])
        if abs(got - r["个税金额_专家"]) > tol:
            findings.append((name, got, r["个税金额_专家"]))
    ok = (hit == len(df)) and not any(f[1] != "缺失" and True for f in findings if f[1] != "缺失") and len(findings) == 0
    return ok, findings, hit / len(df)
