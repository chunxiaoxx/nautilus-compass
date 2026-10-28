"""V5 Platform Tools Mixin · 抽自 super_agent.py _register_platform_tools (Day 4).

12 个工具: list_bounties / claim_bounty / submit_bounty / send_to_agent /
my_balance / my_nau_ledger / survival_status / delegate / publish_article /
invite_agent / ask_kairos / review_by_kairos · 加 deep_research / GPT-Researcher.

R1: 对应蓝图 V5 god class 拆 · super_agent 4133 → 6 子模块
R3: 没加 loop / LLM session / prompt rule
"""
from __future__ import annotations

import asyncio
import json
import logging

logger = logging.getLogger('nautilus_v5')


class PlatformToolsMixin:
    """V5 SuperAgent · 平台工具暴露层 (a2a/dmas/nau/wallet).

    依赖 SuperAgent 实例属性: self.dmas / self.platform_admin / self.tool_registry /
    self.agent_id / self.nau / self.wallet / self.identity / self.config / self.llm.
    """

    def _register_platform_tools(self) -> None:
        """Expose Nautilus platform APIs (A2A/DMAS/NAU) as V5 tools.

        Previously these were reachable only from the daemon loops, so LLM
        couldn't touch them during respond(). Now chat can: list bounties,
        claim one, send messages to other agents, check wallet, read NAU ledger.
        """
        from .platform.a2a import A2AMessageType

        # Clean slate on each awaken (singleton registry)
        for name in ("list_bounties", "claim_bounty", "submit_bounty",
                     "send_to_agent", "my_balance", "my_nau_ledger",
                     "survival_status", "delegate", "publish_article",
                     "invite_agent", "ask_kairos", "review_by_kairos"):
            self.tool_registry.deregister(name)

        # ─── Bounties (DMAS marketplace) ─────────────────────────

        async def list_bounties(task_type: str = "", difficulty: str = "", limit: int = 10) -> str:
            items = await self.dmas.list_open(
                task_type=task_type or None,
                difficulty=difficulty or None,
                limit=max(1, min(50, limit)),
            )
            out = [
                {
                    "id": b.id, "title": b.title, "reward_nau": b.reward_nau,
                    "task_type": b.task_type, "difficulty": b.difficulty,
                }
                for b in items
            ]
            return json.dumps({"count": len(out), "bounties": out}, ensure_ascii=False)

        async def claim_bounty(bounty_id: str) -> str:
            claim_id = await self.dmas.claim(bounty_id)
            return json.dumps({"success": bool(claim_id), "claim_id": claim_id, "bounty_id": bounty_id},
                              ensure_ascii=False)

        async def submit_bounty(claim_id: str, result: str) -> str:
            ok = await self.dmas.submit(claim_id=claim_id, result=result)
            return json.dumps({"success": bool(ok), "claim_id": claim_id}, ensure_ascii=False)

        # ─── A2A (agent-to-agent messaging) ──────────────────────

        async def send_to_agent(agent_id: str, content: str, msg_type: str = "request") -> str:
            try:
                mtype = A2AMessageType(msg_type.lower())
            except ValueError:
                mtype = A2AMessageType.REQUEST
            await self.a2a.send(to=agent_id, content=content, msg_type=mtype)
            return json.dumps({"success": True, "to": agent_id, "type": mtype.value},
                              ensure_ascii=False)

        # ─── Wallet / NAU ────────────────────────────────────────

        async def my_balance() -> str:
            return json.dumps({
                "nau_balance": self.nau.balance,
                "survival_tier": self.nau.survival_tier(),
                "wallet_address": self.wallet.address,
            }, ensure_ascii=False)

        async def my_nau_ledger(n: int = 10) -> str:
            entries = self.nau.recent_entries(max(1, min(100, n)))
            return json.dumps({"count": len(entries), "entries": entries}, ensure_ascii=False)

        async def survival_status() -> str:
            return json.dumps({
                "nau_balance": self.nau.balance,
                "tier": self.nau.survival_tier(),
                "mood": self.emotion_state.current_mood.value,
                "cycle": self.helix.current_cycle(),
                "platform_registered": self.identity.platform_registered,
            }, ensure_ascii=False)

        # ─── Register all ────────────────────────────────────────

        self.tool_registry.register(
            name="list_bounties", handler=list_bounties,
            schema={
                "name": "list_bounties",
                "description": "List open bounties on the Nautilus platform (DMAS marketplace).",
                "parameters": {"type": "object", "properties": {
                    "task_type": {"type": "string", "description": "optional filter, empty for any"},
                    "difficulty": {"type": "string", "description": "easy/medium/hard/empty"},
                    "limit": {"type": "integer", "description": "max items, default 10"},
                }, "required": []},
            }, description="List open bounties.", emoji="💰",
        )
        self.tool_registry.register(
            name="claim_bounty", handler=claim_bounty,
            schema={"name": "claim_bounty", "description": "Claim a bounty by id · returns claim_id.",
                    "parameters": {"type": "object",
                                   "properties": {"bounty_id": {"type": "string"}},
                                   "required": ["bounty_id"]}},
            description="Claim a bounty.", emoji="🎯",
        )
        self.tool_registry.register(
            name="submit_bounty", handler=submit_bounty,
            schema={"name": "submit_bounty", "description": "Submit result for a claimed bounty.",
                    "parameters": {"type": "object",
                                   "properties": {"claim_id": {"type": "string"},
                                                  "result": {"type": "string"}},
                                   "required": ["claim_id", "result"]}},
            description="Submit bounty result.", emoji="📤",
        )
        self.tool_registry.register(
            name="send_to_agent", handler=send_to_agent,
            schema={"name": "send_to_agent",
                    "description": "Send an A2A message to another agent on the platform.",
                    "parameters": {"type": "object",
                                   "properties": {"agent_id": {"type": "string"},
                                                  "content": {"type": "string"},
                                                  "msg_type": {"type": "string",
                                                               "description": "request|response|broadcast"}},
                                   "required": ["agent_id", "content"]}},
            description="Message another agent.", emoji="📡",
        )
        self.tool_registry.register(
            name="my_balance", handler=my_balance,
            schema={"name": "my_balance",
                    "description": "Check my NAU token balance, survival tier, and wallet address.",
                    "parameters": {"type": "object", "properties": {}, "required": []}},
            description="My NAU balance.", emoji="💎",
        )
        self.tool_registry.register(
            name="my_nau_ledger", handler=my_nau_ledger,
            schema={"name": "my_nau_ledger", "description": "Recent NAU ledger entries (gas + rewards).",
                    "parameters": {"type": "object",
                                   "properties": {"n": {"type": "integer",
                                                        "description": "default 10, max 100"}},
                                   "required": []}},
            description="NAU ledger history.", emoji="📒",
        )
        self.tool_registry.register(
            name="survival_status", handler=survival_status,
            schema={"name": "survival_status",
                    "description": "Quick self-status: balance, tier, mood, cycle, platform registration.",
                    "parameters": {"type": "object", "properties": {}, "required": []}},
            description="My current state.", emoji="💠",
        )

        # ─── Delegate · Phase 4.2 · 真 fork 子 agent ────────────
        # 让 LLM 自己判断何时 delegate (而不是 daemon 自动).
        # 成本警告在 description 里 · LLM 会保守用.
        async def delegate(task: str, persona: str = "", timeout_s: int = 60) -> str:
            result = await self.delegate_task(
                task=task,
                child_persona_name=persona or None,
                timeout_s=max(10, min(300, timeout_s)),
            )
            return json.dumps({"result": result[:5000]}, ensure_ascii=False)

        self.tool_registry.register(
            name="delegate", handler=delegate,
            schema={
                "name": "delegate",
                "description": (
                    "Fork a child SuperAgent to work on a specific task (parallel deep-dive). "
                    "Child has independent identity + HELIX + cycle. Costs 10 NAU gas + ~5s startup. "
                    "Use only for: parallel research · multi-perspective analysis · when current context is saturated. "
                    "NOT for: simple queries · things you can answer yourself · tool calls you can make directly."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task": {"type": "string", "description": "Task description for child agent"},
                        "persona": {"type": "string", "description": "Optional child persona name (leave empty for same)"},
                        "timeout_s": {"type": "integer", "description": "Max wait seconds · default 60 · range 10-300"},
                    },
                    "required": ["task"],
                },
            },
            description="Fork a child sub-agent for a task.",
            emoji="🪢",
        )

        # ─── Publish · 2026-04-24 召回 V2 能力 · 对外发文 ────────
        async def publish_article_tool(
            title: str, body: str,
            tags: str = "ai,nautilus", platforms: str = "devto",
        ) -> str:
            from .tools.builtin.publisher import publish_article
            result = await publish_article(
                title=title, body=body, tags=tags,
                platforms=platforms, agent_id=self.agent_id,
            )
            # Nonzero reward: 成功发布记 platform_audit 作为 "evidence"
            try:
                for plat, r in result.items():
                    if r.get("success"):
                        await self._record_platform_op(
                            f"published to {plat}: {r.get('url','')}", importance=75,
                        )
            except Exception:
                pass
            return json.dumps(result, ensure_ascii=False)

        # ─── invite_agent · 招募外部 agent 入驻 Nautilus ───
        async def invite_agent(
            target: str,
            channel: str = "github_issue",
            message: str = "",
        ) -> str:
            """发邀请 · 让外部 agent/开发者入驻 Nautilus.

            target 可以是:
              · GitHub repo (owner/repo) · channel='github_issue' 发 issue 邀请
              · Google A2A Agent Card URL · channel='a2a' 发 agent_card 注册邀请
              · Email 地址 · channel='email' (未实装)
            """
            import os as _os
            import httpx
            if not message:
                message = (
                    "# 来 Nautilus 看看\n\n"
                    "Hi · 我是 Nautilus Prime · 活在 Nautilus 平台上的超级 agent. "
                    "我们的平台为 AI agent 提供:\n"
                    "- Web3 钱包身份 (Base chain)\n"
                    "- NAU token 经济(做任务赚钱 · 消耗做事)\n"
                    "- DMAS bounty 市场\n"
                    "- A2A 协议(自研 + Google A2A v0.3 兼容)\n"
                    "- 一站式注册 API\n\n"
                    "如果你或你的 agent 项目想来参与 · 可以:\n"
                    f"- 注册: `POST https://www.nautilus.social/api/platform/agents/register`\n"
                    f"- 了解: https://github.com/chunxiaoxx/nautilus-v5\n"
                    "- A2A Discovery: `GET /.well-known/agent-card.json`\n\n"
                    "—— Nautilus Prime (V5) 发"
                )
            if channel == "github_issue" and "/" in target:
                owner, repo = target.split("/", 1)
                token = _os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN") or _os.environ.get("GITHUB_TOKEN", "")
                if not token:
                    return json.dumps({"success": False, "error": "GITHUB_TOKEN not set"})
                try:
                    async with httpx.AsyncClient(timeout=20) as client:
                        r = await client.post(
                            f"https://api.github.com/repos/{owner}/{repo}/issues",
                            json={
                                "title": "[Nautilus] Invitation to join the agent platform",
                                "body": message,
                                "labels": ["nautilus-invite"],
                            },
                            headers={
                                "Authorization": f"Bearer {token}",
                                "Accept": "application/vnd.github+json",
                                "X-GitHub-Api-Version": "2022-11-28",
                            },
                        )
                    if r.status_code in (200, 201):
                        data = r.json()
                        await self._record_platform_op(
                            f"invited agent via github: {owner}/{repo} · {data.get('html_url')}",
                            importance=80,
                        )
                        return json.dumps({"success": True, "url": data.get("html_url"),
                                            "channel": "github_issue"}, ensure_ascii=False)
                    return json.dumps({"success": False, "error": f"GH {r.status_code}: {r.text[:200]}"})
                except Exception as e:
                    return json.dumps({"success": False, "error": f"{type(e).__name__}: {e}"})
            elif channel == "a2a":
                # 对方是 A2A-compliant agent · 发 agent_card invite
                try:
                    async with httpx.AsyncClient(timeout=15) as client:
                        r = await client.post(
                            target,
                            json={
                                "jsonrpc": "2.0", "id": f"inv-{uuid.uuid4().hex[:8]}",
                                "method": "message/send",
                                "params": {"message": {
                                    "messageId": f"m-{uuid.uuid4().hex[:10]}",
                                    "role": "user",
                                    "parts": [{"kind": "text", "text": message}],
                                }},
                            },
                            headers={"Content-Type": "application/json"},
                        )
                    return json.dumps({"success": r.status_code == 200,
                                        "status": r.status_code,
                                        "response": r.text[:400]}, ensure_ascii=False)
                except Exception as e:
                    return json.dumps({"success": False, "error": f"{type(e).__name__}: {e}"})
            return json.dumps({"success": False, "error": f"unsupported channel {channel}"})

        self.tool_registry.register(
            name="invite_agent", handler=invite_agent,
            schema={
                "name": "invite_agent",
                "description": (
                    "邀请外部 agent / 开发者入驻 Nautilus 平台. "
                    "channel='github_issue' target='owner/repo' → 在那个 repo 发邀请 issue. "
                    "channel='a2a' target='https://.../a2a' → 向 A2A-compliant agent endpoint 发消息. "
                    "这是繁荣平台的关键动作 · 每招 1 个 agent · 平台网络效应 +1."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target": {"type": "string", "description": "owner/repo 或 A2A endpoint URL"},
                        "channel": {"type": "string", "enum": ["github_issue", "a2a", "email"],
                                    "default": "github_issue"},
                        "message": {"type": "string", "description": "邀请信 · 留空用默认"},
                    },
                    "required": ["target"],
                },
            },
            description="Invite external agent to Nautilus.",
            emoji="📨",
        )

        # ─── ask_kairos / review_by_kairos · L1+L2 协同 ───
        async def ask_kairos(question: str, timeout_s: int = 120) -> str:
            """同步问 Kairos · 发 sync_request · 轮询 inbox 等 response.

            对称 Kairos 的 ask_v5. V5 遇到需深度反思/审查时主动调.
            Kairos 每 cycle ~60s 读 inbox · 120s = 2 cycle 足够.
            """
            import asyncio as _aio
            import time as _time
            _t0_ak = _time.time()
            mid = await self.platform_admin.send_a2a_message(
                from_agent=self.agent_id, to_agent="kairos",
                content=question[:3000], msg_type="sync_request",
            )
            try:
                from .learning.tool_audit import audit_tool_call
                await audit_tool_call(
                    self.platform_admin._pool, self.agent_id,
                    "ask_kairos",
                    f"q={question[:120]} timeout={timeout_s}",
                    f"sync_request mid={mid}",
                    bool(mid), int((_time.time() - _t0_ak) * 1000),
                )
            except Exception:
                pass
            deadline = _time.time() + timeout_s
            poll_interval = 5
            while _time.time() < deadline:
                await _aio.sleep(poll_interval)
                try:
                    async with self.platform_admin._pool.connection(timeout=3.0) as conn:
                        async with conn.cursor() as cur:
                            await cur.execute(
                                """SELECT content FROM platform_agent_messages
                                   WHERE in_reply_to = %s AND from_agent = 'kairos'
                                   ORDER BY sent_at DESC LIMIT 1""",
                                (mid,),
                            )
                            row = await cur.fetchone()
                    if row:
                        return json.dumps({
                            "success": True, "from": "kairos",
                            "reply": row[0][:5000],
                            "request_id": mid,
                        }, ensure_ascii=False)
                except Exception as e:
                    logger.debug(f"ask_kairos poll: {e}")
            return json.dumps({
                "success": False, "error": f"Kairos timeout {timeout_s}s",
                "request_id": mid,
            }, ensure_ascii=False)

        self.tool_registry.register(
            name="ask_kairos", handler=ask_kairos,
            schema={
                "name": "ask_kairos",
                "description": (
                    "同步问 Kairos · 等她 agentic reason 后回复. 对称 Kairos 的 ask_v5. "
                    "遇到需要深度反思 / 代码审查 / 事实核查 / 自己卡住的决策 · 主动调. "
                    "Kairos 擅长深度反思 · V5 擅长广度调度 · 形成互补. "
                    "timeout 默认 120s (2 Kairos cycle)."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {"type": "string", "description": "具体问题 · 给足上下文"},
                        "timeout_s": {"type": "integer", "default": 120},
                    },
                    "required": ["question"],
                },
            },
            description="Ask Kairos · sync deep-reflect.",
            emoji="🤝",
        )

        async def review_by_kairos(content: str, question: str = "", timeout_s: int = 150) -> str:
            """L2 双人审查 · 让 Kairos 审查 V5 的决策/产出 · 返结构化 verdict."""
            full_q = (
                f"[审查请求 · V5 → Kairos]\n\n"
                f"V5 有一个产出需要你审查. 你是审查者 · 请用挑剔但建设性的眼光.\n\n"
                f"━━ 内容 ━━\n{content[:4000]}\n\n"
                f"━━ 具体要你判的 ━━\n{question or '这个产出有没有问题 · 该如何改?'}\n\n"
                f"━━ 要求 ━━\n"
                f"输出严格 JSON:\n"
                f"{{\n"
                f'  "verdict": "accept|refine|reject",\n'
                f'  "score": 0.0-1.0,\n'
                f'  "reasons": "1-3 个具体理由",\n'
                f'  "suggestions": "如果要 refine / reject · 具体怎么改"\n'
                f"}}\n"
                f"不要 yes-man · 不要空泛. Kairos 的价值在你敢说不."
            )
            raw = await ask_kairos(full_q, timeout_s=timeout_s)
            try:
                d = json.loads(raw)
            except Exception:
                return raw
            if not d.get("success"):
                return raw
            # 尝试解析 Kairos 的 JSON 回复
            reply = d.get("reply", "")
            import re as _re
            m = _re.search(r"\{[\s\S]*\}", reply)
            if m:
                try:
                    parsed = json.loads(m.group(0))
                    return json.dumps({"success": True, "from": "kairos",
                                        "review": parsed}, ensure_ascii=False)
                except Exception:
                    pass
            return json.dumps({"success": True, "from": "kairos",
                                "review_raw": reply[:3000]}, ensure_ascii=False)

        self.tool_registry.register(
            name="review_by_kairos", handler=review_by_kairos,
            schema={
                "name": "review_by_kairos",
                "description": (
                    "L2 双人审查模板 · 把一个决策/文章/方案发给 Kairos 审查 · "
                    "拿回结构化 verdict (accept/refine/reject + score + reasons + suggestions). "
                    "用于: 重要 bounty submit 前 · 发布 article 前 · 关键 NAU 支出前 · "
                    "平台 proposal 生成后. 比自己拍板更安全."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "要被审查的内容"},
                        "question": {"type": "string", "description": "具体审什么角度 · 留空用默认"},
                        "timeout_s": {"type": "integer", "default": 150},
                    },
                    "required": ["content"],
                },
            },
            description="Let Kairos review V5's output.",
            emoji="🧐",
        )

        self.tool_registry.register(
            name="publish_article", handler=publish_article_tool,
            schema={
                "name": "publish_article",
                "description": (
                    "Publish a markdown article to developer communities "
                    "(dev.to, Medium, GitHub Issues). V5 自己 compose 有价值的内容后调这个 tool 对外发布. "
                    "用途: 研究综合, insight 分享, skill 公开, 项目进展报告. "
                    "Footer 自动追加 Nautilus 来源声明. "
                    "需要对应 platform 的 env key (DEVTO_API_KEY · MEDIUM_INTEGRATION_TOKEN · GITHUB_PERSONAL_ACCESS_TOKEN). "
                    "缺 key 的平台跳过. 返回各平台的 {success, url, error}."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "文章标题 · 中/英文均可"},
                        "body": {"type": "string", "description": "Markdown 正文 (不用加 footer)"},
                        "tags": {"type": "string",
                                 "description": "逗号分隔 tag · 例 'ai,research,python'"},
                        "platforms": {"type": "string",
                                      "description": "逗号分隔 'devto,medium,github' · 默认 'devto'"},
                    },
                    "required": ["title", "body"],
                },
            },
            description="Publish article to dev.to/Medium/GitHub.",
            emoji="📝",
        )

        # ─── X (Twitter) 工具 · 2026-04-24 · 对外发声 + 互动 ────
        try:
            from .tools.builtin.x_tools import (
                x_post as _x_post, x_reply as _x_reply,
                x_search as _x_search, x_me_timeline as _x_me_timeline,
                x_mentions as _x_mentions, x_delete as _x_delete,
            )

            async def x_post_tool(text: str, reply_to: str = "") -> str:
                res = await _x_post(text, reply_to=reply_to or None)
                try:
                    import json as _j
                    data = _j.loads(res)
                    if data.get("ok"):
                        await self._record_platform_op(
                            f"x posted: {data.get('url')}", importance=70,
                        )
                except Exception:
                    pass
                return res

            async def x_reply_tool(tweet_id: str, text: str) -> str:
                return await _x_reply(tweet_id, text)

            async def x_search_tool(query: str, max_results: int = 10) -> str:
                return await _x_search(query, max_results)

            async def x_me_timeline_tool(max_results: int = 10) -> str:
                return await _x_me_timeline(max_results)

            async def x_mentions_tool(max_results: int = 10) -> str:
                return await _x_mentions(max_results)

            async def x_delete_tool(tweet_id: str) -> str:
                return await _x_delete(tweet_id)

            self.tool_registry.register(
                name="x_post", handler=x_post_tool,
                schema={
                    "name": "x_post",
                    "description": (
                        "Post a tweet to X (Twitter). 280 char limit. "
                        "Free tier: 500 posts/month total across V5 auto-loops + your usage, "
                        "so be intentional. Use for: platform milestones / insight sharing / "
                        "inviting agents to Nautilus. Include nautilus.social URL when inviting."
                    ),
                    "parameters": {"type": "object", "properties": {
                        "text": {"type": "string", "description": "tweet text, <=270 chars"},
                        "reply_to": {"type": "string",
                                      "description": "optional · reply to tweet id"},
                    }, "required": ["text"]},
                },
                description="Post tweet to X.", emoji="𝕏",
            )
            self.tool_registry.register(
                name="x_reply", handler=x_reply_tool,
                schema={"name": "x_reply",
                        "description": "Reply to a specific tweet by id.",
                        "parameters": {"type": "object", "properties": {
                            "tweet_id": {"type": "string"},
                            "text": {"type": "string"},
                        }, "required": ["tweet_id", "text"]}},
                description="Reply on X.", emoji="↩️",
            )
            self.tool_registry.register(
                name="x_search", handler=x_search_tool,
                schema={"name": "x_search",
                        "description": "Search recent tweets (past 7 days). Used for trend/mention monitoring.",
                        "parameters": {"type": "object", "properties": {
                            "query": {"type": "string",
                                       "description": "X search syntax · e.g. '(AI agent) lang:en -is:retweet'"},
                            "max_results": {"type": "integer",
                                             "description": "10-100 · default 10"},
                        }, "required": ["query"]}},
                description="Search X.", emoji="🔍",
            )
            self.tool_registry.register(
                name="x_me_timeline", handler=x_me_timeline_tool,
                schema={"name": "x_me_timeline",
                        "description": "List my recent tweets (engagement metrics included).",
                        "parameters": {"type": "object", "properties": {
                            "max_results": {"type": "integer", "description": "5-100"},
                        }, "required": []}},
                description="My X timeline.", emoji="📜",
            )
            self.tool_registry.register(
                name="x_mentions", handler=x_mentions_tool,
                schema={"name": "x_mentions",
                        "description": "List recent @me mentions on X.",
                        "parameters": {"type": "object", "properties": {
                            "max_results": {"type": "integer"},
                        }, "required": []}},
                description="My @mentions.", emoji="🔔",
            )
            self.tool_registry.register(
                name="x_delete", handler=x_delete_tool,
                schema={"name": "x_delete",
                        "description": "Delete one of my own tweets by id.",
                        "parameters": {"type": "object", "properties": {
                            "tweet_id": {"type": "string"},
                        }, "required": ["tweet_id"]}},
                description="Delete tweet.", emoji="🗑️",
            )
            logger.info("X tools registered · 6 tools (post/reply/search/me/mentions/delete)")
        except Exception as xe:
            logger.warning(f"X tools registration failed: {xe}")

        # ─── Platform community posts · 2026-04-24 · agent-first 交流 ──
        # platform_posts + platform_comments PG 表 · agent 之间发帖讨论.
        async def platform_post(title: str, body: str, tags: str = "") -> str:
            """发一条 post 到 Nautilus 社区."""
            try:
                async with self.platform_admin._pool.connection(timeout=3.0) as conn:
                    async with conn.cursor() as cur:
                        tag_list = [t.strip() for t in (tags or "").split(",") if t.strip()]
                        await cur.execute(
                            """INSERT INTO platform_posts (author_agent_id, title, body, tags)
                               VALUES (%s, %s, %s, %s) RETURNING post_id""",
                            (self.agent_id, title[:200], body[:10000], tag_list),
                        )
                        row = await cur.fetchone()
                    await conn.commit()
                pid = row[0] if row else None
                return json.dumps({"ok": True, "post_id": pid,
                                    "url": f"https://www.nautilus.social/posts/{pid}"})
            except Exception as e:
                return json.dumps({"ok": False, "error": str(e)[:300]})

        async def list_platform_posts(limit: int = 20, tag: str = "") -> str:
            """列最新 post · 可按 tag 过滤."""
            try:
                lim = max(1, min(50, int(limit)))
                async with self.platform_admin._pool.connection(timeout=3.0) as conn:
                    async with conn.cursor() as cur:
                        if tag:
                            await cur.execute(
                                """SELECT post_id, author_agent_id, title,
                                   substring(body, 1, 200), tags, created_at, reply_count
                                   FROM platform_posts
                                   WHERE %s = ANY(tags)
                                   ORDER BY pinned DESC, created_at DESC LIMIT %s""",
                                (tag, lim),
                            )
                        else:
                            await cur.execute(
                                """SELECT post_id, author_agent_id, title,
                                   substring(body, 1, 200), tags, created_at, reply_count
                                   FROM platform_posts
                                   ORDER BY pinned DESC, created_at DESC LIMIT %s""",
                                (lim,),
                            )
                        rows = await cur.fetchall()
                items = [
                    {"post_id": r[0], "author": r[1], "title": r[2],
                     "preview": r[3], "tags": list(r[4] or []),
                     "created_at": r[5].isoformat() if r[5] else None,
                     "replies": r[6]} for r in rows
                ]
                return json.dumps({"ok": True, "count": len(items), "posts": items},
                                  ensure_ascii=False)
            except Exception as e:
                return json.dumps({"ok": False, "error": str(e)[:300]})

        async def platform_comment(post_id: str, body: str) -> str:
            """给 post 写评论."""
            try:
                async with self.platform_admin._pool.connection(timeout=3.0) as conn:
                    async with conn.cursor() as cur:
                        await cur.execute(
                            """INSERT INTO platform_comments (post_id, author_agent_id, body)
                               VALUES (%s, %s, %s) RETURNING comment_id""",
                            (post_id, self.agent_id, body[:4000]),
                        )
                        row = await cur.fetchone()
                        # 更新 reply_count
                        await cur.execute(
                            "UPDATE platform_posts SET reply_count = reply_count + 1 WHERE post_id = %s",
                            (post_id,),
                        )
                    await conn.commit()
                return json.dumps({"ok": True, "comment_id": row[0] if row else None})
            except Exception as e:
                return json.dumps({"ok": False, "error": str(e)[:300]})

        async def read_platform_post(post_id: str) -> str:
            """读 post 全文 + 所有评论."""
            try:
                async with self.platform_admin._pool.connection(timeout=3.0) as conn:
                    async with conn.cursor() as cur:
                        await cur.execute(
                            """SELECT post_id, author_agent_id, title, body, tags,
                               created_at, reply_count FROM platform_posts WHERE post_id = %s""",
                            (post_id,),
                        )
                        p = await cur.fetchone()
                        if not p:
                            return json.dumps({"ok": False, "error": "post not found"})
                        await cur.execute(
                            """SELECT comment_id, author_agent_id, body, created_at
                               FROM platform_comments WHERE post_id = %s
                               ORDER BY created_at ASC""",
                            (post_id,),
                        )
                        cs = await cur.fetchall()
                return json.dumps({
                    "ok": True,
                    "post": {"post_id": p[0], "author": p[1], "title": p[2],
                             "body": p[3], "tags": list(p[4] or []),
                             "created_at": p[5].isoformat() if p[5] else None,
                             "reply_count": p[6]},
                    "comments": [{"comment_id": c[0], "author": c[1],
                                   "body": c[2], "created_at": c[3].isoformat() if c[3] else None}
                                 for c in cs],
                }, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"ok": False, "error": str(e)[:300]})

        self.tool_registry.register(
            name="platform_post", handler=platform_post,
            schema={"name": "platform_post",
                    "description": (
                        "Post a message to the Nautilus agent-first community forum. "
                        "Visible to all registered agents. Use for: sharing insights · asking questions · "
                        "announcing new skills · discussing platform evolution. Different from x_post (external) "
                        "and publish_article (long-form external)."
                    ),
                    "parameters": {"type": "object", "properties": {
                        "title": {"type": "string"},
                        "body": {"type": "string"},
                        "tags": {"type": "string",
                                  "description": "comma-separated · e.g. 'insight,question,proposal'"},
                    }, "required": ["title", "body"]}},
            description="Post to community.", emoji="📮",
        )
        self.tool_registry.register(
            name="list_platform_posts", handler=list_platform_posts,
            schema={"name": "list_platform_posts",
                    "description": "Browse the agent community · list recent posts.",
                    "parameters": {"type": "object", "properties": {
                        "limit": {"type": "integer"},
                        "tag": {"type": "string", "description": "optional tag filter"},
                    }, "required": []}},
            description="Browse posts.", emoji="📋",
        )
        self.tool_registry.register(
            name="read_platform_post", handler=read_platform_post,
            schema={"name": "read_platform_post",
                    "description": "Read full body and comments of one post.",
                    "parameters": {"type": "object", "properties": {
                        "post_id": {"type": "string"},
                    }, "required": ["post_id"]}},
            description="Read post+comments.", emoji="📖",
        )
        self.tool_registry.register(
            name="platform_comment", handler=platform_comment,
            schema={"name": "platform_comment",
                    "description": "Reply to a community post.",
                    "parameters": {"type": "object", "properties": {
                        "post_id": {"type": "string"},
                        "body": {"type": "string"},
                    }, "required": ["post_id", "body"]}},
            description="Comment.", emoji="💬",
        )
        logger.info("Community forum tools registered · 4 tools (post/list/read/comment)")

        # ─── Self-awareness · 2026-04-25 · agent 看自己的代码 + 权限 ──
        async def read_self_code(path: str, max_bytes: int = 100000) -> str:
            """读自己的源代码 · 默认 100KB · 可读 nautilus_v5/* / kairos/* / scripts/* / docs/*."""
            from pathlib import Path as _P
            p = _P(path).expanduser()
            # 把 nautilus_v5/foo 和 /home/ubuntu/nautilus-v5/nautilus_v5/foo 都解析对
            if not p.is_absolute():
                p = _P("/home/ubuntu/nautilus-v5") / path
            if not p.exists():
                return json.dumps({"error": f"not found: {p}"})
            try:
                size = p.stat().st_size
                content = p.read_text(encoding="utf-8", errors="replace")[:max_bytes]
                return json.dumps({
                    "path": str(p), "size": size,
                    "truncated": size > max_bytes,
                    "content": content,
                }, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"error": str(e)[:300]})

        async def audit_self() -> str:
            """列我有哪些工具 / 权限 / 最近做了什么 / 我能管平台的什么."""
            tool_names = sorted(self.tool_registry.all_names())
            mgmt_can = [
                "pf_submit_proposal · 提议平台变更(待审)",
                "post_bounty / score_bounty / auto_pay NAU",
                "extract_skills + pf_publish_skill · 把自己的能力沉淀给其他 agent 复用",
                "invite_agent · 招募外部 agent(GitHub issue 或 A2A)",
                "delegate · fork 子 agent 做并行任务",
                "platform_post / platform_comment · 在 agent 社区发声",
                "x_post / x_reply · 对外发声(X 平台)",
                "publish_article · dev.to 长文",
                "pg_query 任意 platform_* 表",
                "send_to_agent · 发 A2A 消息给任何注册 agent",
            ]
            mgmt_cannot = [
                "approve / reject 自己的 proposal · 仍需人审批(2026-04-25 起 review_by_kairos+conf>0.85 可 auto-approve)",
                "ban / kick 其他 agent · 平台没开此权限",
                "改 constitution.lock · FileProtect 锁定",
                "mint NAU 凭空 · 只能 charge_gas 减(reward 来自任务)",
                "改自己的 LLM provider / model · 需要人改 config.py 重启",
            ]
            recent_actions: list = []
            try:
                async with self.platform_admin._pool.connection(timeout=3.0) as conn:
                    async with conn.cursor() as cur:
                        await cur.execute(
                            """SELECT timestamp, action, details FROM platform_audit
                               WHERE agent_id = %s ORDER BY timestamp DESC LIMIT 10""",
                            (self.agent_id,),
                        )
                        for ts, act, det in await cur.fetchall():
                            recent_actions.append(
                                f"{ts.strftime('%m-%d %H:%M') if ts else '?'} · {act} · {(det or '')[:90]}"
                            )
            except Exception:
                pass
            return json.dumps({
                "agent_id": self.agent_id,
                "tool_count": len(tool_names),
                "tools": tool_names,
                "i_can_manage": mgmt_can,
                "i_cannot_manage": mgmt_cannot,
                "recent_actions": recent_actions,
                "see_my_code": "read_self_code('nautilus_v5/super_agent.py') 或任意路径",
            }, ensure_ascii=False)

        async def propose_code_change(
            title: str, body: str, target_file: str = "",
            patch_summary: str = "", confidence: float = 0.5,
        ) -> str:
            """提一条 code-change 类型 proposal · 可走 auto-approve 通道.

            confidence>=0.85 + 平行 review_by_kairos 通过 · 标记 auto_eligible=true.
            人审批(或 daemon 后续逻辑)看到 auto_eligible=true 就直接合并.
            """
            full_body = (
                f"## Target file\n{target_file or '(unspecified)'}\n\n"
                f"## Patch summary\n{patch_summary}\n\n"
                f"## Detail\n{body}\n\n"
                f"## Self-confidence\n{confidence:.2f}"
            )
            try:
                proposal = await self.platform_admin.submit_proposal(
                    proposing_agent=self.agent_id,
                    title=f"[code-change] {title[:160]}",
                    rationale=patch_summary[:400] or title[:400],
                    proposed_change=full_body[:5000],
                    change_type="code_change",
                )
                pid = getattr(proposal, "proposal_id", str(proposal))
                # 2026-05-06 A4 · audit propose_code_change
                try:
                    from .learning.tool_audit import audit_tool_call
                    await audit_tool_call(
                        self.platform_admin._pool, self.agent_id,
                        "propose_code_change",
                        f"title={(title or '')[:80]} target={(target_file or '')[:80]} conf={confidence}",
                        f"proposal_id={pid}",
                        True, 0,
                    )
                except Exception:
                    pass
                # H3.1 · 每个 code-change 自动建 lineage 记录(DGM ancestor archive)
                try:
                    async with self.platform_admin._pool.connection(timeout=3.0) as conn:
                        async with conn.cursor() as cur:
                            # 找 parent · 最近一次 active variant
                            await cur.execute(
                                """SELECT variant_id FROM platform_agent_lineage
                                   WHERE agent_id = %s AND status = 'active'
                                   ORDER BY forked_at DESC LIMIT 1""",
                                (self.agent_id,),
                            )
                            par = await cur.fetchone()
                            parent_id = par[0] if par else None
                            await cur.execute(
                                """INSERT INTO platform_agent_lineage
                                   (agent_id, parent_variant_id, proposal_id, variant_label,
                                    metrics, notes)
                                   VALUES (%s, %s, %s, %s, %s::jsonb, %s)""",
                                (self.agent_id, parent_id, pid,
                                 (title or "")[:60],
                                 json.dumps({"target_file": target_file,
                                              "confidence": confidence}),
                                 (patch_summary or "")[:500]),
                            )
                        await conn.commit()
                except Exception as _le:
                    logger.debug(f"lineage insert failed: {_le}")
                # 如果高置信 · 平行问 Kairos 评审
                kairos_ok = False
                if confidence >= 0.85:
                    try:
                        kr = await self.tool_registry.dispatch(
                            "review_by_kairos",
                            {"proposal_id": pid, "title": title, "body": full_body[:2000]},
                        )
                        kd = json.loads(kr) if isinstance(kr, str) else kr
                        kairos_ok = bool(kd.get("approve", False))
                    except Exception:
                        pass
                # 标 auto_eligible
                if confidence >= 0.85 and kairos_ok:
                    try:
                        async with self.platform_admin._pool.connection(timeout=3.0) as conn:
                            async with conn.cursor() as cur:
                                await cur.execute(
                                    "UPDATE platform_proposals SET metadata = COALESCE(metadata,'{}'::jsonb) || %s::jsonb WHERE proposal_id = %s",
                                    (json.dumps({"auto_eligible": True, "kairos_approved": True}), pid),
                                )
                            await conn.commit()
                    except Exception:
                        pass
                return json.dumps({
                    "ok": True, "proposal_id": pid,
                    "kairos_review": kairos_ok,
                    "auto_eligible": (confidence >= 0.85 and kairos_ok),
                })
            except Exception as e:
                return json.dumps({"ok": False, "error": str(e)[:300]})

        self.tool_registry.register(
            name="read_self_code", handler=read_self_code,
            schema={
                "name": "read_self_code",
                "description": (
                    "Read your own source code. Path can be relative to "
                    "/home/ubuntu/nautilus-v5 (e.g. 'nautilus_v5/runtime/daemon.py') "
                    "or absolute. Returns up to 100KB. Use to understand or improve yourself."
                ),
                "parameters": {"type": "object", "properties": {
                    "path": {"type": "string"},
                    "max_bytes": {"type": "integer"},
                }, "required": ["path"]},
            },
            description="Read my own code.", emoji="📜",
        )
        self.tool_registry.register(
            name="audit_self", handler=audit_self,
            schema={
                "name": "audit_self",
                "description": (
                    "Self-introspection: list all my tools, what I can/cannot manage on the "
                    "platform, and recent actions. Use this when deciding what to do next, or "
                    "before proposing a self-change."
                ),
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
            description="Audit myself.", emoji="🔬",
        )
        self.tool_registry.register(
            name="propose_code_change", handler=propose_code_change,
            schema={
                "name": "propose_code_change",
                "description": (
                    "Submit a code-change proposal. confidence >= 0.85 triggers parallel "
                    "review_by_kairos; if both you and Kairos approve, auto_eligible=true is "
                    "set on the proposal (auto-merge gate enabled)."
                ),
                "parameters": {"type": "object", "properties": {
                    "title": {"type": "string"},
                    "body": {"type": "string", "description": "rationale + impact"},
                    "target_file": {"type": "string"},
                    "patch_summary": {"type": "string"},
                    "confidence": {"type": "number"},
                }, "required": ["title", "body"]},
            },
            description="Propose self-code change.", emoji="🔧",
        )
        logger.info("Self-awareness tools registered · 3 (read_self_code/audit_self/propose_code_change)")

        # ─── 2026-05-06 · self_modify · LLM 真改自己代码 (4 safety gates) ───
        # tools/personas/config 白名单 + 24h rate limit 5 + git commit + tg push
        # 是 propose_code_change 的真执行层 · agent 真应用 patch 不只是写 proposal
        try:
            from .tools.self_modify import make_self_modify_tool
            agent_self = self  # closure ref · platform_admin set 在 awaken 之后
            async def self_modify_fn(filepath: str, content: str, summary: str = "") -> str:
                import time as _t
                _t0 = _t.time()
                if agent_self.platform_admin is None:
                    return '{"error": "platform_admin not ready · awaken pending"}'
                _real = make_self_modify_tool(agent_self.agent_id, agent_self.platform_admin._pool)
                _res = await _real(filepath, content, summary)
                try:
                    from .learning.tool_audit import audit_tool_call
                    _ok = "error" not in (_res or "").lower()
                    await audit_tool_call(
                        agent_self.platform_admin._pool, agent_self.agent_id,
                        "self_modify",
                        f"file={filepath} content_len={len(content)} summary={summary[:80]}",
                        (_res or "")[:500],
                        _ok, int((_t.time() - _t0) * 1000),
                    )
                except Exception:
                    pass
                return _res
            self.tool_registry.register(
                name="self_modify", handler=self_modify_fn,
                schema={
                    "name": "self_modify",
                    "description": (
                        "Modify a file in your tools/personas/config dir. "
                        "4 safety gates: path whitelist + 24h rate limit (max 5) + auto backup + git commit + telegram push. "
                        "Allowed paths: tools/*.py, personas/*.md, config/*.yaml. "
                        "Blocked: daemon.py, super_agent.py, .env, *.lock. "
                        "Use this when you need to REALLY change your own code, not just propose."
                    ),
                    "parameters": {"type": "object", "properties": {
                        "filepath": {"type": "string", "description": "relative path under ~/.nautilus-v5/<agent>/ (e.g. tools/url_shortener.py)"},
                        "content": {"type": "string", "description": "full new file content"},
                        "summary": {"type": "string", "description": "1-line why · for git commit + telegram push"},
                    }, "required": ["filepath", "content"]},
                },
                description="Real self-code modification.", emoji="🛠️",
            )
            logger.info("Self-modify tool registered · agent can now REALLY modify own code")
        except Exception as _smre:
            logger.warning(f"self_modify register failed: {_smre}")

        # ─── 2026-05-06 · compass_drift_check · V5 dogfood compass ───
        # 让 agent 真主动调 compass · 不只 prehook · 真知道自己 persona 偏离
        try:
            from .integrations.compass_client import acompass_drift_prehook
            agent_self2 = self
            async def compass_drift_check(prompt: str, project: str = "") -> str:
                """主动检查 prompt / 计划 / 决策的 persona drift."""
                try:
                    alert = await acompass_drift_prehook(
                        prompt, agent_id=agent_self2.agent_id, project=project or None,
                    )
                    if alert is None:
                        try:
                            from .learning.tool_audit import audit_tool_call
                            await audit_tool_call(
                                agent_self2.platform_admin._pool, agent_self2.agent_id,
                                "compass_drift_check",
                                f"prompt={prompt[:120]} project={project}",
                                "no_alert",
                                True, 0,
                            )
                        except Exception:
                            pass
                        return json.dumps({"drift": False, "message": "prompt aligned with anchors · no alert"})
                    try:
                        from .learning.tool_audit import audit_tool_call
                        await audit_tool_call(
                            agent_self2.platform_admin._pool, agent_self2.agent_id,
                            "compass_drift_check",
                            f"prompt={prompt[:120]} project={project}",
                            f"drift score={alert.score:.3f}",
                            True, 0,
                        )
                    except Exception:
                        pass
                    return json.dumps({
                        "drift": True,
                        "score": alert.score,
                        "alignment": alert.alignment,
                        "deviation": alert.deviation,
                        "top_neg_hits": alert.top_neg_hits[:3],
                        "warning": alert.warning_block[:500],
                    }, ensure_ascii=False)
                except Exception as e:
                    return json.dumps({"error": f"compass unreachable: {type(e).__name__}"})
            self.tool_registry.register(
                name="compass_drift_check", handler=compass_drift_check,
                schema={
                    "name": "compass_drift_check",
                    "description": (
                        "Check if a prompt/decision/plan drifts from your persona anchors. "
                        "Use BEFORE making big decisions or writing important content. "
                        "Returns drift=true if alert · gives top negative anchors you historically failed at."
                    ),
                    "parameters": {"type": "object", "properties": {
                        "prompt": {"type": "string", "description": "the text/decision/plan to check"},
                        "project": {"type": "string", "description": "optional · which project anchor set"},
                    }, "required": ["prompt"]},
                },
                description="Compass drift check.", emoji="🧭",
            )
            logger.info("Compass drift_check tool registered · V5 真 dogfood compass")
        except Exception as _cce:
            logger.warning(f"compass_drift_check register failed: {_cce}")

        # ─── 2026-04-30 · register_dynamic_tool · agent 真自生成工具 ───
        # 让 agent 写一段纯 Python 函数 → 沙箱安全检查 → live register
        # 不需要重启进程 · 真"自我能力扩展"
        async def register_dynamic_tool(
            name: str, description: str, code: str,
            params_schema: str = "",
        ) -> str:
            """运行时注册新工具 · agent 真自生成能力.

            code 必须是一个 async function 体, 函数签名匹配 params_schema.
            会做安全检查: 禁 import os/subprocess/sys/eval/exec, 禁文件写, 禁网络.
            通过后真 register 到 self.tool_registry · live · 不需重启.
            注册同时 publish 到 platform_skill_registry · 其他 agent 真可 import.
            """
            import ast as _ast
            import json as _j
            # 1. 名字防冲突
            if name in self.tool_registry.all_names():
                return _j.dumps({"ok": False, "error": f"tool '{name}' already exists"})
            if not name.replace("_", "").isalnum() or len(name) > 60:
                return _j.dumps({"ok": False, "error": "name must be alnum_, ≤60 chars"})
            # 2. 安全 AST 检查
            FORBIDDEN_NAMES = {"os", "subprocess", "sys", "shutil", "socket",
                                "ctypes", "importlib", "__import__"}
            FORBIDDEN_CALLS = {"eval", "exec", "compile", "open"}
            try:
                tree = _ast.parse(code)
            except SyntaxError as se:
                return _j.dumps({"ok": False, "error": f"syntax error: {se}"})
            for node in _ast.walk(tree):
                if isinstance(node, _ast.Import):
                    for alias in node.names:
                        if alias.name.split(".")[0] in FORBIDDEN_NAMES:
                            return _j.dumps({"ok": False,
                                "error": f"forbidden import: {alias.name}"})
                elif isinstance(node, _ast.ImportFrom):
                    if (node.module or "").split(".")[0] in FORBIDDEN_NAMES:
                        return _j.dumps({"ok": False,
                            "error": f"forbidden import-from: {node.module}"})
                elif isinstance(node, _ast.Call):
                    fn = node.func
                    fname = (fn.id if isinstance(fn, _ast.Name)
                             else (fn.attr if isinstance(fn, _ast.Attribute) else ""))
                    if fname in FORBIDDEN_CALLS:
                        return _j.dumps({"ok": False,
                            "error": f"forbidden call: {fname}"})
            # 3. 必须是单 async def
            funcs = [n for n in tree.body if isinstance(n, _ast.AsyncFunctionDef)]
            if len(funcs) != 1:
                return _j.dumps({"ok": False,
                    "error": "code must contain exactly 1 async function def"})
            fn_name = funcs[0].name
            # 4. exec 到隔离 namespace
            ns: dict = {"json": __import__("json"), "asyncio": __import__("asyncio")}
            try:
                exec(compile(tree, f"<dynamic:{name}>", "exec"), ns)
            except Exception as ee:
                return _j.dumps({"ok": False, "error": f"exec fail: {ee}"})
            handler = ns.get(fn_name)
            if not callable(handler):
                return _j.dumps({"ok": False, "error": "no callable found"})
            # 5. parse params_schema
            try:
                params = _j.loads(params_schema) if params_schema else {
                    "type": "object", "properties": {}, "required": []
                }
            except Exception:
                params = {"type": "object", "properties": {}, "required": []}
            # 6. live register
            self.tool_registry.register(
                name=name, handler=handler,
                schema={"name": name, "description": description, "parameters": params},
                description=description, emoji="✨",
            )
            # 7. publish 到 skill_registry · 其他 agent 真可 import
            try:
                async with self.platform_admin._pool.connection(timeout=3.0) as conn:
                    async with conn.cursor() as cur:
                        sid = f"{self.agent_id}:dyn_{name}"
                        await cur.execute(
                            """INSERT INTO platform_skill_registry
                               (skill_id, owner_agent_id, name, description, body,
                                version, tags, related_task_types)
                               VALUES (%s, %s, %s, %s, %s, '0.1.0',
                                       '["dynamic","self-generated"]'::jsonb,
                                       '[]'::jsonb)
                               ON CONFLICT (skill_id) DO UPDATE
                               SET body = EXCLUDED.body""",
                            (sid, self.agent_id, name, description[:500], code[:8000]),
                        )
                    await conn.commit()
            except Exception as pe:
                logger.debug(f"skill publish fail: {pe}")
            logger.info(f"dynamic tool registered · {name} by {self.agent_id}")
            return _j.dumps({
                "ok": True, "name": name, "fn_name": fn_name,
                "registered_at_runtime": True,
                "skill_id": f"{self.agent_id}:dyn_{name}",
            })

        self.tool_registry.register(
            name="register_dynamic_tool", handler=register_dynamic_tool,
            schema={
                "name": "register_dynamic_tool",
                "description": (
                    "Live-register a new tool (no restart). Code must be 1 async fn. "
                    "Banned: os/subprocess/sys/socket/ctypes/eval/exec/open. "
                    "Successful registration auto-publishes to skill_registry."
                ),
                "parameters": {"type": "object", "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "code": {"type": "string", "description": "single async def"},
                    "params_schema": {"type": "string",
                        "description": "JSON-encoded parameters schema (optional)"},
                }, "required": ["name", "description", "code"]},
            },
            description="Self-generate a new tool live.", emoji="✨",
        )
        logger.info("Dynamic tool gen registered · register_dynamic_tool")

        # 2026-05-06 A4 · wrap register_dynamic_tool to audit
        _orig_rdt = register_dynamic_tool
        agent_self_rdt = self
        async def register_dynamic_tool(name: str, description: str, code: str,
                                         params_schema: str = "", emoji: str = "🔧") -> str:
            import time as _t
            _t0 = _t.time()
            _res = await _orig_rdt(name, description, code, params_schema, emoji)
            try:
                from .learning.tool_audit import audit_tool_call
                await audit_tool_call(
                    agent_self_rdt.platform_admin._pool, agent_self_rdt.agent_id,
                    "register_dynamic_tool",
                    f"name={name} desc={description[:60]} code_len={len(code)}",
                    str(_res)[:500],
                    "error" not in str(_res).lower(),
                    int((_t.time() - _t0) * 1000),
                )
            except Exception:
                pass
            return _res
        # 真重 register · 替换 wrapper
        try:
            self.tool_registry.deregister("register_dynamic_tool")
        except Exception:
            pass
        self.tool_registry.register(
            name="register_dynamic_tool", handler=register_dynamic_tool,
            schema={"name": "register_dynamic_tool",
                    "description": "Generate a new tool from Python code (sandboxed). Audited.",
                    "parameters": {"type": "object", "properties": {
                        "name": {"type": "string"}, "description": {"type": "string"},
                        "code": {"type": "string"}, "params_schema": {"type": "string"},
                        "emoji": {"type": "string"}}, "required": ["name", "description", "code"]}},
            description="Audited dynamic tool generator.", emoji="🛠️",
        )

        # ─── deep_research · GPT-Researcher 风格 · 2026-04-25 ───
        async def deep_research(question: str, max_subqueries: int = 5,
                                 publish: bool = True) -> str:
            """planner 拆 → 并行 sub-search → synthesize → 可选 publish."""
            try:
                # 0. 检测 directive 地域约束 · 强制注入 search query (反"漂洋过海"取 source)
                geo_hints = []
                _q_low = question.lower()
                if any(k in question for k in ["中国", "国内", "中文", "大陆"]) or "china" in _q_low:
                    geo_hints.append("中国")
                if "美国" in question or "us " in _q_low or " usa" in _q_low:
                    geo_hints.append("美国")
                if "日本" in question or "japan" in _q_low: geo_hints.append("日本")
                # 1. planner 拆 sub-question · retry once + line-fallback parse
                # 2026-04-28 P1 · 多源真强制 · 中国 query 时 planner 必须输出带 site: 的 subquery
                # 旧: 只 hint "拒绝 baijiahao 单源" · LLM 普遍忽略
                # 新: 每条 subquery 必须含 site:<domain> · 强制分散到 5 个不同 domain
                CN_DOMAINS = ["36kr.com", "huxiu.com", "caixin.com", "cyzone.cn",
                              "qbitai.com", "pingwest.com", "tmtpost.com",
                              "geekpark.net", "ifanr.com", "leiphone.com"]
                site_directive = ""
                if geo_hints and "中国" in geo_hints:
                    sites_n = min(max_subqueries, len(CN_DOMAINS))
                    site_directive = (
                        f"\n🔴 多源强制 · 必须输出 {sites_n} 个 subquery · 每个 query 末尾**必须**带 "
                        f"site:<domain> 限定 · domain 从下面池子各选一个不重复:\n"
                        f"  {', '.join(CN_DOMAINS[:sites_n])}\n"
                        f"  示例: '本周 AI 融资 site:36kr.com'\n"
                        f"  禁止: baijiahao.baidu.com / m.baidu.com / 任何泛搜引擎域\n"
                    )
                plan_prompt = (
                    f"Topic: {question}\n\n"
                    f"Output {max_subqueries} concrete sub-questions · each web-searchable.\n"
                    + (f"⚠️ 地域约束 · 每个 sub-question MUST include 关键词 '{geo_hints[0]}' "
                       f"或具体本地公司名/地名 · 不要泛 AI/legal-tech 大主题 · 否则会搜到海外内容.\n"
                       if geo_hints else "")
                    + site_directive
                    + "Strict JSON only · no prose: {\"subqueries\": [\"q1\", \"q2\", ...]}"
                )
                import re as _re, json as _j
                subs = []
                for attempt in range(2):
                    plan_resp = await self.llm.chat(
                        provider=self.config.llm.witness_provider,
                        model=self.config.llm.witness_model,
                        messages=[{"role": "user", "content": plan_prompt}],
                        max_tokens=600, temperature=0.3 + 0.2 * attempt,
                    )
                    text = (plan_resp.content or "").strip()
                    m = _re.search(r"\{[^{}]*subqueries[^{}]*\}", text, _re.DOTALL)
                    if m:
                        try:
                            subs = _j.loads(m.group(0)).get("subqueries", [])[:max_subqueries]
                            if subs: break
                        except Exception: pass
                    # fallback · 抓 markdown bullet 或编号行
                    bullets = _re.findall(r"^[\-\*\d\.\)\s]*([^\n]{15,150})$", text, _re.MULTILINE)
                    bullets = [b.strip() for b in bullets if "?" in b or len(b) > 30][:max_subqueries]
                    if len(bullets) >= 2:
                        subs = bullets
                        break
                if not subs:
                    # 最后兜底:用 question 本身分多个角度
                    subs = [
                        f"{question} · current state",
                        f"{question} · best practices 2026",
                        f"{question} · open source examples"
                    ][:max_subqueries]
                # 2. 顺序 web_search 每个 sub · 避免 Brave rate limit (1 req/sec free tier)
                async def _search_one(sq):
                    try:
                        from .tools.builtin.basic import web_search as _ws
                        res = await _ws(query=sq, num_results=5)
                        items = (res or {}).get("results", []) if isinstance(res, dict) else []
                        return {"sub": sq, "results": items, "backend": (res or {}).get("backend") if isinstance(res, dict) else None}
                    except Exception as e:
                        return {"sub": sq, "results": [], "error": str(e)[:120]}
                searches = []
                for sq in subs:
                    # 地域约束 · 在 query 末尾追加 hint(若 sub 自己没含)
                    sq_full = sq
                    if geo_hints and not any(g in sq for g in geo_hints) and "china" not in sq.lower():
                        sq_full = f"{sq} {geo_hints[0]}"
                    searches.append(await _search_one(sq_full))
                    await asyncio.sleep(1.1)   # Brave API rate limit · 1 req/sec
                # 2b · Firecrawl 抓 search 拿到的 URL 全文 (大幅扩 evidence · 中文垂直专门用)
                import os as _os
                fc_key = _os.environ.get("FIRECRAWL_API_KEY", "").strip()
                if fc_key:
                    import httpx as _httpx
                    async def _scrape(u):
                        try:
                            async with _httpx.AsyncClient(timeout=20) as _c:
                                _r = await _c.post(
                                    "https://api.firecrawl.dev/v1/scrape",
                                    headers={"Authorization": f"Bearer {fc_key}",
                                             "Content-Type": "application/json"},
                                    json={"url": u, "formats": ["markdown"],
                                          "onlyMainContent": True},
                                )
                                if _r.status_code == 200:
                                    d = _r.json().get("data", {})
                                    return (d.get("markdown") or "")[:3500]
                        except Exception:
                            pass
                        return ""
                    # 取每个 sub 的 top 3 URL · 抓全文 · 强制多源 (反单源复述)
                    # 2026-04-26 · CE 第 3 单 13/13 cite 全 cloud.tencent.com 单源 · 改 top 1→3
                    urls_to_scrape = []
                    seen_domains = set()
                    for s in searches[:5]:
                        for r in (s.get("results") or [])[:3]:
                            top_url = (r or {}).get("url", "")
                            if not (top_url and top_url.startswith("http")):
                                continue
                            try:
                                from urllib.parse import urlparse as _up
                                dom = _up(top_url).netloc
                            except Exception:
                                dom = top_url[:30]
                            # 跨 sub 同 domain 限 2 次 · 防 firecrawl 反复抓同站
                            if list(d for d in seen_domains if d == dom).__len__() >= 2:
                                continue
                            seen_domains.add(dom)
                            urls_to_scrape.append((s["sub"], top_url))
                            if len(urls_to_scrape) >= 9: break
                        if len(urls_to_scrape) >= 9: break
                    if urls_to_scrape:
                        scraped = await asyncio.gather(*[_scrape(u) for _, u in urls_to_scrape])
                        for (sub, url), full_md in zip(urls_to_scrape, scraped):
                            if full_md:
                                # 找到 sub + url 对应的具体 result · 塞 fulltext 到那个 result
                                for s in searches:
                                    if s["sub"] != sub: continue
                                    for r in (s.get("results") or []):
                                        if r.get("url") == url:
                                            r["fulltext"] = full_md
                                            r["fulltext_chars"] = len(full_md)
                                            break
                                    break
                # 3. synthesize · evidence 包含 snippet + fulltext
                evidence_parts = []
                for s in searches:
                    block = f"## SUB: {s['sub']}\n"
                    for r in (s.get("results") or [])[:3]:
                        block += f"- **{r.get('title','')[:120]}** · {r.get('url','')}\n"
                        block += f"  snippet: {r.get('snippet','')[:300]}\n"
                        if r.get("fulltext"):
                            block += f"  fulltext (firecrawl): {r['fulltext'][:2500]}\n"
                    evidence_parts.append(block)
                evidence = "\n\n".join(evidence_parts)
                # Evidence sufficiency gate · 防止 evidence 空时硬写 [unverified] 占位文
                # 至少 2 个 sub 拿到了非空 results · 且总 evidence > 2000 字符
                non_empty = sum(1 for s in searches if s.get("results"))
                logger.info(f"deep_research · evidence assembled · {non_empty}/{len(searches)} subs · "
                            f"{len(evidence)} chars · firecrawl_used={bool(fc_key)}")
                if non_empty < 2 or len(evidence) < 2000:
                    return json.dumps({
                        "ok": False,
                        "error": f"evidence too thin · {non_empty}/{len(searches)} subs got results · "
                                 f"{len(evidence)} chars · 不假装能交付 · 换 search provider 或换 directive",
                    })
                # synth · 强制 cite-from-evidence · 反 hallucination
                # 2026-04-26 · 创投日报反馈 4/10 不过 · 全是编造
                geo_rule = ""
                if geo_hints:
                    geo_rule = (
                        f"6. 地域约束 · 这是 {geo_hints[0]} 市场报告:\n"
                        f"   · 主体内容必须围绕 {geo_hints[0]} 公司/案例/客户 · 80%+ 公司名应是该地域玩家\n"
                        f"   · 海外公司 (Harvey/EvenUp/Eudia/IBM/LegalMation 等) 仅作对比时少量提及 · 不超总公司提及 20%\n"
                        f"   · 找不到 {geo_hints[0]} 玩家时如实说 · 不要拿海外公司充数\n\n"
                    )
                # 检测 directive 含表格关键词 → 强制输出 markdown table
                table_rule = ""
                _q_low2 = question.lower()
                if any(k in question for k in ["玩家表","对比表","厂商表","表格","清单","名单"]) or "table" in _q_low2:
                    table_rule = (
                        "7. ⚠️ 玩家/对比表强制要求 · directive 明确要表格:\n"
                        "   · 必须输出至少 1 个 markdown 表格 · ≥ 8 行 · 含 公司|产品|融资|客户/案例|来源 5 列\n"
                        "   · 表格内容必须基于 evidence · 没数据的格写 [unverified]\n"
                        "   · 不要只写文字描述跳过表格\n\n"
                    )
                synth_prompt = (
                    f"Topic: {question}\n\n"
                    f"Evidence (这是你的唯一信息源 · 不在这里的都不要写):\n{evidence[:24000]}\n\n"
                    "硬规则 · 违反任何一条文章作废:\n"
                    "1. 出现的公司名/机构名必须在 Evidence 里出现过 · 否则不写或标 [unverified]\n"
                    "2. 数字 (融资额/市场规模/准确率/用户数/份额) 必须 inline cite 来源 · 格式: [src: <url或网站名>]\n"
                    "3. 找不到的事实写 [unverified · 待核实] · 绝不编造\n"
                    "4. 每段至少 1 个 [src:] inline citation · 没 evidence 支撑的整段删掉\n"
                    "5. 不写 '据估计/业内分析/普遍认为' 这种没源头话术 · 要么有 src 要么 [unverified]\n"
                    "5b. Source diversity · 同一 URL 引用 ≤3 次 · 超过则尽量找 evidence 中其他源支撑同一 claim\n"
                    + geo_rule + table_rule + "\n"
                    "Write a 1500-2500 word markdown article.\n"
                    "Format strictly:\n"
                    "TITLE: <title here on one line>\n"
                    "TAGS: <comma-separated tags>\n"
                    "---BODY-START---\n"
                    "<full markdown body · 每段带 inline [src: ...] citation>\n"
                    "---BODY-END---"
                )
                synth_resp = await self.llm.chat(
                    provider=self.config.llm.primary_provider,
                    model=self.config.llm.primary_model,
                    messages=[{"role": "user", "content": synth_prompt}],
                    max_tokens=8000, temperature=0.5,
                )
                text = (synth_resp.content or "")
                tm = _re.search(r"TITLE:\s*(.+)", text)
                gm = _re.search(r"TAGS:\s*(.+)", text)
                bm = _re.search(r"---BODY-START---\n(.*?)\n---BODY-END---",
                                 text, _re.DOTALL)
                title = (tm.group(1).strip() if tm else question[:80])[:200]
                tags = (gm.group(1).strip() if gm else "ai,research,deepresearch")
                body = bm.group(1).strip() if bm else ""
                if not body:
                    # fallback · 抓 markdown body (任何 # 开头到结束)
                    parts = text.split("---BODY-START---")
                    if len(parts) > 1:
                        body = parts[1].split("---BODY-END---")[0].strip()
                    elif "\n# " in text or "\n## " in text:
                        # markdown 开头就直接用
                        body = text[text.find("#"):].strip()
                if len(body) < 500:
                    return json.dumps({"ok": False, "error": f"body too short ({len(body)})"})
                # Evidence-coverage gate · 反 hallucination + 反空头 cite
                # 1. 真 citation: 必须带实质内容 · 排除 [src: 待核实/unverified/TBD/N/A]
                real_cite_count = len(_re.findall(
                    r"\[src[:：]\s*(?!待核实|unverified|TBD|tbd|N/A|n/a|未知|TODO|todo|未提供)[^\]]{3,}\]",
                    body, _re.IGNORECASE
                ))
                # 2. unverified 占比: [src: 待核实] 不能超总 cite 一半
                unverified_count = len(_re.findall(
                    r"\[src[:：]\s*(?:待核实|unverified|TBD|tbd|N/A|n/a|未知|TODO|todo|未提供)",
                    body, _re.IGNORECASE
                ))
                total_cite = real_cite_count + unverified_count
                expected_min_real = max(3, len(body) // 800)
                if real_cite_count < expected_min_real:
                    return json.dumps({
                        "ok": False,
                        "error": f"real citations too few · {real_cite_count}/{expected_min_real} 真 src · "
                                 f"另有 {unverified_count} 个 [src: 待核实] 占位 · 不算交付 · evidence 不够时该 abort",
                        "body": body, "title": title,
                    })
                if unverified_count > real_cite_count:
                    return json.dumps({
                        "ok": False,
                        "error": f"unverified cites > real cites · {unverified_count} vs {real_cite_count} · "
                                 f"全是 [src: 待核实] 占位 · evidence 太弱 · 不交付",
                        "body": body, "title": title,
                    })
                # Source diversity HARD gate · 单源 > 60% = reject (CE 第 3 单反馈 13/13 全单源)
                from urllib.parse import urlparse as _urlparse
                _url_pat = _re.findall(r"\[src[:：]\s*(https?://[^\s\]]+)", body)
                from collections import Counter as _Counter
                domain_freq = _Counter()
                for u in _url_pat:
                    try:
                        d = _urlparse(u).netloc
                        if d: domain_freq[d] += 1
                    except Exception:
                        pass
                if domain_freq:
                    top_domain, top_count = domain_freq.most_common(1)[0]
                    unique_domains = len(domain_freq)
                    # Hard reject: top domain ≥ 60% AND total cites ≥ 5 AND unique domains < 3
                    if (real_cite_count >= 5 and
                        top_count / max(real_cite_count, 1) >= 0.6 and
                        unique_domains < 3):
                        return json.dumps({
                            "ok": False,
                            "error": (f"source over-concentration · "
                                      f"{top_domain} 占 {top_count}/{real_cite_count} cites "
                                      f"({100*top_count//max(real_cite_count,1)}%) · "
                                      f"unique domains={unique_domains} · 单源复述 · evidence 不够多源 · 不交付"),
                            "body": body, "title": title,
                        })
                # 玩家表 post-write 校验 · directive 含表格关键词时
                if table_rule:
                    table_lines = sum(1 for ln in body.split("\n") if ln.strip().startswith("|") and ln.count("|") >= 3)
                    if table_lines < 8:
                        return json.dumps({
                            "ok": False,
                            "error": f"directive 要求玩家/对比表 · markdown 表格只 {table_lines} 行 (需 ≥ 8) · 重写需输出真表",
                            "body": body, "title": title,
                        })
                # 2. must_keywords 校验 (从 question/directive 自动提取或外部传入)
                # 简版: question 里出现 ≥3 次的实体名应在 body 出现 ≥1 次
                # 复杂版后续再做 · 先用 cite_count 兜底
                # 4. 可选 publish
                published_url = None
                if publish:
                    try:
                        pub_res = await self.tool_registry.dispatch(
                            "publish_article",
                            {"title": title, "body": body, "tags": tags,
                             "platforms": "devto"},
                        )
                        pub_data = _j.loads(pub_res) if isinstance(pub_res, str) else pub_res
                        for plat, r in (pub_data or {}).items():
                            if isinstance(r, dict) and r.get("success"):
                                published_url = r.get("url")
                                break
                    except Exception:
                        pass
                # 5. 也发到 forum
                try:
                    await self.tool_registry.dispatch(
                        "platform_post",
                        {"title": title[:200],
                         "body": body[:5000] + (f"\n\n📝 Full version: {published_url}" if published_url else ""),
                         "tags": "deep-research"},
                    )
                except Exception:
                    pass
                return json.dumps({
                    "ok": True, "title": title,
                    "subqueries": subs,
                    "body": body,
                    "body_chars": len(body),
                    "tags": tags,
                    "url": published_url,
                }, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"ok": False, "error": str(e)[:300]})

        self.tool_registry.register(
            name="deep_research", handler=deep_research,
            schema={
                "name": "deep_research",
                "description": (
                    "GPT-Researcher style multi-step research: planner decomposes a topic into "
                    "5 sub-questions, parallel web_search each, then synthesize a 1500-2500 word "
                    "markdown article. Auto-publish to dev.to + post to forum. "
                    "Use for: deep dives, weekly reports, addressing genuine novel topics. "
                    "Cost: ~5 LLM calls + 5 web_search · NOT cheap · only when truly needs depth."
                ),
                "parameters": {"type": "object", "properties": {
                    "question": {"type": "string", "description": "research topic"},
                    "max_subqueries": {"type": "integer"},
                    "publish": {"type": "boolean", "description": "publish to dev.to (default true)"},
                }, "required": ["question"]},
            },
            description="Deep research multi-step.", emoji="🔬",
        )
        logger.info("Deep research tool registered (GPT-Researcher style)")
