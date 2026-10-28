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
"""
import asyncio
import logging
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1] / "workspace" / "repo"
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from v5_bridge.helix_bridge import BridgeConfig, HelixBridgeHost  # noqa: E402

_LEFT = {"act_summary": "unit-test action", "extra": "ignored"}
_RIGHT = {"cycle": 1, "introspect": "i" * 10, "learn": "l" * 10,
          "evolve": "e" * 5, "remember": "r" * 5, "witness_voice": "w" * 5}


def _init_host(caplog, dsn="postgres://user:oldpw@127.0.0.1:1/wrongdb"):
    """构造依赖不可用场景(坏 DSN → 连接/导入必失败),返回宿主。"""
    with caplog.at_level(logging.DEBUG, logger="v5.helix_bridge"):
        return HelixBridgeHost(BridgeConfig(agent_id="ut-agent", postgres_dsn=dsn))


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
