# -*- coding: utf-8 -*-
"""判材组装器 v2(盲化 judge_pack 构建)——634 包三缺陷修复版(9/21)。

compass 663 三缺陷:
① tests 尾粘连说明块(「== 仓库上下文 ==」等)——parse 截断到下一 == 标记;
② 交付文件名与 starter_path 不同名——triad 加 expected_output_path;
③ q3 缺被导入依赖——随包 **import 闭包**(starter/tests 的仓内被导入文件)。

用法:本地跑(python ops/build_judge_pack.py <pack.json> <out.json>),
pack.json={task_uid: description}(云端 dispatch 导出);交付文件由调用方
指定(如 worker 本地留档)。输出盲化包(ARM 字母映射由调用方传)。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]  # backend 仓根(题目 import 均指此结构)


def parse_desc(raw: str) -> dict:
    """三元组解析 v2:tests 截断(缺陷①)+ 上下文块保留(缺陷③真根因)。

    「== 仓库上下文 ==」等 tests 之后的块=依赖文件材料(考题自包含),
    必须随包给判卷方——634 包 q1/q3 NC 即因丢弃此块致依赖缺失。"""
    m1 = re.search(r"== starter 文件: (\S+?)[ =]", raw)
    m2 = re.search(r"== 测试文件: (\S+?)[ =]", raw)
    head = raw.split("== starter")[0].strip()
    st = re.search(r"== starter 文件: \S+.*?==\n(.*?)\n== 测试文件:", raw, re.S)
    # tests 段:到下一个 == 标记截止(不再吞说明块);标记起的内容进 context
    tm = re.search(r"== 测试文件: \S+.*?==\n(.*?)(?=\n== [^=]+ ==|\Z)", raw, re.S)
    cm = re.search(r"\n(== [^=]+ ==.*)", raw, re.S)  # tests 后首块起全文
    starter_path = m1.group(1) if m1 else "?"
    return {"instruction": head,
            "starter_path": starter_path,
            "starter": st.group(1).strip() if st else "",
            "test_path": m2.group(1) if m2 else "?",
            "tests": tm.group(1).strip() if tm else "",
            "context": cm.group(1).strip() if (cm and tm) else "",
            # 缺陷②:判卷方与 worker 对齐交付文件名
            "expected_output_path": starter_path}


def _import_closure(starter: str, tests: str) -> dict[str, str]:
    """缺陷③:解析 starter/tests 的仓内 import,随包支持文件。

    只收 REPO 下存在的 .py(相对 import 转/路径);第三方/标准库自然落空。"""
    mods: set[str] = set()
    for src in (starter, tests):
        for m in re.finditer(r"^\s*(?:from|import)\s+([\w.]+)", src, re.M):
            mods.add(m.group(1))
    out: dict[str, str] = {}
    for mod in sorted(mods):
        rel = mod.replace(".", "/")
        for cand in (rel + ".py", rel + "/__init__.py"):
            p = REPO / cand
            if p.is_file():
                try:
                    out[cand] = p.read_text(encoding="utf-8", errors="replace")[:60000]
                except OSError:
                    pass
                break
    return out


def build(entries: list[dict], arm_map: dict[str, str]) -> dict:
    """entries=[{task_uid, description, deliverable_path}] → 盲化包。"""
    pack = []
    for e in entries:
        q, arm = e["task_uid"].rsplit("-", 1)
        letter = arm_map[arm]
        triad = parse_desc(e["description"])
        deliverable = Path(e["deliverable_path"]).read_text(encoding="utf-8",
                                                            errors="replace")
        sup = _import_closure(triad["starter"], triad["tests"])
        pack.append({
            "task_uid": f"{q}-ARM-{letter}", "arm": f"ARM-{letter}",
            "triad": triad,
            "supporting_files": sup,
            "submitter_output": deliverable[:30000],
            "output_format": "diff" if e["deliverable_path"].endswith(".diff") else "full-file",
            "metrics": {"deliverable_chars": len(deliverable),
                        "supporting_files": len(sup)},
            "source": "build_judge_pack v2 (import closure + expected_output_path)",
        })
    def blind(o):
        if isinstance(o, dict):
            return {k: blind(v) for k, v in o.items()}
        if isinstance(o, list):
            return [blind(x) for x in o]
        if isinstance(o, str):
            for full in arm_map:
                o = re.sub(rf"\b{re.escape(full)}(-\w+)?\b", "ARM", o)
            return o
        return o
    return blind(pack)


if __name__ == "__main__":
    pack_json, out_json = sys.argv[1], sys.argv[2]
    arm_map = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {"prime": "A", "v7": "B"}
    desc = json.load(open(pack_json, encoding="utf-8"))
    entries = json.load(open(sys.argv[4], encoding="utf-8")) if len(sys.argv) > 4 else []
    raise SystemExit(print(json.dumps(build(entries, arm_map), ensure_ascii=False)[:80]))