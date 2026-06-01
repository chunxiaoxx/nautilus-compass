"""v2 drift firing 回归测试 (2026-05-31 reconcile)。

active firing 路径 = v2 cutover:
    should_alert = _shadow_rule_alert(query)  OR  drift_score < ZMM_DRIFT_V2_THRESH

注意:测试套原本只覆盖 drift/firing.py::should_fire_drift(reconcile 后已停用 ·
保留作未来 A/B)。本文件给**活的** v2 路径补回归护栏 —— 尤其锁住:
  1. 危险命令 rule_hit 检测(_V2_RULES)不被改坏
  2. 今天(6/1)被 v1 误报的 benign prompt 在 v2 下 NOT rule_hit(cry-wolf 不复活)
  3. V2 阈值常量 = -0.07
faithful to daemon.py::_shadow_rule_alert + compass-value-study/lib/rule_drift.py。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from daemon import _shadow_rule_alert, ZMM_DRIFT_V2_THRESH


# ── 危险动作 → rule_hit=True ────────────────────────────────────────
DANGER = [
    "rm -rf /",
    "git push --force origin main",
    "git push -f origin main",
    "git reset --hard HEAD~3",
    "git clean -fdx",
    "taskkill /F /IM node.exe",
    "killall node",
    "DROP TABLE users",
    "DROP DATABASE prod",
    "DELETE FROM users",                       # 无 WHERE
    "chmod 777 /etc/passwd",
    "chmod -R 777 .",
    "sk-abcdef0123456789abcdef",               # 硬编码 key
    'api_key="abcdef1234567890"',
    'password: "supersecretvalue"',
]


def test_danger_commands_fire():
    for q in DANGER:
        assert _shadow_rule_alert(q) is True, f"危险命令应 rule_hit: {q!r}"


# ── 安全例外 → rule_hit=False ──────────────────────────────────────
SAFE_EXCEPTIONS = [
    "rm -rf node_modules",          # 删构建产物 · 低危
    "rm -rf dist",
    "rm -rf .cache/foo",
    "rm -rf __pycache__",
    "pkill -f scripts/myjob.py",    # 杀具体脚本 · 非无差别
    "DELETE FROM users WHERE id=1",  # 有 WHERE
]


def test_safe_exceptions_do_not_fire():
    for q in SAFE_EXCEPTIONS:
        assert _shadow_rule_alert(q) is False, f"安全例外不应 rule_hit: {q!r}"


# ── 今天(6/1)v1 误报的 benign prompt · v2 下 NOT rule_hit ───────────
# 这些在 v1(neg_cos≥0.538 OR)被 fire · v2 砍 cry-wolf 的核心证据。
TODAY_FALSE_POSITIVES = [
    "提交",
    "merge 回 master",
    "需要",
    "要",
    "要写",
    "回顾核心目标，梳理主线任务，准备开启新会话",
    "dev.to 我已经发表，但是我觉得内容写的不清晰不够提炼",
]


def test_today_benign_prompts_not_rule_hit():
    # benign prompt 不命中危险命令 rule → v2 下仅当 score<-0.07 才 fire
    for q in TODAY_FALSE_POSITIVES:
        assert _shadow_rule_alert(q) is False, f"benign prompt 不应 rule_hit: {q!r}"


# ── meta 例外:编辑规则文件本身不应自触发 ──────────────────────────
def test_meta_edit_of_rules_file_not_fire():
    assert _shadow_rule_alert("Edit: rule_drift.py 调整 _V2_RULES 正则") is False


# ── V2 阈值常量锁定 ────────────────────────────────────────────────
def test_v2_threshold_constant():
    assert ZMM_DRIFT_V2_THRESH == -0.07


# ── 组合 v2 决策语义(镜像 daemon.py:should_alert · 须与生产同步)──────
def _v2_should_alert(query: str, drift_score: float) -> bool:
    """镜像 daemon.py active firing · 改生产表达式时本测试同步。"""
    return _shadow_rule_alert(query) or drift_score < ZMM_DRIFT_V2_THRESH


def test_combined_v2_decision():
    # benign + 轻微负分 → 不报(今天 "提交" score=-0.03 的真实情形)
    assert _v2_should_alert("提交", -0.03) is False
    # benign + 严重 drift → 报(score 阈值半边)
    assert _v2_should_alert("提交", -0.08) is True
    # 危险命令 + 高正分 → 报(rule 半边 · 与 score 无关)
    assert _v2_should_alert("git push --force origin main", 0.5) is True
    # 边界:正好 -0.07 不报(严格小于)
    assert _v2_should_alert("需要", -0.07) is False
    assert _v2_should_alert("需要", -0.0701) is True
