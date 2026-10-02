#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lint-report · narrative-drift guard(VerifyPack 第七命令)。

报告叙事层 ↔ 数据层一致性校验。预注册判据 L1-L6 见
docs/plans/NARRATIVE_DRIFT_LINT_CHARTER_20261002.md(只许加严)。

设计原则(立项档 §三):**不解析自然语言语义**。
- enum_set:散文 scope 内出现的受控词表词汇,必须 ⊆ 数据值域(hard)
- number :报告数字 == 数据重导出数字(hard;复合分数 n/d 支持)

用法:
  python -m verifypack lint --report R.md --assertions A.json --data D.json
exit 0=GREEN / 1=RED(逐条 PASS/FAIL 输出)。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


class LintError(ValueError):
    """断言文件本身非法(区别于报告 RED)。"""


def _get(node, seg: str):
    if isinstance(node, list):
        return [item.get(seg) for item in node if isinstance(item, dict)]
    if isinstance(node, dict):
        return node.get(seg)
    raise LintError(f"jsonpath 段 {seg!r} 越界:节点既非 dict 也非 list")


def extract_source(data, jpath: str):
    """支持 #/a/b(嵌套取值)与 #/a/*/b(列表字段→集合)。"""
    segs = [s for s in jpath.lstrip("#").strip("/").split("/") if s]
    node = data
    for seg in segs:
        if seg == "*":
            if isinstance(node, list):
                continue  # 透传:下一段由 _get 对每个元素取字段
            if isinstance(node, dict):
                node = list(node.values())
                continue
            raise LintError("'*' 作用于非容器节点")
        node = _get(node, seg)
    if isinstance(node, list):  # 保持多值;单值原样
        return node
    return node


def extract_scope(text: str, spec: dict) -> str:
    """scope 定位:heading 前缀 / anchor 锚点 / whole。"""
    if spec.get("whole"):
        return text
    lines = text.splitlines()
    if "heading" in spec:
        pref = spec["heading"]
        start = end = None
        for i, ln in enumerate(lines):
            if ln.startswith(pref):
                start = i + 1
            elif start is not None and ln.startswith("#"):
                end = i
                break
        if start is None:
            raise LintError(f"heading 未命中: {pref!r}")
        return "\n".join(lines[start:end if end is not None else len(lines)])
    if "anchor" in spec:
        m = re.search(rf"<!--\s*vp:assert\s+id={re.escape(spec['anchor'])}\s*-->", text)
        if not m:
            raise LintError(f"锚点缺失: {spec['anchor']!r}")
        nxt = re.search(r"<!--\s*vp:assert", text[m.end():])
        stop = m.end() + (nxt.start() if nxt else len(text) - m.end())
        return text[m.end():stop]
    raise LintError(f"scope 规格无法识别: {spec}")


def _fmt(value, fmt: str) -> str:
    if fmt == "int":
        return str(int(value))
    if fmt.startswith("round"):
        k = int(fmt[5:] or "0")
        return f"{round(float(value), k):.{k}f}"
    if fmt == "percent":
        return str(round(float(value) * 100, 1))
    raise LintError(f"未知 fmt: {fmt!r}")


def check_enum_set(a: dict, data, text: str) -> tuple[bool, str]:
    vals = extract_source(data, a["source"])
    domain = {str(v) for v in (vals if isinstance(vals, list) else [vals]) if v is not None}
    scope = extract_scope(text, a["prose_scope"])
    for pat in a.get("allow_patterns", []):  # 剥离豁免形态(key 标注/元数据括号),剩纯叙述
        scope = re.sub(pat, " ", scope)
    found = {v for v in a["vocab_all"] if re.search(rf"(?<![\w/]){re.escape(v)}(?![\w/])", scope)}
    extra = found - domain
    if extra:
        return False, f"受控词越域: 散文出现 {sorted(extra)},数据值域={sorted(domain)}"
    missing = set(a.get("expect", [])) - found
    if missing and a.get("severity") == "hard":
        return False, f"expect 词未出现于 scope: {sorted(missing)}"
    return True, f"值域={sorted(domain)},散文命中 {sorted(found)}"


def check_number(a: dict, data, text: str) -> tuple[bool, str]:
    scope = extract_scope(text, a["prose_scope"])
    if a.get("fmt") == "frac":
        num = extract_source(data, a["num"])
        den = extract_source(data, a["den"])
        want = f"{num}/{den}"
    else:
        v = extract_source(data, a["source"])
        want = _fmt(v, a.get("fmt", "identity"))
    if re.search(rf"(?<![\w.]){re.escape(want)}(?![\w])", scope):
        return True, f"数字 {want} 在 scope 复现"
    return False, f"数字 {want} 未在 scope 找到"


def run_lint(report: str, assertions_file: str, data_file: str) -> int:
    text = Path(report).read_text(encoding="utf-8")
    assertions = json.loads(Path(assertions_file).read_text(encoding="utf-8"))["assertions"]
    data = json.loads(Path(data_file).read_text(encoding="utf-8"))
    red = 0
    print(f"lint-report · {Path(report).name} × {len(assertions)} 断言")
    for a in assertions:
        try:
            ok, msg = (check_enum_set if a["kind"] == "enum_set" else check_number)(a, data, text)
        except LintError as e:
            ok, msg = False, f"断言规格错误: {e}"
        tag = "PASS" if ok else "FAIL"
        sev = a.get("severity", "hard")
        line = f"[{tag}] {a['id']}({a['kind']}{'/'+sev if sev!='hard' else ''}) {msg}"
        print(line)
        if not ok and sev != "soft":
            red += 1
    print(f"== {'RED' if red else 'GREEN'} ({red} hard fail) ==")
    return 1 if red else 0


def main(argv: list[str] | None = None) -> int:
    import argparse
    p = argparse.ArgumentParser(prog="verifypack-lint", description=__doc__)
    p.add_argument("--report", required=True)
    p.add_argument("--assertions", required=True)
    p.add_argument("--data", required=True)
    a = p.parse_args(argv)
    return run_lint(a.report, a.assertions, a.data)


if __name__ == "__main__":
    sys.exit(main())
