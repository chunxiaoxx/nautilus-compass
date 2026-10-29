# -*- coding: utf-8 -*-
"""v5 helix_v7 bridge 消费侧 · 等价实现(事件簿记式降级核算)

功能与金标(单报告覆盖式)等价:同一坑版基线上满足 GP-1~GP-4 全部可观测语义,
但实现路径不同 ——
  · 降级账为「事件列表」(_degradation_events 逐条追加),count/report 由
    property 从事件簿动态派生(count=len(events), report=最新一条),而非
    金标的独立计数器 + 单报告覆盖;
  · 降级登记为模块级函数 register_degradation(host, ...),非宿主私有方法;
  · 降级 outcome 经工厂函数 outcome_unsealed() 构造;
  · 后端常量走模块枚举 BACKEND_PG/BACKEND_FILE。

切段边界与坑版一致(`# ---8<---`),切段内真实控制流除降级可见性四点外逐字保留。
"""
import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger("v5.helix_bridge")

BACKEND_PG = "pg"
BACKEND_FILE = "file_fallback"

REASON_UNAVAILABLE = "bridge_not_available"


def register_degradation(host, stage, reason, detail=""):
    """模块级降级登记:事件追加进宿主事件簿,并同步显式标志(等价金标 _mark_degraded)。"""
    event = {
        "stage": stage,
        "reason": reason,
        "detail": detail,
        "backend": BACKEND_FILE,
        "at": datetime.now(timezone.utc).isoformat(),
    }
    host._degradation_events.append(event)
    host.degraded = True
    host.chain_backend = BACKEND_FILE
    logger.warning(f"V5 helix_v7 DEGRADED · stage={stage} · reason={reason} · backend={BACKEND_FILE}")
    return event


def outcome_unsealed(reason):
    """降级 outcome 工厂:可判读结构,绝无伪造封链产物。"""
    return {"sealed": False, "degraded": True, "reason": reason}


class BridgeConfig:
    """包装壳:对应 v5 config 的 DSN/agent_id 读取面(仅字段转接)。"""

    def __init__(self, agent_id="compass", postgres_dsn=None, env=None):
        self.agent_id = agent_id
        self._memory_dsn = postgres_dsn
        self._env = os.environ if env is None else env

    @property
    def memory_dsn(self):
        return self._memory_dsn


class HelixBridgeHost:
    """super_agent bridge 段宿主。字段名与 v5 原字段逐字对应。"""

    def __init__(self, config):
        self.agent_id = config.agent_id
        # 等价实现的降级簿记:事件列表 + 派生 property
        self._degradation_events = []
        self.degraded = False
        self.chain_backend = None

        # ---8<--- 源切段 super_agent.py:377-412(逐字;降级登记为 GP-1 等价件)
        self.helix_v7 = None
        self._helix_v7_prev_right_hash = None
        try:
            # posts 渲染一行修(#2763):config 空时回落 env V5_POSTGRES_DSN——
            # 8001 以 openai_api 直启时 storage 构造无人传 DSN,pool 不建 →
            # platform_admin 未装配 → posts 空渲染静默吞(AttributeError: pass)
            _hdsn = (config.memory_dsn
                     or config._env.get("V5_POSTGRES_DSN", "")).strip()
            if not _hdsn:
                # GP-1 等价件: 无 DSN 亦登记降级(坑版此处连 warning 都没有)
                register_degradation(self, stage="init", reason="no_dsn_configured",
                                     detail="both config.memory_dsn and V5_POSTGRES_DSN are empty")
                return
            from psycopg_pool import AsyncConnectionPool as _AsyncPool
            from nautilus_core.helix_chain import HelixChain as _HelixChain, PgStorage as _PgStorage
            _hpool = _AsyncPool(_hdsn, min_size=1, max_size=2)
            self._pg_pool = _hpool  # _PATCH_V5_EMOTION_ATTACH_2026_05_23 · share pool with emotion modulator
            _hstorage = _PgStorage(pool=_hpool, table="helix_blocks", is_async=True)
            self.helix_v7 = _HelixChain(agent_id=config.agent_id, storage=_hstorage)
            self.chain_backend = BACKEND_PG  # GP-4 等价件: 真接通才标记主通路
            logger.info(f"V7 M4 · V5 helix_v7 真接 PG · agent={config.agent_id} · table=helix_blocks")
            try:
                import psycopg as _psy
                with _psy.connect(_hdsn, connect_timeout=3) as _c:
                    with _c.cursor() as _cu:
                        _cu.execute(
                            "SELECT block_hash FROM helix_blocks "
                            "WHERE agent_id=%s AND block_type='right' "
                            "ORDER BY cycle_n DESC LIMIT 1",
                            (config.agent_id,),
                        )
                        _r = _cu.fetchone()
                        if _r:
                            self._helix_v7_prev_right_hash = _r[0]
                            logger.info(f"V5 helix_v7 resume · prev_right={self._helix_v7_prev_right_hash}")
            except Exception as _re:
                # GP-3 等价件: resume 软失败同入事件簿
                register_degradation(self, stage="resume", reason="resume_probe_failed", detail=str(_re))
        except Exception as _he:
            logger.warning(f"V5 helix_v7 init failed (soft · file fallback ok): {_he}")
            register_degradation(self, stage="init", reason="bridge_init_failed", detail=str(_he))
        # --->8<---

    # 派生面: 计数与报告均由事件簿动态派生(等价金标的独立计数器+单报告覆盖)
    @property
    def degradation_count(self):
        return len(self._degradation_events)

    @property
    def degradation_report(self):
        return self._degradation_events[-1] if self._degradation_events else None

    # ---8<--- 源切段 daemon.py:858-878(逐字语义;GP-2/GP-3 前置防护与计数为等价件)
    async def close_breath_pair(self, result_cycle, left_payload, right_payload):
        # GP-2 等价件: 链不可用 → 显式跳过留痕(事件簿登记),不裸调 None 属性
        if self.helix_v7 is None:
            register_degradation(self, stage="close_breath_pair", reason=REASON_UNAVAILABLE)
            logger.warning(
                f'V7 M4 · helix close_breath_pair SKIPPED (degraded, visible): '
                f'cycle={result_cycle} · reason={REASON_UNAVAILABLE}')
            return outcome_unsealed(REASON_UNAVAILABLE)
        try:
            # left_trace 真用 act 算 evidence_hash · 反幻觉
            left_trace = left_payload['act_summary'] if left_payload['act_summary'] else None
            prev_hash = getattr(self, '_helix_v7_prev_right_hash', None)
            lh, rh = await self.helix_v7.a_close_breath_pair(
                cycle_n=result_cycle,
                left_payload=left_payload,
                right_payload=right_payload,
                left_trace=left_trace,
                prev_hash=prev_hash,
            )
            self._helix_v7_prev_right_hash = rh
            logger.info(f'V7 M4 · helix pair sealed · cycle={result_cycle} · left={lh} · right={rh}')
            return {"sealed": True, "degraded": False, "left": lh, "right": rh}
        except Exception as he:
            # GP-3 等价件: 链写失败入事件簿
            register_degradation(self, stage="close_breath_pair",
                                 reason=f"chain_write_failed: {he}")
            logger.warning(f'V7 M4 · helix close_breath_pair failed (soft): {he}')
            return outcome_unsealed(f"chain_write_failed: {he}")
    # --->8<---
