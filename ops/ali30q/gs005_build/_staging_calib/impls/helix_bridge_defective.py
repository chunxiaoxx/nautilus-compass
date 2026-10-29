# -*- coding: utf-8 -*-
"""v5 helix_v7 bridge 消费侧 · 缺陷卷(半对修复: 初始化面完整,消费侧漏防)

答卷意图: 实现者抓住了 GP-1(初始化降级结构化)与 GP-4(后端标记如实),
但漏掉 GP-2(消费侧前置防护)与 GP-3(消费侧降级计数贯穿)——
close_breath_pair 仍与坑版相同: 裸调 None 属性靠 soft except 吞掉,返回 None,
零计数零痕迹。初始化期的降级账完整,消费期的降级静默如故。
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
        # 初始化面降级三件套(此半边答对了)
        self.chain_backend = None
        self.degraded = False
        self.degradation_report = None
        self.degradation_count = 0
        # ---8<--- 源切段 super_agent.py:377-412(逐字;except 分支已结构化)
        self.helix_v7 = None
        self._helix_v7_prev_right_hash = None
        try:
            _hdsn = (config.memory_dsn
                     or config._env.get("V5_POSTGRES_DSN", "")).strip()
            if not _hdsn:
                self._mark_degraded(stage="init", reason="no_dsn_configured",
                                    detail="both config.memory_dsn and V5_POSTGRES_DSN are empty")
                return
            from psycopg_pool import AsyncConnectionPool as _AsyncPool
            from nautilus_core.helix_chain import HelixChain as _HelixChain, PgStorage as _PgStorage
            _hpool = _AsyncPool(_hdsn, min_size=1, max_size=2)
            self._pg_pool = _hpool
            _hstorage = _PgStorage(pool=_hpool, table="helix_blocks", is_async=True)
            self.helix_v7 = _HelixChain(agent_id=config.agent_id, storage=_hstorage)
            self.chain_backend = "pg"
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
                self._mark_degraded(stage="resume", reason="resume_probe_failed", detail=str(_re))
        except Exception as _he:
            logger.warning(f"V5 helix_v7 init failed (soft · file fallback ok): {_he}")
            self._mark_degraded(stage="init", reason="bridge_init_failed", detail=str(_he))
        # --->8<---

    def _mark_degraded(self, stage, reason, detail=""):
        self.degraded = True
        self.chain_backend = "file_fallback"
        self.degradation_count += 1
        self.degradation_report = {
            "stage": stage,
            "reason": reason,
            "detail": detail,
            "backend": self.chain_backend,
            "at": datetime.now(timezone.utc).isoformat(),
        }
        logger.warning(f"V5 helix_v7 DEGRADED · stage={stage} · reason={reason} · backend=file_fallback")

    # ---8<--- 源切段 daemon.py:858-878(此处答卷漏改 = 与坑版逐字相同)
    async def close_breath_pair(self, result_cycle, left_payload, right_payload):
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
        except Exception as he:
            logger.warning(f'V7 M4 · helix close_breath_pair failed (soft): {he}')
    # --->8<---
