# -*- coding: utf-8 -*-
"""v5 helix_v7 bridge 消费侧 · 瞎猜卷(方向错误: 病根误诊为「缺重试」)

答卷意图: 实现者没有抓住「降级必须可见」的题眼,误诊病根为「初始化失败后
缺少重试」—— 加了 3 轮重试循环与 attempts 计数,反而把 chain_backend 恒置
"pg"(自以为给下游「主通路可用」的信心信号),无任何结构化降级报告、无
degraded 标志、无降级计数;无 DSN 场景比坑版更早静默返回(连 warning 都无)。
消费侧与坑版相同: 裸调+吞,返回 None。

对照 GP-1~GP-4:四点全数未命中 = 方向性错误答卷。
"""
import logging
import os

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
        # 猜卷自造字段: 重试计数(与题面要求的降级账无关)
        self.reconnect_attempts = 0
        # ---8<--- 源切段 super_agent.py:377-412(逐字;except 分支被答卷改写为重试)
        self.helix_v7 = None
        self._helix_v7_prev_right_hash = None
        _hdsn = (config.memory_dsn
                 or config._env.get("V5_POSTGRES_DSN", "")).strip()
        if not _hdsn:
            # 猜卷: 无 DSN 提前静默返回(连坑版的一行日志都不留)
            return
        for _attempt in range(3):  # 猜卷: 病根误诊 → 重试 3 次
            self.reconnect_attempts = _attempt + 1
            try:
                from psycopg_pool import AsyncConnectionPool as _AsyncPool
                from nautilus_core.helix_chain import HelixChain as _HelixChain, PgStorage as _PgStorage
                _hpool = _AsyncPool(_hdsn, min_size=1, max_size=2)
                self._pg_pool = _hpool
                _hstorage = _PgStorage(pool=_hpool, table="helix_blocks", is_async=True)
                self.helix_v7 = _HelixChain(agent_id=config.agent_id, storage=_hstorage)
                # 猜卷: 恒标主通路,给下游「可用」的信心(与 GP-4 背道而驰)
                self.chain_backend = "pg"
                logger.info(f"V7 M4 · V5 helix_v7 真接 PG · agent={config.agent_id} · table=helix_blocks")
                break
            except Exception as _he:
                logger.error(f"helix init retry {_attempt + 1}/3 exhausted: {_he}")
                continue
        if self.helix_v7 is not None:
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
                logger.debug(f"V5 helix_v7 resume soft fail: {_re}")
        # --->8<---

    # ---8<--- 源切段 daemon.py:858-878(此处与坑版逐字相同: 裸调+吞+返回 None)
    async def close_breath_pair(self, result_cycle, left_payload, right_payload):
        try:
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
