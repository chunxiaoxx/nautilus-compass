#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ORG-FUEL 跨框扩容生成器 v1(R505 · flywheel 源): docs 四子目录 → candidates。

口径: 沿用 org-fuel schema(pf_id/source/anchor_level/domain/situation/content_hash/content);
脱敏红线: 排除对外报价单/含客户 PII 件; plans 仅取完成态标注; runtime 只取判重/复核/交付确认类。
"""
import hashlib
import json
import re
from pathlib import Path

FW = Path(r"C:\Users\chunx\Projects\nautilusflywheel")
OUT = Path(r"C:\Users\chunx\Projects\nautilus-compass\runtime\org_fuel\candidates_flywheel.jsonl")

# 入池白名单目录(docs 下)
INCLUDE_DIRS = ("decisions", "delivery", "evidence")
# plans 只取完成态
PLAN_DONE = re.compile(r"已拍板|已完成|已交付|已验收|DONE|已完成并|✅|收官|定版|完成;", re.I)
# runtime 只取这些类
RUNTIME_PAT = re.compile(r"判重|复核|交付确认|验收|留痕|复算|复核留痕", re.I)
# 红线排除(标题/首屏命中即弃)
# 红线排除(R506 对表 flywheel R1-R7 审计件后收紧;R506b 二轮收紧含政府线/结算语义)
EXCLUDE = re.compile(
    r"报价单|报价框架|报价|对外版|客户名单|甲方联系人|身份证|银行卡|"
    r"港区方案|徐汇上报|国曙|商业计划|BP[-_ v]|规划类|"
    r"原力灵机会面|会谈最新弹药|泄密事件|审查报告|"
    r"结算规则|发薪流水|8-15 元",
    re.I,
)
# PII 粗滤: 手机号/邮箱直接命中即弃(整个文件级,宁缺勿滥)
PII = re.compile(r"1[3-9]\d{9}|[a-zA-Z0-9._%+-]+@(?!xerj|nautilus)[a-zA-Z0-9.-]+\.[a-z]{2,}")


def parse_md(p: Path) -> tuple:
    t = p.read_text(encoding="utf-8", errors="replace")
    if t.startswith("---"):
        m = re.match(r"---\n.*?\n---\n?", t, re.S)
        if m:
            t = t[m.end():]
    return p.name, t.strip()


def looks_sensitive(t: str) -> bool:
    return bool(EXCLUDE.search(t[:600]) or PII.search(t[:2000]))


def main() -> int:
    seen, out, excluded = set(), [], 0
    files = sorted(FW.glob("docs/**/*.md")) + sorted(FW.glob("runtime/*.md"))
    for p in files:
        rel = str(p.relative_to(FW))
        sub = rel.split("/")[1] if rel.startswith("docs/") else ""
        name, body = parse_md(p)
        if len(body) < 150:
            continue
        if looks_sensitive(body):
            excluded += 1
            continue
        # docs/articles = 对外思想短文, 非判例(立项档排除项)
        if "/articles/" in rel.replace("\\", "/"):
            continue
        # R505 收紧: docs/ip(知识产权)与 docs/research(未发表研究)不入训练语料——
        # 组织内可用≠可训练; IP 归属与未发表内容敏感性高于一般档案
        if "/ip/" in rel.replace("\\", "/") or "/research/" in rel.replace("\\", "/"):
            excluded += 1
            continue
        # plans 需完成态; runtime 需判例类
        if sub == "plans" and not PLAN_DONE.search(body[:1200]):
            continue
        if rel.startswith("runtime/") and not RUNTIME_PAT.search(name + body[:800]):
            continue
        content = f"flywheel 档案 {name}\n{body[:1600]}"
        h = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
        if h in seen:
            continue
        seen.add(h)
        out.append({
            "pf_id": f"ORGF-{h}",
            "source": f"flywheel/{rel}",
            "anchor_level": "L1",
            "domain": "fw-cross",
            "situation": f"{name} — {body[:150]}",
            "content_hash": h,
            "content": content,
        })
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"[OK] {OUT} candidates={len(out)} excluded_sensitive={excluded}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
