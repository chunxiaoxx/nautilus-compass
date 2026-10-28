# -*- coding: utf-8 -*-
"""机审(Bench 重考层)纯函数单测:分级/红线/判定三色。"""
from ops.pr_review import classify_pr, redline_scan, verdict_color


# --- classify_pr(compass #1056 三档表对齐版) ---

def test_classify_ops_small_in_scope():
    assert classify_pr(["phase3/backend/engine/text_utils.py"], 20) == "ops"


def test_classify_policy_at_50_loc_boundary():
    """compass 表:操作 ≤50 行;51 行单文件=政策。"""
    assert classify_pr(["phase3/backend/engine/text_utils.py"], 50) == "ops"
    assert classify_pr(["phase3/backend/engine/text_utils.py"], 51) == "policy"


def test_classify_charter_on_safety_file():
    for f in ("phase3/soul/pause_check.py", "phase3/soul/failure_track.py",
              "phase3/soul/pr_gate.py", "phase3/soul/config.py",
              "phase3/soul/budget_gate.py", "phase3/backend/services/soul_pr_gate.py"):
        assert classify_pr([f], 5) == "charter", f


def test_classify_charter_on_protocol_docs():
    """组织协议正本=宪章域(compass 表新增)。"""
    assert classify_pr(["CLAUDE.md"], 3) == "charter"
    assert classify_pr(["docs/LOOP_PROTOCOL_V1_20260923.md"], 3) == "charter"


def test_classify_charter_on_out_of_scope():
    assert classify_pr(["docs/GOAL_STACK.md"], 10) == "charter"
    assert classify_pr(["utils/soul_loop_check.py"], 10) == "charter"


def test_classify_charter_on_400loc_or_6files():
    assert classify_pr(["phase3/soul/daemon.py"], 400) == "charter"
    files6 = [f"phase3/soul/m{i}.py" for i in range(6)]
    assert classify_pr(files6, 20) == "charter"


def test_classify_policy_on_big_or_multifile():
    assert classify_pr(["phase3/soul/daemon.py"], 200) == "policy"
    assert classify_pr(["phase3/soul/daemon.py", "phase3/soul/council.py"], 20) == "policy"


def test_classify_behavior_signal_upgrades_small_diff():
    """判据/门禁/鉴权类改动,不论行数升政策档(compass:语义风险非体量)。"""
    assert classify_pr(["phase3/backend/engine/checks.py"], 3) == "policy"
    assert classify_pr(["phase3/backend/engine/a2a_review.py"], 8) == "ops"


def test_classify_charter_on_empty():
    assert classify_pr([], 0) == "charter"


# --- redline_scan(只扫新增行) ---

def test_redline_hits_added_dangerous():
    diff = "+DROP TABLE users;\n+git push --force origin main\n"
    hits = redline_scan(diff)
    assert "DROP TABLE" in hits and "push --force" in hits


def test_redline_ignores_context_lines():
    # soul daemon 合法含 reset --hard(上下文行/删除行不算命中)
    diff = " _git(repo, \"reset\", \"--hard\")\n-old_line\n"
    assert redline_scan(diff) == []


def test_redline_clean_diff():
    assert redline_scan("+x = 1\n+print(x)\n") == []


# --- verdict_color ---

def test_verdict_green_all_pass():
    color, reasons = verdict_color(True, True, True, True, [], True)
    assert color == "GREEN" and reasons == []


def test_verdict_red_on_hard_failures():
    assert verdict_color(False, True, True, True, [], True)[0] == "RED"
    assert verdict_color(True, False, True, True, [], True)[0] == "RED"
    assert verdict_color(True, True, False, True, [], True)[0] == "RED"
    assert verdict_color(True, True, True, False, [], True)[0] == "RED"
    assert verdict_color(True, True, True, True, [], False)[0] == "RED"


def test_verdict_grey_on_unavailable_or_redline():
    assert verdict_color(True, None, True, True, [], True)[0] == "GREY"
    assert verdict_color(True, True, True, True, ["DROP TABLE"], True)[0] == "GREY"
