# -*- coding: utf-8 -*-
"""v5 helix_v7 bridge 消费侧(真实代码切段包装)· 坑版(事故原样语义)

源1: nautilus-v5 `nautilus_v5/super_agent.py:377-412` @0293e5ccd56c43030f92c0540d837c3d24ed8b3a
      (_PATCH_V5_HELIX_V7_BRIDGE_2026_05_18)
源2: nautilus-v5 `nautilus_v5/daemon.py:858-878` @0293e5ccd56c43030f92c0540d837c3d24ed8b3a
      (消费侧 a_close_breath_pair · soft except)
真实修复证据: nautilus-core commit defb148c658e81e574c1c13bb334b38964b6c9e6(10/4「补缺失件」
      PgStorage + HelixChain.a_close_breath_pair;坑版本 repo 中该文件不存在 = 事故态)。

切段边界以 `# ---8<---` 标注,逐字保留原逻辑;包装壳(BridgeConfig/HelixBridgeHost/方法签名)
仅为使切段可独立运行,不改变切段内任何控制流与可观测行为。
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
        # ---8<--- 源切段 super_agent.py:377-412(逐字;config→config 包装属性)
        self.helix_v7 = None
        self._helix_v7_prev_right_hash = None
        try:
            # posts 渲染一行修(#2763):config 空时回落 env V5_POSTGRES_DSN——
            # 8001 以 openai_api 直启时 storage 构造无人传 DSN,pool 不建 →
            # platform_admin 未装配 → posts 空渲染静默吞(AttributeError: pass)
            _hdsn = (config.memory_dsn
                     or config._env.get("V5_POSTGRES_DSN", "")).strip()
            if _hdsn:
                from psycopg_pool import AsyncConnectionPool as _AsyncPool
                from nautilus_core.helix_chain import HelixChain as _HelixChain, PgStorage as _PgStorage
                _hpool = _AsyncPool(_hdsn, min_size=1, max_size=2)
                self._pg_pool = _hpool  # _PATCH_V5_EMOTION_ATTACH_2026_05_23 · share pool with emotion modulator
                _hstorage = _PgStorage(pool=_hpool, table="helix_blocks", is_async=True)
                self.helix_v7 = _HelixChain(agent_id=config.agent_id, storage=_hstorage)
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
                    logger.debug(f"V5 helix_v7 resume soft fail: {_re}")
        except Exception as _he:
            logger.warning(f"V5 helix_v7 init failed (soft · file fallback ok): {_he}")
        # --->8<---

    # ---8<--- 源切段 daemon.py:858-878(逐字语义;self.agent→self 宿主直挂)
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
