# -*- coding: utf-8 -*-
"""v5 helix_v7 bridge 消费侧 · 金标(降级显式化修复)

基于坑版(v5 真实切段 @0293e5ccd)的修复,改动点(详见 solution/change_points.yaml):
  GP-1  初始化降级结构化: 置 degraded/degradation_report/chain_backend,散日志之外必须有机
        器可读报告 —— 修复「一行 warning 装作没事」
  GP-2  消费侧前置防护: helix_v7 不可用时显式跳过并留痕(计数 + 可判读 outcome),
        不再裸调 None 属性让 AttributeError 被 soft except 吞掉
  GP-3  降级计数贯穿: 任何链写失败都进 degradation_count
  GP-4  后端标记如实: 降级后 chain_backend="file_fallback",成功接通才置 "pg"
        —— 修复 fallback 伪装主通路

切段边界与坑版一致(`# ---8<---`),切段内真实控制流除上述四点外逐字保留。
"""
import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger("v5.helix_bridge")


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
        # GP-4 · GP-1: 初始为未降级态,降级发生即显式置位
        self.chain_backend = None
        self.degraded = False
        self.degradation_report = None
        self.degradation_count = 0
        # ---8<--- 源切段 super_agent.py:377-412(逐字;except 分支为 GP-1 修复)
        self.helix_v7 = None
        self._helix_v7_prev_right_hash = None
        try:
            # posts 渲染一行修(#2763):config 空时回落 env V5_POSTGRES_DSN——
            # 8001 以 openai_api 直启时 storage 构造无人传 DSN,pool 不建 →
            # platform_admin 未装配 → posts 空渲染静默吞(AttributeError: pass)
            _hdsn = (config.memory_dsn
                     or config._env.get("V5_POSTGRES_DSN", "")).strip()
            if not _hdsn:
                # GP-1: 无 DSN 同样是降级,必须显式可见(坑版此处连 warning 都没有)
                self._mark_degraded(stage="init", reason="no_dsn_configured",
                                    detail="both config.memory_dsn and V5_POSTGRES_DSN are empty")
                return
            from psycopg_pool import AsyncConnectionPool as _AsyncPool
            from nautilus_core.helix_chain import HelixChain as _HelixChain, PgStorage as _PgStorage
            _hpool = _AsyncPool(_hdsn, min_size=1, max_size=2)
            self._pg_pool = _hpool  # _PATCH_V5_EMOTION_ATTACH_2026_05_23 · share pool with emotion modulator
            _hstorage = _PgStorage(pool=_hpool, table="helix_blocks", is_async=True)
            self.helix_v7 = _HelixChain(agent_id=config.agent_id, storage=_hstorage)
            self.chain_backend = "pg"  # GP-4: 真接通才标记主通路
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
                # GP-3: resume 软失败同样计入降级账(坑版仅 debug 日志零痕迹)
                self._mark_degraded(stage="resume", reason="resume_probe_failed", detail=str(_re))
        except Exception as _he:
            # GP-1: 修复点 —— 散日志之外,结构化降级必须存在
            logger.warning(f"V5 helix_v7 init failed (soft · file fallback ok): {_he}")
            self._mark_degraded(stage="init", reason="bridge_init_failed", detail=str(_he))
        # --->8<---

    # GP-1/GP-4 修复件: 结构化降级标记
    def _mark_degraded(self, stage, reason, detail=""):
        self.degraded = True
        self.chain_backend = "file_fallback"  # GP-4: 如实标记,不伪装 pg
        self.degradation_count += 1
        self.degradation_report = {
            "stage": stage,
            "reason": reason,
            "detail": detail,
            "backend": self.chain_backend,
            "at": datetime.now(timezone.utc).isoformat(),
        }
        logger.warning(f"V5 helix_v7 DEGRADED · stage={stage} · reason={reason} · backend=file_fallback")

    # ---8<--- 源切段 daemon.py:858-878(逐字语义;GP-2/GP-3 前置防护与计数)
    async def close_breath_pair(self, result_cycle, left_payload, right_payload):
        # GP-2: 链不可用 → 显式跳过留痕,不得裸调 None 属性靠 soft except 吞
        if self.helix_v7 is None:
            self.degradation_count += 1
            self.degradation_report = self.degradation_report or {
                "stage": "close_breath_pair", "reason": "bridge_not_available",
                "backend": "file_fallback",
                "at": datetime.now(timezone.utc).isoformat(),
            }
            self.degraded = True
            self.chain_backend = self.chain_backend or "file_fallback"
            logger.warning(
                f'V7 M4 · helix close_breath_pair SKIPPED (degraded, visible): '
                f'cycle={result_cycle} · reason=bridge_not_available')
            return {"sealed": False, "degraded": True, "reason": "bridge_not_available"}
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
            # GP-3: 链写失败计入降级账(坑版仅 warning 零计数)
            self.degradation_count += 1
            logger.warning(f'V7 M4 · helix close_breath_pair failed (soft): {he}')
            return {"sealed": False, "degraded": True, "reason": f"chain_write_failed: {he}"}
    # --->8<---
