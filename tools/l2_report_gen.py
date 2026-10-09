#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L2 深度报告生成器 v0(T5.2 · 2026-10-09 R436)。

定位:从 judge_status API 的 done 卡自动生成 L2 报告**草稿**(骨架+数据零丢失填充),
人工判读员段留槽位——生成物未经判读员署名不得作为 L2 收费交付件(判读免费/装订
收费两线定价的边界纪律,见 docs/metering 判分两线定价档)。

判据(预注册 v0):
  G1 渲染零丢失: verdict_detail 全字段原文入报告
  G2 sha 一致:   criteria_sha16 + submission 原样呈现
  G3 人工槽位:   L2-ANALYST 段+未署名不得收费声明
  G4 非 done 拒绝: status != ok/done 时 ValueError
  G5 证据层保真: [实测]/[推断]/[不可验] 原样保留,本工具不产生新断言

用法:
  python tools/l2_report_gen.py nautilus-l1-0002                # 打印到 stdout
  python tools/l2_report_gen.py nautilus-l1-0002 -o report.md   # 落盘
  python tools/l2_report_gen.py nautilus-l1-0002 --base URL     # 自定 API 基址
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

DEFAULT_BASE = "https://nautilus.social"
CST = timezone(timedelta(hours=8))
GENERATOR_VERSION = "l2gen-v0"


def fetch_card(card_id: str, base: str = DEFAULT_BASE) -> dict:
    url = f"{base}/api/judge_status?id={card_id}"
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        # 平台对不存在的 id 回 502/404 —— 统一转拒绝语义(G4 家族,exit 2)
        raise ValueError(f"API HTTP {e.code} —— 卡不存在或接口异常: {card_id}") from e


def validate_card(card: dict) -> None:
    """G4:非 ok/done 卡拒绝生成。"""
    if not card.get("ok"):
        raise ValueError(f"API 返回 ok={card.get('ok')}(卡不存在或接口异常)")
    if card.get("status") != "done":
        raise ValueError(f"status={card.get('status')!r} ≠ done —— 未交付卡不出 L2 报告")


def render_report(card: dict, generated_at: str) -> str:
    """纯函数渲染。G1/G2/G3/G5 判据在此落地。"""
    vd = card.get("verdict_detail") or {}
    steps = card.get("steps") or []
    lines: list[str] = []
    add = lines.append

    add(f"# L2 深度报告(草稿) · {card.get('id')}")
    add("")
    add(f"> 由 `{GENERATOR_VERSION}` 自动生成于 {generated_at} · **草稿件——未经判读员署名,")
    add("> 不得作为 L2 收费交付件**(判读永久免费/装订收费边界,判据零放宽)。")
    add("")
    add("## 一、卡面摘要")
    add("")
    add(f"- 判读卡: {card.get('id')} · {card.get('title')}")
    add(f"- 判定: `{card.get('verdict')}` · 状态: {card.get('status')}")
    add(f"- 判据 sha16: `{card.get('criteria_sha16')}` ([判据披露](https://nautilus.social/criteria/))")
    add(f"- 提交物 sha16: `{card.get('submission')}`")
    add(f"- 结果页: {card.get('result_url')}")
    add("")
    add("## 二、判定与证据链(原文零改动)")
    add("")
    for key, label in (("metadata", "被测元数据"), ("evaluation_evidence", "评测证据"),
                       ("three_state", "三态判定"), ("disposition", "处置")):
        if key in vd:
            add(f"### {label}")
            add("")
            add(vd[key])
            add("")
    add("## 三、流程时间线")
    add("")
    add("| 时点 | 环节 | 状态 |")
    add("|---|---|---|")
    for row in steps:
        cells = " | ".join(str(c) for c in row)
        add(f"| {cells} |" if len(row) == 3 else f"| {cells} | — |")
    add("")
    add("## 四、独立复算指引")
    add("")
    add("```bash")
    add(f"# 判读状态 API(卡面原始 JSON)")
    add(f"curl -s \"https://nautilus.social/api/judge_status?id={card.get('id')}\" | python -m json.tool")
    add("```")
    add("")
    add("复算免费开放;判据 sha16 锚定预注册口径。对判定有异议走复核通道(免费)。")
    add("")
    add("## 五、L2-ANALYST 槽位(人工判读员填写)")
    add("")
    add("<!-- TODO-L2-ANALYST: 归因分析 / 上下文背景 / 方法论评注 / 建议 -->")
    add("")
    add("**本段为空即报告未署名,不得收费交付。**")
    add("")
    add("---")
    add(f"*生成器 `{GENERATOR_VERSION}` · 判读岗 compass · 证据三层标注沿用卡面原文*")
    add("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("card_id")
    p.add_argument("-o", "--out", help="落盘路径(缺省 stdout)")
    p.add_argument("--base", default=DEFAULT_BASE)
    a = p.parse_args(argv)

    card = fetch_card(a.card_id, a.base)
    validate_card(card)
    now = datetime.now(CST).strftime("%Y-%m-%d %H:%M%z")
    rpt = render_report(card, generated_at=now)

    if a.out:
        out = Path(a.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rpt, encoding="utf-8")
        print(f"[OK] {a.out} ({len(rpt)}B)")
    else:
        sys.stdout.write(rpt)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        raise SystemExit(main())
    except ValueError as e:
        print(f"[REJECT] {e}", file=sys.stderr)
        raise SystemExit(2)
