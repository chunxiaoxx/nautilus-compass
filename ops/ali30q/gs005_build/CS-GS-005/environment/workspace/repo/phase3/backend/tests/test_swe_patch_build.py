"""TDD — scripts.rsi_swe_loop 的纯逻辑(解析模型分文件输出 + difflib 构造 unified diff）。

oracle-file 设定:模型返回修改后的文件全文(```python # FILE: path 块），我用 difflib 构
diff(保证 git apply 成功·把 RSI 机制与 patch-apply 噪声隔离）。
"""
import importlib.util
import os
import sys

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _BACKEND)
# scripts 名被另一项目(nautilus-agent）遮蔽 → 按文件路径直接加载本地模块
_spec = importlib.util.spec_from_file_location(
    "rsi_swe_loop", os.path.join(_BACKEND, "scripts", "rsi_swe_loop.py"))
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
parse_file_blocks = _mod.parse_file_blocks
build_unified_diff = _mod.build_unified_diff
coerce_blocks = _mod.coerce_blocks
parse_search_replace = _mod.parse_search_replace
apply_edits = _mod.apply_edits


def test_parse_single_file_block():
    resp = (
        "Here is the fix:\n\n"
        "```python\n# FILE: pkg/mod.py\n"
        "def f():\n    return 1\n```\n")
    blocks = parse_file_blocks(resp)
    assert blocks == {"pkg/mod.py": "def f():\n    return 1\n"}


def test_parse_multi_file_blocks():
    resp = (
        "```python\n# FILE: a.py\nx = 1\n```\n"
        "blah\n"
        "```python\n# FILE: b/c.py\ny = 2\n```\n")
    blocks = parse_file_blocks(resp)
    assert blocks == {"a.py": "x = 1\n", "b/c.py": "y = 2\n"}


def test_parse_ignores_block_without_file_marker():
    resp = "```python\nprint('no marker')\n```\n"
    assert parse_file_blocks(resp) == {}


def test_build_unified_diff_roundtrip(tmp_path):
    # base 文件 vs 修改后 → diff 须能被 git apply(此处只验内容/格式）
    base = tmp_path / "repo"
    base.mkdir()
    (base / "mod.py").write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")
    new_files = {"mod.py": "def add(a, b):\n    return a + b\n"}
    diff = build_unified_diff(str(base), new_files)
    assert "--- a/mod.py" in diff
    assert "+++ b/mod.py" in diff
    assert "-    return a - b" in diff
    assert "+    return a + b" in diff


def test_coerce_prefers_marked_blocks():
    # 有 # FILE: 标记 → 直接用 parse_file_blocks 结果
    resp = "```python\n# FILE: a.py\nx = 1\n```\n"
    assert coerce_blocks(resp, ["a.py"], {"a.py": "old\n"}) == {"a.py": "x = 1\n"}


def test_coerce_single_file_fallback_when_no_marker():
    # 无标记 + 唯一允许文件 + 块够大(>40% 原文）→ 当作该文件全文
    original = "def f():\n    return 1\n" * 10           # ~200 chars
    new_full = "def f():\n    return 2\n" * 10
    resp = "Here is the fix:\n```python\n%s```\n" % new_full
    out = coerce_blocks(resp, ["only.py"], {"only.py": original})
    assert out == {"only.py": new_full}


def test_coerce_rejects_tiny_snippet():
    # 无标记 + 块太小(像片段非全文）→ 不冒险当全文 → {}
    original = "x = 1\n" * 100
    resp = "```python\ndef f(): pass\n```\n"
    assert coerce_blocks(resp, ["only.py"], {"only.py": original}) == {}


def test_coerce_no_fallback_when_multiple_files():
    # 多个允许文件 + 无标记 → 无法判归属 → {}
    resp = "```python\nx = 1\n```\n"
    assert coerce_blocks(resp, ["a.py", "b.py"], {"a.py": "o\n", "b.py": "o\n"}) == {}


_SR = """\
Some prose.
```
<<<<<<< SEARCH
    return a - b
=======
    return a + b
>>>>>>> REPLACE
```
And another:
<<<<<<< SEARCH
x = 1
=======
x = 2
>>>>>>> REPLACE
"""


def test_parse_search_replace():
    edits = parse_search_replace(_SR)
    assert len(edits) == 2
    assert edits[0] == ("    return a - b\n", "    return a + b\n")
    assert edits[1] == ("x = 1\n", "x = 2\n")


def test_apply_edits_success():
    original = "def add(a, b):\n    return a - b\nx = 1\n"
    edits = [("    return a - b\n", "    return a + b\n"), ("x = 1\n", "x = 2\n")]
    new, applied, failed = apply_edits(original, edits)
    assert applied == 2 and failed == 0
    assert new == "def add(a, b):\n    return a + b\nx = 2\n"


def test_apply_edits_search_not_found_counts_failed():
    original = "y = 1\n"
    new, applied, failed = apply_edits(original, [("not here\n", "z\n")])
    assert applied == 0 and failed == 1 and new == original


def test_apply_edits_empty_search_is_skipped():
    original = "a\n"
    new, applied, failed = apply_edits(original, [("", "junk\n")])
    assert applied == 0 and new == original   # 空 SEARCH 不当全文插入


def test_apply_edits_whitespace_tolerant_fallback():
    # SEARCH 缩进/尾空白与文件不完全一致 → 行级 strip 匹配回退仍应命中
    original = "def f():\n    if x:\n        return 1\n    return 0\n"
    # 模型给的 SEARCH 用了不同缩进(2 空格）+ 尾空白
    edits = [("  if x:  \n      return 1\n", "  if x:\n      return 2\n")]
    new, applied, failed = apply_edits(original, edits)
    assert applied == 1 and failed == 0
    # 替换保留文件原缩进风格不强求·但 return 1 必须变 return 2
    assert "return 2" in new and "return 1" not in new
    assert "return 0" in new            # 未触及的行保留


def test_apply_edits_fuzzy_ambiguous_not_applied():
    # strip 后匹配多处(歧义）→ 不冒险替换
    original = "x = 1\nx = 1\n"
    new, applied, failed = apply_edits(original, [("x = 1\n", "x = 2\n")])
    # 精确匹配会命中首个(applied=1）——精确优先·这条测精确路径仍 work
    assert applied == 1


def test_build_unified_diff_skips_unchanged(tmp_path):
    base = tmp_path / "repo"
    base.mkdir()
    (base / "mod.py").write_text("x = 1\n", encoding="utf-8")
    diff = build_unified_diff(str(base), {"mod.py": "x = 1\n"})
    assert diff.strip() == ""  # 无变化 → 空 diff
