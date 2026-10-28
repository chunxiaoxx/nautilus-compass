"""判材组装 v2 三修(663 三缺陷):tests 截断/import 闭包/expected_output_path。"""
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
PHASE3 = BACKEND.parent
for p in (str(PHASE3), str(BACKEND)):
    if p not in sys.path:
        sys.path.insert(0, p)

from ops.build_judge_pack import parse_desc, _import_closure, build

DESC = """[三臂对照·题1/3 · 72h 交卷]
任务:修复下面的 starter 代码,使提供的测试全部通过。
交付:完整修复后文件(或 unified diff)。

== starter 文件: proof/local_outcomes.py (当前含 bug 版) ==
\"\"\"Path B docstring\"\"\"
from proof.l1_grouper_compat import normalize

def f(x):
    return normalize(x)

== 测试文件: tests/test_local_outcomes.py (考卷·以本测试为准) ==
from proof.local_outcomes import f

def test_f():
    assert f(1) == 1

== 仓库上下文 ==
本说明块不应进入 tests 段(663 缺陷①)。"""


def test_parse_tests_truncated_before_context_block():
    t = parse_desc(DESC)
    assert "仓库上下文" not in t["tests"], "tests 段吞了说明块(缺陷①未修)"
    assert "test_f" in t["tests"]
    assert t["starter_path"] == "proof/local_outcomes.py"
    assert t["expected_output_path"] == t["starter_path"]  # 缺陷②
    # 缺陷③真根因:上下文块(依赖材料)必须随包,不能丢
    assert "仓库上下文" in t.get("context", ""), "上下文块被丢=判卷方缺依赖(634 NC 根因)"


def test_import_closure_real_repo_modules():
    # 引真实仓内模块(phase3 结构)→ 随包;虚构/标准库落空不报错
    sup = _import_closure("from models.org_mailbox import OrgMailbox\nimport os", "")
    assert any("models/org_mailbox" in k for k in sup), f"真实仓依赖漏: {list(sup)}"
    sup2 = _import_closure("import os\nimport nonexistent_zzz", "")
    assert all("nonexistent" not in k for k in sup2)


def test_build_blinds_arm_names(tmp_path):
    d = tmp_path / "local_outcomes.diff"
    d.write_text("--- a/proof/local_outcomes.py\n+++ b/proof/local_outcomes.py\n", encoding="utf-8")
    pack = build([{"task_uid": "q1-prime", "description": DESC,
                   "deliverable_path": str(d)}], {"prime": "A"})
    p = pack[0]
    assert p["task_uid"] == "q1-ARM-A"
    assert "prime" not in json.dumps(pack) if (json := __import__("json")) else True
    assert p["triad"]["expected_output_path"]
