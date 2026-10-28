"""Offline tests: g2b1 variant generator core (design 2026-08-28-variant-generation-design.md)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

import g2_b1_variant_gen as vg  # noqa: E402


def _row(repo="nautilus-core", n_sources=1, subject="fix(x): thing"):
    return {"schema_version": "g2-b1-task-v1",
            "buggy_commit": "a" * 40, "reference_fix_commit": "b" * 40,
            "subject": subject,
            "test_files": ["tests/test_x.py"],
            "source_files": [f"src/m{i}.py" for i in range(n_sources)],
            "repo_path": rf"C:\Users\chunx\Projects\{repo}"}


def test_select_templates_excludes_archived_v5_and_prefers_core():
    rows = [_row(repo="nautilus-v5.archived-20260827"),
            _row(repo="nautilus-v5"),
            _row(repo="nautilus-compass"),
            _row(n_sources=3),
            _row(subject="docs: update readme")]
    out = vg.select_templates(rows, limit=10)
    repos = [r["repo_path"].rsplit("\\", 1)[-1] for r in out]
    assert "nautilus-v5.archived-20260827" not in repos
    assert all(r["subject"].startswith("fix(") for r in out)
    # 单源文件优先排在多源文件前
    assert len(out[0]["source_files"]) <= len(out[-1]["source_files"])


def test_novelty_pure_rename_below_threshold():
    t = vg._diff_lines("-    if response.status == 429:\n+    if code in RATE:\n"
                       "+        raise EvidenceError(\"RATE_LIMITED\")\n")
    v = vg._diff_lines("-    if response.status == 9999:\n+    if code in LIMIT:\n"
                       "+        raise EvidenceError(\"LIMITED\")\n")
    assert vg.novelty_score(t, v) < 0.3


def test_novelty_structural_change_above_threshold():
    t = vg._diff_lines("-    if response.status == 429:\n"
                       "+    if code in RATE_CODES:\n+        raise EvidenceError(\"R\")\n")
    v = vg._diff_lines("-    total = a + b\n-    cache[key] = total\n"
                       "+    if key not in cache:\n+        cache[key] = compute(key)\n"
                       "+    return cache[key]\n+    log_access(key)\n")
    assert vg.novelty_score(t, v) >= 0.3


def test_variant_uid_naming():
    """变体 uid = 合成内容哈希(独立命名空间,不与模板 ref 前缀匹配域冲突)。"""
    u1 = vg.variant_task_uid("e49e8ade7849", op="1a", n=1)
    u2 = vg.variant_task_uid("e49e8ade7849", op="1a", n=2)
    u3 = vg.variant_task_uid("e49e8ade7849", op="1b", n=1)
    assert u1 == vg.variant_task_uid("e49e8ade7849", op="1a", n=1)  # 确定性
    assert len({u1, u2, u3}) == 3
    for u in (u1, u2, u3):
        h = u.split(":", 1)[1]
        assert len(h) == 12 and all(c in "0123456789abcdef" for c in h)
        assert not h.startswith("e49e8ade78")  # 不落在模板对账前缀域内


def test_make_variant_row_schema():
    tpl = _row()
    patch = "--- a/src/m0.py\n+++ b/src/m0.py\n@@ -1 +1 @@\n-x = 1\n+x = 2\n"
    row = vg.make_variant_row(tpl, op="1a", n=1, patch=patch)
    assert row["schema_version"] == "g2-b1-task-v1"
    assert row["task_uid"] == vg.variant_task_uid("b" * 10, "1a", 1)
    assert row["variant_of"] == "g2b1:" + "b" * 12
    assert row["variant_op"] == "1a"
    assert row["template_task_uid"] == "g2b1:" + "b" * 12
    assert row["variant_patch"] == patch
    # 变体起点 = 模板 fix;合成 bug 由 patch 表达(无合成 commit)
    assert row["buggy_commit"] == row["reference_fix_commit"]
    assert row["repo_path"] == tpl["repo_path"]
    assert "[variant:1a]" in row["subject"]


# ---------- OP-1 LLM 提案 + 变体双门 ----------

TEMPLATE_DIFF = """--- a/src/m0.py
+++ b/src/m0.py
@@ -10,3 +10,3 @@
-    if response.status == 429:
+    if code in RATE_CODES:
         raise EvidenceError("RATE_LIMITED")
"""

GOOD_PATCH = "--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-x = 2\n+x = 1\n"
NOT_RED_PATCH = "--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-x = 2\n+x = 2.0\n"


def _fixture_repo(tmp_path):
    import subprocess
    r = tmp_path / "repo"
    r.mkdir()

    def sh(*a):
        subprocess.run(a, cwd=r, check=True, capture_output=True)

    sh("git", "init", "-q")
    sh("git", "config", "user.email", "t@t")
    sh("git", "config", "user.name", "t")
    (r / "app.py").write_text("x = 1\n", encoding="utf-8")
    sh("git", "add", "-A")
    sh("git", "commit", "-qm", "buggy")
    (r / "app.py").write_text("x = 2\n", encoding="utf-8")
    (r / "tests").mkdir()
    (r / "tests" / "test_app.py").write_text(
        "from app import x\n\ndef test_two():\n    assert x == 2\n",
        encoding="utf-8")
    sh("git", "add", "-A")
    sh("git", "commit", "-qm", "fix")
    rev = subprocess.run(["git", "rev-parse", "HEAD"], cwd=r,
                         capture_output=True, text=True).stdout.strip()
    return r, rev


def test_propose_patch_prompt_and_extraction():
    captured = {}

    def fake_completer(prompt):
        captured["prompt"] = prompt
        return f"```diff\n{GOOD_PATCH}```"

    patch = vg.propose_patch(fake_completer, TEMPLATE_DIFF,
                             sources=["app.py"], op="1a")
    assert patch == GOOD_PATCH
    assert "RATE_CODES" in captured["prompt"]      # 模板 diff 在 prompt 里
    assert "1a" in captured["prompt"]


def test_propose_patch_rejects_non_diff():
    assert vg.propose_patch(lambda p: "I cannot do that.", TEMPLATE_DIFF,
                            sources=["app.py"], op="1a") is None


def test_propose_patch_accepts_executor_completer_dict():
    """executor 的 completer 返回 {content,...} dict,不是 str。"""
    patch = vg.propose_patch(
        lambda p: {"content": f"```diff\n{GOOD_PATCH}```"},
        TEMPLATE_DIFF, sources=["app.py"], op="1a")
    assert patch == GOOD_PATCH


def test_propose_patch_unwraps_json_artifact():
    """SYSTEM_PROMPT 使模型回 JSON artifact——unified_diff 字段解包(8/28 pilot 实测)。"""
    artifact = json.dumps({"artifact_version": "g2-b1-candidate-v1",
                           "summary_code": "invert_guard",
                           "unified_diff": GOOD_PATCH})
    patch = vg.propose_patch(lambda p: {"content": artifact},
                             TEMPLATE_DIFF, sources=["app.py"], op="1a")
    assert patch == GOOD_PATCH


def test_verify_variant_accepts_red_and_rejects_not_red(tmp_path):
    repo, fix = _fixture_repo(tmp_path)
    row = {"reference_fix_commit": fix, "variant_patch": GOOD_PATCH,
           "test_files": ["tests/test_app.py"]}
    gate = vg.verify_variant(str(repo), row)
    assert gate["gate_a_starter_fails"] is True
    assert gate["gate_b_fix_passes"] is True
    assert gate["passed"] is True

    row_nr = {"reference_fix_commit": fix, "variant_patch": NOT_RED_PATCH,
              "test_files": ["tests/test_app.py"]}
    assert vg.verify_variant(str(repo), row_nr)["passed"] is False
