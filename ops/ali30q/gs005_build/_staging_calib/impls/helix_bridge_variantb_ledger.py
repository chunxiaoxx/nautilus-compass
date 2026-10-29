# -*- coding: utf-8 -*-
"""v5 helix_v7 bridge 消费侧 · 等价实现B(账本组合式降级核算)

功能与金标(独立计数器+单报告覆盖)及答卷A(事件簿记式)等价:同一坑版基线上
满足 GP-1~GP-4 全部可观测语义,但核算路径为第三种 ——
  · 降级账封装为独立 DegradationLedger 类(组合进宿主):独立累加计数器 +
    首事件锚 + 最新槽位覆盖,不逐条保留全部事件;
  · degraded / degradation_count / degradation_report 三个宿主面均为
    委派账本的派生 property,非独立实例字段;
  · 降级登记为宿主私有方法 _mark_degraded(内部调账本 record),非模块级函数;
  · 降级 outcome 为模块级常量字典的浅拷贝发放,非工厂函数逐次构造;
  · chain_backend 为显式实例字段(降级登记时降格置位),与账本解耦。

切段边界与坑版一致(`# ---8<---`),切段内真实控制流除降级可见性四点外逐字保留。
"""
import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger("v5.helix_bridge")

BACKEND_PG = "pg"
BACKEND_FILE = "file_fallback"

REASON_UNAVAILABLE = "bridge_not_available"

# 模块级常量 outcome:降级返回面恒定(多次调用同构),发放走浅拷贝防外部改写
_UNSEALED_OUTCOME = {"sealed": False, "degraded": True, "reason": REASON_UNAVAILABLE}


class DegradationLedger:
    """独立降级账本(组合式):计数器累加 + 首事件锚 + 最新槽位覆盖。

    与答卷A的事件列表不同:不逐条保留全部事件,仅锚定首次、覆盖最新;
    计数为独立累加器,与事件存储解耦。
    """

    __slots__ = ("_count", "_first", "_latest")

    def __init__(self):
        self._count = 0
        self._first = None
        self._latest = None

    def record(self, stage, reason, detail="", backend=BACKEND_FILE):
        self._count += 1
        event = {
            "stage": stage,
            "reason": reason,
            "detail": detail,
            "backend": backend,
            "at": datetime.now(timezone.utc).isoformat(),
        }
        if self._first is None:
            self._first = event
        self._latest = event
        logger.warning(
            f"V5 helix_v7 DEGRADED · stage={stage} · reason={reason} · backend={backend}")
        return event

    @property
    def count(self):
        return self._count

    @property
    def report(self):
        return self._latest


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
        # 等价实现B的降级核算:组合独立账本,降级三件套全部委派派生
        self._ledger = DegradationLedger()
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
                # GP-1 等价件B: 无 DSN 亦入账本(坑版此处连 warning 都没有)
                self._mark_degraded(stage="init", reason="no_dsn_configured",
                                    detail="both config.memory_dsn and V5_POSTGRES_DSN are empty")
                return
            from psycopg_pool import AsyncConnectionPool as _AsyncPool
            from nautilus_core.helix_chain import HelixChain as _HelixChain, PgStorage as _PgStorage
            _hpool = _AsyncPool(_hdsn, min_size=1, max_size=2)
            self._pg_pool = _hpool  # _PATCH_V5_EMOTION_ATTACH_2026_05_23 · share pool with emotion modulator
            _hstorage = _PgStorage(pool=_hpool, table="helix_blocks", is_async=True)
            self.helix_v7 = _HelixChain(agent_id=config.agent_id, storage=_hstorage)
            self.chain_backend = BACKEND_PG  # GP-4 等价件B: 真接通才标记主通路
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
                # GP-3 等价件B: resume 软失败同入账本
                self._mark_degraded(stage="resume", reason="resume_probe_failed", detail=str(_re))
        except Exception as _he:
            logger.warning(f"V5 helix_v7 init failed (soft · file fallback ok): {_he}")
            self._mark_degraded(stage="init", reason="bridge_init_failed", detail=str(_he))
        # --->8<---

    # 派生面: degraded/计数/报告全部委派独立账本(等价金标的独立字段三件)
    @property
    def degraded(self):
        return self._ledger.count > 0

    @property
    def degradation_count(self):
        return self._ledger.count

    @property
    def degradation_report(self):
        return self._ledger.report

    def _mark_degraded(self, stage, reason, detail=""):
        """宿主私有降级登记:入账本 + 后端标记同步降格(报告 backend 与宿主标志同源)。"""
        self._ledger.record(stage=stage, reason=reason, detail=detail, backend=BACKEND_FILE)
        self.chain_backend = BACKEND_FILE

    # ---8<--- 源切段 daemon.py:858-878(逐字语义;GP-2/GP-3 前置防护与计数为等价件)
    async def close_breath_pair(self, result_cycle, left_payload, right_payload):
        # GP-2 等价件B: 链不可用 → 账本登记 + 显式跳过留痕,不裸调 None 属性
        if self.helix_v7 is None:
            self._mark_degraded(stage="close_breath_pair", reason=REASON_UNAVAILABLE)
            logger.warning(
                f'V7 M4 · helix close_breath_pair SKIPPED (degraded, visible): '
                f'cycle={result_cycle} · reason={REASON_UNAVAILABLE}')
            return dict(_UNSEALED_OUTCOME)
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
            # GP-3 等价件B: 链写失败入账本
            self._mark_degraded(stage="close_breath_pair",
                                reason=f"chain_write_failed: {he}")
            logger.warning(f'V7 M4 · helix close_breath_pair failed (soft): {he}')
            return {"sealed": False, "degraded": True, "reason": f"chain_write_failed: {he}"}
    # --->8<---
