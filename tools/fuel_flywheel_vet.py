#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R506 · flywheel 423 candidates 过 flywheel 红线 R1-R7 重筛(其审计件为正本判据)。

红线实现:
- R1/R2/R5: 港区投资/泄密审计/报价盘口/政府线方案件按文件名排除;
- R4: 谈判/intel 件按文件名排除;
- R6: PII 角色化(手机号/邮箱→占位);结算语义件按文件名排除;
- R7: runtime 仅取 git 跟踪清单内 + 白名单类名。
"""
import csv
import json
import re
import subprocess
from pathlib import Path

FW = Path(r"C:\Users\chunx\Projects\nautilusflywheel")
SRC = Path(r"C:\Users\chunx\Projects\nautilus-compass\runtime\org_fuel\candidates_flywheel.jsonl")
OUT = Path(r"C:\Users\chunx\Projects\nautilus-compass\runtime\org_fuel\candidates_flywheel_vetted.jsonl")

# 文件名红线(R1/R2/R4/R5/R6-结算)
FILENAME_BAN = re.compile(
    r"港区方案|泄密事件|原力灵机会面|会谈最新弹药|报价单|报价框架|orbbec-quote|"
    r"徐汇上报|国曙|BP|collector-recruit-copy-pack| intel",
    re.I,
)
# PII 角色化
PHONE = re.compile(r"1[3-9]\d{9}")
EMAIL = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}")


def runtime_whitelist() -> set:
    """R7: git ls-files runtime/ 跟踪清单。"""
    try:
        out = subprocess.run(
            ["git", "ls-files", "runtime/"], cwd=str(FW), capture_output=True, text=True, timeout=30
        ).stdout
        return set(out.splitlines())
    except Exception:
        return set()


def redact_pii(t: str) -> str:
    t = PHONE.sub("[phone]", t)
    t = EMAIL.sub("[email]", t)
    return t


def main() -> int:
    wl = runtime_whitelist()
    rows = [json.loads(l) for l in SRC.read_text(encoding="utf-8").splitlines() if l.strip()]
    out, dropped, pii_redacted = [], [], 0
    for r in rows:
        src = r["source"].replace("\\", "/")
        name = src.rsplit("/", 1)[-1]
        # 文件名红线
        if FILENAME_BAN.search(name):
            dropped.append((r["pf_id"], f"R1/2/4/5 文件名红线: {name}"))
            continue
        # R7: runtime 须在 git 跟踪清单
        if src.startswith("runtime/"):
            git_path = src
            if git_path not in wl:
                dropped.append((r["pf_id"], "R7 runtime 未跟踪"))
                continue
        body = r.get("content", "")
        # R6: PII 角色化(内容级)
        nb = redact_pii(body)
        if nb != body:
            pii_redacted += 1
            r["content"] = nb
            r["pii_redacted"] = True
        # R6-结算语义: 正文命中结算规则细节即弃(保守)
        if re.search(r"8-15 元/h|发薪流水|结算规则", nb):
            dropped.append((r["pf_id"], "R6 结算语义"))
            continue
        out.append(r)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"[OK] 重筛: {len(rows)} → {len(out)} (drop {len(rows)-len(out)}: 红线/PII)")
    for pf, why in dropped:
        print("  drop:", pf, "|", why)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
