"""fde_bench_runner 纯 helper 单测(产出代码抽取/围栏剥离/verifier 取出).

effect 部分(子进程跑 bench_eval)不单测; 这些纯函数证抽取逻辑.
"""
from __future__ import annotations

import json

from services.fde_bench_runner import (
    strip_code_fence,
    extract_solution_code,
    verifier_source,
    extract_swe_patch,
    coerce_swe_patch_from_full_file,
)

_ORIG = "def f(x):\n    return x\n\ndef g(y):\n    return y + 1\n"
_FIXED = "def f(x):\n    return x\n\ndef g(y):\n    return y + 2\n"  # g 改 +1→+2


def test_strip_code_fence_python():
    s = "好的, 修复如下:\n```python\ndef f():\n    return 1\n```\n说明..."
    assert strip_code_fence(s) == "def f():\n    return 1"


def test_strip_code_fence_no_fence():
    assert strip_code_fence("def f():\n    return 1\n") == "def f():\n    return 1"


def test_extract_solution_from_dict_code():
    assert extract_solution_code({"code": "def g(): pass"}) == "def g(): pass"


def test_extract_solution_from_dict_text_with_fence():
    out = {"text": "```py\nx=1\n```"}
    assert extract_solution_code(out) == "x=1"


def test_extract_solution_from_str():
    assert extract_solution_code("def h(): pass") == "def h(): pass"


def test_verifier_source_from_spec():
    task = {"description": json.dumps({"fde_class": 3, "verifier_inline": "print('{}')"})}
    assert verifier_source(task) == "print('{}')"


def test_verifier_source_absent():
    task = {"description": json.dumps({"fde_class": 3})}
    assert verifier_source(task) is None


# ── C(6/21):整文件 → coerce 成 unified diff(防 producer 格式不一致)──

def _spec(orig=_ORIG, path="m.py", paths=None):
    return {"original_files": {path: orig}, "edit_paths": paths if paths is not None else [path]}


def test_coerce_full_file_single_editpath_makes_diff():
    """kairos 整文件产出 + 内嵌原文 → git unified diff(含 diff --git + 改动行)。"""
    out = {"code": "v5-daemon-fde-produce", "text": "```python\n" + _FIXED + "```"}
    patch = coerce_swe_patch_from_full_file(out, _spec())
    assert patch.startswith("diff --git a/m.py b/m.py")
    assert "-    return y + 1" in patch and "+    return y + 2" in patch
    # 且 extract_swe_patch 认可 coerce 出的结果(下游 verify 能用)
    assert extract_swe_patch({"text": patch}) != ""


def test_coerce_strips_path_header_comment():
    """产出首行 "# m.py" 文件头注释被剥(不污染 diff)。"""
    out = {"text": "# m.py\n" + _FIXED}
    patch = coerce_swe_patch_from_full_file(out, _spec())
    assert "+# m.py" not in patch          # 头注释没被当成新增行
    assert "+    return y + 2" in patch


def test_coerce_empty_when_multi_editpath():
    """多 edit_path 无法把整文件对应到具体文件 → 保守返 ""。"""
    out = {"text": _FIXED}
    assert coerce_swe_patch_from_full_file(out, _spec(paths=["m.py", "n.py"])) == ""


def test_coerce_empty_when_no_change():
    """产出 == 原文(无修复)→ ""。"""
    out = {"text": _ORIG}
    assert coerce_swe_patch_from_full_file(out, _spec()) == ""


def test_coerce_empty_when_missing_original():
    """spec 无 original_files → ""(不瞎编 diff)。"""
    out = {"text": _FIXED}
    assert coerce_swe_patch_from_full_file(out, {"edit_paths": ["m.py"]}) == ""


def test_coerce_not_needed_when_already_diff():
    """producer 直给 diff 时 extract_swe_patch 已认·coerce 是兜底不是替代。"""
    real_diff = "diff --git a/m.py b/m.py\n--- a/m.py\n+++ b/m.py\n@@ -1 +1 @@\n-a\n+b\n"
    assert extract_swe_patch({"text": real_diff}) != ""
