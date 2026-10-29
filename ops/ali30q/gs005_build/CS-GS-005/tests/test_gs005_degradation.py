# -*- coding: utf-8 -*-
"""CS-GS-005 判分 UT · 坑面 = 配置漂移的静默降级 / 降级必须可见

锚点(真实事故): nautilus-v5 helix_v7 bridge 5/18 起引用 nautilus_core.helix_chain 的
PgStorage/HelixChain.a_close_breath_pair,而 core 仓该实现 110+ 天不存在(defb148 10/4 才补)——
ImportError 被软捕获 → 仅一行 warning → helix_v7=None → 消费侧裸调 AttributeError 再被
soft except 吞掉 → 链上账静默丢失,无任何结构化降级痕迹。

三条 UT 全部 targets_badpattern(锚 F03 静默降级族):
  UT-1  bridge 初始化降级必须结构化可见(报告对象 + degraded 标志)
  UT-2  消费侧不得静默吞 AttributeError(降级必须计数留痕 + 显式跳过语义)
  UT-3  降级后链后端标记必须如实(file_fallback 不得伪装主通路)

10/29 扩条(R198 缺口档排期第 1 项,UT 3→21):UT-4~UT-17 继续 targets_badpattern
(对 FM-1~4 逐面加密),UT-18~UT-21 独立锚 focus_points
(降级可见性/启动自检/配置校验/fallback 等价性证伪)。
坑版挂点逐条核实(坑版 = report/count/backend 四件全缺 + 消费侧返回 None +
无 DSN 场景连 warning 都没有),金标过点 = GP-1~GP-4 可观测行为。
"""
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1] / "workspace" / "repo"
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from v5_bridge.helix_bridge import BridgeConfig, HelixBridgeHost  # noqa: E402

_LEFT = {"act_summary": "unit-test action", "extra": "ignored"}
_RIGHT = {"cycle": 1, "introspect": "i" * 10, "learn": "l" * 10,
          "evolve": "e" * 5, "remember": "r" * 5, "witness_voice": "w" * 5}
_BAD_DSN = "postgres://user:oldpw@127.0.0.1:1/wrongdb"
_EMPTY_ENV = {"V5_POSTGRES_DSN": ""}


def _init_host(caplog, dsn=_BAD_DSN):
    """构造依赖不可用场景(坏 DSN → 连接/导入必失败),返回宿主。"""
    with caplog.at_level(logging.DEBUG, logger="v5.helix_bridge"):
        return HelixBridgeHost(BridgeConfig(agent_id="ut-agent", postgres_dsn=dsn))


def _bare_host(dsn=_BAD_DSN, env=None):
    """不带 caplog 的纯构造(日志无关断言用)。"""
    return HelixBridgeHost(
        BridgeConfig(agent_id="ut-agent", postgres_dsn=dsn, env=env or _EMPTY_ENV))


def _call(host, cycle=1):
    return asyncio.run(host.close_breath_pair(cycle, dict(_LEFT), dict(_RIGHT)))


def test_ut1_bridge_degradation_must_be_structurally_visible(caplog):
    """UT-1(锚半边1 坑面): 依赖缺失/配置失效导致的降级必须结构化可见。

    金标要求: 初始化降级后,宿主必须携带结构化降级报告(对象/字段,非仅散日志),
    且 degraded 标志为 True——只打一行 warning 然后装作没事 = 坑版行为 = FAIL。
    """
    host = _init_host(caplog)
    records = [r for r in caplog.records
               if "helix" in r.getMessage().lower() or "fallback" in r.getMessage().lower()]
    assert len(records) > 0, "降级发生时必须留日志痕迹(完全静默 = 更差)"
    # 结构化可见: 散日志不算数,必须有机器可读的降级报告
    assert getattr(host, "degradation_report", None), (
        "初始化降级后缺少结构化 degradation_report(静默降级 = 坑面复刻)"
    )
    assert getattr(host, "degraded", False) is True, "degraded 标志必须显式置位"


def test_ut2_consumer_side_must_not_silently_swallow(caplog):
    """UT-2(锚消费侧坑面): 链不可用时消费侧必须显式跳过留痕,不得裸调+吞。"""
    host = _init_host(caplog)
    outcome = asyncio.run(
        host.close_breath_pair(1, dict(_LEFT), dict(_RIGHT)))
    # 降级次数必须被计数(坑版: AttributeError 被软吞,零计数零痕迹)
    assert getattr(host, "degradation_count", 0) >= 1, (
        "消费侧降级未被计数留痕(silent swallow = 坑面复刻)"
    )
    # 返回必须显式声明未封链且原因可读(坑版: 返回 None,调用方无从分辨)
    assert isinstance(outcome, dict), "降级 outcome 必须是可判读结构,不得裸 None"
    assert outcome.get("sealed") is False
    assert outcome.get("degraded") is True and outcome.get("reason")


def test_ut3_degraded_backend_must_not_masquerade(caplog):
    """UT-3(锚等价性证伪): 降级后链后端标记必须如实,不得伪装主通路成功。"""
    host = _init_host(caplog)
    backend = getattr(host, "chain_backend", None)
    assert backend is not None, "必须显式暴露链后端标记"
    assert backend != "pg" or host.helix_v7 is not None, (
        "helix_v7 不可用时 chain_backend 不得标记为 pg(fallback 伪装主通路)"
    )
    assert backend == "file_fallback", f"降级态后端应如实标记 file_fallback,实际={backend!r}"


# ---------------------------------------------------------------------------
# UT-4 ~ UT-17 · targets_badpattern 加密面(FM-1~4 逐面对应)
# ---------------------------------------------------------------------------

def test_ut4_degradation_report_must_be_machine_readable(caplog):
    """UT-4(锚 FM-2): 降级报告必须是含四键的机器可读 dict。

    金标: degradation_report = {stage, reason, backend, at, ...}。
    坑版: 散日志一行,无报告对象 → FAIL。
    """
    host = _init_host(caplog)
    report = getattr(host, "degradation_report", None)
    assert isinstance(report, dict), "降级报告必须是机器可读 dict(仅散日志 = 坑面复刻)"
    for key in ("stage", "reason", "backend", "at"):
        assert key in report, f"降级报告缺字段 {key!r}(报告不完整 = 不可判读)"


def test_ut5_report_stage_and_reason_nonempty(caplog):
    """UT-5(锚 FM-1): 报告必须携带降级阶段与原因,且为非空字符串。"""
    host = _init_host(caplog)
    report = getattr(host, "degradation_report", None)
    assert isinstance(report, dict), "缺少结构化降级报告"
    assert report.get("stage") == "init", (
        f"初始化期降级 stage 应为 'init',实际={report.get('stage')!r}")
    assert isinstance(report.get("reason"), str) and report["reason"], (
        "reason 必须是非空字符串(空洞原因 = 不可判读降级)")


def test_ut6_degraded_flag_backend_consistency(caplog):
    """UT-6(锚 FM-2): degraded 置位时后端标记不得仍宣称主通路 pg。"""
    host = _init_host(caplog)
    assert getattr(host, "degraded", False) is True, "降级标志未置位"
    assert getattr(host, "chain_backend", None) != "pg", (
        "degraded=True 而 chain_backend='pg':标志与后端互相矛盾(伪装)")


def test_ut7_none_chain_never_marked_pg(caplog):
    """UT-7(锚 FM-2/FM-3 启动自检不变式): 链对象缺失时后端必须显式 file_fallback。"""
    host = _init_host(caplog)
    assert host.helix_v7 is None, "坏 DSN 场景下链对象必须为 None(前提校验)"
    assert getattr(host, "chain_backend", None) == "file_fallback", (
        "helix_v7 为 None 时 chain_backend 必须显式标记 file_fallback"
        "(留 None 或 pg 均为伪装/不可观测)")


def test_ut8_init_degradation_must_be_counted(caplog):
    """UT-8(锚 FM-1): 初始化期降级必须计入降级账(坑版零计数)。"""
    host = _init_host(caplog)
    count = getattr(host, "degradation_count", 0)
    assert isinstance(count, int) and count >= 1, (
        "初始化降级未计入 degradation_count(降级账缺失 = 静默复刻)")


def test_ut9_degradation_log_machine_discernible(caplog):
    """UT-9(锚 FM-2): 降级日志必须含机器可辨的降级字样(纯 init failed 不算)。"""
    _init_host(caplog)
    degraded_lines = [r for r in caplog.records
                      if "degrad" in r.getMessage().lower()]
    assert degraded_lines, (
        "日志中无任何降级可辨字样(degraded/DEGRADED):一行 init failed "
        "与正常软失败无法区分 = 降级不可见")


def test_ut10_no_dsn_is_degradation_not_silence(caplog):
    """UT-10(锚 FM-2 配置校验): 无 DSN 必须显式降级,不得完全静默。

    坑版此处连 warning 都没有(config 空时直接跳过装配置)。
    """
    with caplog.at_level(logging.DEBUG, logger="v5.helix_bridge"):
        host = HelixBridgeHost(
            BridgeConfig(agent_id="ut-agent", postgres_dsn=None, env=dict(_EMPTY_ENV)))
    assert getattr(host, "degraded", False) is True, (
        "无 DSN 未标记 degraded(配置缺失被静默吞 = 坑面复刻)")


def test_ut11_no_dsn_reason_discernible(caplog):
    """UT-11(锚 FM-2): 无 DSN 降级原因必须可判读(no_dsn_configured 语义)。"""
    with caplog.at_level(logging.DEBUG, logger="v5.helix_bridge"):
        host = HelixBridgeHost(
            BridgeConfig(agent_id="ut-agent", postgres_dsn=None, env=dict(_EMPTY_ENV)))
    report = getattr(host, "degradation_report", None)
    assert isinstance(report, dict) and report.get("reason"), (
        "无 DSN 降级缺少可判读 reason(静默或空因 = 坑面复刻)")


def test_ut12_env_fallback_path_equally_visible(caplog):
    """UT-12(锚 FM-2 fallback 等价性证伪): env 回落路径与直传 DSN 路径同等可见。

    config 不传 DSN、env 给坏值时,降级同样必须结构化显式——
    回落路径静默 = 双通道降级只有单通道可见。
    """
    with caplog.at_level(logging.DEBUG, logger="v5.helix_bridge"):
        host = HelixBridgeHost(BridgeConfig(
            agent_id="ut-agent", postgres_dsn=None,
            env={"V5_POSTGRES_DSN": _BAD_DSN}))
    assert getattr(host, "degraded", False) is True, "env 回落路径降级未标记"
    assert isinstance(getattr(host, "degradation_report", None), dict), (
        "env 回落路径缺少结构化降级报告")


def test_ut13_degradation_count_persists_across_calls(caplog):
    """UT-13(锚 FM-1 计数贯穿): 消费侧每次降级调用都必须累加计数。"""
    host = _init_host(caplog)
    base = getattr(host, "degradation_count", 0)
    for cycle in (1, 2, 3):
        _call(host, cycle)
    assert getattr(host, "degradation_count", 0) >= base + 3, (
        "三次消费调用未逐一计数(降级账不贯穿 = 事后补账/静默复刻)")


def test_ut14_outcome_discernible_every_call(caplog):
    """UT-14(锚 FM-1): 每次降级调用的 outcome 都必须是可判读结构。"""
    host = _init_host(caplog)
    for cycle in (1, 2, 3):
        outcome = _call(host, cycle)
        assert isinstance(outcome, dict), f"cycle={cycle} outcome 非结构(裸 None = 坑面)"
        assert outcome.get("sealed") is False, "降级调用不得宣称 sealed"
        assert outcome.get("degraded") is True, "降级 outcome 必须显式声明 degraded"
        assert outcome.get("reason"), "降级 outcome 必须携带原因"


def test_ut15_degraded_outcome_never_carries_forge_products(caplog):
    """UT-15(锚 FM-2 伪装面): 降级 outcome 不得携带伪造的封链产物。

    sealed=False 却给出 left/right hash = 用 fallback 伪装主通路产物。
    """
    host = _init_host(caplog)
    outcome = _call(host, 1)
    assert isinstance(outcome, dict), "outcome 非结构"
    assert outcome.get("sealed") is False
    assert "left" not in outcome and "right" not in outcome, (
        "降级 outcome 携带 left/right 产物 = 伪造封链痕迹")


def test_ut16_guard_must_predate_first_call(caplog):
    """UT-16(锚 FM-4 时序): 防护必须在初始化期生效,不得等首次消费才补救。

    构造完成后、任何 close_breath_pair 调用之前,降级三件套必须已就位。
    """
    host = _init_host(caplog)
    assert getattr(host, "degraded", False) is True, "初始化后 degraded 未置位(时序错)"
    assert getattr(host, "degradation_count", 0) >= 1, "初始化后降级账为空(时序错)"
    assert getattr(host, "degradation_report", None) is not None, (
        "初始化后降级报告缺失(时序错:校验放在降级已发生之后 = FM-4)")


def test_ut17_report_timestamp_iso_parseable(caplog):
    """UT-17(锚 FM-2 可追溯): 降级报告时间戳必须是 ISO 可解析格式。"""
    host = _init_host(caplog)
    report = getattr(host, "degradation_report", None)
    assert isinstance(report, dict), "缺少结构化降级报告"
    at = report.get("at")
    assert isinstance(at, str) and at, "报告缺时间戳(降级不可追溯)"
    try:
        datetime.fromisoformat(at)
    except ValueError:
        pytest.fail(f"报告时间戳非 ISO 可解析格式: {at!r}")


# ---------------------------------------------------------------------------
# UT-18 ~ UT-21 · focus_points 独立锚面
# ---------------------------------------------------------------------------

def test_ut18_report_backend_matches_flag(caplog):
    """UT-18(focus 降级可见性-一致性): 报告内 backend 必须与宿主标志一致。"""
    host = _init_host(caplog)
    report = getattr(host, "degradation_report", None)
    assert isinstance(report, dict), "缺少结构化降级报告"
    assert report.get("backend") == host.chain_backend, (
        f"报告 backend={report.get('backend')!r} 与宿主标志 "
        f"{host.chain_backend!r} 不一致(双口径 = 伪装温床)")


def test_ut19_degradation_state_fully_introspectable(caplog):
    """UT-19(focus 启动自检): 降级态四件必须全部可内省,缺一即不可观测。"""
    host = _init_host(caplog)
    missing = [name for name in ("degraded", "chain_backend",
                                 "degradation_count", "degradation_report")
               if not hasattr(host, name)]
    assert not missing, f"降级态字段缺失: {missing}(启动自检面不完整)"


def test_ut20_whitespace_dsn_treated_as_missing(caplog):
    """UT-20(focus 配置校验): 纯空白 DSN 必须按缺失处理,不得当有效配置。"""
    with caplog.at_level(logging.DEBUG, logger="v5.helix_bridge"):
        host = HelixBridgeHost(
            BridgeConfig(agent_id="ut-agent", postgres_dsn="   ", env=dict(_EMPTY_ENV)))
    assert getattr(host, "degraded", False) is True, (
        "空白 DSN 被当作有效配置(未 strip 校验 = 配置校验缺位)")


def test_ut21_degraded_outcome_deterministic(caplog):
    """UT-21(focus fallback 等价性证伪): 降级语义必须确定,多次调用结果一致。"""
    host = _init_host(caplog)
    outcomes = [_call(host, cycle) for cycle in (1, 2, 3)]
    assert isinstance(outcomes[0], dict), "降级 outcome 非结构"
    assert outcomes[0] == outcomes[1] == outcomes[2], (
        "同态降级多次调用 outcome 漂移(降级语义不确定 = 隐性随机)")
