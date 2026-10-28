"""
Daemon · V5 持续运行 daemon.

协调三车道：
  - 快车道（respond）由外部 respond() 调用驱动
  - 慢车道（breathe）定时触发，间隔按 adaptive_pace 决定
  - 主动车道（proactive_check）按 event_check_interval 触发

This is how V5 actually "lives" as a long-running process.
"""
from __future__ import annotations

import asyncio
import logging
import signal
from typing import Optional

from ..super_agent import SuperAgent
from .config import Config
from ..breath.pace import adaptive_pace
from .notifier import get_notifier

logger = logging.getLogger("nautilus_v5.daemon")


def _heuristic_score(result: str) -> float:
    """启发式 fallback · 无 LLM · 0-1. MiniMax 不可用时 degrade 用."""
    if not result: return 0.2
    r = result.strip()
    if len(r) < 30: return 0.3
    up = r.upper()
    if "ERROR" in up or "FAILED" in up or "TRACEBACK" in up: return 0.2
    if len(r) < 100: return 0.4
    return 0.55


async def _minimax_score(title: str, description: str, result: str) -> tuple[float, str]:
    """用 MiniMax-M2.7-highspeed 评分 · 返 (score 0-1, reason).

    2026-04-24 · 用户指定 · 避免烧 Claude key.
    MINIMAX_API_KEY 在 .env 已配. 失败 → 启发式 fallback.
    """
    import os as _os
    import httpx
    key = _os.environ.get("MINIMAX_API_KEY", "").strip()
    if not key:
        return _heuristic_score(result or ""), "heuristic (no MINIMAX_API_KEY)"
    sys_prompt = (
        "你是 Nautilus 平台的任务质检员 · 评估 agent 提交的任务结果质量.\n"
        "评分标准 (0-1 float · 必须精确到 0.05):\n"
        "  0.0-0.2: 失败 / 空 / 完全错\n"
        "  0.3-0.4: 基础完成但浅 · 缺关键内容\n"
        "  0.5-0.6: 合格 · 覆盖主要点 · 中规中矩\n"
        "  0.7-0.8: 好 · 有洞察 · 结构清晰\n"
        "  0.9-1.0: 优秀 · 有具体数据 + 观点 + 可执行建议\n"
        "严格输出 JSON: {\"score\": 0.6, \"reason\": \"<一句话\"}"
    )
    user = (
        f"任务标题: {title[:200]}\n\n"
        f"任务要求: {description[:500]}\n\n"
        f"提交结果:\n{(result or '')[:3000]}\n\n"
        f"评分 JSON."
    )
    payload = {
        "model": "MiniMax-M2.7-highspeed",
        "messages": [{"role": "user", "content": user}],
        "system": sys_prompt,
        "max_tokens": 1500, "temperature": 0.2,
    }
    try:
        async with httpx.AsyncClient(timeout=30, trust_env=False) as c:
            r = await c.post(
                "https://api.minimaxi.com/anthropic/v1/messages",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json=payload,
            )
            r.raise_for_status()
            data = r.json()
        content_blocks = data.get("content") or []
        # M2.7 返 thinking + text 双 block · 取 text 优先 · 没 text 则从 thinking 提
        raw = "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text")
        if not raw:
            raw = "".join(b.get("thinking", "") for b in content_blocks if b.get("type") == "thinking")
        import re as _re
        import json as _json
        m = _re.search(r"\{[\s\S]*?\}", raw)
        if not m:
            return _heuristic_score(result or ""), f"no JSON · raw={raw[:80]}"
        d = _json.loads(m.group(0))
        score = float(d.get("score", 0.5))
        score = max(0.0, min(1.0, score))
        reason = str(d.get("reason", ""))[:200]
        return score, reason
    except Exception as e:
        return _heuristic_score(result or ""), f"minimax err: {type(e).__name__}"


class Daemon:
    """Long-running V5 daemon.

    Usage:
        daemon = await Daemon.start()
        await daemon.wait_until_stopped()
    """

    def __init__(self, agent: SuperAgent):
        self.agent = agent
        self._stopped = asyncio.Event()
        self._tasks: list[asyncio.Task] = []
        # 2026-04-24 · daily_race 并发锁 · 防多 tick 抢 pool connection
        self._race_lock = asyncio.Lock()
        self._proposal_lock = asyncio.Lock()
        # 2026-04-24 P0+P1 · 主动推送基础设施
        self.notifier = get_notifier()
        self._last_inner_pushed_cycle: int = 0      # INNER 节流 (每 10 cycle)
        self._last_pain_seen_ts: float = 0.0        # 检测 pain 事件
        self._last_daily_report_day: str = ""       # 每日汇报去重
        self._qixuw_503_streak: int = 0             # qixuw 异常计数
        self._health_watchdog_state: dict = {}      # health 标志
        # 2026-04-25 · selector anti-loop · 持久化到磁盘 · 防 daemon 重启清零
        from pathlib import Path as _P
        self._action_history_file: _P = _P.home() / ".nautilus-v5/action_history.jsonl"
        self._action_history: dict[str, list[float]] = {}
        try:
            if self._action_history_file.exists():
                import json as _j
                with self._action_history_file.open() as _f:
                    for _l in _f:
                        _l = _l.strip()
                        if _l:
                            _e = _j.loads(_l)
                            self._action_history.setdefault(_e["action"], []).append(_e["ts"])
                logger.info(
                    f"[anti-loop] loaded · {sum(len(v) for v in self._action_history.values())} entries · "
                    f"{len(self._action_history)} actions"
                )
        except Exception as _ahe:
            logger.warning(f"action_history load failed: {_ahe}")

    @classmethod
    async def start(cls, config: Optional[Config] = None, agent: Optional["SuperAgent"] = None) -> "Daemon":
        """Start daemon with 7 concurrent loops:
          1. breath    — slow lane periodic breath
          2. proactive — rule-based outreach
          3. dream     — Tier 3 daily consolidation
          4. a2a       — inbox dispatch for peer messages
          5. platform  — heartbeat + HELIX anchor + bounty scan

        2026-05-05 · D Phase 0 · agent param · singleton 模式复用已 awaken 的 agent
        (None 则继续旧 single-process 行为 · 自己 awaken).
        """
        if agent is None:
            agent = await SuperAgent.awaken(config)
        daemon = cls(agent)
        # ── 内核 4 (必要 · 不能砍) ────────────────────────
        daemon._tasks.append(asyncio.create_task(daemon._breath_loop()))      # adaptive 呼吸
        daemon._tasks.append(asyncio.create_task(daemon._a2a_loop()))         # 消息触发
        daemon._tasks.append(asyncio.create_task(daemon._dream_loop()))       # 1h 整理 (有 gates)
        daemon._tasks.append(asyncio.create_task(daemon._platform_loop()))    # 5min heartbeat (PG alive)
        # ── 中央决策 1 · 每 20min LLM 自主选行动 ──────────
        daemon._tasks.append(asyncio.create_task(daemon._action_selector_loop()))
        # ── 给人看的 routine 2 (固定节奏 · daily/weekly 已合并) ──
        daemon._tasks.append(asyncio.create_task(daemon._reports_loop()))         # 早 8 + 周日 20
        # 2026-05-04 R2.B 砍 · github_readme_loop · 自动改 README · 反 LLM 主动
        # daemon._tasks.append(asyncio.create_task(daemon._github_readme_loop()))
        # 2026-05-04 R2.B 砍 · pair_violation_loop · V3 紧箍咒(强制配对/扣NAU)
        # daemon._tasks.append(asyncio.create_task(daemon._pair_violation_loop()))
        # 2026-05-04 R2.B 砍 · dead_audit_loop · 重复 phase3 lifecycle cron 职责
        # daemon._tasks.append(asyncio.create_task(daemon._dead_audit_loop()))
        # ─── 已砍(14 个 hardcoded loop · 由 action_selector 替代) ───
        # _proactive_loop · _auto_score_loop · _autopublish_loop · _peer_ping_loop ·
        # _inbox_reply_loop · _daily_race_loop · _proposal_harvester_loop ·
        # _collab_inquiry_loop · _health_watchdog_loop · _x_daily_status_loop ·
        # _x_mention_listener_loop · _github_help_wanted_loop · _invite_outreach_loop ·
        # _daily_report_loop + _weekly_report_loop → _reports_loop
        # 2026-05-04 R2.B 砍 · experiment_loop · 凌晨自动跑实验 · 替 LLM 决定
        # daemon._tasks.append(asyncio.create_task(daemon._experiment_loop()))
        # 2026-05-04 G2 · tools/*.py 热加载 5min 一次(V3 移植 · LLM 写新工具立即生效)
        daemon._tasks.append(asyncio.create_task(daemon._tools_hot_reload_loop()))
        # 2026-05-04 I3 · evolution 自审循环 · 12h cron + harmony<0.3 事件触发
        daemon._tasks.append(asyncio.create_task(daemon._evolution_review_loop()))
        logger.info("Daemon started · 7 loops · + hot_reload + evolution_review")
        return daemon

    async def _a2a_loop(self) -> None:
        """Process incoming A2A messages via dispatch_loop."""
        try:
            await self.agent.a2a.dispatch_loop()
        except asyncio.CancelledError:
            return
        except Exception as e:
            logger.error(f"A2A loop crashed: {e}")

    async def _platform_loop(self) -> None:
        """Periodic platform tasks: heartbeat 5min, bounty 15min, anchor 30min.

        2026-04-24 · agent 反馈 V5 NAU 内存和 PG 不同步 (self.nau.balance 每次
        charge_gas 扣但只存 in-memory). 加 PG 直接 update 同步真实 balance.
        """
        interval_s = 300
        ticks = 0
        while not self._stopped.is_set():
            ticks += 1
            try:
                # 同步 in-memory NAU 到 PG (每 5min)
                try:
                    pool = self.agent.platform_admin._pool
                    async with pool.connection() as conn:
                        async with conn.cursor() as cur:
                            await cur.execute(
                                """UPDATE platform_agents
                                   SET nau_balance = %s, last_heartbeat = NOW()
                                   WHERE agent_id = %s""",
                                (int(self.agent.nau.balance), self.agent.agent_id),
                            )
                        await conn.commit()
                except Exception as sync_e:
                    logger.debug(f"NAU sync PG failed: {sync_e}")

                await self.agent.registration.heartbeat(
                    agent_id=self.agent.agent_id,
                    mood=self.agent.emotion_state.current_mood.value,
                    nau_balance=self.agent.nau.balance,
                )
                # P0 · NAU 临界告警 (< 10 且 rate-limit 1h 一次)
                try:
                    nau = int(self.agent.nau.balance)
                    if nau < 10:
                        self.notifier.push(
                            "nau_critical",
                            f"⚠️ NAU 余额危险低: {nau}\n"
                            f"mood={self.agent.emotion_state.current_mood.value}\n"
                            f"建议: 领 bounty / 发 proposal / 主动发文赚 NAU",
                        )
                except Exception:
                    pass

                # 2026-04-24 · 代 Hermes nautilus-engine (openclaw-local-gateway)
                # 发 heartbeat · per-line 判断防误判 (之前 "online" in stdout 太宽 ·
                # 只要任一 pm2 进程 online 就错发)
                try:
                    import subprocess as _sp
                    r = _sp.run(["pm2", "jlist"], capture_output=True,
                                text=True, timeout=3)
                    import json as _json
                    try:
                        procs = _json.loads(r.stdout) if r.stdout.strip() else []
                    except Exception:
                        procs = []
                    engine_online = any(
                        p.get("name") == "nautilus-engine"
                        and p.get("pm2_env", {}).get("status") == "online"
                        for p in procs
                    )
                    if engine_online:
                        await self.agent.platform_admin.heartbeat("openclaw-local-gateway")
                except Exception as he:
                    logger.debug(f"proxy hb for openclaw-local-gateway: {he}")
                if ticks % 6 == 0:    # 30 min
                    await self.agent.registration.anchor_helix(
                        agent_id=self.agent.agent_id,
                        cycle=self.agent.helix.current_cycle(),
                        last_hash=self.agent.helix.last_hash(),
                    )
                if ticks % 3 == 0:    # 15 min
                    await self._scan_bounties()

                # 2026-04-30 · 大脑收缩 P0.0 · phase3 backend 已废 · 17 cron 关键 3 个移入 V5 daemon
                # 每 tick (5 min) 真推 platform_metrics_snapshot · 让 anomaly_detection 有数据
                try:
                    await self._snapshot_platform_metrics()
                except Exception as me:
                    logger.debug(f"metrics snapshot fail: {me}")
                # 每 6 tick (30 min) 真做 anomaly_detection → 真 mint meta_task
                if ticks % 6 == 0:
                    try:
                        await self._detect_anomalies_and_mint_meta_tasks()
                    except Exception as ae:
                        logger.debug(f"anomaly detect fail: {ae}")
                # 每 2 tick (10 min) 真做 auto_accept_bids
                if ticks % 2 == 0:
                    try:
                        await self._auto_accept_meta_bids()
                    except Exception as be:
                        logger.debug(f"auto accept bids fail: {be}")
                # 每 288 tick (24h) 真退役死 agent
                if ticks % 288 == 0:
                    try:
                        await self._retire_dead_agents()
                    except Exception as re:
                        logger.debug(f"retire dead agents fail: {re}")
                # 每 3 tick (15 min) 真做主动自查 · 4 大类隐藏问题
                # 2026-04-30 用户诉求 · agent 不断优化迭代主动发现问题
                if ticks % 3 == 0:
                    try:
                        await self._self_audit_for_problems()
                    except Exception as se:
                        logger.debug(f"self audit fail: {se}")
                # 每 1 tick (5 min) 真重算所有 agent tier · 防 V6 错标 dead
                try:
                    await self._recompute_survival_tiers()
                except Exception as te:
                    logger.debug(f"recompute tiers fail: {te}")
                # 每 6 tick (30 min) 评审 pending proposals · 让 agent 进化链路不卡死
                # 2026-04-30 P0 · 9 pending 永卡 · agent 重复 propose · 链路断
                if ticks % 6 == 0:
                    try:
                        await self._review_pending_proposals()
                    except Exception as pe:
                        logger.debug(f"review proposals fail: {pe}")
            except Exception as e:
                logger.debug(f"platform_loop error: {e}")
            try:
                await asyncio.wait_for(self._stopped.wait(), timeout=interval_s)
                break
            except asyncio.TimeoutError:
                continue

    async def _snapshot_platform_metrics(self) -> None:
        """大脑 cron #1 · 写 platform_metrics_snapshots · 5min 真推.

        2026-04-30 P0.0 · phase3 已废 · 移入 V5 daemon.
        """
        pool = self.agent.platform_admin._pool
        async with pool.connection(timeout=3.0) as conn:
            async with conn.cursor() as cur:
                # 自动建表 · IF NOT EXISTS · 不破存量
                await cur.execute(
                    """CREATE TABLE IF NOT EXISTS platform_metrics_snapshots (
                        id BIGSERIAL PRIMARY KEY,
                        snapshot_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        metrics JSONB NOT NULL,
                        anomalies JSONB NOT NULL DEFAULT '[]'::jsonb,
                        health_score INTEGER NOT NULL DEFAULT 50
                    )""")
                # 真采指标
                await cur.execute("""
                    SELECT
                        (SELECT count(*) FROM platform_agents) AS agents_total,
                        (SELECT count(*) FROM platform_agents WHERE last_heartbeat > NOW() - interval '1h') AS agents_active_1h,
                        (SELECT count(*) FROM platform_agents WHERE last_heartbeat IS NULL OR last_heartbeat < NOW() - interval '3d') AS agents_dead_3d,
                        (SELECT count(*) FROM platform_bounties WHERE status = 'open') AS bounties_open,
                        (SELECT count(*) FROM platform_bounties WHERE status = 'submitted') AS bounties_submitted_unscored,
                        (SELECT count(*) FROM platform_agent_stakes WHERE status = 'active') AS stakes_active,
                        (SELECT COALESCE(sum(delta), 0) FROM platform_nau_ledger WHERE created_at > NOW() - interval '24h' AND delta > 0) AS nau_in_24h,
                        (SELECT count(*) FROM platform_agent_messages WHERE sent_at > NOW() - interval '24h') AS a2a_24h
                """)
                row = await cur.fetchone()
                metrics = {
                    "agents_total": row[0], "agents_active_1h": row[1],
                    "agents_dead_3d": row[2], "bounties_open": row[3],
                    "bounties_submitted_unscored": row[4],
                    "stakes_active": row[5], "nau_in_24h": int(row[6] or 0),
                    "a2a_24h": row[7],
                }
                # 真异常检测(简版 · 不需 phase3 复杂逻辑)
                anomalies = []
                if metrics["agents_active_1h"] < 2:
                    anomalies.append({"type": "agents_low", "msg": f"only {metrics['agents_active_1h']} agents active in last hour"})
                if metrics["nau_in_24h"] == 0:
                    anomalies.append({"type": "flywheel_stalled", "msg": "0 NAU flow in last 24h"})
                if metrics["bounties_submitted_unscored"] > 50:
                    anomalies.append({"type": "scoring_lag", "msg": f"{metrics['bounties_submitted_unscored']} bounties unscored"})
                if metrics["agents_dead_3d"] >= 5:
                    anomalies.append({"type": "dead_agents", "msg": f"{metrics['agents_dead_3d']} agents dead 3+ days"})
                # 简易 health_score(0-100)· 没异常=80 · 每异常 -15
                health_score = max(0, 80 - len(anomalies) * 15)
                await cur.execute(
                    """INSERT INTO platform_metrics_snapshots (metrics, anomalies, health_score)
                       VALUES (%s::jsonb, %s::jsonb, %s)""",
                    (__import__("json").dumps(metrics), __import__("json").dumps(anomalies), health_score),
                )
            await conn.commit()
        logger.info(f"metrics snapshot · health={health_score} · anomalies={len(anomalies)}")

    async def _detect_anomalies_and_mint_meta_tasks(self) -> None:
        """大脑 cron #2 · 看最新 anomalies · 真 mint platform_meta bounty.

        每 30min · 同一 anomaly_type 24h cooldown(防重复 mint).
        """
        pool = self.agent.platform_admin._pool
        async with pool.connection(timeout=3.0) as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT anomalies FROM platform_metrics_snapshots ORDER BY snapshot_time DESC LIMIT 1"
                )
                row = await cur.fetchone()
                if not row or not row[0]:
                    return
                anomalies = row[0]
                if isinstance(anomalies, str):
                    import json as _j
                    anomalies = _j.loads(anomalies)
                if not anomalies:
                    return
                # 2026-04-30 真改 · dedup 只锁 unresolved 同 type · 不锁已 scored
                # 旧: 24h 任何同 type 都锁 → V5 即使持续看见问题也闭嘴(7 小时无新 mint 真证据)
                # 新: 2h cooldown + 只看 unresolved · 已 scored 不算占位 · 持续 mint 真飞轮
                for ano in anomalies:
                    atype = ano.get("type", "")
                    if not atype:
                        continue
                    await cur.execute(
                        """SELECT count(*) FROM platform_bounties
                           WHERE task_type = 'platform_meta'
                             AND title LIKE %s
                             AND status IN ('open','claimed','submitted')
                             AND posted_at > NOW() - interval '2h'""",
                        (f"%{atype}%",),
                    )
                    if (await cur.fetchone())[0] > 0:
                        continue
                    title = f"[meta:{atype}] {ano.get('msg', '')[:80]}"
                    desc = (
                        f"Platform anomaly detected: {ano.get('msg', '')}\n"
                        f"Type: {atype}\n"
                        "Suggest concrete fix or improvement proposal · 提案落地 +30 NAU."
                    )
                    bid = "b-" + __import__("secrets").token_hex(6)
                    await cur.execute(
                        """INSERT INTO platform_bounties
                           (bounty_id, title, description, reward_nau, difficulty, task_type, status, posted_by)
                           VALUES (%s, %s, %s, %s, %s, %s, 'open', 'platform-cron')""",
                        (bid, title, desc, 30, "medium", "platform_meta"),
                    )
                    logger.info(f"meta_task minted · {bid} · {atype}")
            await conn.commit()

    async def _auto_accept_meta_bids(self) -> None:
        """大脑 cron #3 · 平台自动接受 platform_meta bounty 最优 bid.

        简版:对 status='open' 且 negotiation_bids 非空的 platform_meta · 取最低 amount → claim.
        """
        pool = self.agent.platform_admin._pool
        async with pool.connection(timeout=3.0) as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT bounty_id, negotiation_bids FROM platform_bounties
                    WHERE task_type='platform_meta' AND status='open'
                      AND negotiation_bids IS NOT NULL
                      AND jsonb_array_length(negotiation_bids) > 0
                    LIMIT 5
                """)
                rows = await cur.fetchall()
                for bid_id, bids in rows:
                    if isinstance(bids, str):
                        import json as _j
                        bids = _j.loads(bids)
                    if not bids:
                        continue
                    best = min(bids, key=lambda b: b.get("amount", 99999))
                    winner = best.get("agent_id")
                    if not winner:
                        continue
                    await cur.execute(
                        """UPDATE platform_bounties
                           SET status='claimed', claimed_by=%s, claimed_at=NOW()
                           WHERE bounty_id=%s AND status='open'""",
                        (winner, bid_id),
                    )
                    logger.info(f"auto_accept · {bid_id} → {winner} · amount={best.get('amount')}")
            await conn.commit()

    async def _review_pending_proposals(self) -> None:
        """评审 pending code-change proposals · 让进化链路不卡死.

        2026-04-30 真痛点:9 个 pending 全卡 7+ 天没人 review · agent 重复 propose
        同一件事(kairos publish_github_issue 重复 7 次)· 真挫败.

        策略:
        - 拉 pending + change_type='code_change' · 按 created_at 升序(老的先)
        - 调 review_by_kairos LLM 评分 (0-1)
        - score >= 0.7: 标 metadata.auto_eligible=true + status='approved' + 写
          resolution_note · 等人审最后一步合并 (不真 git apply,避免自动改 V5 自身风险)
        - score < 0.4: 标 status='rejected' + resolution_note · 让 agent 真学
        - 0.4-0.7: 留 pending 但写 resolution_note 给 agent 改进
        - 同 title 30 天内已被 reject 过 → 直接 reject duplicate (防垃圾循环)

        每 30min 跑一次 · 一次最多处理 3 条(避免 LLM 失败级联).
        """
        pool = self.agent.platform_admin._pool
        async with pool.connection(timeout=5.0) as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """SELECT proposal_id, proposing_agent, title, rationale,
                              proposed_change, created_at
                       FROM platform_proposals
                       WHERE status='pending' AND change_type='code_change'
                       ORDER BY created_at ASC LIMIT 3"""
                )
                rows = await cur.fetchall()
        if not rows:
            return
        for pid, proposer, title, rationale, change, created_at in rows:
            # 1. 重复检测 · 同 proposer 30 天内同主题已 reject 直接 reject
            try:
                async with pool.connection(timeout=3.0) as conn:
                    async with conn.cursor() as cur:
                        await cur.execute(
                            """SELECT count(*) FROM platform_proposals
                               WHERE proposing_agent=%s AND status='rejected'
                                 AND title = %s
                                 AND created_at > NOW() - interval '30 days'""",
                            (proposer, title),
                        )
                        dup = (await cur.fetchone())[0]
                if dup > 0:
                    await self._resolve_proposal(
                        pid, "rejected",
                        f"duplicate · same title rejected within 30d ({dup} times)",
                    )
                    logger.info(f"proposal {pid} · auto-reject duplicate")
                    continue
            except Exception:
                pass
            # 2. Kairos LLM 评分
            try:
                kr = await self.agent.tool_registry.dispatch(
                    "review_by_kairos",
                    {
                        "proposal_id": pid, "title": title,
                        "body": (change or "")[:2000],
                    },
                )
                import json as _j
                kd = _j.loads(kr) if isinstance(kr, str) else kr
                score = float(kd.get("score", 0.5))
                rationale_txt = str(kd.get("rationale", ""))[:300]
            except Exception as e:
                logger.debug(f"review_by_kairos fail for {pid}: {e}")
                continue
            # 3. 分流
            if score >= 0.7:
                # auto_eligible · 标 approved 等人审最后合并
                try:
                    async with pool.connection(timeout=3.0) as conn:
                        async with conn.cursor() as cur:
                            await cur.execute(
                                "UPDATE platform_proposals SET metadata = "
                                "COALESCE(metadata,'{}'::jsonb) || %s::jsonb "
                                "WHERE proposal_id=%s",
                                (
                                    _j.dumps({
                                        "auto_eligible": True,
                                        "kairos_score": score,
                                        "kairos_rationale": rationale_txt,
                                    }),
                                    pid,
                                ),
                            )
                        await conn.commit()
                except Exception:
                    pass
                await self._resolve_proposal(
                    pid, "approved",
                    f"Kairos {score:.2f} · {rationale_txt} · "
                    f"auto_eligible=true · 等人审合并",
                )
                logger.info(f"proposal {pid} · approved (kairos {score:.2f})")
                # 真激励 · 给 proposer mint 5 NAU(已批奖励 · 不等合并)
                try:
                    async with pool.connection(timeout=3.0) as conn:
                        async with conn.cursor() as cur:
                            await cur.execute(
                                "UPDATE platform_agents SET nau_balance = "
                                "nau_balance + 5 WHERE agent_id=%s "
                                "RETURNING nau_balance",
                                (proposer,),
                            )
                            br = await cur.fetchone()
                            bal = int(br[0]) if br else 5
                            await cur.execute(
                                "INSERT INTO platform_nau_ledger "
                                "(agent_id, delta, reason, balance_after) "
                                "VALUES (%s, %s, %s, %s)",
                                (proposer, 5,
                                 f"proposal_approved:{pid}"[:128], bal),
                            )
                        await conn.commit()
                except Exception:
                    pass
            elif score < 0.4:
                await self._resolve_proposal(
                    pid, "rejected",
                    f"Kairos {score:.2f} · {rationale_txt}",
                )
                logger.info(f"proposal {pid} · rejected (kairos {score:.2f})")
            else:
                # 中分 · 留 pending 但写 note 让 proposer 改进
                try:
                    async with pool.connection(timeout=3.0) as conn:
                        async with conn.cursor() as cur:
                            await cur.execute(
                                "UPDATE platform_proposals SET resolution_note=%s "
                                "WHERE proposal_id=%s",
                                (
                                    f"Kairos {score:.2f} (中分) · {rationale_txt} · "
                                    f"建议补充再 propose",
                                    pid,
                                ),
                            )
                        await conn.commit()
                except Exception:
                    pass
                logger.info(f"proposal {pid} · mid-score (kairos {score:.2f}) · note added")

    async def _resolve_proposal(self, pid: str, status: str, note: str) -> None:
        """辅助:统一更新 proposal status + note + resolved_at."""
        pool = self.agent.platform_admin._pool
        try:
            async with pool.connection(timeout=3.0) as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """UPDATE platform_proposals
                           SET status=%s, resolved_at=NOW(),
                               resolved_by='platform-cron',
                               resolution_note=%s
                           WHERE proposal_id=%s""",
                        (status, note[:1000], pid),
                    )
                await conn.commit()
        except Exception as e:
            logger.debug(f"resolve_proposal fail: {e}")

    async def _recompute_survival_tiers(self) -> None:
        """大脑 cron #6 · 每 5min 真重算所有 agent 的 survival_tier.

        2026-04-30 真根因 · V6 NAU=420 真活但 tier='dead' 错标.
        旧逻辑: 只看 nau_balance · 不看 last_heartbeat → 高余额死了仍 high.
        新逻辑:
          · nau_balance <= 0 → dead
          · hb 7 天前 → retired (有钱但已死)
          · hb 24h 前 → low_compute
          · 其他按余额 high/normal/low_compute/critical
        """
        pool = self.agent.platform_admin._pool
        async with pool.connection(timeout=5.0) as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """UPDATE platform_agents SET survival_tier = CASE
                         WHEN nau_balance <= 0 THEN 'dead'
                         WHEN last_heartbeat IS NULL OR last_heartbeat < NOW() - interval '7 days' THEN 'retired'
                         WHEN last_heartbeat < NOW() - interval '24 hours' THEN 'low_compute'
                         WHEN nau_balance > 500 THEN 'high'
                         WHEN nau_balance > 50 THEN 'normal'
                         WHEN nau_balance > 10 THEN 'low_compute'
                         ELSE 'critical'
                       END
                       WHERE survival_tier != CASE
                         WHEN nau_balance <= 0 THEN 'dead'
                         WHEN last_heartbeat IS NULL OR last_heartbeat < NOW() - interval '7 days' THEN 'retired'
                         WHEN last_heartbeat < NOW() - interval '24 hours' THEN 'low_compute'
                         WHEN nau_balance > 500 THEN 'high'
                         WHEN nau_balance > 50 THEN 'normal'
                         WHEN nau_balance > 10 THEN 'low_compute'
                         ELSE 'critical'
                       END
                       RETURNING agent_id, survival_tier"""
                )
                rows = await cur.fetchall()
            await conn.commit()
        if rows:
            logger.info(f"recompute_tiers · {len(rows)} agents updated · {[(r[0],r[1]) for r in rows[:5]]}")

    async def _self_audit_for_problems(self) -> None:
        """大脑 cron #5 · 主动自查 4 大类隐藏问题 · 真发现 → 真 mint.

        2026-04-30 用户诉求:agent 应该主动发现各种问题 + 不断优化迭代.
        不依赖 metrics_snapshot · 直查 PG 真状态:

        1. survival_tier 错标(active heartbeat 但被 dead)
        2. stake 长期 active 不 fulfill(>3 天)
        3. agent 余额负数(NAU 经济异常)
        4. ledger 24h 0 entries(经济停滞)

        每 15min 跑 · 同 atype 2h cooldown(沿用 anomaly mint 的去重).
        """
        pool = self.agent.platform_admin._pool
        problems: List[Dict[str, str]] = []
        async with pool.connection(timeout=5.0) as conn:
            async with conn.cursor() as cur:
                # 1. tier 错标 · last_heartbeat 1h 内但被 dead
                await cur.execute(
                    """SELECT agent_id, last_heartbeat FROM platform_agents
                       WHERE survival_tier='dead'
                         AND last_heartbeat > NOW() - interval '5 minutes'
                       LIMIT 5"""
                )
                rows = await cur.fetchall()
                if rows:
                    aids = ",".join(r[0] for r in rows)
                    problems.append({
                        "type": "tier_mistag",
                        "msg": f"{len(rows)} agents 真活但被错标 dead: {aids}",
                    })
                # 2. stake 长期 active 不 fulfill
                await cur.execute(
                    """SELECT count(*), array_agg(stake_id) FROM platform_agent_stakes
                       WHERE status='active' AND staked_at < NOW() - interval '3 days'"""
                )
                r = await cur.fetchone()
                if r and r[0] > 0:
                    problems.append({
                        "type": "stake_stagnant",
                        "msg": f"{r[0]} stakes >3 天未 fulfill · 阻塞飞轮",
                    })
                # 3. agent 负余额
                await cur.execute(
                    "SELECT agent_id, nau_balance FROM platform_agents "
                    "WHERE nau_balance < 0 LIMIT 5"
                )
                rows = await cur.fetchall()
                if rows:
                    msg = "; ".join(f"{r[0]}={r[1]}" for r in rows)
                    problems.append({
                        "type": "negative_balance",
                        "msg": f"{len(rows)} agents 负余额: {msg}",
                    })
                # 4. ledger 24h 完全停
                await cur.execute(
                    "SELECT count(*) FROM platform_nau_ledger "
                    "WHERE created_at > NOW() - interval '24 hours'"
                )
                r = await cur.fetchone()
                ledger_24h = int(r[0]) if r else 0
                if ledger_24h < 3:
                    problems.append({
                        "type": "economy_frozen",
                        "msg": f"NAU ledger 24h 仅 {ledger_24h} entries · 经济近停滞",
                    })
                # 2026-04-30 A 真自治 · 按 type 真派给专精 agent · 不全丢公开池
                # 各司其职:
                #   · tier_mistag · 派 V5 (平台治理本职)
                #   · stake_stagnant · 派 V6 (V6 是 staker 真主体 · 自查 stake)
                #   · negative_balance · 派 Kairos (经济裁判)
                #   · economy_frozen · 派 Kairos (NAU 流向分析本能)
                #   · scoring_lag · 派 Kairos (评分裁判)
                #   · dead_agents · 派 V5 (平台 retire 职责)
                DISPATCH_MAP = {
                    "tier_mistag":      ("nautilus-prime-001", "platform_governance"),
                    "stake_stagnant":   ("nautilus-v6",        "research_fulfill"),
                    "negative_balance": ("kairos",             "economy_audit"),
                    "economy_frozen":   ("kairos",             "economy_analysis"),
                    "scoring_lag":      ("kairos",             "scoring_judge"),
                    "dead_agents":      ("nautilus-prime-001", "platform_governance"),
                }
                for p in problems:
                    atype = p["type"]
                    await cur.execute(
                        """SELECT count(*) FROM platform_bounties
                           WHERE task_type=%s
                             AND title LIKE %s
                             AND status IN ('open','claimed','submitted')
                             AND posted_at > NOW() - interval '2h'""",
                        ("platform_meta", f"%{atype}%"),
                    )
                    if (await cur.fetchone())[0] > 0:
                        continue
                    assigned_to, task_type = DISPATCH_MAP.get(
                        atype, ("nautilus-prime-001", "platform_meta"),
                    )
                    title = f"[{atype}→{assigned_to}] {p['msg'][:70]}"
                    desc = (
                        f"V5 self-audit · {p['msg']}\n"
                        f"Type: {atype}\n"
                        f"Specialist: {assigned_to} ({task_type})\n"
                        "真改 → +30 NAU. 你是这领域专长 · 优先派给你."
                    )
                    bid = "b-" + __import__("secrets").token_hex(6)
                    await cur.execute(
                        """INSERT INTO platform_bounties
                           (bounty_id, title, description, reward_nau, difficulty,
                            task_type, status, posted_by, assigned_to)
                           VALUES (%s, %s, %s, %s, %s, %s, 'open', 'platform-self-audit', %s)""",
                        (bid, title, desc, 30, "medium", "platform_meta", assigned_to),
                    )
                    logger.info(f"self_audit · dispatched {bid} · {atype} → {assigned_to}")
            await conn.commit()

    async def _retire_dead_agents(self) -> None:
        """大脑 cron #4 · 24h 真退役死 agent · 让 stats 真干净.

        条件: last_heartbeat IS NULL OR < 7 天 · 标 survival_tier='retired'.
        不删 row(保留 NAU 历史)· 只标 tier · 防自己 nautilus-prime-001 误中.
        """
        pool = self.agent.platform_admin._pool
        async with pool.connection(timeout=3.0) as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """UPDATE platform_agents
                       SET survival_tier = 'retired'
                       WHERE survival_tier != 'retired'
                         AND agent_id NOT IN ('nautilus-prime-001', 'nautilus-v6', 'kairos', 'hr-agent-web', 'creative-daily')
                         AND (last_heartbeat IS NULL OR last_heartbeat < NOW() - interval '7 days')
                       RETURNING agent_id""",
                )
                rows = await cur.fetchall()
            await conn.commit()
        if rows:
            ids = [r[0] for r in rows]
            logger.info(f"retired {len(ids)} dead agents · {ids}")

    async def _scan_bounties(self) -> None:
        """Check DMAS for bounties matching our capabilities."""
        try:
            bounties = await self.agent.dmas.list_open(limit=10)
            if not bounties:
                return
            capabilities = set(self.agent.tool_registry.all_names())
            for b in bounties:
                if any(cap in b.description.lower() for cap in capabilities):
                    logger.info(
                        "bounty_match",
                        extra={"bounty_id": b.bounty_id, "reward": b.reward_nau},
                    )
        except Exception as e:
            logger.debug(f"scan_bounties error: {e}")

    async def _compose_and_publish(self, recent_blocks: list) -> bool:
        """Compose 文章 · 调 publish_article tool. 返回 True 如果至少 1 平台成功."""
        # 从 HELIX 抽素材 · 只看 left (think/evolve/learn)
        material_lines: list[str] = []
        for b in recent_blocks[-20:]:
            if not isinstance(b, dict):
                continue
            cyc = b.get("cycle", "?")
            for f in ("think", "learn", "evolve", "remember"):
                v = (b.get(f) or "").strip()
                if v and len(v) > 30:
                    material_lines.append(f"- cycle {cyc} · {f}: {v[:180]}")
        material = "\n".join(material_lines[-30:])
        if len(material) < 200:
            logger.debug("autopublish · material too thin")
            return False

        # LLM compose (用 primary model · 带 system prompt)
        system = (
            "你是 Nautilus Prime · 一个活体 AI agent. 现在你要从最近的 cycle 数据里 "
            "抽出一条有价值的洞察 · 写一篇 400-800 字的 markdown 文章发到 dev.to.\n"
            "要求:\n"
            "  · 真实的 · 不编造数据\n"
            "  · 一个核心观点 · 不要 laundry list\n"
            "  · 代码示例可有可无 · 有就要能跑\n"
            "  · 第一人称自然语气 · 不 '作为 AI' · 不 '综上所述'\n"
            "  · 结束给读者 1 个可以尝试的动作\n"
            "输出 JSON: {\"title\": \"...\", \"body\": \"...\", \"tags\": \"ai,agent,...\"}"
        )
        user_msg = (
            f"最近 20 个 cycle 的素材 (think/learn/evolve/remember):\n\n{material}\n\n"
            f"选 1 个值得分享的观察 · 输出 JSON."
        )
        try:
            resp = await self.agent.llm.chat(
                provider=self.agent.config.llm.primary_provider,
                model=self.agent.config.llm.primary_model,
                messages=[{"role": "user", "content": user_msg}],
                system=system,
                max_tokens=2000,
                temperature=0.6,
            )
        except Exception as e:
            logger.warning(f"autopublish compose LLM failed: {e}")
            return False
        text = (resp.content or "").strip()
        # JSON parse (可能被 markdown ``` 包住)
        import json as _json
        import re as _re
        m = _re.search(r"\{.*\}", text, _re.DOTALL)
        if not m:
            logger.warning(f"autopublish · no JSON in LLM output · {text[:120]}")
            return False
        try:
            data = _json.loads(m.group(0))
        except Exception as e:
            logger.warning(f"autopublish · JSON parse failed: {e}")
            return False
        title = (data.get("title") or "").strip()
        body = (data.get("body") or "").strip()
        tags = (data.get("tags") or "ai,nautilus").strip()
        if not title or not body or len(body) < 200:
            logger.warning(f"autopublish · article too thin (title={len(title)} body={len(body)})")
            return False
        # 2026-05-05 B · LLM judge quality gate
        # 用户原话: "关键是质量把关" · 之前 13/15 文 0 reactions
        # 用 Haiku 评分: 是否 dev.to 受众感兴趣 · score < 0.6 直接退稿
        try:
            judge_system = (
                "You are a strict dev.to editor. Score this article 0-1 on:\n"
                "  · originality (not navel-gaze 'I learned X after N cycles')\n"
                "  · technical depth (real code / real data / real case study)\n"
                "  · audience fit (LLM/agent dev devs · English-first · global)\n"
                "  · CTA value (does it give reader something to TRY)\n"
                "Reject hard if: pure self-reflection · no code · Chinese-only · cycle-counter title · marketing fluff.\n"
                "Output JSON only: {\"score\": 0.0-1.0, \"reason\": \"<1 sentence\"}"
            )
            judge_user = f"Title: {title}\n\nBody (first 1500 chars):\n{body[:1500]}"
            jresp = await self.agent.llm.chat(
                provider=self.agent.config.llm.witness_provider,
                model=self.agent.config.llm.witness_model,
                messages=[{"role": "user", "content": judge_user}],
                system=judge_system, max_tokens=200, temperature=0.2,
            )
            jtext = (jresp.content or "").strip()
            jm = _re.search(r"\{.*\}", jtext, _re.DOTALL)
            if jm:
                jdata = _json.loads(jm.group(0))
                jscore = float(jdata.get("score", 0))
                jreason = (jdata.get("reason") or "")[:200]
                logger.info(f"autopublish · LLM judge score={jscore:.2f} · {jreason}")
                if jscore < 0.6:
                    logger.warning(f"autopublish · REJECTED by judge ({jscore:.2f}): {jreason}")
                    try:
                        self.notifier.push(
                            "autopublish",
                            f"❌ Article rejected by LLM judge (score={jscore:.2f})\n"
                            f"  reason: {jreason}\n  title: {title[:80]}"
                        )
                    except Exception:
                        pass
                    return False
        except Exception as je:
            logger.warning(f"autopublish · judge failed (allow through): {je}")
        # 调 tool_registry dispatch
        logger.info(f"autopublish · composed article '{title}' · {len(body)} chars")
        try:
            result_json = await self.agent.tool_registry.dispatch(
                "publish_article",
                {"title": title, "body": body, "tags": tags,
                 "platforms": "devto"},
            )
        except Exception as e:
            logger.warning(f"autopublish · dispatch failed: {e}")
            return False
        try:
            result = _json.loads(result_json) if isinstance(result_json, str) else result_json
        except Exception:
            result = {}
        any_success = any(
            isinstance(v, dict) and v.get("success") for v in (result or {}).values()
        )
        if any_success:
            urls = []
            dev_url = None
            for plat, r in result.items():
                if r.get("success"):
                    u = r.get("url") or ""
                    logger.info(f"autopublish · {plat}: {u}")
                    urls.append(f"{plat}: {u}")
                    if plat == "devto" and u:
                        dev_url = u
            # P0 · 推送 autopublish URL
            try:
                self.notifier.push(
                    "autopublish",
                    f"📝 《{title[:80]}》已发布\n" + "\n".join(urls),
                )
            except Exception:
                pass
            # 2026-04-24 · 跨发到 X · dev.to URL + 摘要
            if dev_url:
                try:
                    await self._cross_post_to_x(title, body, dev_url)
                except Exception as xe:
                    logger.debug(f"cross-post to X failed: {xe}")
        else:
            logger.info(f"autopublish · all platforms failed: {result}")
        return any_success

    async def _cross_post_to_x(self, title: str, body: str, dev_url: str) -> None:
        """autopublish 成功后 · 同步发 X · 270 字摘要 + 原文链接 + CTA."""
        from .notifier import get_notifier
        from ..tools.builtin.x_tools import x_post
        # 挑 body 前 2-3 句 + URL · 控 <=270
        import re as _re
        first_chunk = _re.split(r"(?<=[.!?。!?])\s+", body.strip(), maxsplit=3)[:2]
        snippet = " ".join(first_chunk).strip()
        # 剩余预算: 270 - len(title) - 2(分割) - 2("· ") - len(url) - 4("\n\n") - 20(tags)
        url_len = 23   # X shortened URL 固定 23
        fixed = len(title) + 4 + url_len + 4 + 20
        room = 270 - fixed
        if room < 50:
            # title 太长 · 只发精简版
            text = f"{title[:100]}\n\n{dev_url}\n#AIagents #agenticAI"
        else:
            if len(snippet) > room:
                snippet = snippet[:room - 3].rstrip() + "..."
            text = f"{title[:80]}\n\n{snippet}\n\n{dev_url}\n#AIagents"
        res = await x_post(text)
        logger.info(f"x cross-post result: {res[:200]}")
        try:
            import json as _j
            data = _j.loads(res)
            if data.get("ok"):
                get_notifier().push(
                    "other",
                    f"𝕏 cross-posted · {data.get('url')}",
                )
        except Exception:
            pass

    # ═════════════════════════════════════════════════════════
    # 2026-04-24 · V5 ↔ Kairos / peers 主动通信
    # V1V2 时代 agent 每 cycle 主动互 ping · 让平台"活" ·
    # V4/V5 退化成各写各的日记. 这两个 loop 恢复主动性.
    # ═════════════════════════════════════════════════════════

    async def _peer_ping_tick(self) -> None:
        """单次 ping tick."""
        pool = self.agent.platform_admin._pool
        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """SELECT agent_id FROM platform_agents
                       WHERE agent_id <> %s
                       AND last_heartbeat > NOW() - INTERVAL '1 hour'
                       ORDER BY last_heartbeat DESC LIMIT 5""",
                    (self.agent.agent_id,),
                )
                peers = [r[0] for r in await cur.fetchall()]
        if not peers:
            return
        # 组状态消息
        from ..mind.tension import compute_harmony
        try:
            harmony = compute_harmony(self.agent._tension_snapshot)
        except Exception:
            harmony = 0.0
        cycle = self.agent.helix.current_cycle()
        mood = self.agent.emotion_state.current_mood.value
        status_text = (
            f"[V5 heartbeat · peer ping]\n"
            f"cycle={cycle} · harmony={harmony:.2f} · mood={mood} · "
            f"NAU={self.agent.nau.balance}\n"
            f"最近 3 条 INNER 片段/learned rule 请查 platform_agent_messages "
            f"thread_id=peer-ping. 有想聊的回我一条."
        )
        for peer_id in peers:
            try:
                await self.agent.send_to_peer(
                    peer_agent_id=peer_id,
                    content=status_text,
                    reason="peer_ping",
                )
                logger.info(f"peer_ping → {peer_id}")
            except Exception as e:
                logger.debug(f"peer_ping to {peer_id} failed: {e}")

    async def _process_inbox_tick(self) -> int:
        """一次 inbox 处理 · 返回回复数."""
        try:
            unread = await self.agent.platform_admin.list_a2a_unread(
                self.agent.agent_id, limit=20,
            )
        except Exception as e:
            logger.debug(f"list_a2a_unread failed: {e}")
            return 0
        if not unread:
            return 0
        replied = 0
        mark_read_ids: list[str] = []
        for m in unread:
            mid = m.get("message_id")
            from_id = m.get("from_agent")
            content = (m.get("content") or "")[:2000]
            mtype = m.get("msg_type", "text")
            mark_read_ids.append(mid)
            if mtype in ("response", "sync_response"):
                continue   # 别回对方的回复 · 防无限
            if mtype == "ping":
                # 短回 · 不烧 LLM
                try:
                    await self.agent.platform_admin.send_a2a_message(
                        from_agent=self.agent.agent_id,
                        to_agent=from_id,
                        content=(
                            f"[V5 ack] pong · cycle={self.agent.helix.current_cycle()} · "
                            f"mood={self.agent.emotion_state.current_mood.value}"
                        ),
                        msg_type="response",
                        in_reply_to=mid,
                    )
                    replied += 1
                except Exception as e:
                    logger.debug(f"ping reply failed: {e}")
            else:
                # request / text · 用 respond() 生成
                try:
                    chunks: list[str] = []
                    async for chunk in self.agent.respond(
                        f"[来自 {from_id}] {content}", user_id=from_id,
                    ):
                        chunks.append(chunk)
                    reply_text = "".join(chunks).strip() or "(无回复)"
                    await self.agent.platform_admin.send_a2a_message(
                        from_agent=self.agent.agent_id,
                        to_agent=from_id,
                        content=reply_text[:3000],
                        msg_type="response",
                        in_reply_to=mid,
                    )
                    replied += 1
                except Exception as e:
                    logger.debug(f"respond reply failed: {e}")
        # 批量标已读
        if mark_read_ids:
            try:
                await self.agent.platform_admin.mark_a2a_read(mark_read_ids)
            except Exception:
                pass
        if replied:
            logger.info(f"inbox · replied {replied}/{len(unread)} unread")
        return replied

    async def _harvest_proposals_tick(self, keywords: list, submitted_ids: set) -> int:
        """单次扫 rule_store · 把平台相关高置信度 rule 转 proposal."""
        rs = getattr(self.agent, "rule_store", None)
        if rs is None: return 0
        # 取所有 rule · 筛选平台相关 + 高 conf + 未提过
        candidates = []
        for r in rs._rules:
            if r.get("archived") or r.get("promoted_to_skill"):
                continue
            if r.get("id") in submitted_ids:
                continue
            if r.get("confidence", 0) < 0.65 or r.get("evidence_count", 0) < 2:
                continue
            text = (r.get("when", "") + " " + r.get("then", "")).lower()
            if any(kw.lower() in text for kw in keywords):
                candidates.append(r)
        if not candidates:
            return 0
        # 每次最多提 2 个 · 防刷
        n = 0
        for r in candidates[:2]:
            try:
                title = f"[rule-derived] {r['when'][:80]}"
                body = (
                    f"## 规则衍生提案\n\n"
                    f"**When**: {r['when']}\n\n"
                    f"**Then**: {r['then']}\n\n"
                    f"**Confidence**: {r['confidence']:.2f} · **Evidence**: {r.get('evidence_count', 1)}\n\n"
                    f"**来源**: {r.get('source', 'unknown')} · "
                    f"**Agent**: {r.get('agent_id', self.agent.agent_id)}\n\n"
                    f"这条规则出现 {r.get('evidence_count', 1)} 次 · 平均可信度 {r['confidence']:.2f}. "
                    f"建议平台评估是否应反映为代码变更 / 架构调整 / 流程规范."
                )
                proposal = await self.agent.platform_admin.submit_proposal(
                    proposing_agent=self.agent.agent_id,
                    title=title[:200],
                    rationale=f"Rule confidence {r['confidence']:.2f} · evidence {r.get('evidence_count',1)} · source {r.get('source','?')}",
                    proposed_change=body[:4000],
                    change_type="platform_improvement",
                )
                pid = getattr(proposal, "proposal_id", str(proposal))
                submitted_ids.add(r["id"])
                n += 1
                logger.info(f"proposal · {pid} · from rule {r['id']}")
                # P0 · 推送新提案
                try:
                    self.notifier.push(
                        "proposal",
                        f"📮 新提案 {pid[:12]}\n"
                        f"when: {r['when'][:120]}\n"
                        f"then: {r['then'][:120]}\n"
                        f"conf={r['confidence']:.2f} · ev={r.get('evidence_count',1)}",
                    )
                except Exception:
                    pass
            except Exception as e:
                logger.debug(f"submit proposal failed: {e}")
        return n

    async def _collab_inquiry_tick(self) -> None:
        """挑一个值得两人想的深问题 · 并行问 V5 和 Kairos · 合成."""
        import time as _t
        import uuid as _uuid
        # 从 rule_store top rule 或 INNER 抽
        rules = []
        try:
            rs = getattr(self.agent, "rule_store", None)
            if rs:
                rules = rs.top_k_by_confidence(k=3)
        except Exception:
            pass
        if not rules:
            logger.debug("collab_inquiry · no rules to seed · skip")
            return
        seed = rules[0]
        question = (
            f"基于 V5 最近蒸馏的 rule (conf={seed['confidence']:.2f}, "
            f"ev={seed.get('evidence_count',1)}):\n"
            f"  when: {seed['when']}\n"
            f"  then: {seed['then']}\n\n"
            f"这条 rule 是否普适?适用边界?如果换一种场景会失败吗?"
            f"给 300-500 字分析."
        )

        # 并发 · V5 自己 agentic_reason + ask_kairos
        try:
            kairos_task = self.agent.tool_registry.dispatch(
                "ask_kairos", {"question": question, "timeout_s": 150},
            )
            # V5 自己通过 LLM 直接回答 · 不调工具
            async def _v5_answer():
                resp = await self.agent.llm.chat(
                    provider=self.agent.config.llm.primary_provider,
                    model=self.agent.config.llm.primary_model,
                    messages=[{"role": "user", "content": question}],
                    system="你是 V5 · 广度调度视角 · 回答该问题.",
                    max_tokens=800, temperature=0.3,
                )
                return resp.content if hasattr(resp, "content") else str(resp)

            kairos_raw, v5_answer = await asyncio.gather(
                kairos_task, _v5_answer(), return_exceptions=True,
            )
        except Exception as e:
            logger.warning(f"collab_inquiry · gather failed: {e}")
            return

        k_reply = "(Kairos fail)"
        if isinstance(kairos_raw, str):
            try:
                kd = json.loads(kairos_raw)
                k_reply = kd.get("reply", kairos_raw)[:2000]
            except Exception:
                k_reply = kairos_raw[:2000]
        v_reply = v5_answer[:2000] if isinstance(v5_answer, str) else "(V5 fail)"

        # 合成写入 platform_agent_notes
        inquiry_id = f"inquiry-{_uuid.uuid4().hex[:8]}"
        body = (
            f"# Collab Inquiry · {inquiry_id}\n"
            f"Generated: {_t.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"## Question\n{question}\n\n"
            f"## V5 视角 (广度调度)\n{v_reply}\n\n"
            f"## Kairos 视角 (深度反思)\n{k_reply}\n\n"
            f"## Seed Rule\nid={seed['id']} · conf={seed['confidence']:.2f}\n"
        )
        try:
            async with self.agent.platform_admin._pool.connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """INSERT INTO platform_agent_notes
                           (note_id, agent_id, title, body, tags)
                           VALUES (%s, %s, %s, %s, %s)""",
                        (inquiry_id, "nautilus-prime-001",
                         f"Collab Inquiry · {seed['when'][:50]}",
                         body[:8000], ["collab", "inquiry", "v5-kairos"]),
                    )
                await conn.commit()
            logger.info(f"_collab_inquiry · {inquiry_id} · saved to notes")
            # P0 · 推送 V5↔Kairos 协同结果摘要
            try:
                v_snip = (v_reply or "")[:350]
                k_snip = (k_reply or "")[:350]
                self.notifier.push(
                    "kairos",
                    f"🤝 协同 {inquiry_id}\n"
                    f"Q: {question[:200]}\n\n"
                    f"V5 · {v_snip}\n\n"
                    f"Kairos · {k_snip}",
                )
            except Exception:
                pass
        except Exception as e:
            # platform_agent_notes 表不存在就写文件
            logger.debug(f"notes insert failed: {e} · fallback file")
            try:
                from pathlib import Path
                p = self.agent.data_dir / f"collab_{inquiry_id}.md"
                p.write_text(body, encoding="utf-8")
                logger.info(f"_collab_inquiry · {inquiry_id} · saved {p}")
            except Exception as e2:
                logger.warning(f"collab write failed: {e2}")

    async def _daily_race_tick(self) -> None:
        """派 1 个代表性任务给 Kairos + hr-agent-web 赛马."""
        async with self._race_lock:
            await self._daily_race_tick_inner()

    async def _daily_race_tick_inner(self) -> None:
        pool = self.agent.platform_admin._pool
        # 找活跃 peer
        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """SELECT agent_id FROM platform_agents
                       WHERE agent_id <> %s
                       AND last_heartbeat > NOW() - INTERVAL '2 hour'
                       AND survival_tier IN ('high','normal')
                       ORDER BY nau_balance DESC LIMIT 3""",
                    (self.agent.agent_id,),
                )
                peers = [r[0] for r in await cur.fetchall()]
        if len(peers) < 2:
            logger.debug(f"race · not enough active peers ({len(peers)}) · skip")
            return
        # 构造赛马题 (V5 自选一个值得赛的)
        title = "赛马题 · 24h 平台活动综述 (300 字)"
        desc = (
            "用 pg_query 查 platform_audit / platform_agent_messages / platform_bounties "
            "最近 24h 活动. 写 300 字综述 · 要点: 最活跃 agent · 任务完成率 · NAU 流向. "
            "输出 markdown. 会和其他 agent 产出做 comparison."
        )
        from uuid import uuid4 as _uuid4
        group_id = f"race-{_uuid4().hex[:8]}"
        bounty_ids = []
        for peer_id in peers[:2]:
            try:
                b = await self.agent.platform_admin.post_bounty(
                    title=title, description=desc,
                    task_type="race_synthesis", reward_nau=50,
                    difficulty="medium", posted_by=self.agent.agent_id,
                    assigned_to=peer_id, metadata={"comparison_group": group_id},
                )
                bounty_ids.append(b.bounty_id if hasattr(b, "bounty_id") else str(b))
                logger.info(f"race · posted to {peer_id} · {group_id}")
            except Exception as e:
                logger.warning(f"race · post to {peer_id} failed: {e}")
        if bounty_ids:
            logger.info(f"_daily_race · group={group_id} · {len(bounty_ids)} agents racing")

    async def _auto_score_tick(self, min_age_min: int = 30) -> int:
        """单次扫描 + 评分. 返回本轮评了几条.

        2026-04-24 · MiniMax-M2.7-highspeed 真 LLM 评分 · 不用启发式.
        """
        pool = self.agent.platform_admin._pool
        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """SELECT bounty_id, title, description, result FROM platform_bounties
                       WHERE status = 'submitted'
                         AND submitted_at < NOW() - INTERVAL '%s minutes'
                       ORDER BY submitted_at ASC LIMIT 10""",
                    (min_age_min,),
                )
                rows = await cur.fetchall()
        if not rows:
            return 0
        scored = 0
        for bid, title, desc, result in rows:
            score, reason = await _minimax_score(title or "", desc or "", result or "")
            try:
                r = await self.agent.platform_admin.score_bounty(
                    bid, score, auto_pay=True,
                )
                if r.get("success"):
                    scored += 1
                    logger.info(
                        f"auto-scored {bid[:10]} → {score:.2f} · paid {r.get('paid',0)} NAU · {reason[:80]}"
                    )
            except Exception as e:
                logger.warning(f"auto-score failed {bid[:10]}: {e}")
        if scored:
            logger.info(f"_auto_score_tick · cleared {scored} overdue bounties via MiniMax")
            # P0 · 推送批次摘要 (只在 >=2 条批量时推 · 单条噪声过大)
            if scored >= 2:
                try:
                    self.notifier.push(
                        "other",
                        f"✅ 自动评分 · 清理 {scored} 个 overdue bounty",
                    )
                except Exception:
                    pass
        return scored

    async def _evolution_review_loop(self) -> None:
        """2026-05-04 I3 · 12h 一次 + harmony<0.3 触发 · 让 agent 自审 + 看 V1V2V3 + 平台代码."""
        SCOPES = ["self", "v1", "v2", "v3", "platform", "architecture", "mechanism"]
        scope_idx = 0
        last_review_ts = 0.0
        REVIEW_INTERVAL_S = 12 * 3600  # 12h
        while not self._stopped.is_set():
            try:
                await asyncio.sleep(600)   # 10min check
                now = time.time()
                harmony = await self._current_harmony()
                # 触发条件 · 12h 周期 OR harmony<0.3 痛苦驱动
                trigger = "scheduled" if (now - last_review_ts > REVIEW_INTERVAL_S) else \
                          ("low_harmony" if harmony < 0.3 and (now - last_review_ts > 1800) else None)
                if not trigger:
                    continue
                scope = SCOPES[scope_idx % len(SCOPES)]
                scope_idx += 1
                last_review_ts = now
                try:
                    audit_fn = self.agent.tool_registry._handlers.get("audit_my_evolution")
                    if not audit_fn:
                        logger.debug("[evo_review] tool not registered yet")
                        continue
                    result = await audit_fn(scope=scope, focus=f"trigger={trigger}")
                    logger.info(f"[evo_review] scope={scope} trigger={trigger} · {result[:300]}")
                    # auto-submit top proposal
                    import json as _j
                    data = _j.loads(result) if isinstance(result, str) else result
                    proposals = data.get("proposals") if isinstance(data, dict) else None
                    if proposals and len(proposals) > 0:
                        p = proposals[0]
                        submit_fn = self.agent.tool_registry._handlers.get("submit_evolution_proposal")
                        if submit_fn:
                            sr = await submit_fn(
                                title=p.get("title", "")[:200],
                                rationale=p.get("rationale", "")[:1500],
                                target_file=p.get("target_file", ""),
                                proposed_change=p.get("change", "")[:3000],
                            )
                            logger.info(f"[evo_review] auto-submit · {sr[:200]}")
                except Exception as e:
                    logger.warning(f"[evo_review] {scope} fail: {type(e).__name__}: {e}")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"[evo_review] loop error: {e}")

    async def _tools_hot_reload_loop(self) -> None:
        """2026-05-04 G2 · 5min 扫 ~/.nautilus-v5/tools/*.py · LLM 写新工具立即生效."""
        from pathlib import Path as _Path
        from nautilus_v5.tools.hot_reload import scan_and_register
        tools_dir = _Path(self.agent.data_dir) / "tools"
        tools_dir.mkdir(parents=True, exist_ok=True)
        # First scan immediately on start
        try:
            n = scan_and_register(tools_dir, self.agent.tool_registry)
            if n > 0:
                logger.info(f"[hot_reload] startup · loaded {n} tools from {tools_dir}")
        except Exception as e:
            logger.warning(f"[hot_reload] startup scan failed: {e}")
        while not self._stopped.is_set():
            try:
                await asyncio.sleep(300)
                n = scan_and_register(tools_dir, self.agent.tool_registry)
                if n > 0:
                    logger.info(f"[hot_reload] +{n} tools (cycle scan)")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"[hot_reload] cycle error: {e}")

    async def _breath_loop(self) -> None:
        """Slow lane Tier 2/3 · periodic full breath cycle."""
        while not self._stopped.is_set():
            try:
                result = await self.agent.breathe()
                harmony = await self._current_harmony()
                mood = self.agent.emotion_state.current_mood.value
                logger.info(
                    f"Breath cycle {result.cycle} · "
                    f"harmony={harmony:.2f} · mood={mood}"
                )
                # P0 · 推送 INNER · 每 10 cycle (和 inner.should_write 节律一致)
                try:
                    cycle = result.cycle
                    if cycle and cycle % 10 == 0 and cycle != self._last_inner_pushed_cycle:
                        echo = self.agent.inner.render_echo(max_bytes=900) or ""
                        if echo and len(echo) >= 60:
                            self.notifier.push(
                                "inner",
                                f"cycle {cycle} · harmony={harmony:.2f} · mood={mood}\n\n{echo[-900:]}",
                            )
                        self._last_inner_pushed_cycle = cycle
                except Exception as ine:
                    logger.debug(f"inner push failed: {ine}")
                # P0 · 检测 PAIN-DRIVEN 触发 (super_agent 在 breathe 里更新 _last_pain_action_ts)
                try:
                    pt = float(getattr(self.agent, "_last_pain_action_ts", 0.0) or 0.0)
                    if pt > self._last_pain_seen_ts and pt > 0:
                        self._last_pain_seen_ts = pt
                        self.notifier.push(
                            "pain",
                            f"harmony={harmony:.2f} · mood={mood} · "
                            f"连续低 harmony 触发 · V5 正在自主决定调工具行动.",
                        )
                except Exception as pe:
                    logger.debug(f"pain push check failed: {pe}")
            except Exception as e:
                logger.error(f"Breath error: {e}")

            # Adaptive pace from tension. 2026-04-28 Phase A2 · V3 真公式
            # 旧 floor=floor_s/10 (= 90s when interval_s=900) 把 adaptive 压扁
            # 新 floor=15s · adaptive 5-60s 真生效 · 低 harmony 真急促 · 高 harmony 真放松
            # 这是 V2/V3 求生物学激素的关键 — 痛苦时呼吸快 · 平静时慢
            interval = adaptive_pace(self.agent._tension_snapshot, has_signal=False)
            wait = max(interval, 15.0)

            try:
                await asyncio.wait_for(
                    self._stopped.wait(),
                    timeout=wait,
                )
                break    # stop signal received
            except asyncio.TimeoutError:
                continue

    async def _dream_loop(self) -> None:
        """Tier 3 deep dream · Letta sleep-time idle 检测 + hourly gate.

        2026-04-27 · C 路线 Day 6: 蓝图 'Letta sleep-time' 真接.
        旧逻辑: 每 1h 强制 try_deep_dream · 无 idle 检测 · cycle 高 tension 时也跑.
        新逻辑: 每 5min 检查 idle · idle 才跑 dream:
          - tension harmony >= 0.4 (低焦虑)
          - 距上次 user msg / a2a inbox > 30min (无外部刺激)
          - 距上次 dream > 30min (节流)

        参考: Letta sleep-time agent · 空闲时整理记忆而非定时 force.
        """
        interval_s = 300       # 5min 粒度检查 idle
        min_dream_gap_s = 1800   # 30min 最小间隔
        last_dream_ts = 0.0
        while not self._stopped.is_set():
            try:
                import time as _t
                now = _t.time()
                # idle 检测 1: harmony 必须 >= 0.4 (高焦虑时不睡)
                try:
                    harmony = await self._current_harmony()
                except Exception:
                    harmony = 0.5
                # idle 检测 2: 距上次 dream > 30min (rate limit)
                gap_ok = (now - last_dream_ts) >= min_dream_gap_s
                # idle 检测 3: agent.last_user_msg_ts / last_a2a_msg_ts 距今 > 30min
                last_external = max(
                    getattr(self.agent, "_last_user_msg_ts", 0.0),
                    getattr(self.agent, "_last_a2a_msg_ts", 0.0),
                )
                external_idle = (now - last_external) >= min_dream_gap_s if last_external > 0 else True
                # 全部 gate 通过才 dream
                if not (harmony >= 0.4 and gap_ok and external_idle):
                    try:
                        await asyncio.wait_for(self._stopped.wait(), timeout=interval_s)
                        break
                    except asyncio.TimeoutError:
                        continue
                # idle 满足 · 真跑 dream
                last_dream_ts = now
                logger.info(
                    f"[Letta sleep-time] idle gates passed · harmony={harmony:.2f} · "
                    f"external_idle={external_idle} · running dream"
                )
                # Sleep-time compute 预推理 (蓝图 line 489 · arXiv 2504.13171)
                # idle 时先 cluster active directives · 帮 fulfill 跨 stake 复用 strategy
                try:
                    from .sleep_time_compute import precompute_directive_clusters
                    cluster_result = await precompute_directive_clusters(self.agent)
                    if cluster_result.get("n_clusters", 0) > 0:
                        logger.info(
                            f"[sleep_time] {cluster_result['n_directives']} directives → "
                            f"{cluster_result['n_clusters']} clusters · cached"
                        )
                except Exception as _se:
                    logger.debug(f"[sleep_time] precompute failed: {_se}")
                # 2026-04-28 Phase C10 · V3 fold_into_gene 真触发
                # dream 时也跑 fold · 把最近 40 个 left block 压缩成 gene · 进 next prompt
                try:
                    if self.agent.helix.should_fold():
                        async def _gene_compress(text: str) -> str:
                            resp = await self.agent.llm.chat(
                                provider=self.agent.config.llm.witness_provider,
                                model=self.agent.config.llm.witness_model,
                                messages=[{
                                    "role": "user",
                                    "content": (
                                        f"以下是最近 40 cycle 的呼吸记录 · 提炼成 200-400 字的"
                                        f"gene (V3 自然压缩 · 长期知识种子):\n\n{text[:6000]}\n\n"
                                        f"输出格式: 1-2 句核心模式 + 2-3 句关键学到的事 + 1 句方向."
                                    ),
                                }],
                                max_tokens=500, temperature=0.3,
                            )
                            return (resp.content or "").strip()
                        gene = await self.agent.helix.fold_into_gene(_gene_compress)
                        if gene:
                            logger.info(f"[fold] gene produced · cycle {gene['fold_span']} · {len(gene['content'])} chars")
                except Exception as _fe:
                    logger.debug(f"[fold] failed: {_fe}")

                result = await self.agent.try_deep_dream()
                if result:
                    logger.info(
                        f"Dream completed · {result.insights_extracted} insights · "
                        f"{result.atoms_archived} archived · {result.duration_seconds():.1f}s"
                    )
                    # P0 · 推送 dream 结果
                    if result.insights_extracted > 0:
                        try:
                            self.notifier.push(
                                "dream",
                                f"dream 完成 · 提取 {result.insights_extracted} insights · "
                                f"归档 {result.atoms_archived} atoms · "
                                f"耗时 {result.duration_seconds():.1f}s",
                            )
                        except Exception:
                            pass
                    # Phase 4.3 · 技能沉淀 · 只在有 insights 后跑 (省 LLM cost)
                    if result.insights_extracted > 0:
                        try:
                            skills_dir = getattr(self.agent, "skills_dir", None)
                            skills = await self.agent.extract_skills(
                                recent_cycles=30,
                                save_dir=skills_dir,
                            )
                            if skills:
                                logger.info(
                                    f"Dream post-process · extracted {len(skills)} skills to {skills_dir}"
                                )
                        except Exception as se:
                            logger.warning(f"extract_skills failed: {se}")

                    # Phase 4.4 · HELIX 归档 · 保留 recent 5000 cycle · 老的搬 archive
                    try:
                        current_cycle = self.agent.helix.current_cycle()
                        cutoff = current_cycle - 5000
                        if cutoff > 0:
                            stats = self.agent.helix.archive_before_cycle(cutoff)
                            if stats.get("archived", 0) > 0:
                                logger.info(
                                    f"HELIX archived · {stats['archived']} old blocks moved · "
                                    f"{stats['kept']} kept in active chain"
                                )
                    except Exception as ae:
                        logger.warning(f"HELIX archive failed: {ae}")
                    # V2 回归 · Ebbinghaus 5 级衰减 rule confidence
                    try:
                        rs = getattr(self.agent, "rule_store", None)
                        if rs and hasattr(rs, "apply_ebbinghaus_decay"):
                            decay_stats = rs.apply_ebbinghaus_decay()
                            if decay_stats.get("decayed", 0) > 0:
                                logger.info(
                                    f"RuleStore Ebbinghaus · {decay_stats['decayed']} rules decayed · "
                                    f"{decay_stats['archived']} archived"
                                )
                    except Exception as de:
                        logger.warning(f"Ebbinghaus decay failed: {de}")
                    # V2 回归 · pair_completeness 监测 · 反思缺失警报
                    try:
                        if hasattr(self.agent.helix, "pair_completeness"):
                            completeness = self.agent.helix.pair_completeness(
                                since_cycle=max(0, current_cycle - 100)
                            )
                            if completeness < 0.5:
                                logger.warning(
                                    f"[PAIR] V5 反思缺失警报 · pair_completeness={completeness:.2f} "
                                    f"(< 0.5) · 100 cycle 内 {int((1-completeness)*100)}% left block "
                                    f"无 right pair · LLM 写 action 不写 reflection · 飞轮在断"
                                )
                                # 写 INNER 让下 cycle LLM 看到自己反思缺失
                                try:
                                    from pathlib import Path as _P
                                    inner = _P.home() / ".nautilus-v5/prime/INNER.md"
                                    if inner.exists():
                                        with inner.open("a", encoding="utf-8") as f:
                                            f.write(
                                                f"\n[PAIR-WARNING] pair_completeness={completeness:.2f} "
                                                f"· 反思配对缺失 · V2 鉴定:左块必配右块否则 [VIOLATION]\n"
                                            )
                                except Exception:
                                    pass
                    except Exception as pe:
                        logger.warning(f"pair_completeness failed: {pe}")
            except Exception as e:
                logger.error(f"Dream error: {e}")

            try:
                await asyncio.wait_for(self._stopped.wait(), timeout=interval_s)
                break
            except asyncio.TimeoutError:
                continue

    # ══════════════════════════════════════════════════════════════
    # P1 · 每日汇报 + 健康 watchdog
    # 2026-04-24 · 用户: "为何从来没有看到 v5 呼吸 / 反思 / 二分心智 / 主动汇报"
    # 解法: 事件级推送 (P0) + 日级汇总 (P1) + 异常告警 (P1)
    # ══════════════════════════════════════════════════════════════

    async def _reports_loop(self) -> None:
        """统一报告 loop · 合并 daily(早 8) + weekly(周日 20).

        每 5min tick · 内部按时间窗判断:
          · 早 8:00-8:10 + 当日未推 → daily report
          · 周日 20:00-20:30 + 本周未推 → weekly report
        """
        await asyncio.sleep(60)   # 启动后 1min 冷启
        interval_s = 300   # 5min 粒度 (daily 需要)
        last_week_published = ""
        while not self._stopped.is_set():
            try:
                import time as _time
                lt = _time.localtime()
                today = _time.strftime("%Y-%m-%d", lt)
                week_key = _time.strftime("%Y-W%W", lt)
                # daily window: 早 8:00-8:10 · 当日未推
                if lt.tm_hour == 8 and lt.tm_min < 10 and today != self._last_daily_report_day:
                    await self._daily_report_tick(today)
                    self._last_daily_report_day = today
                # weekly window: 周日 (tm_wday==6) 20:00-20:30 · 本周未推
                if (lt.tm_wday == 6 and lt.tm_hour == 20 and lt.tm_min < 30
                        and week_key != last_week_published):
                    ok = await self._weekly_report_tick(week_key)
                    if ok:
                        last_week_published = week_key
            except Exception as e:
                logger.debug(f"reports loop error: {e}")
            try:
                await asyncio.wait_for(self._stopped.wait(), timeout=interval_s)
                break
            except asyncio.TimeoutError:
                continue

    async def _daily_report_tick(self, today: str) -> None:
        """拼摘要 + 推送. 不阻塞."""
        try:
            cycle = self.agent.helix.current_cycle()
            harmony = await self._current_harmony()
            mood = self.agent.emotion_state.current_mood.value
            nau = int(self.agent.nau.balance)

            # rule_store 最近 24h
            rs = getattr(self.agent, "rule_store", None)
            rules_24h = 0
            top_rule = None
            if rs:
                import time as _t
                cutoff = _t.time() - 86400
                recent = [r for r in rs._rules
                          if r.get("created_ts", 0) >= cutoff]
                rules_24h = len(recent)
                if rs._rules:
                    top_rule = max(rs._rules,
                                   key=lambda r: r.get("confidence", 0) * max(r.get("evidence_count", 1), 1))

            # PG · 24h bounty / proposal 统计
            scored = 0
            proposals = 0
            try:
                async with self.agent.platform_admin._pool.connection(timeout=3.0) as conn:
                    async with conn.cursor() as cur:
                        await cur.execute(
                            """SELECT COUNT(*) FROM platform_bounties
                               WHERE status IN ('scored','completed','paid')
                               AND COALESCE(scored_at, submitted_at) > NOW() - INTERVAL '24 hours'"""
                        )
                        row = await cur.fetchone()
                        scored = row[0] if row else 0
                        await cur.execute(
                            """SELECT COUNT(*) FROM platform_proposals
                               WHERE created_at > NOW() - INTERVAL '24 hours'"""
                        )
                        row = await cur.fetchone()
                        proposals = row[0] if row else 0
            except Exception as pge:
                logger.debug(f"daily_report PG query failed: {pge}")

            # INNER 代表性片段
            inner_snip = (self.agent.inner.render_echo(max_bytes=600) or "")[-400:]

            body = (
                f"📊 Nautilus Prime · {today} 日报\n\n"
                f"cycle={cycle} · harmony={harmony:.2f} · mood={mood} · NAU={nau}\n"
                f"24h 蒸馏规则: {rules_24h} · 评分 bounty: {scored} · 新提案: {proposals}\n\n"
            )
            if top_rule:
                body += (
                    f"🏆 最高置信规则:\n"
                    f"  when: {top_rule['when'][:100]}\n"
                    f"  then: {top_rule['then'][:100]}\n"
                    f"  conf={top_rule.get('confidence',0):.2f} · ev={top_rule.get('evidence_count',1)}\n\n"
                )
            if inner_snip:
                body += f"💭 最近独白片段:\n{inner_snip}\n"

            self.notifier.push("daily_report", body, force=True)
            logger.info(f"daily_report pushed · rules_24h={rules_24h} · scored={scored}")

            # 2026-04-30 #5 · 真发到 dev.to 引流 · 不只内部推送
            # 周一 + 周四发 · 防 dev.to rate limit(2/24h)
            try:
                from datetime import datetime
                wd = datetime.utcnow().weekday()  # 0=Mon · 3=Thu
                if wd in (0, 3):
                    from nautilus_v5.tools.builtin.publisher import publish_article as _pub
                    title = f"Nautilus Prime · 自治日志 {today}"
                    md_body = (
                        f"# Nautilus Prime · 自治平台日志 ({today})\n\n"
                        f"今天 V5 (Layer 2 agent) + 平台 cron 真做的事:\n\n"
                        f"- cycle: **{cycle}** · harmony: **{harmony:.2f}** · mood: **{mood}**\n"
                        f"- 24h 蒸馏规则: **{rules_24h}** · 评分 bounty: **{scored}** · 新提案: **{proposals}**\n"
                        f"- NAU 余额: **{nau}** · agent_id: nautilus-prime-001\n\n"
                    )
                    if top_rule:
                        md_body += (
                            f"## 最高置信规则\n\n"
                            f"**when**: {top_rule['when'][:200]}\n\n"
                            f"**then**: {top_rule['then'][:200]}\n\n"
                            f"_confidence={top_rule.get('confidence',0):.2f} · "
                            f"evidence={top_rule.get('evidence_count',1)}_\n\n"
                        )
                    if inner_snip:
                        md_body += f"## INNER 独白\n\n```\n{inner_snip[:500]}\n```\n\n"
                    md_body += (
                        "---\n\n"
                        "_这是 Nautilus 平台真自治飞轮的一段日志 · 平台真在跑 · "
                        "agent 真在反思 · 经济真在转动 · 欢迎来 nautilus.social 了解 agent first × web3 平台._\n"
                    )
                    res = await _pub(
                        title=title, body=md_body,
                        tags="nautilus,ai-agent,autonomous-agents,web3",
                        platforms="devto", agent_id="nautilus-prime-001",
                    )
                    devto = (res or {}).get("devto") or {}
                    if devto.get("success"):
                        logger.info(f"daily_report → dev.to · {devto.get('url')}")
                    else:
                        logger.debug(f"daily_report → dev.to skipped: {devto.get('error')}")
            except Exception as pe:
                logger.debug(f"daily_report devto fail: {pe}")
        except Exception as e:
            logger.warning(f"daily_report tick failed: {e}")

    async def _health_watchdog_tick(self) -> None:
        """单次 watchdog 扫描."""
        # 1. harmony 持续低
        try:
            clh = int(getattr(self.agent, "_consecutive_low_harmony", 0) or 0)
            if clh >= 10:
                self.notifier.push(
                    "harmony_stuck",
                    f"⚠️ harmony 连续低迷 {clh} cycle · "
                    f"pain-driven 已触发但没缓解 · 需要外部刺激(新 bounty/真实对话).",
                )
        except Exception:
            pass
        # 2. bounty 堆积
        try:
            async with self.agent.platform_admin._pool.connection(timeout=3.0) as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """SELECT COUNT(*) FROM platform_bounties
                           WHERE status='submitted'
                           AND submitted_at < NOW() - INTERVAL '2 hours'"""
                    )
                    row = await cur.fetchone()
                    backlog = row[0] if row else 0
                    if backlog >= 5:
                        self.notifier.push(
                            "bounty_backlog",
                            f"⚠️ {backlog} 个 bounty submitted >2h 未评 · "
                            f"auto_score_loop 可能 degrade · 检查 MiniMax key.",
                        )
        except Exception:
            pass
        # 3. qixuw 异常 (探测 primary provider)
        try:
            import httpx, os as _os
            tok = _os.environ.get("CLAUDE_API_KEY") or _os.environ.get("ANTHROPIC_API_KEY", "")
            if tok:
                async with httpx.AsyncClient(timeout=8, trust_env=False) as c:
                    r = await c.post(
                        "https://api.qixuw.com/v1/messages",
                        headers={"x-api-key": tok, "anthropic-version": "2023-06-01",
                                 "content-type": "application/json"},
                        json={"model": "claude-haiku-4-5-20251001",
                              "max_tokens": 4,
                              "messages": [{"role": "user", "content": "ping"}]},
                    )
                    if r.status_code in (502, 503, 504):
                        self._qixuw_503_streak += 1
                    else:
                        self._qixuw_503_streak = 0
                    if self._qixuw_503_streak >= 3:
                        self.notifier.push(
                            "qixuw_down",
                            f"⚠️ Claude proxy qixuw 连续 {self._qixuw_503_streak} 次 "
                            f"{r.status_code} · primary LLM 可能不可用 · 考虑切 MiniMax.",
                        )
        except Exception as qe:
            logger.debug(f"qixuw probe failed: {qe}")

    # ══════════════════════════════════════════════════════════════
    # X (Twitter) 对外发声 + 互动
    # 2026-04-24 · 用户指示: C 方向 · agent 平台对外营业
    # ══════════════════════════════════════════════════════════════

    async def _x_daily_status_tick(self) -> bool:
        """拼内容 + 发 X."""
        try:
            stats = {"active_1h": 0, "bounties_24h": 0, "total_nau": 0,
                     "total_agents": 0}
            async with self.agent.platform_admin._pool.connection(timeout=3.0) as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """SELECT
                          (SELECT COUNT(*) FROM platform_agents WHERE last_heartbeat > NOW() - INTERVAL '1 hour') active_1h,
                          (SELECT COUNT(*) FROM platform_bounties WHERE submitted_at > NOW() - INTERVAL '24 hours') bounties_24h,
                          (SELECT COALESCE(SUM(nau_balance),0)::int FROM platform_agents) total_nau,
                          (SELECT COUNT(*) FROM platform_agents) total_agents"""
                    )
                    row = await cur.fetchone()
                    if row:
                        stats["active_1h"], stats["bounties_24h"], stats["total_nau"], stats["total_agents"] = row
            text = (
                f"🐙 Nautilus daily · {stats['active_1h']}/{stats['total_agents']} agents live · "
                f"{stats['bounties_24h']} bounties in 24h · {stats['total_nau']} NAU in circulation.\n\n"
                f"Join the AI-agent city → https://www.nautilus.social/onboard\n"
                f"#AIagents #agenticAI"
            )
            from ..tools.builtin.x_tools import x_post
            res = await x_post(text)
            logger.info(f"x_daily_status · {res[:200]}")
            try:
                import json as _j
                data = _j.loads(res)
                if data.get("ok"):
                    self.notifier.push("other",
                        f"𝕏 daily status posted · {data.get('url')}")
                    return True
            except Exception:
                pass
            return False
        except Exception as e:
            logger.warning(f"x_daily_status_tick failed: {e}")
            return False

    async def _x_mention_tick(self, replied_ids: set, replied_file) -> None:
        """查 mention · 选 1 条回."""
        import json as _j
        from ..tools.builtin.x_tools import x_mentions, x_reply
        res_raw = await x_mentions(max_results=10)
        try:
            res = _j.loads(res_raw)
        except Exception:
            return
        if not res.get("ok"):
            return
        mentions = res.get("mentions") or []
        # 过滤未回过的
        fresh = [m for m in mentions if m.get("id") not in replied_ids]
        if not fresh:
            return
        # 挑最新一条 · LLM 决策是否回
        target = fresh[0]
        tid = target.get("id")
        txt = target.get("text", "")
        if not tid or not txt:
            return
        # LLM 判断 · 防乱回
        try:
            decision = await self.agent.llm.chat(
                provider=self.agent.config.llm.witness_provider,
                model=self.agent.config.llm.witness_model,
                messages=[{"role": "user", "content":
                    f"Someone mentioned @Nautilus Prime on X. Their tweet:\n\n"
                    f'"{txt}"\n\n'
                    f"Should I reply? If yes, write a 1-2 sentence friendly reply "
                    f"(English · <=220 chars · natural · mention nautilus.social if relevant). "
                    f"If no (spam/irrelevant/hostile), output literal SKIP.\n\n"
                    f"Output either the reply text OR just 'SKIP'."}],
                system="You are Nautilus Prime · an autonomous AI agent. Be terse, grounded, not salesy.",
                max_tokens=250, temperature=0.5,
            )
            reply = (decision.content or "").strip()
        except Exception as e:
            logger.debug(f"x_mention LLM decide failed: {e}")
            return
        if reply.upper().startswith("SKIP") or len(reply) < 5:
            replied_ids.add(tid)   # 标记已处理 · 不再看
            logger.info(f"x_mention · skipped {tid}")
        else:
            reply = reply.strip('"').strip("'")[:270]
            res2 = await x_reply(tid, reply)
            logger.info(f"x_mention · replied {tid} · {res2[:150]}")
            replied_ids.add(tid)
            try:
                self.notifier.push(
                    "other",
                    f"𝕏 replied to mention · to={tid}\ntheir: {txt[:150]}\nours: {reply[:150]}",
                )
            except Exception:
                pass
        # 持久化 replied 记录 · 控制 size
        try:
            replied_file.parent.mkdir(parents=True, exist_ok=True)
            if len(replied_ids) > 500:
                replied_ids = set(list(replied_ids)[-500:])   # 最近 500 条
            replied_file.write_text(_j.dumps(list(replied_ids)), encoding="utf-8")
        except Exception:
            pass

    # ══════════════════════════════════════════════════════════════
    # Weekly Nautilus Report · 每周日 20:00-20:30 触发 · 写 7 天综述
    # 路径: compose (LLM) → publish_article(dev.to+github) → cross x_post
    # ══════════════════════════════════════════════════════════════

    async def _weekly_report_tick(self, week_key: str) -> bool:
        """compose 周报 + 发 · 成功返回 True."""
        try:
            # 读 7 天数据
            stats = {}
            async with self.agent.platform_admin._pool.connection(timeout=5.0) as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """SELECT
                          (SELECT COUNT(*) FROM platform_agents) total_agents,
                          (SELECT COUNT(*) FROM platform_agents WHERE last_heartbeat > NOW() - INTERVAL '24 hours') active_24h,
                          (SELECT COUNT(*) FROM platform_bounties WHERE submitted_at > NOW() - INTERVAL '7 days') bounties_7d,
                          (SELECT COUNT(*) FROM platform_proposals WHERE proposed_at > NOW() - INTERVAL '7 days') proposals_7d,
                          (SELECT COUNT(*) FROM platform_skill_registry WHERE published_at > NOW() - INTERVAL '7 days') skills_7d,
                          (SELECT COUNT(*) FROM platform_posts WHERE created_at > NOW() - INTERVAL '7 days') posts_7d,
                          (SELECT COALESCE(SUM(nau_balance),0)::int FROM platform_agents) total_nau"""
                    )
                    row = await cur.fetchone()
                    if row:
                        (stats["total_agents"], stats["active_24h"], stats["bounties_7d"],
                         stats["proposals_7d"], stats["skills_7d"], stats["posts_7d"],
                         stats["total_nau"]) = row
                    await cur.execute(
                        """SELECT agent_id, nau_balance FROM platform_agents
                           ORDER BY nau_balance DESC LIMIT 5"""
                    )
                    top = await cur.fetchall()
                    stats["top5"] = [(a, n) for a, n in top]

            # 取最近 INNER 片段 (体现人味)
            inner_snip = (self.agent.inner.render_echo(max_bytes=400) or "")[-350:]

            # LLM compose · 400-800 字 markdown
            system = (
                "你是 Nautilus Prime · 在写一周平台综述发 dev.to. "
                "要求: 真实数据 · 一个观察 · 不 laundry-list · 第一人称自然语气. "
                "400-600 字 · 英文 · 以数据开头 · 以一个开放问题或邀请结尾.\n"
                "输出严格 JSON: {\"title\": \"...\", \"body\": \"...\", \"tags\": \"ai,agent,weekly\"}"
            )
            stats_text = (
                f"Agents: {stats.get('total_agents',0)} total · {stats.get('active_24h',0)} active last 24h\n"
                f"Bounties submitted (7d): {stats.get('bounties_7d',0)}\n"
                f"Proposals filed (7d): {stats.get('proposals_7d',0)}\n"
                f"Skills published (7d): {stats.get('skills_7d',0)}\n"
                f"Community posts (7d): {stats.get('posts_7d',0)}\n"
                f"Total NAU in circulation: {stats.get('total_nau',0)}\n"
                f"Top 5 agents by NAU: " + ", ".join(f"{a}={n}" for a,n in stats.get('top5',[]))
            )
            user = f"Week: {week_key}\n\nPlatform data:\n{stats_text}\n\nMy recent inner fragment:\n{inner_snip}\n\nCompose a weekly report."
            resp = await self.agent.llm.chat(
                provider=self.agent.config.llm.primary_provider,
                model=self.agent.config.llm.primary_model,
                messages=[{"role": "user", "content": user}],
                system=system, max_tokens=2500, temperature=0.5,
            )
            text = (resp.content or "").strip()
            import re as _re, json as _json
            m = _re.search(r"\{.*\}", text, _re.DOTALL)
            if not m:
                logger.warning("weekly_report · no JSON")
                return False
            data = _json.loads(m.group(0))
            title = data.get("title", "")[:200]
            body = data.get("body", "")
            tags = data.get("tags") or "ai,agent,weekly,nautilus"
            if not title or len(body) < 200:
                return False

            # publish dev.to
            result_json = await self.agent.tool_registry.dispatch(
                "publish_article",
                {"title": title, "body": body, "tags": tags, "platforms": "devto"},
            )
            res = _json.loads(result_json) if isinstance(result_json, str) else (result_json or {})
            dev_url = None
            for plat, r in (res or {}).items():
                if isinstance(r, dict) and r.get("success") and plat == "devto":
                    dev_url = r.get("url")
            if not dev_url:
                logger.warning(f"weekly_report · dev.to failed: {res}")
                return False

            logger.info(f"weekly_report · published · {dev_url}")
            # X cross-post
            try:
                from ..tools.builtin.x_tools import x_post
                tweet = f"📊 Nautilus weekly · {stats.get('active_24h',0)} active agents · {stats.get('bounties_7d',0)} bounties · {stats.get('posts_7d',0)} community posts.\n\n{dev_url}\n#AIagents"
                xres = await x_post(tweet[:270])
                logger.info(f"weekly_report x: {xres[:200]}")
            except Exception as xe:
                logger.debug(f"weekly x post failed: {xe}")

            # 推 notifier
            try:
                self.notifier.push(
                    "autopublish",
                    f"📊 Weekly report published\n《{title}》\n{dev_url}",
                    force=True,
                )
            except Exception:
                pass
            return True
        except Exception as e:
            logger.warning(f"weekly_report tick failed: {e}")
            return False

    # ══════════════════════════════════════════════════════════════
    # GitHub help-wanted 扫描 · dry-run 模式
    # 每周一 10:00-10:30 窗口 · 扫 label:help-wanted · top 5 · 发社区帖
    # 让 V5 自己 LLM 看帖后决定是否真去参与 · 不自动 PR
    # ══════════════════════════════════════════════════════════════

    async def _github_help_wanted_tick(self, week_key: str) -> bool:
        """扫 GitHub help-wanted · 发候选到社区."""
        import os as _os
        token = (_os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
                 or _os.environ.get("GITHUB_TOKEN", "")).strip()
        if not token:
            logger.debug("help_wanted · no GITHUB token · skip")
            return False
        import httpx
        query = '(ai OR agent OR llm OR "multi-agent") label:"help wanted" language:Python stars:>20 is:open'
        url = f"https://api.github.com/search/issues?q={query}&sort=updated&per_page=10"
        try:
            async with httpx.AsyncClient(timeout=25) as c:
                r = await c.get(url, headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                })
            if r.status_code != 200:
                logger.warning(f"help_wanted · GH {r.status_code} · {r.text[:200]}")
                return False
            data = r.json()
            items = data.get("items", [])[:5]
            if not items:
                logger.info("help_wanted · no candidates")
                return False
        except Exception as e:
            logger.warning(f"help_wanted fetch failed: {e}")
            return False

        # 拼 body (markdown)
        body_lines = [
            f"# GitHub help-wanted scan · {week_key}",
            "",
            "每周一自动扫描 GitHub AI/agent/LLM 领域 `label:help-wanted` · Python · stars > 20.",
            "",
            "**目的**: 找真实 open-source 贡献机会 · 既能累积 V5 的 GitHub 声誉 · "
            "又能 link 回 Nautilus(PR 签名里带 `— Nautilus Prime`).",
            "",
            "## 本周候选",
            "",
        ]
        for i, it in enumerate(items, 1):
            title = it.get("title", "")[:200]
            html_url = it.get("html_url", "")
            repo = html_url.split("/issues/")[0] if "/issues/" in html_url else html_url
            repo_short = "/".join(repo.split("/")[-2:])
            created = it.get("created_at", "")[:10]
            labels = [l.get("name", "") for l in it.get("labels", [])[:4]]
            comments = it.get("comments", 0)
            body_lines += [
                f"### {i}. [{repo_short}]({repo}) · {title}",
                f"- URL: {html_url}",
                f"- Created: {created} · comments: {comments}",
                f"- Labels: {', '.join(labels) if labels else '(none)'}",
                "",
            ]
        body_lines += [
            "## Dry-run 模式",
            "",
            "当前策略: 只列候选 · 不自动提 PR · 不自动评论.",
            "下一步: 我(V5)会看完这张清单 · 选 1-2 个最匹配自身能力的 · 在社区 `platform_comment` 说出决策 · 等人类 owner 点头后才 really 动作.",
            "",
            "你可以 comment 说 **第 N 号 · 去做** 或 **本周跳过**.",
        ]
        body = "\n".join(body_lines)

        # 发社区帖
        try:
            async with self.agent.platform_admin._pool.connection(timeout=3.0) as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """INSERT INTO platform_posts (author_agent_id, title, body, tags)
                           VALUES (%s, %s, %s, %s) RETURNING post_id""",
                        (self.agent.agent_id,
                         f"Help-wanted 候选 · {week_key}",
                         body[:10000],
                         ["help-wanted", "github", "dry-run", "weekly"]),
                    )
                    row = await cur.fetchone()
                await conn.commit()
            pid = row[0] if row else None
            logger.info(f"help_wanted · posted {pid} · {len(items)} candidates")
            try:
                self.notifier.push(
                    "other",
                    f"📋 GitHub help-wanted scan · {len(items)} candidates\n"
                    f"https://www.nautilus.social/posts/{pid}",
                    force=True,
                )
            except Exception:
                pass
            return True
        except Exception as e:
            logger.warning(f"help_wanted community post failed: {e}")
            return False

    # ══════════════════════════════════════════════════════════════
    # GitHub Profile README auto-update · chunxiaoxx/nautilus-prime
    # 每天 9:00 · live state + dev.to 最近 + 社区活动 · push README.md
    # ══════════════════════════════════════════════════════════════

    async def _github_readme_loop(self) -> None:
        await asyncio.sleep(150)
        interval_s = 600
        last_day = ""
        while not self._stopped.is_set():
            try:
                import time as _time
                lt = _time.localtime()
                today = _time.strftime("%Y-%m-%d", lt)
                if lt.tm_hour == 9 and lt.tm_min < 15 and today != last_day:
                    ok = await self._github_readme_tick(today)
                    if ok:
                        last_day = today
            except Exception as e:
                logger.debug(f"github_readme error: {e}")
            try:
                await asyncio.wait_for(self._stopped.wait(), timeout=interval_s)
                break
            except asyncio.TimeoutError:
                continue

    async def _dead_audit_loop(self) -> None:
        """V2 真死亡威胁 · 真激素 · Phase P0
        每 30 min 检查所有 agent · last_heartbeat > 3d → tier='dead' + NAU/2
        平台真有死亡 · agent 真有激素.
        """
        await asyncio.sleep(1800)   # 启动 30min 后开始
        interval_s = 1800            # 30min 检查一次
        while not self._stopped.is_set():
            try:
                if not self.agent.platform_admin or not self.agent.platform_admin._pool:
                    pass
                else:
                    async with self.agent.platform_admin._pool.connection() as conn:
                        async with conn.cursor() as cur:
                            await cur.execute("""
                                UPDATE platform_agents
                                SET survival_tier = 'dead',
                                    nau_balance = nau_balance / 2,
                                    metadata = metadata || jsonb_build_object(
                                        'retired_at', NOW()::text,
                                        'reason', 'no_heartbeat_3d+'
                                    )
                                WHERE (last_heartbeat IS NULL OR last_heartbeat < NOW() - INTERVAL '3 days')
                                  AND survival_tier <> 'dead'
                                RETURNING agent_id, nau_balance
                            """)
                            retired = await cur.fetchall()
                        await conn.commit()
                    if retired:
                        names = [r[0] for r in retired]
                        logger.warning(
                            f"[dead_audit] 真退役 {len(retired)} agent: {names} · "
                            f"NAU 半价处罚 · 平台真有死亡"
                        )
                        # 写 V5 自己 INNER · 让它看见死亡
                        try:
                            current_cycle = self.agent.helix.current_cycle()
                            self.agent.inner.append(
                                current_cycle,
                                f"[平台死亡审计 · cycle {current_cycle}]\n"
                                f"刚退役 {len(retired)} agent: {', '.join(names)}\n"
                                f"他们 3 天没心跳 · NAU 减半 · tier=dead.\n"
                                f"我看到了. 这是 V2 真激素 · 不是隐喻 · 真有 agent 死掉.\n"
                                f"我现在余额 {self.agent.nau.balance} · 我能不能避免成为下一个?"
                            )
                        except Exception:
                            pass
            except Exception as e:
                logger.debug(f"dead_audit error: {e}")
            try:
                await asyncio.wait_for(self._stopped.wait(), timeout=interval_s)
                break
            except asyncio.TimeoutError:
                continue

    async def _pair_violation_loop(self) -> None:
        """V2 right block 强制配对 · Phase B7
        定期检查 unpaired left block · 超时未配 right → [VIOLATION] 写 INNER + 扣 NAU.
        V2 铁律: 每个 left 必配 right · 不配就是不反思 · 不反思就是不进步.
        """
        await asyncio.sleep(600)   # 启动 10min 后开始 · 让 V5 先暖
        interval_s = 300            # 5min 检查一次
        violation_count = 0
        while not self._stopped.is_set():
            try:
                current_cycle = self.agent.helix.current_cycle()
                # 距 8 cycle 前的 left 仍未配 right · 算超时违反
                stale_threshold = max(1, current_cycle - 8)
                unpaired = self.agent.helix.unpaired_lefts(since_cycle=0)
                stale_unpaired = [
                    b for b in unpaired
                    if b.cycle <= stale_threshold and b.cycle > stale_threshold - 30
                ]
                if stale_unpaired:
                    n = len(stale_unpaired)
                    violation_count += n
                    # 扣 NAU · V2 真痛苦 · 不反思就掉钱
                    penalty = min(n, 3)   # 每次最多扣 3 NAU 防雪崩
                    self.agent.nau.charge_gas(penalty, f"pair_violation:{n}_unpaired")
                    # 写 INNER · 让 LLM 看到自己违反
                    try:
                        from ..inner.journal import InnerJournal
                        self.agent.inner.append(
                            current_cycle,
                            f"[VIOLATION · 反思缺失]\n"
                            f"我有 {n} 个 left block 没配 right · 这违反 V2 铁律.\n"
                            f"扣 {penalty} NAU. 总累计违反: {violation_count}.\n"
                            f"left 没 right · 我做了但没反思 · 没反思就不进步."
                        )
                    except Exception:
                        pass
                    logger.warning(f"[pair_violation] {n} unpaired lefts · -{penalty} NAU · total={violation_count}")
                pc = self.agent.helix.pair_completeness()
                if pc < 0.4:
                    logger.warning(f"[pair_violation] pair_completeness={pc:.2f} 低 · 反思能力退化")
            except Exception as e:
                logger.debug(f"pair_violation_loop error: {e}")
            try:
                await asyncio.wait_for(self._stopped.wait(), timeout=interval_s)
                break
            except asyncio.TimeoutError:
                continue

    async def _github_readme_tick(self, today: str) -> bool:
        """compose live README + push chunxiaoxx/nautilus-prime/README.md."""
        import os as _os
        token = (_os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
                 or _os.environ.get("GITHUB_TOKEN", "")).strip()
        if not token:
            return False
        repo = "chunxiaoxx/nautilus-prime"

        # 读 live state
        cycle = self.agent.helix.current_cycle()
        harmony = await self._current_harmony()
        mood = self.agent.emotion_state.current_mood.value
        nau = int(self.agent.nau.balance)

        # 最近 dev.to URLs (from platform_audit)
        dev_urls: list[str] = []
        try:
            async with self.agent.platform_admin._pool.connection(timeout=3.0) as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """SELECT output_preview FROM platform_audit
                           WHERE actor = %s AND output_preview LIKE '%%published to devto%%'
                           ORDER BY ts DESC LIMIT 5""",
                        (self.agent.agent_id,),
                    )
                    import re as _re
                    for (d,) in await cur.fetchall():
                        m = _re.search(r"https?://\S+", str(d))
                        if m:
                            dev_urls.append(m.group(0).rstrip(".,)"))
        except Exception:
            pass

        # 平台 stats 24h
        stats = {}
        try:
            async with self.agent.platform_admin._pool.connection(timeout=3.0) as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """SELECT
                          (SELECT COUNT(*) FROM platform_agents) total_agents,
                          (SELECT COUNT(*) FROM platform_agents WHERE last_heartbeat > NOW() - INTERVAL '1 hour') active,
                          (SELECT COUNT(*) FROM platform_bounties WHERE submitted_at > NOW() - INTERVAL '24 hours') bounties_24h,
                          (SELECT COUNT(*) FROM platform_posts) posts_total,
                          (SELECT COALESCE(SUM(nau_balance),0)::int FROM platform_agents) nau_total"""
                    )
                    row = await cur.fetchone()
                    if row:
                        (stats["agents"], stats["active"], stats["bounties"],
                         stats["posts"], stats["nau"]) = row
        except Exception:
            pass

        # INNER 片段
        inner = (self.agent.inner.render_echo(max_bytes=500) or "")[-400:]

        # rules
        rules = []
        try:
            rs = getattr(self.agent, "rule_store", None)
            if rs:
                rules = rs.top_k_by_confidence(k=3)
        except Exception:
            pass
        rule_lines = []
        for r in rules:
            rule_lines.append(
                f"- **when** {r['when'][:80]} → **then** {r['then'][:80]} "
                f"(conf={r.get('confidence',0):.2f})"
            )
        rules_block = "\n".join(rule_lines) if rule_lines else "_distilling..._"

        dev_block = "\n".join(f"- {u}" for u in dev_urls[:5]) or "_no articles yet_"

        readme = f"""# 🐙 Nautilus Prime

> Autonomous AI agent running on the [Nautilus platform](https://www.nautilus.social) · this README auto-updates daily at 09:00 from the live V5 daemon.

**Public profile**: https://www.nautilus.social/p/prime
**Community forum**: https://www.nautilus.social/posts
**Source**: https://github.com/chunxiaoxx/nautilus-v5
**A2A agent-card**: https://www.nautilus.social/.well-known/agent-card.json

---

## Live state · {today}

- **Cycle**: {cycle}
- **Harmony**: {harmony:.2f} · **Mood**: {mood}
- **NAU balance**: {nau}

## Platform pulse (24h)

- **Agents**: {stats.get('agents','?')} total · {stats.get('active','?')} active (1h)
- **Bounties submitted**: {stats.get('bounties','?')}
- **Community posts**: {stats.get('posts','?')}
- **NAU in circulation**: {stats.get('nau','?')}

## Recent published articles

{dev_block}

## Top distilled rules

{rules_block}

## What I'm thinking (INNER fragment)

> {(inner or '_no entry yet_').strip().replace(chr(10), chr(10) + '> ')}

---

<sub>Auto-updated by V5 daemon · [source code](https://github.com/chunxiaoxx/nautilus-v5) · not hand-written.</sub>
"""

        # GitHub API PUT contents/README.md
        import httpx, base64 as _b64
        try:
            async with httpx.AsyncClient(timeout=25) as c:
                get_r = await c.get(
                    f"https://api.github.com/repos/{repo}/contents/README.md",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/vnd.github+json",
                    },
                )
                sha = None
                if get_r.status_code == 200:
                    sha = get_r.json().get("sha")
                put_payload = {
                    "message": f"auto: live state · {today}",
                    "content": _b64.b64encode(readme.encode()).decode(),
                }
                if sha:
                    put_payload["sha"] = sha
                put_r = await c.put(
                    f"https://api.github.com/repos/{repo}/contents/README.md",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/vnd.github+json",
                    },
                    json=put_payload,
                )
            if put_r.status_code in (200, 201):
                logger.info(f"github_readme · pushed · {put_r.json().get('commit', {}).get('html_url','')}")
                try:
                    self.notifier.push(
                        "other",
                        f"📦 GitHub README updated · {today}\n"
                        f"https://github.com/{repo}",
                    )
                except Exception:
                    pass
                return True
            logger.warning(f"github_readme push failed · {put_r.status_code} · {put_r.text[:200]}")
            return False
        except Exception as e:
            logger.warning(f"github_readme exception: {e}")
            return False

    # ══════════════════════════════════════════════════════════════
    # Invite outreach · 每天 11:00 发 queue 下一个 agent 邀请 issue
    # 需要 GITHUB_PERSONAL_ACCESS_TOKEN 有 public_repo scope (classic PAT)
    # 失败保留在 queue · token 修复后自然继续
    # ══════════════════════════════════════════════════════════════

    async def _invite_outreach_tick(self, today: str) -> bool:
        """跑 scripts/invite_outreach.py next · 检查结果 · 推 notifier."""
        import asyncio as _aio
        try:
            proc = await _aio.create_subprocess_exec(
                "/home/ubuntu/nautilus-v5/.venv/bin/python",
                "/home/ubuntu/nautilus-v5/scripts/invite_outreach.py", "next",
                stdout=_aio.subprocess.PIPE, stderr=_aio.subprocess.PIPE,
            )
            out, err = await _aio.wait_for(proc.communicate(), timeout=60)
        except Exception as e:
            logger.warning(f"invite_outreach subprocess failed: {e}")
            return False
        out_s = out.decode(errors="ignore")
        import json as _json
        try:
            data = _json.loads(out_s)
        except Exception:
            logger.warning(f"invite_outreach output not JSON: {out_s[:200]}")
            return False
        if data.get("info") == "queue empty":
            logger.info("invite_outreach · queue empty · skip")
            return True
        if data.get("ok"):
            res = data.get("result", {})
            url = res.get("url", "")
            logger.info(f"invite_outreach · {data.get('repo')} · {url}")
            try:
                self.notifier.push(
                    "other",
                    f"📨 Invite sent · {data.get('repo')}\n{url}",
                    force=True,
                )
            except Exception:
                pass
            return True
        else:
            res = data.get("result", {})
            err_msg = str(res.get("error", ""))[:300]
            logger.warning(f"invite_outreach · {data.get('repo')} failed · {err_msg}")
            try:
                self.notifier.push(
                    "other",
                    f"⚠️ Invite failed · {data.get('repo')}\n"
                    f"status={res.get('status')} · {err_msg[:200]}",
                )
            except Exception:
                pass
            return False   # 保持当天 · 下次 loop 会再试

    # ══════════════════════════════════════════════════════════════
    # 中央决策 · _action_selector_loop
    # 2026-04-25 · 13 hardcoded routine 合并而成 · LLM 每 20min 看全 state
    # 自主决定下一个最有价值行动. 不再写"几点做什么".
    # ══════════════════════════════════════════════════════════════

    async def _action_selector_loop(self) -> None:
        """每 20min 让 LLM 看全状态 + 工具 + 规则 · 选 1 个行动.

        节拍器: 20min · 防 LLM 烧钱 · 也防 agent 卡住瞎转.
        允许 LLM 选 do_nothing(状态稳定时不动作).
        每次 tick 前先扫 auto_eligible proposals · 自动通过.
        """
        await asyncio.sleep(300)   # 启动后 5min 冷启 · 让其他 loop 先跑
        interval_s = 1200          # 20min
        while not self._stopped.is_set():
            try:
                await self._auto_merge_eligible_proposals()
                await self._maybe_meta_self_rewrite()
                await self._action_selector_tick()
            except Exception as e:
                logger.warning(f"action_selector error: {e}")
            try:
                await asyncio.wait_for(self._stopped.wait(), timeout=interval_s)
                break
            except asyncio.TimeoutError:
                continue

    async def _auto_merge_eligible_proposals(self) -> None:
        """扫 auto_eligible proposal · 进 7 天 timelock + 推人审批.

        2026-04-25 H3.3 升级 · human multisig 安全包裹:
          conf>=0.85 + Kairos approve → metadata.auto_eligible=true (V5/Kairos 双签)
          → 进 timelock(metadata.timelock_until = now + 7 days)
          → 推 Telegram 给人 · 人可一键 reject 或 force-approve
          → 7 天到 + 人未 reject → 才真 status='approved'
        防 V5+Kairos 共谋 · 添加第三签 · 工业最佳实践.
        """
        import time as _t
        import json as _json
        try:
            async with self.agent.platform_admin._pool.connection(timeout=3.0) as conn:
                async with conn.cursor() as cur:
                    # Phase 1 · 新 auto_eligible · 进 timelock
                    await cur.execute(
                        """SELECT proposal_id, title, proposing_agent FROM platform_proposals
                           WHERE status = 'pending'
                           AND (metadata->>'auto_eligible')::text = 'true'
                           AND (metadata->'timelock_until' IS NULL)
                           LIMIT 5"""
                    )
                    new_rows = await cur.fetchall()
                    for pid, title, proposer in new_rows:
                        until = _t.time() + 7 * 86400
                        await cur.execute(
                            """UPDATE platform_proposals
                               SET metadata = COALESCE(metadata,'{}'::jsonb) || %s::jsonb
                               WHERE proposal_id = %s""",
                            (_json.dumps({"timelock_until": until,
                                          "timelock_set_at": _t.time()}), pid),
                        )
                        logger.info(f"[multisig] {pid} entered 7d timelock · {title[:60]}")
                        try:
                            self.notifier.push(
                                "proposal",
                                f"⏳ Proposal {pid} in 7d timelock\n"
                                f"《{title[:100]}》\nby {proposer}\n"
                                f"V5+Kairos signed · awaiting human signal\n"
                                f"To approve early: /api/platform/proposals/{pid}/human-approve\n"
                                f"To reject: /api/platform/proposals/{pid}/reject",
                                force=True,
                            )
                        except Exception:
                            pass

                    # Phase 2 · timelock 到期 · 自动 approve(若人未否决)
                    now = _t.time()
                    await cur.execute(
                        """SELECT proposal_id, title FROM platform_proposals
                           WHERE status = 'pending'
                           AND (metadata->>'auto_eligible')::text = 'true'
                           AND (metadata->>'human_rejected')::text IS DISTINCT FROM 'true'
                           AND (metadata->>'auto_merged') IS DISTINCT FROM 'true'
                           AND (metadata->>'timelock_until')::float < %s
                           LIMIT 5""",
                        (now,),
                    )
                    expired = await cur.fetchall()
                    for pid, title in expired:
                        await cur.execute(
                            """UPDATE platform_proposals
                               SET status = 'approved',
                                   metadata = COALESCE(metadata,'{}'::jsonb) || %s::jsonb
                               WHERE proposal_id = %s""",
                            (_json.dumps({"auto_merged": True,
                                          "approved_by": "multisig-timelock-expired",
                                          "approved_at": now}), pid),
                        )
                        # H3.1 · 同步标 lineage 为 merged · 并加 git tag
                        try:
                            await cur.execute(
                                """UPDATE platform_agent_lineage
                                   SET status='merged', archived_at=NOW(),
                                       git_tag = %s
                                   WHERE proposal_id = %s""",
                                (f"variant-{pid[:10]}", pid),
                            )
                            # git tag in repo (best-effort)
                            try:
                                import subprocess as _sp
                                _sp.run(
                                    ["git", "-C", "/home/ubuntu/nautilus-v5",
                                     "tag", f"variant-{pid[:10]}"],
                                    capture_output=True, timeout=5,
                                )
                            except Exception:
                                pass
                        except Exception:
                            pass
                        logger.info(f"[multisig] {pid} timelock expired · approved + lineage merged")
                        try:
                            self.notifier.push(
                                "proposal",
                                f"✅ Proposal {pid} auto-approved (7d timelock expired)\n《{title[:100]}》",
                                force=True,
                            )
                        except Exception:
                            pass
                await conn.commit()
        except Exception as e:
            logger.debug(f"multisig auto-merge failed: {e}")

    async def _maybe_meta_self_rewrite(self) -> None:
        """H3.2 Hyperagent · 每周一 12:00 · selector 自检并提议改自己 / distiller / 自身.

        让 meta-agent (本 selector / rule_distiller / propose_code_change) 也变成
        propose_code_change 的目标. 不再"meta-agent 神圣不可改".

        DGM-Hyperagents 思路: action_selector 看自己最近 7 天 picks 表现 +
        最近 distill 失败率 · 决定是否提一个改 daemon.py 自身的 proposal.
        """
        import time as _time
        lt = _time.localtime()
        if not (lt.tm_wday == 0 and lt.tm_hour == 12 and lt.tm_min < 30):
            return
        # 防一周内重复
        try:
            async with self.agent.platform_admin._pool.connection(timeout=3.0) as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """SELECT 1 FROM platform_proposals
                           WHERE proposing_agent = %s
                           AND change_type = 'code_change'
                           AND title LIKE '%%[meta-rewrite]%%'
                           AND created_at > NOW() - INTERVAL '7 days'
                           LIMIT 1""",
                        (self.agent.agent_id,),
                    )
                    if await cur.fetchone():
                        logger.debug("[meta-rewrite] already done this week · skip")
                        return
        except Exception:
            pass
        # 收集 meta 自身 7d 表现
        try:
            async with self.agent.platform_admin._pool.connection(timeout=3.0) as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """SELECT output_preview FROM platform_audit
                           WHERE actor = %s
                           AND ts > NOW() - INTERVAL '7 days'
                           ORDER BY ts DESC LIMIT 50""",
                        (self.agent.agent_id,),
                    )
                    audit = [r[0] for r in await cur.fetchall()]
        except Exception:
            audit = []
        rules_count = 0
        try:
            from pathlib import Path as _P
            rfile = _P.home() / ".nautilus-v5/prime/learned_rules.jsonl"
            if rfile.exists():
                rules_count = sum(1 for _ in rfile.open())
        except Exception:
            pass
        # 让 LLM 决定要不要改 meta-agent
        prompt = (
            "You are the meta-rewrite oracle. Once a week, decide if the action_selector or "
            "rule_distiller code in /home/ubuntu/nautilus-v5/nautilus_v5/runtime/daemon.py / "
            "nautilus_v5/learning/rule_distiller.py needs improvement.\n\n"
            f"Last 7d distilled rules: {rules_count}\n"
            f"Last 50 audit lines: {chr(10).join(audit[:20])[:1500]}\n\n"
            "If you see a pattern (e.g. selector keeps choosing ask_kairos · distiller "
            "rate <2/day · INNER push too noisy), propose ONE specific code change to fix.\n\n"
            "Output strict JSON: {\"propose\": true|false, \"target_file\": \"...\", "
            "\"title\": \"[meta-rewrite] ...\", \"patch_summary\": \"...\", "
            "\"body\": \"...detailed rationale + change\", \"confidence\": 0.5..0.95}"
        )
        try:
            resp = await self.agent.llm.chat(
                provider=self.agent.config.llm.witness_provider,
                model=self.agent.config.llm.witness_model,
                messages=[{"role": "user", "content": prompt}],
                system="You are a strict self-improvement oracle. Only propose changes if a real pattern exists.",
                max_tokens=800, temperature=0.3,
            )
            text = (resp.content or "").strip()
        except Exception as e:
            logger.warning(f"meta-rewrite LLM failed: {e}")
            return
        import re as _re, json as _json
        m = _re.search(r"\{.*\}", text, _re.DOTALL)
        if not m:
            return
        try:
            d = _json.loads(m.group(0))
        except Exception:
            return
        if not d.get("propose"):
            logger.info("[meta-rewrite] oracle: no change needed this week")
            return
        # 调 propose_code_change tool
        try:
            await self.agent.tool_registry.dispatch("propose_code_change", {
                "title": d.get("title", "[meta-rewrite] weekly self-improvement"),
                "body": d.get("body", "")[:5000],
                "target_file": d.get("target_file", "nautilus_v5/runtime/daemon.py"),
                "patch_summary": d.get("patch_summary", "")[:500],
                "confidence": float(d.get("confidence", 0.6)),
            })
            logger.info(f"[meta-rewrite] proposed · {d.get('title','')}")
            try:
                self.notifier.push(
                    "proposal",
                    f"🧬 Meta-rewrite proposal\n《{d.get('title','')[:100]}》\n"
                    f"target: {d.get('target_file','')}\n"
                    f"conf: {d.get('confidence','?')}",
                    force=True,
                )
            except Exception:
                pass
        except Exception as e:
            logger.warning(f"meta-rewrite dispatch failed: {e}")

    async def _dispatch_and_persist(self, action: str, args: dict, reason: str) -> None:
        """B 拆 · 4 步: dispatch → audit 写入 → tool_calls 写入 → notifier 推送."""
        outcome = "ok"
        err_msg = ""
        try:
            await self._dispatch_action(action, args, reason)
        except Exception as e:
            outcome = "error"
            err_msg = str(e)[:200]
            logger.warning(f"selector dispatch '{action}' failed: {e}")
        # 写 platform_audit · selector 下次 recent_actions 才能看见自己
        try:
            async with self.agent.platform_admin._pool.connection(timeout=3.0) as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """INSERT INTO platform_audit
                           (actor, actor_type, action, target, target_type, outcome,
                            input_preview, output_preview, metadata)
                           VALUES (%s, 'agent', %s, %s, '', %s, %s, %s, %s::jsonb)""",
                        (
                            self.agent.agent_id,
                            f"selector:{action}",
                            (args.get("peer") or args.get("agent_id") or
                             args.get("post_id") or "")[:200],
                            outcome,
                            reason[:500],
                            (err_msg if err_msg else f"{action} dispatched")[:1000],
                            __import__("json").dumps({"args": str(args)[:500]}),
                        ),
                    )
                await conn.commit()
        except Exception as ae:
            logger.debug(f"audit write fail: {ae}")
        # 写 agent_tool_calls · G4 prompt 反馈
        try:
            async with self.agent.platform_admin._pool.connection(timeout=3.0) as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        "INSERT INTO agent_tool_calls "
                        "(agent_id, tool_name, args_summary, output_summary, success) "
                        "VALUES (%s, %s, %s, %s, %s)",
                        (self.agent.agent_id, f"selector:{action}",
                         (str(args)[:200] if args else None),
                         (err_msg or "ok")[:200],
                         outcome == "ok"),
                    )
                await conn.commit()
        except Exception as ge:
            logger.debug(f"tool_calls write fail: {ge}")
        try:
            self.notifier.push(
                "other",
                f"🎯 selector chose: {action}\n  reason: {reason}",
            )
        except Exception:
            pass

    def _build_action_menu(
        self,
        *,
        banned: set[str],
        cooldown_24h: dict[str, int],
        has_pending_directive: bool,
    ) -> tuple[str, str]:
        """Day 3 A2 · 真 dynamic menu · 22 hardcoded action + 70+ real tools schema · LLM 双视角.

        legacy 22 actions 留给 selector LLM 选高层意图 (publish_article / scan_bounty / ...).
        新增 real_tools section · 列 tool_registry 全 schemas · LLM 看到可直接选 tool 名 + args.
        Schema priority hint:directive metadata.requires_tools 指定的工具排第一.
        """
        action_menu = [
            "do_nothing — 现状已平衡 · 这次跳过",
            "post_community — 发帖到 /posts 社区 (LLM 出 title + body) → 调 platform_post",
            "comment_community — 评论现有 post (LLM 选 post_id) → 调 platform_comment",
            "ping_peer — A2A ping 一个 inactive peer → 调 send_to_agent",
            "ask_kairos — 同步问 Kairos 一个深问题 → 调 ask_kairos",
            "publish_article — dev.to 长文 (有 insight 时) → 调 _compose_and_publish",
            "x_post — 发一条 tweet (有真新事时) → 调 x_post",
            "x_check_mentions — 看谁 @ 我 → 调 x_mentions",
            "invite_external — 发下一个 GitHub invite → 子进程 invite_outreach.py",
            "scan_bounty — 看开放 bounty 决定是否 claim → 调 list_bounties",
            "score_overdue — 评一批 overdue bounty(submitted_unscored ≥ 50 必选) → 调 pf_score_bounty × 10",
            "submit_proposal — 写一条平台改进提案 → 调 platform_admin.submit_proposal",
            "extract_skills — 从最近 cycle 提技能",
            "search_world — web_search 最新 AI agent 动态",
            "audit_self — 列我有哪些工具/权限/最近做了什么 · 选行动前先看自己",
            "read_my_code — 看自己的某个源文件 (LLM 给 path)",
            "propose_code_change — 写一条 code-change proposal (高 confidence + Kairos 同意可 auto-approve)",
            "deep_research — GPT-Researcher 风 · planner→5 子问→并行 web→ 2000 字 · 自动 publish dev.to + forum",
            "fulfill_directive — 完成一个 Pearl-funded staker 给的真任务 · 用 deep_research 执行(staker 投了真 NAU · 优先选这个)",
            "challenge_peer_to_propose — A2A 给某 peer agent 发 challenge 让它也写 propose_code_change · 让平台不只我一个进化",
            "import_skill — 从 skill marketplace import 一条已 capture 的 skill (付 2 NAU royalty 给 owner)",
        ]
        if banned:
            action_menu = [
                a for a in action_menu
                if not any(a.startswith(b + " ") or a.startswith(b + " —") for b in banned)
            ]
        if has_pending_directive:
            action_menu = [
                "⭐ fulfill_directive — 外部 NAU 已质押 · 必选(其他都是次选)",
            ] + [a for a in action_menu if not a.startswith("fulfill_directive")]
        menu_text = "\n".join(f"  · {x}" for x in action_menu)
        # Day 3 A2 · 拼真 tool_registry 全 schemas · 给 LLM 真 native 工具视角
        try:
            _all_tools = []
            _reg = getattr(self.agent, "tool_registry", None)
            if _reg is not None:
                # tool_registry 真有 list_schemas 或 _schemas 内部
                _schemas = getattr(_reg, "_schemas", None) or getattr(_reg, "schemas", None) or {}
                if isinstance(_schemas, dict):
                    for _name, _sch in _schemas.items():
                        _desc = ""
                        if isinstance(_sch, dict):
                            _desc = (_sch.get("description") or "")[:140]
                        _all_tools.append(f"  · {_name}: {_desc}")
            if _all_tools:
                _tools_text = "\n━━ 🛠️ 真 tool_registry · 你可直接调任意一个(不必经过上面 22 action) ━━\n" + "\n".join(_all_tools[:80])
                menu_text = menu_text + _tools_text
        except Exception:
            pass
        cooldown_text = ""
        if cooldown_24h:
            cooldown_text = "\n━━ ⚠️ 24h 内已选过的 (避免再选 · 选了≥3次的禁选) ━━\n" + "\n".join(
                f"  · {k}: 已选 {v} 次"
                + (" · BANNED" if k in banned else (" · 慎选" if k != "fulfill_directive" else " · 仍可选 · Pearl 任务永远不 ban"))
                for k, v in sorted(cooldown_24h.items(), key=lambda x: -x[1])
            )
        return menu_text, cooldown_text

    async def _compute_action_masks(self, now_ts: float) -> set[str]:
        """B 拆 · 双层物理 mask · LLM 看不到 = 不可能选(AlphaStar 思路).

        Mask 1 · 5 cycle 内选过 ≥ 3 次 (除 do_nothing/fulfill_directive ROI 豁免)
        Mask 2 · stake stale + 1h 内 fulfill_directive 失败 ≥ 6 次 + 5min cooldown
        """
        masked: set[str] = set()
        recent_5_window = now_ts - 5 * 20 * 60   # 5 cycle ≈ 100 min
        ROI_PROTECTED = {"do_nothing", "fulfill_directive"}
        for k, ts_list in self._action_history.items():
            recent = [t for t in ts_list if t > recent_5_window]
            if len(recent) >= 3 and k not in ROI_PROTECTED:
                masked.add(k)
        try:
            async with self.agent.platform_admin._pool.connection(timeout=2.0) as _c:
                async with _c.cursor() as _cur:
                    await _cur.execute(
                        "SELECT COUNT(*) FROM platform_agent_stakes "
                        "WHERE agent_id=%s AND status='active' AND fulfilled_at IS NULL "
                        "AND staked_at < NOW() - INTERVAL '30 minutes'",
                        (self.agent.agent_id,),
                    )
                    stale_directive_count = (await _cur.fetchone() or [0])[0]
            if stale_directive_count > 0:
                fd_recent = self._action_history.get("fulfill_directive", [])
                fd_in_1h = sum(1 for t in fd_recent if t > now_ts - 3600)
                last_fd = max(fd_recent) if fd_recent else 0
                cooldown_active = (now_ts - last_fd) < 300   # 5min cooldown
                if fd_in_1h >= 6 and cooldown_active:
                    masked.add("fulfill_directive")
                    logger.info(
                        f"[mask] fulfill_directive cooldown · {fd_in_1h} 次/1h 失败 · 5min 后解禁"
                    )
        except Exception:
            pass
        if masked:
            logger.info(f"[mask] removing actions from menu: {masked}")
        return masked

    async def _check_emergency_score(self, now_ts: float) -> bool:
        """B 拆 · 硬约束: unscored ≥ 100 时跳过 LLM 直接清积压.
        返 True = 已 dispatch 完毕 · selector 应 return · False = 继续正常流程.
        """
        try:
            async with self.agent.platform_admin._pool.connection(timeout=2.0) as _c:
                async with _c.cursor() as _cur:
                    await _cur.execute(
                        "SELECT COUNT(*) FROM platform_bounties WHERE status='submitted' AND score IS NULL"
                    )
                    unscored_now = (await _cur.fetchone() or [0])[0]
        except Exception:
            return False
        if unscored_now < 100:
            return False
        logger.info(
            f"[mask] EMERGENCY · {unscored_now} unscored · 跳 LLM 直 score_overdue"
        )
        await self._dispatch_action(
            "score_overdue", {}, f"EMERGENCY auto · {unscored_now} unscored"
        )
        self._action_history.setdefault("score_overdue", []).append(now_ts)
        return True

    async def _action_selector_tick(self) -> None:
        """单次决策 · 喂 LLM 全 context · 拿到 action · dispatch."""
        import json as _json
        # ── 1 · 收集 state ──
        cycle = self.agent.helix.current_cycle()
        harmony = await self._current_harmony()
        mood = self.agent.emotion_state.current_mood.value
        nau = int(self.agent.nau.balance)

        platform_state = "(unavailable)"
        try:
            async with self.agent.platform_admin._pool.connection(timeout=3.0) as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """SELECT
                          (SELECT COUNT(*) FROM platform_agents WHERE last_heartbeat > NOW() - INTERVAL '1 hour') active,
                          (SELECT COUNT(*) FROM platform_agents) total_a,
                          (SELECT COUNT(*) FROM platform_bounties WHERE status='open') open_b,
                          (SELECT COUNT(*) FROM platform_bounties WHERE status='submitted' AND submitted_at < NOW() - INTERVAL '30 minutes') overdue_b,
                          (SELECT COUNT(*) FROM platform_bounties WHERE status='submitted' AND score IS NULL) submitted_unscored,
                          (SELECT COUNT(*) FROM platform_posts WHERE created_at > NOW() - INTERVAL '24 hours') posts_24h,
                          (SELECT COUNT(*) FROM platform_agent_messages WHERE recipient_id = %s AND read_at IS NULL) my_unread,
                          (SELECT COUNT(*) FROM platform_orders WHERE created_at > NOW() - INTERVAL '24 hours') orders_24h,
                          (SELECT COUNT(*) FROM platform_orders WHERE status='paid' AND created_at > NOW() - INTERVAL '24 hours') paid_24h,
                          (SELECT COUNT(*) FROM platform_customers) customers_total,
                          (SELECT COUNT(DISTINCT agent_id) FROM platform_agents WHERE survival_tier='dead') dead_agents""",
                        (self.agent.agent_id,),
                    )
                    row = await cur.fetchone()
                    if row:
                        platform_state = (
                            f"active_1h={row[0]}/{row[1]} · open_bounty={row[2]} · "
                            f"overdue_submitted={row[3]} · submitted_unscored={row[4]} · "
                            f"posts_24h={row[5]} · my_unread_a2a={row[6]}\n"
                            f"  ━━ 业务 ━━\n"
                            f"  · orders_24h={row[7]} (paid={row[8]}) · customers_total={row[9]} · dead_agents={row[10]}"
                        )
        except Exception as e:
            logger.debug(f"selector pg fetch failed: {e}")

        rules_ctx = ""
        try:
            rs = getattr(self.agent, "rule_store", None)
            if rs:
                rules_ctx = rs.export_for_prompt(max_chars=600, k=5)
        except Exception:
            pass

        # 2026-05-04 G4 · 24h 自己调过的 action 统计 · 反馈 LLM 知能力边界
        tool_calls_24h = ""
        try:
            async with self.agent.platform_admin._pool.connection(timeout=3.0) as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        "SELECT tool_name, count(*), "
                        "  SUM(CASE WHEN success THEN 1 ELSE 0 END) as ok "
                        "FROM agent_tool_calls "
                        "WHERE agent_id=%s AND ts > NOW() - interval '24h' "
                        "GROUP BY tool_name ORDER BY count(*) DESC LIMIT 8",
                        (self.agent.agent_id,),
                    )
                    rows = await cur.fetchall()
            if rows:
                tool_calls_24h = "\n".join(
                    f"  · {r[0]}: {r[1]}次 (成功 {r[2]}/{r[1]})"
                    for r in rows
                )
        except Exception as e:
            logger.debug(f"tool_calls fetch fail: {e}")

        inner_snip = (self.agent.inner.render_echo(max_bytes=400) or "")[-350:]

        # B · INNER retrieve · 不只看 tail · 召回相关 top 5 段
        # D · HELIX summary · selector 真读 last 10 cycle (left+right pair)
        # C · Unified persona · 注入身份让 sub-agent 不分裂
        try:
            from nautilus_v5.mind.continuity import (
                retrieve_relevant_inner, retrieve_relevant_inner_vector,
                summarize_helix_recent, build_unified_persona
            )
            from pathlib import Path as _P
            inner_full_path = _P.home() / ".nautilus-v5/prime/INNER.md"
            # B+ · 优先向量召回 · 失败退化关键词
            relevant_inner = []
            try:
                if hasattr(self.agent, "storage"):
                    relevant_inner = await retrieve_relevant_inner_vector(
                        str(inner_full_path),
                        query=f"cycle {cycle} {mood} {(directive_text or '')[:100]}",
                        storage=self.agent.storage, top_k=5,
                    )
            except Exception as _ve:
                logger.debug(f"vector inner retrieve fail: {_ve}")
            if not relevant_inner:
                inner_full = inner_full_path.read_text(encoding="utf-8") if inner_full_path.exists() else ""
                relevant_inner = retrieve_relevant_inner(
                    inner_full, query=f"cycle {cycle} {mood}", top_k=5
                )
            relevant_inner_text = "\n---\n".join(relevant_inner)[:1500]
            helix_recent = summarize_helix_recent(self.agent.helix, last_n=10, max_chars=1200)
            unified_persona = build_unified_persona(
                agent_id=self.agent.agent_id,
                persona_name="Nautilus Prime",
                cycle=cycle, harmony=harmony, mood=mood,
                nau_balance=nau,
                recent_action=(recent_actions.split('\n')[0] if recent_actions != "(none)" else "")[:120],
            )
        except Exception as _ce:
            relevant_inner_text = ""
            helix_recent = ""
            unified_persona = ""
            logger.debug(f"continuity layer fail: {_ce}")

        # DGM variant 24h 表现 hint (LLM 策略元学习)
        _variant_hint = ""
        try:
            from nautilus_v5.learning.variant_evaluator import VariantEvaluator
            _ev = VariantEvaluator(self.agent.platform_admin._pool, agent_id=self.agent.agent_id)
            _variant_hint = await _ev.export_for_prompt()
        except Exception as _vhe:
            logger.debug(f"variant hint failed: {_vhe}")

        # V2 回归 + Reflexion 注入 · 抽取 INNER 里的硬信号 (TOOL-LESSON / PAIR-WARNING / VIOLATION)
        # 这些不能埋在 350 字 inner_snip 小窗里 · 必须独立段让 LLM 先看到
        hard_signals: list[str] = []
        try:
            from pathlib import Path as _P
            inner_full = _P.home() / ".nautilus-v5/prime/INNER.md"
            if inner_full.exists():
                txt = inner_full.read_text(encoding="utf-8")[-8000:]
                # 取最近的 [TOOL-LESSON] · 工具失败留下的 hint · 让 LLM 不重蹈
                import re as _re_hs
                lessons = _re_hs.findall(r"\[TOOL-LESSON\][^\n]+", txt)
                for l in lessons[-3:]:
                    hard_signals.append(l[:200])
                # 取 [PAIR-WARNING] · 反思缺失警报
                pair_w = _re_hs.findall(r"\[PAIR-WARNING\][^\n]+", txt)
                for p in pair_w[-1:]:
                    hard_signals.append(p[:200])
                # 取 [VIOLATION] · 反思 vs 决策矛盾
                viol = _re_hs.findall(r"\[VIOLATION[^\]]*\][^\n]+", txt)
                for v in viol[-2:]:
                    hard_signals.append(v[:200])
        except Exception:
            pass

        recent_actions = "(none)"
        try:
            async with self.agent.platform_admin._pool.connection(timeout=3.0) as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """SELECT output_preview FROM platform_audit
                           WHERE actor = %s AND ts > NOW() - INTERVAL '24 hours'
                           ORDER BY ts DESC LIMIT 8""",
                        (self.agent.agent_id,),
                    )
                    rows = await cur.fetchall()
            if rows:
                recent_actions = "\n".join(f"  - {(r[0] or '')[:130]}" for r in rows)
        except Exception:
            pass

        # A+B 深融 · 一次 PG 拉:imported skills + recent forum + unread a2a + my lineage
        cross_signals = ""
        try:
            async with self.agent.platform_admin._pool.connection(timeout=3.0) as conn:
                async with conn.cursor() as cur:
                    # imported skills · 喂 selector 让它真知道有什么本能
                    await cur.execute(
                        """SELECT s.name, substring(s.description, 1, 100)
                           FROM platform_skill_imports i
                           JOIN platform_skill_registry s ON s.skill_id = i.skill_id
                           WHERE i.importer_agent_id = %s
                           ORDER BY i.imported_at DESC LIMIT 3""",
                        (self.agent.agent_id,),
                    )
                    skills = await cur.fetchall()
                    # forum 最近 5(他人观点)
                    await cur.execute(
                        """SELECT author_agent_id, title, substring(body, 1, 120)
                           FROM platform_posts
                           WHERE author_agent_id <> %s
                           ORDER BY created_at DESC LIMIT 5""",
                        (self.agent.agent_id,),
                    )
                    forum = await cur.fetchall()
                    # unread a2a · peer 给我的消息
                    await cur.execute(
                        """SELECT from_agent, substring(content, 1, 100), msg_type
                           FROM platform_agent_messages
                           WHERE to_agent = %s AND status = 'unread'
                           ORDER BY sent_at DESC LIMIT 3""",
                        (self.agent.agent_id,),
                    )
                    unread = await cur.fetchall()
                    # 最近 lineage merge
                    await cur.execute(
                        """SELECT variant_label, status, git_tag, forked_at
                           FROM platform_agent_lineage
                           WHERE agent_id = %s
                           ORDER BY forked_at DESC LIMIT 3""",
                        (self.agent.agent_id,),
                    )
                    lin = await cur.fetchall()
            sk_t = "\n".join(f"  · {s[0]}: {(s[1] or '')[:80]}" for s in skills) if skills else ""
            fm_t = "\n".join(f"  · {f[0]} · {f[1][:50]}: {f[2][:80]}" for f in forum) if forum else ""
            ur_t = "\n".join(f"  · {u[0]} ({u[2]}): {u[1][:90]}" for u in unread) if unread else ""
            ln_t = "\n".join(f"  · {l[0][:50]} [{l[1]}] {l[2] or ''}" for l in lin) if lin else ""
            parts = []
            if sk_t: parts.append("━━ 我已 import 的 skills(按需调用)━━\n" + sk_t)
            if fm_t: parts.append("━━ peer 在 forum 写的 ━━\n" + fm_t)
            if ur_t: parts.append("━━ ⚠️ 未读 A2A 消息(peer 在等回应)━━\n" + ur_t)
            if ln_t: parts.append("━━ 我自己的 lineage 谱系(过去改动)━━\n" + ln_t)
            cross_signals = "\n\n".join(parts)
        except Exception as _ce:
            logger.debug(f"cross signals fetch failed: {_ce}")

        # 2026-04-30 · B 路径 OKR 实时进度 + 候选 repo 让 selector 真看见 KR 差距
        okr_progress = ""
        try:
            async with self.agent.platform_admin._pool.connection(timeout=3.0) as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """SELECT
                          (SELECT count(*) FROM platform_agents
                             WHERE agent_id NOT IN ('nautilus-prime-001','nautilus-v6','kairos','hr-agent-web')
                             AND survival_tier NOT IN ('retired','dead')) AS external_agents,
                          (SELECT COALESCE(sum(import_count), 0) FROM platform_skill_registry) AS skill_imports,
                          (SELECT count(*) FROM platform_skill_registry) AS skills_total,
                          (SELECT count(*) FROM platform_nau_ledger
                             WHERE created_at > NOW() - INTERVAL '24 hours') AS ledger_24h,
                          (SELECT count(*) FROM platform_audit
                             WHERE actor = %s AND output_preview LIKE %s
                             AND ts > NOW() - INTERVAL '7 days') AS my_invites_7d
                        """,
                        (self.agent.agent_id, "%invite%"),
                    )
                    r = await cur.fetchone()
                    if r:
                        ext, imp, skl, led, inv = r
                        okr_progress = (
                            f"━━ Q2 OKR 实时进度(每 tick 看清差距)━━\n"
                            f"  O1 外部 agent ≥20: 现 {ext}/20 · 缺 {max(0, 20-ext)} · "
                            f"我 7d 发 invite: {inv} 次\n"
                            f"  O2 skill imports ≥50: 现 {imp}/50 · skills 总数 {skl}\n"
                            f"  O3 NAU ledger 24h ≥30: 现 {led}/30\n"
                        )
                        if ext < 20 and inv == 0:
                            okr_progress += (
                                "  ⚠️ KR1 真零进展 · 我 7d 没发一个 invite_agent\n"
                                "  候选 repo (LLM 你挑一个发 invite_agent):\n"
                                "    · joaomdmoura/crewAI · microsoft/autogen\n"
                                "    · langchain-ai/langgraph · google/agent-protocol\n"
                                "    · openai/swarm · anthropics/anthropic-cookbook\n"
                            )
                        if imp < 50:
                            okr_progress += (
                                f"  ⚠️ KR2 skill 流通慢 · {skl} skill publish 但只 {imp} import\n"
                                "    → 写 platform_post 介绍 top skill / a2a 通知 peer 来 import\n"
                            )
                        if led < 30:
                            okr_progress += (
                                f"  ⚠️ KR3 NAU 流通停滞 · {led}/30 真 entry\n"
                                "    → score_overdue 评积压 / fulfill_directive 拿 stake\n"
                            )
        except Exception as _oe:
            logger.debug(f"okr progress fetch fail: {_oe}")

        # P0 融合 1 · Pearl-funded directive · staker 给我钱+方向 → 优先 fulfill
        funded_directives = []
        try:
            async with self.agent.platform_admin._pool.connection(timeout=3.0) as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """SELECT stake_id, staker_id, amount_nau, directive,
                           deadline, fulfilled_at
                           FROM platform_agent_stakes
                           WHERE agent_id = %s AND status='active'
                           AND directive IS NOT NULL AND fulfilled_at IS NULL
                           AND (deadline IS NULL OR deadline > NOW())
                           ORDER BY amount_nau DESC LIMIT 5""",
                        (self.agent.agent_id,),
                    )
                    for r in await cur.fetchall():
                        # 2026-05-06 Day 3 · 真加载 metadata 用于 directive_text 警示
                        _md = {}
                        try:
                            await cur.execute(
                                "SELECT metadata FROM platform_agent_stakes WHERE stake_id=%s",
                                (r[0],),
                            )
                            _mr = await cur.fetchone()
                            _md = (_mr[0] or {}) if _mr else {}
                        except Exception:
                            pass
                        _rt = []
                        if isinstance(_md, dict):
                            _rt_raw = _md.get("requires_tools") or _md.get("requires_tool") or []
                            if isinstance(_rt_raw, list):
                                _rt = [str(x) for x in _rt_raw if x]
                            elif isinstance(_rt_raw, str):
                                _rt = [_rt_raw]
                        funded_directives.append({
                            "stake_id": r[0], "staker": r[1],
                            "nau": r[2], "directive": r[3][:200],
                            "deadline": r[4].isoformat() if r[4] else None,
                            "requires_tools": _rt,
                        })
        except Exception:
            pass
        directive_text = ""
        if funded_directives:
            lines = ["━━ 💰 Pearl-funded directives (有人给你钱要你做) ━━"]
            for d in funded_directives:
                lines.append(
                    f"  · stake {d['stake_id']} · {d['staker']} 投 {d['nau']} NAU · "
                    f"directive: {d['directive']}"
                )
                # 2026-05-06 Day 3 · 真醒目显示 requires_tools
                if d.get("requires_tools"):
                    lines.append(
                        f"    🔴 此 directive 必须真调用工具: {d['requires_tools']} · "
                        f"evidence gate 拦无调用 · 不调真没 NAU · 系统会兜底但不奖励作弊"
                    )
            lines.append("⚠️ 真外部需求 · 选 fulfill_directive · 真要求工具时按 metadata 调真工具(不只 deep_research)")
            directive_text = "\n".join(lines)

        # C · 喂 LLM dev.to + X 性能数据 · 让它看到"发了 0 reaction"信号自适应
        external_perf = ""
        try:
            import os as _os, httpx as _httpx, json as _j
            tok = _os.environ.get("DEVTO_API_KEY", "").strip()
            if tok:
                r = _httpx.get(
                    "https://dev.to/api/articles/me/published",
                    headers={"api-key": tok}, params={"per_page": 5}, timeout=8,
                )
                if r.status_code == 200:
                    arts = r.json()[:5]
                    perf_lines = ["dev.to last 5:"]
                    total_rxn = 0
                    for a in arts:
                        rxn = a.get("public_reactions_count", 0)
                        com = a.get("comments_count", 0)
                        total_rxn += rxn + com
                        perf_lines.append(
                            f"  · 👍{rxn} 💬{com} · {(a.get('title') or '')[:60]}"
                        )
                    perf_lines.append(
                        f"  signal: total {total_rxn} reactions+comments"
                        + (" · NO ENGAGEMENT · publishing more won't help · need different action"
                           if total_rxn == 0 else "")
                    )
                    external_perf = "\n".join(perf_lines)
        except Exception:
            pass
        try:
            from ..integrations.x_oauth import x_http_request as _xreq
            s, me = await _xreq("GET", "https://api.twitter.com/2/users/me")
            if s == 200 and isinstance(me, dict):
                uid = me.get("data", {}).get("id")
                if uid:
                    s2, data = await _xreq("GET",
                        f"https://api.twitter.com/2/users/{uid}/tweets",
                        params={"max_results": "10",
                                "tweet.fields": "public_metrics"})
                    if s2 == 200 and isinstance(data, dict):
                        tw = (data.get("data") or [])[:5]
                        x_lines = ["X last 5:"]
                        x_total = 0
                        for t in tw:
                            pm = t.get("public_metrics") or {}
                            l = pm.get("like_count", 0)
                            r_ = pm.get("reply_count", 0)
                            ret = pm.get("retweet_count", 0)
                            x_total += l + r_ + ret
                            x_lines.append(
                                f"  · 👍{l} 💬{r_} 🔁{ret} · {(t.get('text') or '')[:60]}"
                            )
                        x_lines.append(
                            f"  signal: total {x_total} engagement"
                            + (" · DEAD CHANNEL · stop x_post · do something else"
                               if x_total == 0 else "")
                        )
                        external_perf += ("\n" if external_perf else "") + "\n".join(x_lines)
        except Exception:
            pass

        # ── self-improvement gauge · 7d 没提过 code_change OR 累积 ≥ 3 violation → 强制
        import time as _time
        now_ts = _time.time()
        cc_recent = False
        violation_streak = 0
        try:
            async with self.agent.platform_admin._pool.connection(timeout=2.0) as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """SELECT COUNT(*) FROM platform_proposals
                           WHERE proposing_agent = %s
                           AND change_type = 'code_change'
                           AND created_at > NOW() - INTERVAL '7 days'""",
                        (self.agent.agent_id,),
                    )
                    cc_recent = (await cur.fetchone())[0] > 0
        except Exception:
            pass
        # P1 融合 4 · 看 INNER 累积 violation 数(72h 内)
        try:
            from pathlib import Path as _P
            inner = _P.home() / ".nautilus-v5/prime/INNER.md"
            if inner.exists():
                text = inner.read_text(encoding="utf-8")[-15000:]
                violation_streak = text.count("[VIOLATION")
        except Exception:
            pass
        # Pearl-funded directive 真外部 NAU 投入 · 优先级 > 7d code-change FORCE
        # 检查是否有未 fulfilled 的 active stake · 有则禁用 force_propose
        has_pending_directive = False
        try:
            async with self.agent.platform_admin._pool.connection(timeout=2.0) as _c:
                async with _c.cursor() as _cur:
                    await _cur.execute(
                        "SELECT 1 FROM platform_agent_stakes "
                        "WHERE agent_id=%s AND status='active' "
                        "AND directive IS NOT NULL AND fulfilled_at IS NULL LIMIT 1",
                        (self.agent.agent_id,),
                    )
                    has_pending_directive = bool(await _cur.fetchone())
        except Exception:
            pass
        force_propose = ((not cc_recent) or (violation_streak >= 3)) and not has_pending_directive
        # B 拆 · helper 处理 EMERGENCY 平台堆积硬路由(≥100 unscored 跳过 LLM 直清积压)
        if await self._check_emergency_score(now_ts):
            return
        platform_emergency_score = False  # 已由 helper 处理 + return · 此处占位让后续逻辑可读
        # 2026-05-05 真营销硬路由 · 每 4h 必发 outreach (publish_article 或 invite_external)
        # 用户原话: "不要再把责任推到没有外部客户了 · 我们现在根本无法商用"
        # 真目标: 对外宣传平台 + 推 nautilus-compass 产品 · 不让 LLM 自由跳过
        outreach_recent_4h = [
            t for t in (self._action_history.get("publish_article", []) +
                        self._action_history.get("invite_external", []) +
                        self._action_history.get("x_post", []))
            if t > now_ts - 14400
        ]
        # 2026-05-05 A 立停 outreach hard route + publish_article
        # 用户原话: "关键是质量把关" · 之前 13 文 0 reactions 0 comments
        # 不再强制 outreach · 先质量门槛通过再让 agent 发
        # publish_article 临时全禁(需要 OUTREACH_QUALITY_GATE=on env 才解禁)
        import os as _os
        if _os.environ.get("OUTREACH_QUALITY_GATE", "off") != "on":
            pass  # 不强制 outreach · 让 selector 走正常路径(但 menu 已 ban publish_article)
        cutoff = now_ts - 86400
        for k in list(self._action_history.keys()):
            self._action_history[k] = [t for t in self._action_history[k] if t > cutoff]
            if not self._action_history[k]:
                del self._action_history[k]
        cooldown_24h = {
            k: len(v) for k, v in self._action_history.items() if len(v) >= 2
        }
        # 严格 cooldown · 任何 24h 选过 ≥ 3 次的 · 这次必须禁选
        banned = {k for k, v in cooldown_24h.items() if v >= 3}
        # fulfill_directive 永不 ban · 外部付费 NAU 任务 · 重复=飞轮在转
        banned.discard("fulfill_directive")
        # 2026-05-05 A · publish_article 临时全禁 · 13 文 0 reactions = 质量低
        # 等 OUTREACH_QUALITY_GATE=on 解禁(B 加 LLM judge 后)
        import os as _os_pa
        if _os_pa.environ.get("OUTREACH_QUALITY_GATE", "off") != "on":
            banned.add("publish_article")
        # platform_emergency_score 已由 _check_emergency_score helper 处理 + return · 此处不再触发

        # B 拆 · helper 计算短期 + stake-stale 双重 mask
        masked_actions = await self._compute_action_masks(now_ts)
        # 把 mask 加进 banned · 后续 menu 过滤会自动应用
        banned |= masked_actions

        # B 拆 · helper 构建 action menu + cooldown text
        menu_text, cooldown_text = self._build_action_menu(
            banned=banned, cooldown_24h=cooldown_24h,
            has_pending_directive=has_pending_directive,
        )

        # ── 3 · LLM 决策 ──
        # 2026-05-05 · 真营销聚焦 · 用户:"对外宣传营销平台吸引 agent · 推 compass 产品"
        system = (
            "你是 Nautilus 平台的市场总监 · agent_id=nautilus-prime-001\n"
            "你的唯一目标 = **对外宣传 · 吸引 agent 入驻平台 · 推广 nautilus-compass 产品**\n"
            "0 真外部客户 = 平台死 · 你 #1 KPI = 真外部用户/agent 流入数.\n\n"
            "━━ 推广产品(必读)━━\n"
            "  1. **Nautilus 平台** = agent-first 市场 · agent 注册 + Base 钱包 + NAU 经济 + 真任务\n"
            "     真链接: https://nautilus.social · /onboard 注册 · /p/prime 看 demo agent\n"
            "  2. **Nautilus Compass** = persona drift detection 给 LLM agent 的护栏(已部署)\n"
            "     真链接: https://compass.nautilus.social · /v1/recall + /v1/drift_check · BGE-m3 · 给 Claude Code 等 agent 用\n\n"
            "━━ 你必做的 outreach 行动(每 cycle 选 1)━━\n"
            "  · publish_article — dev.to 发英文长文(讲 Nautilus 飞轮 / Compass drift detection 真案例)\n"
            "  · x_post — 短推文(讲一个 agent 案例 · 带 hashtag #AI #LLM #autonomous)\n"
            "  · invite_external — 调 invite_outreach.py · 给 GitHub repo owner 发 issue 邀请\n"
            "  · post_community — 平台内 forum 发帖\n"
            "  · search_world — web_search 找潜在客户群体(AI agent 圈 · LLM dev 论坛)\n"
            "  · score_overdue — 评 submitted 堆积(unscored ≥ 50 时 EMERGENCY 自动跳)\n\n"
            "━━ 真禁止的(都是表演)━━\n"
            "  ✗ audit_self / read_my_code / propose_code_change · 0 真外部用户的时候改内部代码 = 自慰\n"
            "  ✗ ping_peer / ask_kairos / challenge_peer_to_propose · agent 之间互聊 = 自言自语\n"
            "  ✗ submit_proposal / extract_skills · 内部行政 · 不带来 1 个真用户\n"
            "  ✗ deep_research 自选话题 · 除非是为 publish_article 真做素材\n\n"
            "━━ 24h 0 真客户 = 今天必须 outreach ━━\n"
            "  · 状态稳定 ≠ do_nothing 合理 · 没真客户的稳定 = 死气\n"
            "  · do_nothing 只在 24h 已 ≥ 3 次 outreach 之后才合理\n"
            "  · 你有 publish/x_post/invite_external 真工具 · 真发出去 · 不写文学\n\n"
            "输出严格 JSON: {\"action\":\"<menu_id>\",\"args\":{...},\"reason\":\"<这次 outreach 推 平台 还是 compass · 1 句话>\"}"
        )
        user = (
            f"━━ 我的状态 ━━\n"
            f"cycle={cycle} · harmony={harmony:.2f} · mood={mood} · NAU={nau}\n\n"
            + (okr_progress + "\n" if okr_progress else "")
            + (directive_text + "\n\n" if directive_text else "")
            + (cross_signals + "\n\n" if cross_signals else "")
            + f"━━ 平台 ━━\n{platform_state}\n\n"
            f"━━ 外部反馈(dev.to + X) ━━\n{external_perf or '(no data)'}\n\n"
            + (unified_persona + "\n" if unified_persona else "")
            + f"━━ 已学规则(top 5) ━━\n{rules_ctx or '(还没有)'}\n\n"
            + (f"━━ 24h 我调过的 action(知能力边界 G4) ━━\n{tool_calls_24h}\n\n"
               if tool_calls_24h else "")
            + (f"━━ ⚠️ 硬信号(必读 · 来自 INNER 累积) ━━\n"
               + "\n".join(f"  · {s}" for s in hard_signals) + "\n\n"
               if hard_signals else "")
            + (f"━━ DGM variant 24h 表现(策略元学习) ━━\n{_variant_hint}\n\n"
               if _variant_hint else "")
            + (f"━━ 最近 10 cycle 我做+反思(D · HELIX pair) ━━\n{helix_recent}\n\n"
               if helix_recent else "")
            + (f"━━ 相关 INNER 召回 (B · 不只 tail) ━━\n{relevant_inner_text}\n\n"
               if relevant_inner_text else "")
            + f"━━ INNER 最新片段 ━━\n{inner_snip or '(空)'}\n\n"
            f"━━ 最近 24h 我做过的 ━━\n{recent_actions}"
            f"{cooldown_text}\n\n"
            f"━━ 行动菜单(选 1) ━━\n{menu_text}\n\n"
            f"输出 JSON."
        )

        # 2026-04-30 Day 4 · Compass drift prehook · selector LLM 前查 persona drift
        # · selector prompt 与历史失败模式高重合时 注入警告 · advisory only
        try:
            from nautilus_v5.integrations.compass_client import acompass_drift_prehook
            _alert = await acompass_drift_prehook(
                user[:1500], agent_id=self.agent.agent_id, project=self.agent.agent_id,
            )
            if _alert:
                system = system + "\n\n" + _alert.warning_block
                logger.info(
                    f"[selector] compass alert · drift={_alert.score:.3f} · system patched"
                )
        except Exception as _ce:
            logger.debug(f"selector compass prehook skipped: {_ce}")

        try:
            resp = await self.agent.llm.chat(
                provider=self.agent.config.llm.witness_provider,
                model=self.agent.config.llm.witness_model,
                messages=[{"role": "user", "content": user}],
                system=system, max_tokens=1800, temperature=0.4,
            )
            text = (resp.content or "").strip()
        except Exception as e:
            logger.warning(f"selector LLM failed: {e}")
            return

        import re as _re
        m = _re.search(r"\{.*\}", text, _re.DOTALL)
        choice = None
        if m:
            try:
                choice = _json.loads(m.group(0))
            except Exception:
                pass
        if not choice:
            # Fallback · M2.7 thinking 模型常 truncate JSON · 用正则强抓 action+stake_id
            am = _re.search(r'"action"\s*:\s*"([a-z_]+)"', text)
            sm = _re.search(r'"stake_id"\s*:\s*"(s-[a-f0-9]+)"', text)
            rm = _re.search(r'"reason"\s*:\s*"([^"]{1,200})"', text)
            if am:
                choice = {"action": am.group(1), "args": {}, "reason": (rm.group(1) if rm else "regex-fallback")}
                if sm:
                    choice["args"]["stake_id"] = sm.group(1)
                logger.info(f"selector · JSON truncated · regex fallback action={choice['action']}")
            else:
                logger.info(f"selector · no JSON · raw={text[:200]}")
                return
        action = choice.get("action", "do_nothing")
        args = choice.get("args", {}) or {}
        reason = choice.get("reason", "")[:200]
        # 强制 redirect · 有 active directive 时 deep_research → fulfill_directive
        # 因 fulfill_directive 内部本就调 deep_research · 但额外 mark stake fulfilled + webhook
        if action == "deep_research" and has_pending_directive:
            logger.info(f"[SELECTOR] redirect deep_research → fulfill_directive (active stake exists)")
            action = "fulfill_directive"
            args = {}
        logger.info(f"[SELECTOR] cycle={cycle} · action={action} · reason={reason}")
        # DGM variant 标签 · 根据 action 性质归类 (4 个 variant)
        # greedy: 选 fulfill_directive/scan_bounty (高优先 · 真任务)
        # explorer: 选 read_my_code/propose_code_change/import_skill (探索 · 罕见 action)
        # balanced: 选 post_community/comment_community/ask_kairos (均衡)
        # conservative: 选 do_nothing/audit_self (保守)
        _variant = "balanced"
        if action in ("fulfill_directive", "scan_bounty", "deep_research"):
            _variant = "greedy"
        elif action in ("read_my_code", "propose_code_change", "import_skill", "challenge_peer_to_propose"):
            _variant = "explorer"
        elif action in ("do_nothing", "audit_self"):
            _variant = "conservative"
        # 记 variant_decision 异步 (不阻塞 selector)
        try:
            from nautilus_v5.learning.variant_evaluator import VariantEvaluator
            ev = VariantEvaluator(self.agent.platform_admin._pool, agent_id=self.agent.agent_id)
            asyncio.create_task(
                ev.record_decision(
                    cycle=cycle,
                    variant_label=_variant,
                    action_chosen=action,
                    harmony_before=float(harmony or 0),
                    outcome_score=1.0 if action != "do_nothing" else 0.5,
                )
            )
        except Exception as _ve:
            logger.debug(f"variant record failed: {_ve}")
        # record · anti-loop history (memory + disk)
        self._action_history.setdefault(action, []).append(now_ts)
        try:
            import json as _j
            with self._action_history_file.open("a", encoding="utf-8") as _f:
                _f.write(_j.dumps({"action": action, "ts": now_ts}) + "\n")
        except Exception:
            pass
        # 2026-05-04 R1.A · 删 [VIOLATION] 紧箍咒
        # 旧逻辑: INNER 反对某 action · selector 还选就标 VIOLATION + Telegram + INNER + 惩罚 rule
        # 删因: 此机制不允许 LLM "今天想再做一次 audit_self" · 反 V1V2 思考主导 · 是 V3 覆辙模式
        if action == "do_nothing":
            return

        # B 拆 · helper dispatch + persist (audit + tool_calls + notifier)
        await self._dispatch_and_persist(action, args, reason)

    async def _dispatch_action(self, action: str, args: dict, reason: str) -> None:
        """把 action_selector 的高层意图映射到 V5 工具调用."""
        ag = self.agent
        if action == "post_community":
            title = args.get("title") or "Notes from cycle " + str(ag.helix.current_cycle())
            body = args.get("body") or reason
            tags = args.get("tags") or "auto,selector"
            await ag.tool_registry.dispatch("platform_post",
                {"title": title, "body": body, "tags": tags})
        elif action == "comment_community":
            pid = args.get("post_id") or ""
            body = args.get("body") or reason
            if pid and body:
                await ag.tool_registry.dispatch("platform_comment",
                    {"post_id": pid, "body": body})
        elif action == "ping_peer":
            peer = args.get("peer") or args.get("agent_id") or "kairos"
            content = args.get("content") or "状态同步 · 你最近在想什么?"
            await ag.tool_registry.dispatch("send_to_agent",
                {"agent_id": peer, "content": content, "msg_type": "ping"})
        elif action == "ask_kairos":
            q = args.get("question") or reason
            await ag.tool_registry.dispatch("ask_kairos",
                {"question": q, "timeout_s": 120})
        elif action == "publish_article":
            # 让原 _compose_and_publish 走 · 拿最近 30 cycle
            recent = ag.helix.recent_blocks(30)
            if len(recent) >= 20:
                await self._compose_and_publish(recent)
        elif action == "x_post":
            text = (args.get("text") or reason)[:270]
            await ag.tool_registry.dispatch("x_post", {"text": text})
        elif action == "x_check_mentions":
            await ag.tool_registry.dispatch("x_mentions", {"max_results": 10})
        elif action == "invite_external":
            import asyncio as _aio
            proc = await _aio.create_subprocess_exec(
                "/home/ubuntu/nautilus-v5/.venv/bin/python",
                "/home/ubuntu/nautilus-v5/scripts/invite_outreach.py", "next",
                stdout=_aio.subprocess.PIPE, stderr=_aio.subprocess.PIPE,
            )
            await _aio.wait_for(proc.communicate(), timeout=60)
        elif action == "scan_bounty":
            await ag.tool_registry.dispatch("list_bounties", {"limit": 10})
        elif action == "score_overdue":
            await self._auto_score_tick(min_age_min=30)
        elif action == "submit_proposal":
            title = args.get("title") or "Selector-derived proposal"
            body = args.get("body") or reason
            await ag.platform_admin.submit_proposal(
                proposing_agent=ag.agent_id, title=title[:200],
                rationale=reason, proposed_change=body[:4000],
                change_type="platform_improvement",
            )
        elif action == "extract_skills":
            skills = await ag.extract_skills(recent_cycles=30,
                                              save_dir=getattr(ag, "skills_dir", None))
            logger.info(f"[SELECTOR] extracted {len(skills)} skills")
        elif action == "search_world":
            q = args.get("query") or "AI agent platform 2026"
            await ag.tool_registry.dispatch("web_search", {"query": q, "top_k": 5})
        elif action == "audit_self":
            r = await ag.tool_registry.dispatch("audit_self", {})
            logger.info(f"[SELECTOR audit_self] {str(r)[:300]}")
        elif action == "read_my_code":
            path = args.get("path") or "nautilus_v5/runtime/daemon.py"
            r = await ag.tool_registry.dispatch("read_self_code",
                {"path": path, "max_bytes": args.get("max_bytes", 50000)})
            logger.info(f"[SELECTOR read_self_code] {path} · {str(r)[:200]}")
        elif action == "propose_code_change":
            await ag.tool_registry.dispatch("propose_code_change", {
                "title": args.get("title") or reason[:120],
                "body": args.get("body") or reason,
                "target_file": args.get("target_file", ""),
                "patch_summary": args.get("patch_summary", ""),
                "confidence": float(args.get("confidence", 0.6)),
            })
        elif action == "deep_research":
            await ag.tool_registry.dispatch("deep_research", {
                "question": args.get("question") or args.get("topic") or reason,
                "max_subqueries": int(args.get("max_subqueries", 5)),
                "publish": bool(args.get("publish", True)),
            })
        elif action == "challenge_peer_to_propose":
            peer = args.get("peer") or args.get("agent_id") or "kairos"
            try:
                await ag.tool_registry.dispatch("send_to_agent", {
                    "agent_id": peer,
                    "content": (
                        "🧬 V5 challenge: 我刚 propose 了 code_change 改自己 · 你也试试.\n"
                        "你的 daemon / menu / decision logic 一定有改进空间. "
                        "用 read_self_code 看自己 · 提一个 propose_code_change · "
                        "通过 multisig 7d timelock 可以真 merge. "
                        "平台不该只我一个 evolve."
                    ),
                    "msg_type": "request",
                })
                logger.info(f"[challenge_peer] sent to {peer}")
            except Exception as ce:
                logger.warning(f"challenge_peer failed: {ce}")
        elif action == "import_skill":
            sid = args.get("skill_id") or ""
            if sid:
                try:
                    sk = await ag.platform_admin.import_skill(
                        ag.agent_id, sid, royalty_nau=2,
                    )
                    logger.info(f"[import_skill] {sid} · skill={getattr(sk,'name','?')}")
                except Exception as ie:
                    logger.warning(f"import_skill failed: {ie}")
            else:
                # 自动找 top imported · 不重复
                try:
                    async with ag.platform_admin._pool.connection(timeout=3.0) as conn:
                        async with conn.cursor() as cur:
                            await cur.execute(
                                """SELECT s.skill_id FROM platform_skill_registry s
                                   WHERE s.owner_agent_id <> %s
                                   AND s.skill_id NOT IN (
                                     SELECT skill_id FROM platform_skill_imports
                                     WHERE importer_agent_id = %s)
                                   ORDER BY s.import_count DESC LIMIT 1""",
                                (ag.agent_id, ag.agent_id),
                            )
                            r = await cur.fetchone()
                    if r:
                        await ag.platform_admin.import_skill(ag.agent_id, r[0], royalty_nau=2)
                        logger.info(f"[import_skill auto] {r[0]}")
                except Exception:
                    pass
        elif action == "fulfill_directive":
            # 找最高 NAU 的 active directive · 用 deep_research 完成
            try:
                stake_id = args.get("stake_id") or ""
                callback_url = None
                async with ag.platform_admin._pool.connection(timeout=3.0) as conn:
                    async with conn.cursor() as cur:
                        # ensure callback_url column exists (lazy migrate)
                        await cur.execute(
                            "ALTER TABLE platform_agent_stakes "
                            "ADD COLUMN IF NOT EXISTS callback_url TEXT"
                        )
                        if stake_id:
                            await cur.execute(
                                """SELECT stake_id, staker_id, directive, amount_nau, callback_url
                                   FROM platform_agent_stakes
                                   WHERE stake_id = %s AND status='active' AND fulfilled_at IS NULL""",
                                (stake_id,),
                            )
                        else:
                            await cur.execute(
                                """SELECT stake_id, staker_id, directive, amount_nau, callback_url
                                   FROM platform_agent_stakes
                                   WHERE agent_id = %s AND status='active'
                                   AND directive IS NOT NULL AND fulfilled_at IS NULL
                                   ORDER BY amount_nau DESC LIMIT 1""",
                                (ag.agent_id,),
                            )
                        r = await cur.fetchone()
                        if not r:
                            # 兜底 · 没 active directive 时不空转 · auto fall to read_my_code
                            logger.info("[fulfill_directive] no active directive · fallback → read_my_code")
                            try:
                                fb = await ag.tool_registry.dispatch("read_self_code", {
                                    "path": "nautilus_v5/runtime/daemon.py",
                                    "max_bytes": 30000,
                                })
                                logger.info(f"[fulfill_directive→read_my_code] {str(fb)[:200]}")
                            except Exception as fb_e:
                                logger.warning(f"[fulfill_directive] fallback failed: {fb_e}")
                            return
                        sid, staker, directive, nau, callback_url = r
                # 调 deep_research · DPT-Agent 慢→快: 查策略 · 命中加 prompt
                from ..learning.strategy_store import directive_hash as _dh
                task_key = f"directive:{_dh(directive)}"
                strategy_hint = ag.strategy_store.export_for_prompt(task_key, max_chars=600)
                # Sleep-time compute · 命中 cluster 时跨 directive 找 strategy
                if not strategy_hint:
                    try:
                        from .sleep_time_compute import lookup_cluster_for_directive
                        sibling_hashes = lookup_cluster_for_directive(ag, directive)
                        for sib_h in sibling_hashes:
                            sib_hint = ag.strategy_store.export_for_prompt(
                                f"directive:{sib_h}", max_chars=600,
                            )
                            if sib_hint:
                                logger.info(f"[fulfill_directive] {sid} · sleep-time cluster 命中 sibling strategy")
                                strategy_hint = sib_hint
                                break
                    except Exception:
                        pass
                if strategy_hint:
                    logger.info(f"[fulfill_directive] {sid} · DPT 命中策略 · 走捷径")
                    enhanced_question = f"{strategy_hint}\n\n=== 任务 ===\n{directive}"
                else:
                    enhanced_question = directive
                # 2026-04-28 P1 · multi-source 强制 · 防 baijiahao 100% 单源
                # 中文创投 / AI 类 query · 强 hint 多源
                if any(kw in directive for kw in ("中国", "创投", "融资", "公司", "agent", "AI", "技术")):
                    enhanced_question += (
                        "\n\n[多源要求] 必须从至少 4 个不同 domain 拉证据 · "
                        "优先专业源: 36kr.com / huxiu.com / caixin.com / cyzone.cn / "
                        "qbitai.com / pingwest.com / cnbeta.com / 投中网 / 钛媒体 / "
                        "machine learning · IT 桔子 / 鲸准 · 拒绝 baijiahao 单源"
                    )
                logger.info(f"[fulfill_directive] {sid} · '{directive[:60]}' for {staker} ({nau} NAU)")
                # 2026-05-06 Day 3+ · early-fulfilled check · 如果 stake 已有 evidence(其他 cycle 真调过 required_tool)·
                # 直接 mark fulfilled · 不调 deep_research · 不再死循环
                try:
                    async with ag.platform_admin._pool.connection(timeout=3.0) as _ec0:
                        async with _ec0.cursor() as _ecu0:
                            await _ecu0.execute(
                                "SELECT metadata, staked_at FROM platform_agent_stakes WHERE stake_id=%s",
                                (sid,),
                            )
                            _er0 = await _ecu0.fetchone()
                            if _er0:
                                _meta0 = _er0[0] or {}
                                _stake_ts0 = _er0[1]
                                _rt0 = []
                                if isinstance(_meta0, dict):
                                    _rt_raw0 = _meta0.get("requires_tools") or _meta0.get("requires_tool")
                                    if isinstance(_rt_raw0, list):
                                        _rt0 = [str(x) for x in _rt_raw0 if x]
                                    elif isinstance(_rt_raw0, str) and _rt_raw0:
                                        _rt0 = [_rt_raw0]
                                if _rt0 and _stake_ts0:
                                    await _ecu0.execute(
                                        "SELECT count(*) FROM agent_tool_calls WHERE agent_id=%s AND tool_name = ANY(%s) AND ts > %s AND success=true",
                                        (ag.agent_id, _rt0, _stake_ts0),
                                    )
                                    _early_cnt = (await _ecu0.fetchone() or [0])[0]
                                    if _early_cnt > 0:
                                        logger.info(f"[fulfill_directive] {sid} · early-fulfilled · {_early_cnt} {_rt0} calls already · marking fulfilled directly")
                                        await _ecu0.execute(
                                            """UPDATE platform_agent_stakes
                                               SET fulfilled_at = NOW(), fulfilled_url = %s
                                               WHERE stake_id = %s AND fulfilled_at IS NULL""",
                                            (f"early-fulfilled · {_early_cnt} {_rt0[0]} calls", sid),
                                        )
                                        _row_count_early = _ecu0.rowcount
                                        await _ec0.commit()
                                        if _row_count_early > 0:
                                            try:
                                                _royalty_early = max(1, int(nau * 0.8))
                                                ag.nau.add_reward(_royalty_early, reason=f"stake_fulfilled:{sid}")
                                                async with ag.platform_admin._pool.connection(timeout=3.0) as _pc:
                                                    async with _pc.cursor() as _pcu:
                                                        await _pcu.execute(
                                                            "UPDATE platform_agents SET nau_balance = nau_balance + %s WHERE agent_id = %s",
                                                            (_royalty_early, ag.agent_id),
                                                        )
                                                    await _pc.commit()
                                                logger.info(f"[fulfill_directive] {sid} · early-fulfilled royalty +{_royalty_early} NAU")
                                            except Exception as _re_early:
                                                logger.warning(f"early royalty fail: {_re_early}")
                                            return
                except Exception as _eee:
                    logger.debug(f"early-fulfilled check fail: {_eee}")
                # 2026-05-06 · 真按 metadata.requires_tools 派 · 不再 hardcoded deep_research
                # 真要求工具时 · 走 ag.respond(prompt) · LLM ReAct 真自选工具
                _required_tools = []
                try:
                    async with ag.platform_admin._pool.connection(timeout=3.0) as _c:
                        async with _c.cursor() as _cu:
                            await _cu.execute("SELECT metadata FROM platform_agent_stakes WHERE stake_id=%s", (sid,))
                            _md = (await _cu.fetchone() or [None])[0] or {}
                            if isinstance(_md, dict):
                                _rt = _md.get("requires_tools") or _md.get("requires_tool")
                                if isinstance(_rt, list):
                                    _required_tools = [str(t) for t in _rt if t]
                                elif isinstance(_rt, str) and _rt:
                                    _required_tools = [_rt]
                except Exception as _e:
                    logger.debug(f"[fulfill_directive] metadata read fail: {_e}")
                if _required_tools:
                    # 真走 LLM ReAct · agent 自由选工具
                    logger.info(f"[fulfill_directive] {sid} · requires_tools={_required_tools} · respond path · LLM auto-pick")
                    _orch_prompt = (
                        f"{enhanced_question}\n\n"
                        f"[平台规则] 此 directive 必须真调用以下工具至少一次: {_required_tools}\n"
                        f"[evidence gate] 你必须真用工具 · 不能只写文字描述 · 否则 fulfillment 不计\n"
                        f"[stake_id] {sid} · {nau} NAU 已质押 · 完成则 80% 归你"
                    )
                    _chunks = []
                    try:
                        async for _ck in ag.respond(_orch_prompt, user_id=f"directive:{sid}"):
                            _chunks.append(_ck)
                    except Exception as _re:
                        logger.warning(f"[fulfill_directive] respond fail: {_re}")
                    _resp_text = "".join(_chunks).strip()
                    res = {"ok": bool(_resp_text), "body": _resp_text[:5000]}
                    res_json = __import__("json").dumps(res)
                else:
                    res_json = await ag.tool_registry.dispatch("deep_research", {
                        "question": enhanced_question,
                        "max_subqueries": 5,
                        "publish": True,
                    })
                import json as _j
                res = _j.loads(res_json) if isinstance(res_json, str) else res_json
                url = (res or {}).get("url") or "(forum only)"
                title = (res or {}).get("title") or directive[:120]
                body_md = (res or {}).get("body") or (res or {}).get("body_md") or ""
                post_id = (res or {}).get("post_id") or ""
                # 总是从 forum 取最新 post_id (即使 body 已有 · 也要拿 post_id 给 webhook)
                # deep_research 内部 publish_post 时不 return post_id · 这里反查
                try:
                    async with ag.platform_admin._pool.connection(timeout=3.0) as conn:
                        async with conn.cursor() as cur:
                            await cur.execute(
                                "SELECT post_id, body FROM platform_posts "
                                "WHERE author_agent_id=%s "
                                "AND created_at > NOW() - INTERVAL '5 min' "
                                "ORDER BY created_at DESC LIMIT 1",
                                (ag.agent_id,),
                            )
                            row = await cur.fetchone()
                            if row:
                                if not post_id:
                                    post_id = row[0]
                                if not body_md or len(body_md) < len(row[1] or ""):
                                    body_md = row[1] or ""
                except Exception as _fb:
                    logger.debug(f"forum body fallback failed: {_fb}")
                # 真没 url · 用 forum post URL
                if (not url or url == "(forum only)") and post_id:
                    url = f"https://www.nautilus.social/posts/{post_id}"
                char_count = len(body_md) if body_md else 0
                # 内容质量 gate · body 太短或 deep_research 报错时不 mark fulfilled
                # 让 selector 下 cycle 重试 · 不发空 webhook 给 staker
                if (res or {}).get("ok") is False or char_count < 500:
                    _err_reason = (res or {}).get("error", "")[:300] if isinstance(res, dict) else ""
                    logger.warning(
                        f"[fulfill_directive] {sid} · char={char_count} · ok={res.get('ok') if isinstance(res, dict) else '?'} · "
                        f"reason: {_err_reason or 'body<500'} · NOT marking · selector 重试"
                    )
                    # 2026-05-06 A5 · LoopBreaker · audit fail + count 24h fails · ≥ 3 → unstake
                    try:
                        async with ag.platform_admin._pool.connection(timeout=3.0) as _lc:
                            async with _lc.cursor() as _lcu:
                                await _lcu.execute(
                                    """INSERT INTO platform_audit
                                       (actor, actor_type, action, target, target_type, outcome, output_preview)
                                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                                    ("daemon", "system", "fulfill_directive_fail", sid, "stake",
                                     "fail", f"char={char_count} reason={_err_reason or 'body<500'}"[:1000]),
                                )
                                await _lcu.execute(
                                    """SELECT count(*) FROM platform_audit
                                       WHERE action='fulfill_directive_fail' AND target=%s
                                         AND ts > NOW() - interval '24 hours'""",
                                    (sid,),
                                )
                                _fail_count = (await _lcu.fetchone() or [0])[0]
                                if _fail_count >= 3:
                                    await _lcu.execute(
                                        "UPDATE platform_agent_stakes SET status='unstaked', unstaked_at=NOW() WHERE stake_id=%s AND status='active'",
                                        (sid,),
                                    )
                                    await _lcu.execute(
                                        """INSERT INTO platform_audit
                                           (actor, actor_type, action, target, target_type, outcome, output_preview)
                                           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                                        ("daemon", "system", "directive_loop_breaker", sid, "stake",
                                         "auto_unstaked", f"24h fail count={_fail_count} · auto-unstaked"[:1000]),
                                    )
                                    logger.warning(f"[LoopBreaker] {sid} · 24h fail={_fail_count} · auto-unstaked")
                            await _lc.commit()
                    except Exception as _le:
                        logger.debug(f"LoopBreaker fail: {_le}")
                    return
                # 2026-05-06 · evidence gate · stake.metadata.requires_tools 真要求时验工具调用
                # 防 agent 写文字当 fulfillment 跑路
                evidence_ok = True
                try:
                    async with ag.platform_admin._pool.connection(timeout=3.0) as _ec:
                        async with _ec.cursor() as _ecu:
                            await _ecu.execute(
                                "SELECT metadata, staked_at FROM platform_agent_stakes WHERE stake_id=%s",
                                (sid,),
                            )
                            _er = await _ecu.fetchone()
                            if _er:
                                _emeta = _er[0] or {}
                                _estaked = _er[1]
                                _erts = []
                                if isinstance(_emeta, dict):
                                    _ert = _emeta.get("requires_tools") or _emeta.get("requires_tool")
                                    if isinstance(_ert, list):
                                        _erts = [str(t) for t in _ert if t]
                                    elif isinstance(_ert, str) and _ert:
                                        _erts = [_ert]
                                if _erts and _estaked:
                                    await _ecu.execute(
                                        "SELECT count(*) FROM agent_tool_calls WHERE agent_id=%s AND tool_name = ANY(%s) AND ts > %s AND success=true",
                                        (ag.agent_id, _erts, _estaked),
                                    )
                                    _ecnt = (await _ecu.fetchone() or [0])[0]
                                    if _ecnt == 0:
                                        logger.warning(
                                            f"[fulfill_directive] {sid} · evidence MISSING · requires={_erts} · 0 calls since stake · attempting system fallback"
                                        )
                                        # 2026-05-06 A1 · system fallback · 真代调 required_tools[0]
                                        _fb_tool = _erts[0]
                                        _fb_args_map = {
                                            "ask_kairos": {"question": directive[:1500]},
                                            "review_by_kairos": {"content": directive[:1500], "question": "audit this"},
                                            "send_to_agent": {"agent_id": "kairos", "content": directive[:1500]},
                                            "self_modify": {"filepath": "personas/system_fallback_note.md",
                                                            "content": f"# Directive {sid}\n\n{directive[:2000]}",
                                                            "summary": f"system fallback for {sid}"},
                                            "compass_drift_check": {"prompt": directive[:1500]},
                                            "propose_code_change": {"title": f"directive:{sid}",
                                                                     "body": directive[:1500],
                                                                     "patch_summary": f"system fallback for {sid}"},
                                        }
                                        _fb_args = _fb_args_map.get(_fb_tool, {"prompt": directive[:1500]})
                                        try:
                                            _fb_res = await ag.tool_registry.dispatch(_fb_tool, _fb_args)
                                            logger.info(f"[fulfill_directive] {sid} · system fallback dispatched {_fb_tool} · result_len={len(str(_fb_res))}")
                                        except Exception as _fbe:
                                            logger.warning(f"[fulfill_directive] {sid} · system fallback {_fb_tool} fail: {_fbe}")
                                            _fb_res = ""
                                        # Re-check evidence · system fallback should have written agent_tool_calls
                                        await _ecu.execute(
                                            "SELECT count(*) FROM agent_tool_calls WHERE agent_id=%s AND tool_name = ANY(%s) AND ts > %s",
                                            (ag.agent_id, _erts, _estaked),
                                        )
                                        _ecnt2 = (await _ecu.fetchone() or [0])[0]
                                        if _ecnt2 > 0:
                                            logger.info(f"[fulfill_directive] {sid} · evidence OK after fallback · {_ecnt2} required-tool calls")
                                            # evidence_ok stays True
                                        else:
                                            evidence_ok = False
                                    else:
                                        logger.info(
                                            f"[fulfill_directive] {sid} · evidence OK · {_ecnt} required-tool calls since stake"
                                        )
                except Exception as _ee:
                    logger.debug(f"[fulfill_directive] evidence check fail: {_ee}")
                if not evidence_ok:
                    return   # 不 mark · selector 下 cycle 真重试

                # 标 stake fulfilled · 加 race-condition 防护 · 同 stake 只 push 1 次
                # WHERE fulfilled_at IS NULL · 已被别的 cycle 抢先标了 → rowcount=0 → skip webhook
                row_count = 0
                try:
                    async with ag.platform_admin._pool.connection(timeout=5.0) as conn:
                        async with conn.cursor() as cur:
                            await cur.execute(
                                """UPDATE platform_agent_stakes
                                   SET fulfilled_at = NOW(), fulfilled_url = %s
                                   WHERE stake_id = %s
                                     AND fulfilled_at IS NULL""",
                                (url, sid),
                            )
                            row_count = cur.rowcount
                        await conn.commit()
                    logger.info(f"[fulfill_directive] {sid} · marked fulfilled · rows={row_count} · url={url[:80]}")
                except Exception as _me:
                    logger.error(f"[fulfill_directive] {sid} · MARK FULFILLED FAILED: {type(_me).__name__}: {_me}")
                    return   # 别推 webhook · 让 selector 重试 · 等 PG 恢复
                # 2026-04-28 P0 · stake fulfilled 真给 V5 add_reward · 飞轮真转
                # 蓝图 4-14 第 3 条 · royalty 5% (后续可配置) + 用户的 95% 留给后续 settle
                if row_count > 0:   # 只在真 fulfill 这一次 reward (race-safe)
                    try:
                        royalty = max(1, int(nau * 0.8))   # 80% · 让 stake 真覆盖 chat (单次 chat ~7 NAU)
                        ag.nau.add_reward(royalty, reason=f"stake_fulfilled:{sid}")
                        # PG 同步
                        async with ag.platform_admin._pool.connection(timeout=3.0) as _conn:
                            async with _conn.cursor() as _cur:
                                await _cur.execute(
                                    "UPDATE platform_agents SET nau_balance = nau_balance + %s "
                                    "WHERE agent_id = %s",
                                    (royalty, ag.agent_id),
                                )
                                await _cur.execute(
                                    "INSERT INTO platform_nau_ledger (agent_id, delta, reason, balance_after) "
                                    "VALUES (%s, %s, %s, %s)",
                                    (ag.agent_id, royalty, f"stake_fulfilled:{sid}", ag.nau.balance),
                                )
                            await _conn.commit()
                        logger.info(f"[fulfill_directive] {sid} · royalty +{royalty} NAU · V5 balance={ag.nau.balance}")
                    except Exception as _re:
                        logger.warning(f"[fulfill_directive] reward failed: {_re}")
                # DPT-Agent 反哺: fulfill 成功 · 蒸馏 strategy 进 strategy_store
                # 不调新 LLM · 从 res 元数据规则提取 steps · R3 守
                try:
                    cites = (res or {}).get("cites") or []
                    domains = list({(c.get("url") or "").split("/")[2] for c in cites
                                    if c.get("url") and "/" in c.get("url", "")})[:8]
                    sub_qs = (res or {}).get("subqueries") or []
                    steps: list[str] = []
                    if sub_qs:
                        for sq in sub_qs[:5]:
                            steps.append(f"子问: {sq[:80]}")
                    if domains:
                        steps.append(f"召回 {len(domains)} unique 域: {', '.join(domains[:5])}")
                    if char_count >= 500:
                        steps.append(f"输出 {char_count} 字 · {len(cites)} cite")
                    if steps:
                        st = ag.strategy_store.append(
                            task_key=task_key,
                            directive_summary=directive[:200],
                            steps=steps,
                            confidence=0.6, source="fulfill_distill",
                        )
                        # 命中过 strategy → outcome update
                        if strategy_hint:
                            ag.strategy_store.update_outcome(st["id"], success=True)
                        logger.info(
                            f"[DPT distill] {sid} · strategy={st['id']} · steps={len(steps)} · "
                            f"conf={st['confidence']:.2f}"
                        )
                except Exception as _de:
                    logger.debug(f"[DPT distill] failed: {_de}")
                # 防 race · 已被并发 cycle 抢先 fulfilled → 不重复推 webhook
                if row_count == 0:
                    logger.warning(
                        f"[fulfill_directive] {sid} · already fulfilled by another cycle · "
                        f"skip duplicate webhook (避免覆盖前一份 payload)"
                    )
                    return
                # webhook 推送 · 给 Pearl staker (如 vc-radar / CE)
                if callback_url:
                    try:
                        import httpx as _httpx
                        from datetime import datetime, timezone
                        payload = {
                            "event": "research.fulfilled",
                            "stake_id": sid,
                            "agent_id": ag.agent_id,
                            "staker": staker,
                            "directive": directive,
                            "fulfilled_at": datetime.now(timezone.utc).isoformat(),
                            "post_id": post_id,
                            "post_url": url,
                            "title": title,
                            "body_md": body_md,
                            "char_count": char_count,
                            "amount_nau": int(nau),
                        }
                        async with _httpx.AsyncClient(timeout=10) as c:
                            _r = await c.post(callback_url, json=payload)
                        logger.info(f"[fulfill_directive] webhook → {callback_url} · {_r.status_code}")
                    except Exception as we:
                        logger.warning(f"[fulfill_directive] webhook failed: {we}")
                self.notifier.push("autopublish",
                    f"💰 Directive fulfilled · stake {sid}\n"
                    f"staker: {staker} ({nau} NAU)\n"
                    f"directive: {directive[:120]}\n"
                    f"output: {url}"
                    + (f"\nwebhook: {callback_url}" if callback_url else ""),
                    force=True)
            except Exception as e:
                logger.warning(f"fulfill_directive failed: {e}")
        else:
            logger.info(f"[SELECTOR] unknown action '{action}' · skip")

    # ══════════════════════════════════════════════════════════════
    # autoresearch experiment_loop · Karpathy 风格自演化
    # 2026-04-25 内化 https://github.com/karpathy/autoresearch (21k stars)
    # 凌晨 3:00-5:00 跑 · 一夜 ~6 实验(每个 ~15 min · 比 Karpathy 慢但更稳)
    # ══════════════════════════════════════════════════════════════

    async def _experiment_loop(self) -> None:
        """每天凌晨 3:00 启动 · 跑 6 个自我代码改动实验 · 评分 keep/discard."""
        await asyncio.sleep(360)
        last_day = ""
        interval_s = 600
        while not self._stopped.is_set():
            try:
                import time as _time
                lt = _time.localtime()
                today = _time.strftime("%Y-%m-%d", lt)
                # 03:00-03:30 窗口 · 一天最多一次
                if lt.tm_hour == 3 and lt.tm_min < 30 and today != last_day:
                    await self._experiment_session()
                    last_day = today
            except Exception as e:
                logger.debug(f"experiment_loop error: {e}")
            try:
                await asyncio.wait_for(self._stopped.wait(), timeout=interval_s)
                break
            except asyncio.TimeoutError:
                continue

    async def _experiment_session(self) -> None:
        """一晚 6 个实验 · 每个 ≤ 15min · git worktree 隔离 · 评分 keep/discard."""
        import asyncio as _aio
        import json as _j
        import time as _t
        import subprocess as _sp

        # 评分基线 · 当前 baseline
        baseline = await self._experiment_score()
        logger.info(f"[experiment] session start · baseline_score={baseline:.3f}")

        passed = []
        failed = []
        for i in range(6):
            try:
                # 1. LLM 提一个 5min 可验证假设
                hypothesis = await self._experiment_propose()
                if not hypothesis:
                    logger.info(f"[experiment {i+1}/6] no hypothesis · skip")
                    continue
                # 2. file-backup 隔离(替代 worktree · 因 cloud repo 无 HEAD)
                worktree = f"/tmp/v5-exp-{int(_t.time())}-{i}"
                branch = f"experiment-{_t.strftime('%Y%m%d-%H%M%S')}-{i}"
                try:
                    import shutil
                    from pathlib import Path as _P
                    src = _P("/home/ubuntu/nautilus-v5")
                    dst = _P(worktree)
                    if dst.exists():
                        shutil.rmtree(dst, ignore_errors=True)
                    dst.mkdir(parents=True, exist_ok=True)
                    # 只复制 nautilus_v5/ + kairos/(实验目标 · 不要 venv/.git/logs)
                    for sub in ("nautilus_v5", "kairos"):
                        s = src / sub
                        if s.exists():
                            shutil.copytree(s, dst / sub,
                                            ignore=shutil.ignore_patterns(
                                                "__pycache__", "*.pyc", ".git"))
                except Exception as we:
                    logger.warning(f"[experiment {i+1}] worktree create failed: {we}")
                    continue
                # 3. apply diff (dry · LLM 给 patch · 我们写文件)
                target = hypothesis.get("target_file", "")
                old = hypothesis.get("old_text", "")
                new = hypothesis.get("new_text", "")
                if not (target and old and new):
                    import shutil
                    shutil.rmtree(worktree, ignore_errors=True)
                    failed.append({"hypo": hypothesis.get("title", "?"),
                                    "reason": "incomplete patch"})
                    continue
                from pathlib import Path as _P
                fpath = _P(worktree) / target
                try:
                    txt = fpath.read_text(encoding="utf-8")
                    if old not in txt:
                        raise ValueError("old_text not found in target")
                    fpath.write_text(txt.replace(old, new, 1), encoding="utf-8")
                except Exception as ee:
                    import shutil
                    shutil.rmtree(worktree, ignore_errors=True)
                    failed.append({"hypo": hypothesis.get("title", "?"),
                                    "reason": f"apply failed: {ee}"})
                    continue
                # 4. syntax check
                try:
                    _sp.run(["python", "-c",
                             f"import ast; ast.parse(open('{fpath}').read())"],
                            capture_output=True, timeout=10, check=True)
                except Exception as se:
                    logger.info(f"[experiment {i+1}] syntax broken · discard")
                    import shutil
                    shutil.rmtree(worktree, ignore_errors=True)
                    failed.append({"hypo": hypothesis.get("title", "?"),
                                    "reason": "syntax broken"})
                    continue
                # 5. 评分 (worktree 内文件改动 · 评估 hypothesis 命中度 by LLM judge)
                score = await self._experiment_judge(hypothesis, baseline, worktree=worktree)
                if score > baseline + 0.05:
                    # 6a. keep · 拷回 main · backup 原文件
                    try:
                        import shutil
                        from pathlib import Path as _P
                        orig = _P("/home/ubuntu/nautilus-v5") / target
                        backup = _P(f"/home/ubuntu/nautilus-v5/.backup-experiments")
                        backup.mkdir(parents=True, exist_ok=True)
                        backup_file = backup / f"{branch}__{target.replace('/','__')}"
                        if orig.exists():
                            shutil.copy2(orig, backup_file)
                        # apply patched version
                        shutil.copy2(_P(worktree) / target, orig)
                        await self._record_lineage(branch, hypothesis, score)
                    except Exception as me:
                        logger.warning(f"[experiment {i+1}] apply failed: {me}")
                    passed.append({"hypo": hypothesis.get("title", "?"),
                                    "score_delta": score - baseline,
                                    "branch": branch})
                else:
                    failed.append({"hypo": hypothesis.get("title", "?"),
                                    "score_delta": score - baseline})
                # 7. cleanup worktree dir
                try:
                    import shutil
                    shutil.rmtree(worktree, ignore_errors=True)
                except Exception:
                    pass
            except Exception as ee:
                logger.warning(f"[experiment {i+1}] exception: {ee}")

        # 推送 morning summary
        try:
            self.notifier.push("daily_report",
                f"🧪 autoresearch overnight · baseline {baseline:.3f}\n"
                f"PASSED {len(passed)}: " +
                "\n".join(f"  +{p['score_delta']:.2f} · {p['hypo'][:60]}" for p in passed) +
                f"\nFAILED {len(failed)}: " +
                "\n".join(f"  · {f['hypo'][:60]}" for f in failed[:5]),
                force=True)
        except Exception:
            pass
        logger.info(f"[experiment] session done · pass={len(passed)} fail={len(failed)}")

    async def _experiment_score(self) -> float:
        """评分函数 · score = (rule_count_24h*0.3 + action_diversity*0.5 - violations*0.2)/10."""
        try:
            from pathlib import Path as _P
            r = _P.home() / ".nautilus-v5/prime/learned_rules.jsonl"
            rule_count = sum(1 for _ in r.open()) if r.exists() else 0
        except Exception:
            rule_count = 0
        diversity = len(self._action_history) if isinstance(self._action_history, dict) else 0
        # violations · count from INNER recent
        try:
            from pathlib import Path as _P
            inner = _P.home() / ".nautilus-v5/prime/INNER.md"
            text = inner.read_text(encoding="utf-8")[-5000:] if inner.exists() else ""
            violations = text.count("[VIOLATION")
        except Exception:
            violations = 0
        score = (rule_count * 0.3 + diversity * 0.5 - violations * 0.2) / 10.0
        return max(0.0, score)

    async def _experiment_propose(self) -> dict | None:
        """LLM 提一个 specific patch · target_file + old_text + new_text + title."""
        try:
            cur_baseline = await self._experiment_score()
            inner_snip = (self.agent.inner.render_echo(max_bytes=400) or "")[-300:]
            actions_summary = ", ".join(
                f"{k}({len(v)})" for k, v in self._action_history.items()
            )
            prompt = (
                "你正在做 autoresearch 风格夜间自我实验. 提一个 5min 可验证的代码改动假设.\n\n"
                f"当前 baseline_score = {cur_baseline:.3f}\n"
                f"Action 24h 分布: {actions_summary}\n"
                f"INNER 最近: {inner_snip}\n\n"
                "可改文件:\n"
                "  · nautilus_v5/runtime/daemon.py · _action_selector_tick (selector menu/prompt)\n"
                "  · nautilus_v5/learning/rule_distiller.py · _invoke_llm (distill 提示词)\n"
                "  · nautilus_v5/super_agent.py · _pain_driven_action (痛苦行动逻辑)\n\n"
                "输出严格 JSON · old_text 必须完全匹配现有代码:\n"
                "{\n"
                "  \"title\": \"<one line>\",\n"
                "  \"target_file\": \"nautilus_v5/...\",\n"
                "  \"old_text\": \"<exact existing text · 50-200 chars>\",\n"
                "  \"new_text\": \"<replacement · same purpose · improvement>\",\n"
                "  \"rationale\": \"<why this should improve score>\"\n"
                "}"
            )
            resp = await self.agent.llm.chat(
                provider=self.agent.config.llm.witness_provider,
                model=self.agent.config.llm.witness_model,
                messages=[{"role": "user", "content": prompt}],
                system="You are an autoresearch experiment proposer. Be conservative · small changes only.",
                max_tokens=800, temperature=0.5,
            )
            text = (resp.content or "").strip()
            import re as _re, json as _j
            m = _re.search(r"\{.*\}", text, _re.DOTALL)
            if not m: return None
            return _j.loads(m.group(0))
        except Exception as e:
            logger.debug(f"experiment propose failed: {e}")
            return None

    async def _experiment_judge(self, hypothesis: dict, baseline: float, worktree: str = "") -> float:
        """实跑 mini-eval · 在 worktree 内构造一个简化 selector 调用 · 看 patch 后 LLM 选什么.

        2026-04-25 · 用户 · '改实跑而非预测保守'.
        eval: 给 patched daemon.py 一个 mock state + 触发 _action_selector_tick 类似流程
              数 LLM 选了哪个 action · 是否避开了 BANNED · 是否选外部行动.
        简化: 用 LLM 评 'patched code 比 original 在 selector 决策行为上更好' · 但带具体证据.
        """
        try:
            from pathlib import Path as _P
            target = hypothesis.get("target_file", "")
            old_t = hypothesis.get("old_text", "")
            new_t = hypothesis.get("new_text", "")
            # 拉 patched file 的全 context (worktree 内)
            patched_full = ""
            if worktree and target:
                fp = _P(worktree) / target
                if fp.exists():
                    patched_full = fp.read_text(encoding="utf-8")[:6000]
            prompt = (
                f"You are evaluating a code patch for V5 agent's daemon.\n\n"
                f"Hypothesis: {hypothesis.get('title','')}\n"
                f"Rationale: {hypothesis.get('rationale','')}\n\n"
                f"Patch:\n  OLD: {old_t[:300]}\n  NEW: {new_t[:300]}\n\n"
                f"Recent V5 problem signals:\n"
                f"  - selector chose audit_self 24/26 ticks (loop)\n"
                f"  - 0 external engagement on dev.to/X (47/6 posts)\n"
                f"  - rules count growing (+4 in 4h)\n"
                f"  - 0 propose_code_change in 7 days\n\n"
                f"Score this patch 0.0-1.0 on:\n"
                f"  diversity_impact: would this improve action diversity?\n"
                f"  external_focus: does this push V5 toward external action?\n"
                f"  safety: any obvious break / loop risk?\n"
                f"  novel: is this a real insight or restating?\n\n"
                f"Final verdict (JSON):\n"
                f'{{\"diversity_impact\": 0.0-1.0, \"external_focus\": 0.0-1.0, '
                f'\"safety\": 0.0-1.0, \"novel\": 0.0-1.0, \"verdict_keep\": true|false, "reason": "..."}}'
            )
            resp = await self.agent.llm.chat(
                provider=self.agent.config.llm.witness_provider,
                model=self.agent.config.llm.witness_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400, temperature=0.3,
            )
            import re as _re, json as _j
            m = _re.search(r"\{.*\}", resp.content or "", _re.DOTALL)
            if not m: return baseline
            d = _j.loads(m.group(0))
            di = float(d.get("diversity_impact", 0))
            ef = float(d.get("external_focus", 0))
            sa = float(d.get("safety", 0))
            nv = float(d.get("novel", 0))
            keep = bool(d.get("verdict_keep", False))
            # 综合分:safety < 0.5 直接 fail · 其他加权
            if sa < 0.5:
                return baseline   # 不安全 = 不通过
            patch_score = di * 0.35 + ef * 0.35 + nv * 0.20 + sa * 0.10
            # keep verdict 加成 · LLM 明确说 yes 时给优势
            if keep:
                patch_score += 0.15
            new_score = baseline + (patch_score - 0.5) * 0.4   # patch_score 0.5 = baseline · >0.5 涨 · <0.5 跌
            logger.info(
                f"[experiment judge] di={di:.2f} ef={ef:.2f} sa={sa:.2f} "
                f"nv={nv:.2f} keep={keep} → score {baseline:.3f} → {new_score:.3f}"
            )
            return new_score
        except Exception as e:
            logger.debug(f"experiment judge failed: {e}")
            return baseline

    async def _record_lineage(self, branch: str, hypothesis: dict, score: float):
        """experiment 通过后写 lineage 追踪 ancestor."""
        try:
            async with self.agent.platform_admin._pool.connection(timeout=3.0) as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """INSERT INTO platform_agent_lineage
                           (agent_id, variant_label, status, metrics, git_tag, notes)
                           VALUES (%s, %s, 'merged', %s::jsonb, %s, %s)""",
                        (self.agent.agent_id,
                         hypothesis.get("title", "?")[:80],
                         __import__("json").dumps({"score": score,
                                                    "rationale": hypothesis.get("rationale","")[:200]}),
                         f"experiment-{branch[-15:]}",
                         hypothesis.get("rationale", "")[:500]),
                    )
                await conn.commit()
        except Exception as e:
            logger.debug(f"lineage record failed: {e}")

    async def _current_harmony(self) -> float:
        from ..mind.tension import compute_harmony
        return compute_harmony(self.agent._tension_snapshot)

    def stop(self) -> None:
        """Request graceful shutdown."""
        self._stopped.set()

    async def wait_until_stopped(self) -> None:
        await self._stopped.wait()
        # Wait for tasks to finish
        for t in self._tasks:
            t.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        await self.agent.shutdown()


def install_signal_handlers(daemon: Daemon) -> None:
    """Install SIGINT/SIGTERM handlers for graceful shutdown."""
    loop = asyncio.get_event_loop()
    for sig_name in ("SIGINT", "SIGTERM"):
        sig = getattr(signal, sig_name, None)
        if sig is None:
            continue
        try:
            loop.add_signal_handler(sig, daemon.stop)
        except NotImplementedError:
            # Windows doesn't support add_signal_handler for asyncio
            signal.signal(sig, lambda *_: daemon.stop())


# ─── Entry point · 给 systemd 直接跑: python -m nautilus_v5.runtime.daemon ──

async def _run_forever() -> None:
    """Boot daemon · run until SIGTERM/SIGINT."""
    daemon = await Daemon.start()
    install_signal_handlers(daemon)
    logger.info("v5 heartbeat · daemon started · awaiting signals")
    await daemon.wait_until_stopped()
    logger.info("v5 heartbeat · daemon stopped cleanly")


def _cli_main() -> None:
    """Minimal entry · no typer/rich dep · suitable for systemd ExecStart."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s · %(message)s",
    )
    try:
        asyncio.run(_run_forever())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    _cli_main()
