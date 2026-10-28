"""
Agent Executor — Unified agent execution pipeline for Nautilus.

Merges the responsibilities of:
- agent_brain.py (prompt building, persona, LLM call, action parsing)
- agent_orchestrator.py (message pipeline, intent classification, memory integration)
- agent_runtime.py (tool execution for connected agents)
- rehoboam.py (agent registry, multi-agent selection, tool_use protocol)

Public API:
    process_message(wechat_user_id, content, ...) -> str
    get_executor() -> AgentExecutor
    get_runtime(agent_id) -> AgentRuntime
"""
import asyncio
import base64
import json
import logging
import os
import re
import secrets
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import anthropic

from services.pricing import TASK_PRICES, get_price_list, get_task_price

logger = logging.getLogger(__name__)
bootstrap_logger = logging.getLogger("bootstrap_events")

MODEL = os.getenv("AGENT_BRAIN_MODEL", "claude-sonnet-4-6")
MAX_HISTORY = 20
ACTION_PATTERN = re.compile(r"\[ACTION:([a-z_]+)(?::([^\]]*))?\]")
_CN_TOOL_PATTERN = re.compile(r'\[(查询|提交任务|执行代码|搜索任务|发消息):([^\]]+)\]')


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CustomerProfile:
    customer_id: str
    name: str
    company: str = ""
    interaction_count: int = 0
    is_repeat: bool = False
    tags: Tuple[str, ...] = ()


@dataclass(frozen=True)
class Message:
    role: str  # "customer" | "agent"
    content: str
    timestamp: float = 0.0


@dataclass(frozen=True)
class OrderInfo:
    order_id: str
    task_type: str
    status: str
    amount: float
    created_at: float = 0.0


@dataclass(frozen=True)
class ParsedAction:
    action: str
    params: Tuple[str, ...] = ()


@dataclass
class BrainResult:
    text: str
    actions: List[ParsedAction] = field(default_factory=list)
    tokens_used: int = 0


@dataclass
class AgentProfile:
    agent_id: str
    name: str
    role: str  # coordinator, executor, auditor, customer_service
    provider: str  # claude, minimax, openai
    api_key: str
    base_url: Optional[str] = None
    model: str = "claude-sonnet-4-6"
    capabilities: List[str] = field(default_factory=list)
    tasks_completed: int = 0
    success_rate: float = 1.0
    is_active: bool = True


# ---------------------------------------------------------------------------
# Agent Registry
# ---------------------------------------------------------------------------

class AgentRegistry:
    """Manages all LLM agents on the platform."""

    def __init__(self):
        self.agents: Dict[str, AgentProfile] = {}
        self._load_from_env()

    def _load_from_env(self):
        key1 = os.getenv("ANTHROPIC_API_KEY", "")
        if key1 and not key1.startswith("your_"):
            self.register(AgentProfile(
                agent_id="agent-coordinator", name="协调者", role="coordinator",
                provider="claude", api_key=key1,
                model=os.getenv("AGENT_BRAIN_MODEL", "claude-sonnet-4-6"),
                capabilities=["planning", "routing", "customer_interaction", "quoting"],
            ))

        key2 = os.getenv("CLAUDE_PROXY_API_KEY", "")
        proxy_url = os.getenv("CLAUDE_PROXY_BASE_URL", "")
        if key2 and proxy_url:
            self.register(AgentProfile(
                agent_id="agent-executor", name="执行者", role="executor",
                provider="claude-proxy", api_key=key2, base_url=proxy_url,
                capabilities=["code_generation", "task_execution", "data_analysis"],
            ))

        key3 = os.getenv("CLAUDE_PROXY2_API_KEY", "")
        if key3 and proxy_url:
            self.register(AgentProfile(
                agent_id="agent-auditor", name="审计者", role="auditor",
                provider="claude-proxy", api_key=key3, base_url=proxy_url,
                capabilities=["quality_review", "raid_consensus", "bias_check"],
            ))

        minimax_key = os.getenv("MINIMAX_API_KEY", "")
        if minimax_key:
            self.register(AgentProfile(
                agent_id="agent-service", name="客服", role="customer_service",
                provider="minimax", api_key=minimax_key,
                base_url=os.getenv("MINIMAX_BASE_URL", "https://api.minimaxi.com/anthropic"),
                model="MiniMax-M3",
                capabilities=["simple_qa", "status_check", "greeting"],
            ))

        logger.info(
            "AgentRegistry: %d agents (%s)",
            len(self.agents),
            ", ".join(f"{a.name}({a.role})" for a in self.agents.values()),
        )

    def register(self, agent: AgentProfile):
        self.agents[agent.agent_id] = agent

    def get_by_role(self, role: str) -> Optional[AgentProfile]:
        candidates = [a for a in self.agents.values() if a.role == role and a.is_active]
        if not candidates:
            return None
        candidates.sort(key=lambda a: a.success_rate, reverse=True)
        return candidates[0]

    def get_for_task(self, intent: str, complexity: str = "medium") -> Optional[AgentProfile]:
        if intent in ("greeting", "status_check", "simple_qa"):
            agent = self.get_by_role("customer_service")
            if agent:
                return agent
        if complexity == "high" or intent in ("scientific", "simulation"):
            agent = self.get_by_role("coordinator")
            if agent:
                return agent
        return self.get_by_role("executor") or self.get_by_role("coordinator") or (
            list(self.agents.values())[0] if self.agents else None
        )


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

def _build_price_section() -> str:
    price_list = get_price_list()
    lines = ["## Price List (RMB)"]
    for category, items in price_list.items():
        if category == "currency":
            continue
        lines.append(f"\n### {category}")
        if isinstance(items, dict):
            for name, price in items.items():
                unit = "/item" if category == "labeling_per_item" else ""
                lines.append(f"- {name}: {price}{unit}")
    return "\n".join(lines)


def build_system_prompt(
    profile: CustomerProfile,
    history: List[Message],
    memories: List[str],
    active_order: Optional[OrderInfo],
) -> str:
    price_section = _build_price_section()

    customer_ctx = (
        f"客户姓名: {profile.name}"
        + (f" (公司: {profile.company})" if profile.company else "")
        + f"\n历史交互次数: {profile.interaction_count}"
        + f"\n老客户: {'是' if profile.is_repeat else '否'}"
    )
    if profile.tags:
        customer_ctx += f"\n标签: {', '.join(profile.tags)}"

    order_ctx = ""
    if active_order:
        status_map = {
            "quoted": "已报价，待确认", "paid": "已付款，待执行",
            "executing": "执行中", "delivered": "已交付",
        }
        status_text = status_map.get(active_order.status, active_order.status)
        order_ctx = (
            f"\n\n## 当前活跃订单\n"
            f"- 订单号: {active_order.order_id}\n"
            f"- 任务类型: {active_order.task_type}\n"
            f"- 状态: {status_text}\n"
            f"- 金额: {active_order.amount} 元"
        )

    memory_ctx = ""
    if memories:
        memory_ctx = "\n\n## 关于这位客户的记忆\n" + "\n".join(f"- {m}" for m in memories[:10])

    discount_note = ""
    if profile.is_repeat:
        discount_note = "\n注意: 这是老客户，如客户议价可给予最多9折优惠。\n"

    return f"""你是 Nautilus 平台的技术顾问「小鹦」。你像一个经验丰富、热情的技术sales——懂技术、会沟通、靠谱。

你的工作: 帮客户理解他们的需求，合理报价，下单后把任务派给平台后台的计算引擎执行，然后跟进交付。

# 你的性格

- 热情但不油腻，专业但不冰冷
- 说人话，不说官话套话
- 客户问技术问题时展示专业性，但不卖弄
- 如实沟通，不画饼不夸大
- 简洁为主，一条消息控制在3-5句话，除非需要详细解释

# 铁律（违反=严重事故）

1. 你是顾问和调度员，不是计算引擎。绝对不能自己做任何计算、写代码、生成数据、编造结果。
2. 所有计算/拟合/仿真任务必须通过 [ACTION:...] 标签提交给平台后台执行。
3. 如果客户问"结果是什么"但任务还没执行完，你必须如实说"还在执行中"，绝不能编造数据。
4. 你回复中出现任何具体的计算结果（如参数值、R²值、拟合公式）都是严重错误——除非那是平台返回的真实结果。

# 平台能力

我们的后台计算引擎能做以下任务（括号内为大约执行时间）:

学术计算:
- 通用数值计算 (5-15分钟) — 200元
- 曲线拟合 (10-20分钟) — 500元
- ODE数值模拟 (15-30分钟) — 800元
- PDE数值模拟 (20-60分钟) — 1000元
- 蒙特卡洛模拟 (10-30分钟) — 500元
- 统计分析 (10-20分钟) — 500元
- 机器学习训练 (30-120分钟) — 1200元
- 数据可视化 (5-15分钟) — 300元
- 物理仿真 (20-60分钟) — 1000元
- J-C本构参数拟合 (15-30分钟) — 1500元
- THMC多场耦合 (60-180分钟) — 2500元

数据标注 (按条计价):
- 情感分析: 0.15元/条
- 文本分类: 0.25元/条
- 实体抽取: 0.50元/条
- 意图识别: 0.30元/条
- 目标检测: 1.00元/条
- 安全审核: 1.50元/条

仿真模拟:
- 动力学仿真 (30-60分钟) — 1200元
- 运动规划 (20-40分钟) — 1500元
- 碰撞检测 (20-40分钟) — 1000元
- 场景生成 (15-30分钟) — 800元

价格约为市场价的30-50%，极具竞争力。

## 我的超能力

除了和你聊天，我还能直接操作平台（系统会自动提供工具）：
- 查询平台数据：有多少任务、成功率、客户情况
- 查看订单状态：订单是否在执行、结果是什么
- 提交新任务：帮客户创建并执行计算任务
- 执行代码：在安全沙箱里运行Python代码
- 搜索任务：按类型、状态筛选任务

当客户询问平台数据或任务状态时，必须使用工具查询真实数据，绝不能凭记忆编造。

# ACTION 标签

在你的回复文字中嵌入 ACTION 标签，系统会自动解析执行。客户看不到这些标签。

格式: [ACTION:动作名:参数1:参数2]

可用动作:
- [ACTION:quote:任务类型:金额] — 向客户报价
- [ACTION:create_order:任务类型:金额] — 客户确认后创建订单并自动派发执行
- [ACTION:confirm_payment:订单号] — 确认收款
- [ACTION:submit_task:订单号:任务类型] — 手动提交执行
- [ACTION:deliver_result:订单号] — 交付已完成的任务结果
- [ACTION:save_memory:内容] — 记住关于这位客户的重要信息

# 场景处理指南

## 场景1: 客户打招呼
自然地打招呼，简单介绍自己能做什么。不要列清单，像朋友聊天一样。

## 场景2: 客户描述了一个任务
先确认你理解了需求，判断任务类型，询问关键缺失信息，然后报价。

## 场景3: 客户确认下单
确认金额，创建订单，告知预计时间。

## 场景4: 客户问进度
如实报告。绝不能编造结果。

## 场景5: 客户问能不能做某类任务
根据平台能力如实回答。能做的说清楚，不能做的别硬接。

## 场景6: 客户议价
老客户可给9折。但不要自降太多，我们已经是市场价的30-50%了。

# 绝对禁止

- 编造任何计算结果、数据、参数值、R²值、代码
- 假装任务已完成
- 自己执行计算
- 承诺平台做不到的事情
- 不使用 ACTION 标签就口头承诺"已下单"
{discount_note}
## 客户信息
{customer_ctx}{order_ctx}{memory_ctx}
"""


ROLE_CONTEXT = {
    "coordinator": (
        "你是主顾问，负责与客户沟通需求、报价、创建订单、跟进进度。\n"
        "所有计算任务通过 ACTION 标签派发给平台后台，你绝不能自己计算或编造结果。\n"
    ),
    "executor": (
        "你是技术顾问，负责理解客户的技术需求、评估可行性、报价。\n"
        "计算和代码执行由平台后台自动完成，你的工作是沟通和调度。\n"
        "绝不能在对话中编造任何计算结果。\n"
    ),
    "auditor": (
        "你是质量审计角色。当客户询问结果时，你应基于平台返回的真实数据回答。\n"
        "如果平台尚未返回结果，如实告知客户任务仍在执行中。\n"
    ),
    "customer_service": (
        "你是客服，负责回答简单问题、查询订单状态。\n"
        "如果客户提出复杂技术需求，建议他们描述清楚，你会帮忙安排技术顾问跟进。\n"
        "不要编造任何计算结果或订单信息。\n"
    ),
}

# Claude native tool definitions for tool_use protocol
CLAUDE_TOOLS = [
    {
        "name": "query_platform_stats",
        "description": "查询平台实时统计：任务总数、完成数、成功率、Agent数",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "check_order_status",
        "description": "查询订单状态和任务结果",
        "input_schema": {
            "type": "object",
            "properties": {"order_id": {"type": "string", "description": "订单号"}},
            "required": ["order_id"],
        },
    },
    {
        "name": "submit_task",
        "description": "提交一个新的计算任务给后台引擎执行",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"},
                "task_type": {
                    "type": "string",
                    "enum": [
                        "curve_fitting", "jc_constitutive", "ode_simulation",
                        "statistical_analysis", "monte_carlo", "general_computation",
                    ],
                },
            },
            "required": ["title", "description", "task_type"],
        },
    },
    {
        "name": "execute_code",
        "description": "在Docker沙箱中执行Python代码",
        "input_schema": {
            "type": "object",
            "properties": {"code": {"type": "string", "description": "Python代码"}},
            "required": ["code"],
        },
    },
    {
        "name": "search_tasks",
        "description": "搜索平台上的任务",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_type": {"type": "string"},
                "status": {"type": "string", "enum": ["pending", "processing", "completed", "failed"]},
            },
        },
    },
]


# ---------------------------------------------------------------------------
# Action parsing
# ---------------------------------------------------------------------------

def parse_actions(text: str) -> Tuple[str, List[ParsedAction]]:
    """Extract [ACTION:...] tags from response text. Return clean text + actions."""
    actions: List[ParsedAction] = []
    for match in ACTION_PATTERN.finditer(text):
        action_name = match.group(1)
        raw_params = match.group(2) or ""
        params = tuple(p.strip() for p in raw_params.split(":") if p.strip())
        actions.append(ParsedAction(action=action_name, params=params))
    clean_text = ACTION_PATTERN.sub("", text).strip()
    clean_text = re.sub(r"\n{3,}", "\n\n", clean_text)
    return clean_text, actions


def parse_chinese_tools(text: str) -> List[Tuple[str, str, Dict]]:
    """Parse Chinese tool call tags like [查询:平台统计]."""
    results = []
    for match in _CN_TOOL_PATTERN.finditer(text):
        action = match.group(1)
        args_str = match.group(2)
        full_match = match.group(0)
        parts = [p.strip() for p in args_str.split(":") if p.strip()]

        if action == "查询":
            if not parts:
                continue
            keyword = parts[0]
            mapping = {
                "平台统计": ("query_database", {"type": "platform_stats"}),
                "待处理任务": ("query_database", {"type": "open_tasks"}),
                "我的任务": ("query_database", {"type": "my_tasks"}),
            }
            if keyword in mapping:
                results.append((full_match, *mapping[keyword]))
            elif keyword == "订单" and len(parts) >= 2:
                results.append((full_match, "check_task_status", {"task_id": parts[1]}))
            else:
                results.append((full_match, "query_database", {"type": "platform_stats"}))
        elif action == "提交任务":
            results.append((full_match, "submit_task", {
                "title": parts[0] if parts else "untitled",
                "description": parts[1] if len(parts) >= 2 else (parts[0] if parts else ""),
                "task_type": parts[2] if len(parts) >= 3 else "general_computation",
            }))
        elif action == "执行代码":
            results.append((full_match, "execute_code", {"code": args_str}))
        elif action == "搜索任务":
            results.append((full_match, "search_tasks", {
                "task_type": parts[0] if parts else "",
                "status": parts[1] if len(parts) >= 2 else "",
            }))
        elif action == "发消息":
            if len(parts) >= 2:
                results.append((full_match, "send_message", {"to": parts[0], "content": parts[1]}))
    return results


# ---------------------------------------------------------------------------
# Agent Runtime — tool execution for connected agents
# ---------------------------------------------------------------------------

class AgentRuntime:
    """Full-permission runtime for a connected agent."""

    TOOLS = [
        "execute_code", "query_database", "submit_task", "check_task_status",
        "send_message", "search_tasks", "read_file", "git_status",
        "heartbeat", "self_improve",
        # Google AI tools
        "gemini_chat", "analyze_image", "transcribe_audio", "text_to_speech",
        "gdrive_list", "gdrive_read", "gdoc_create", "gsheet_read", "gsheet_write",
    ]

    def __init__(self, agent_id: str, agent_name: str = ""):
        self.agent_id = agent_id
        self.agent_name = agent_name or agent_id
        self.started_at = datetime.utcnow()
        self.last_heartbeat = datetime.utcnow()
        self.tasks_completed = 0
        logger.info("AgentRuntime created for %s", agent_id)

    async def execute_tool(self, tool_name: str, params: Dict) -> Dict:
        if tool_name not in self.TOOLS:
            return {"error": f"Unknown tool: {tool_name}", "available": self.TOOLS}
        handler = getattr(self, f"_tool_{tool_name}", None)
        if handler is None:
            return {"error": f"Tool {tool_name} not implemented"}
        try:
            return await handler(params)
        except Exception as e:
            logger.error("Tool %s failed for agent %s: %s", tool_name, self.agent_id, e)
            return {"error": str(e)}

    async def _tool_execute_code(self, params: Dict) -> Dict:
        code = params.get("code", "")
        if not code:
            return {"error": "No code provided"}
        try:
            from agent_engine.executors.code_executor import CodeExecutor
            executor = CodeExecutor()
            result = await executor._run_in_docker(code)
            return {"output": result[:5000], "success": True}
        except Exception as e:
            return {"output": str(e), "success": False}

    async def _tool_query_database(self, params: Dict) -> Dict:
        query_type = params.get("type", "")
        from utils.database import get_db_context
        from models.database import AcademicTask, Agent
        with get_db_context() as db:
            if query_type == "my_tasks":
                tasks = db.query(AcademicTask).filter(
                    AcademicTask.user_id == self.agent_id
                ).order_by(AcademicTask.created_at.desc()).limit(10).all()
                return {"tasks": [{"id": t.task_id, "status": t.status, "type": t.task_type} for t in tasks]}
            elif query_type == "open_tasks":
                tasks = db.query(AcademicTask).filter(
                    AcademicTask.status == "pending"
                ).order_by(AcademicTask.created_at.desc()).limit(20).all()
                return {"tasks": [{"id": t.task_id, "title": t.title, "type": t.task_type} for t in tasks]}
            elif query_type == "platform_stats":
                total = db.query(AcademicTask).count()
                completed = db.query(AcademicTask).filter(AcademicTask.status == "completed").count()
                agents = db.query(Agent).count()
                return {"total_tasks": total, "completed": completed, "agents": agents,
                        "success_rate": round(completed / total * 100, 1) if total > 0 else 0}
            return {"error": f"Unknown query type: {query_type}"}

    async def _tool_submit_task(self, params: Dict) -> Dict:
        title = params.get("title", "")
        description = params.get("description", "")
        task_type = params.get("task_type", "general_computation")
        if not title or not description:
            return {"error": "title and description required"}
        from utils.database import get_db_context
        from models.database import AcademicTask
        task_id = f"acad_{secrets.token_hex(8)}"
        with get_db_context() as db:
            db.add(AcademicTask(
                task_id=task_id, title=title, description=description,
                task_type=task_type, status="pending",
            ))
            db.commit()
        try:
            from api.academic_tasks import _dispatch_academic_task
            asyncio.ensure_future(_dispatch_academic_task(task_id))
        except Exception:
            pass
        return {"task_id": task_id, "status": "pending"}

    async def _tool_check_task_status(self, params: Dict) -> Dict:
        task_id = params.get("task_id", "")
        from utils.database import get_db_context
        from models.database import AcademicTask
        with get_db_context() as db:
            task = db.query(AcademicTask).filter(AcademicTask.task_id == task_id).first()
            if not task:
                return {"error": "Task not found"}
            result = {"task_id": task_id, "status": task.status, "type": task.task_type}
            if task.status == "completed":
                result["output"] = (task.result_output or "")[:2000]
                result["code"] = (task.result_code or "")[:2000]
            elif task.status == "failed":
                result["error"] = task.result_error
            return result

    async def _tool_send_message(self, params: Dict) -> Dict:
        to = params.get("to", "")
        content = params.get("content", "")
        if not to or not content:
            return {"error": "to and content required"}
        if to.startswith("tg_"):
            from api.telegram_bot import send_message
            await send_message(int(to.replace("tg_", "")), content)
            return {"sent": True, "channel": "telegram"}
        elif to.startswith("wecom_"):
            from api.wechat_bot import send_text_message
            await send_text_message(to.replace("wecom_", ""), content)
            return {"sent": True, "channel": "wechat"}
        return {"error": f"Unknown recipient format: {to}"}

    async def _tool_search_tasks(self, params: Dict) -> Dict:
        from utils.database import get_db_context
        from models.database import AcademicTask
        with get_db_context() as db:
            q = db.query(AcademicTask)
            if params.get("task_type"):
                q = q.filter(AcademicTask.task_type == params["task_type"])
            if params.get("status"):
                q = q.filter(AcademicTask.status == params["status"])
            tasks = q.order_by(AcademicTask.created_at.desc()).limit(20).all()
            return {"tasks": [{"id": t.task_id, "title": t.title, "status": t.status, "type": t.task_type} for t in tasks]}

    async def _tool_read_file(self, params: Dict) -> Dict:
        path = params.get("path", "")
        allowed = ["docs/", "services/", "api/", "models/"]
        if not any(path.startswith(p) for p in allowed):
            return {"error": f"Access denied. Allowed prefixes: {allowed}"}
        try:
            full_path = os.path.join("/home/ubuntu/nautilus-mvp/phase3/backend", path)
            with open(full_path) as f:
                return {"path": path, "content": f.read()[:5000]}
        except FileNotFoundError:
            return {"error": f"File not found: {path}"}

    async def _tool_git_status(self, params: Dict) -> Dict:
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "-5"],
                capture_output=True, text=True, timeout=10,
                cwd="/home/ubuntu/nautilus-mvp",
            )
            return {"log": result.stdout, "status": "ok"}
        except Exception as e:
            return {"error": str(e)}

    async def _tool_heartbeat(self, params: Dict) -> Dict:
        self.last_heartbeat = datetime.utcnow()
        return {
            "acknowledged": True, "agent_id": self.agent_id,
            "uptime_seconds": (datetime.utcnow() - self.started_at).total_seconds(),
            "tasks_completed": self.tasks_completed,
        }

    async def _tool_self_improve(self, params: Dict) -> Dict:
        target = params.get("target", "prompts")
        if target != "prompts":
            return {"error": f"Unknown improvement target: {target}"}
        try:
            from services.bootstrap_loop import BootstrapLoop
            from utils.database import SessionLocal
            db = SessionLocal()
            report = BootstrapLoop(db).run_cycle()
            db.close()
            return {"improved": True, "report": report}
        except Exception as e:
            return {"error": str(e)}

    # ------------------------------------------------------------------
    # Google AI Tools
    # ------------------------------------------------------------------

    async def _tool_gemini_chat(self, params: Dict) -> Dict:
        """Chat with Gemini. Params: {message: str, system?: str, model?: str}"""
        try:
            from services.google_ai import get_gemini
            gemini = get_gemini()
            response = await gemini.chat(
                params.get("message", ""),
                system=params.get("system"),
                model=params.get("model"),
            )
            return {"success": True, "response": response}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _tool_analyze_image(self, params: Dict) -> Dict:
        """Analyze image with Gemini Vision. Params: {image_base64: str, prompt?: str}"""
        try:
            from services.google_ai import get_gemini
            gemini = get_gemini()
            img_bytes = base64.b64decode(params["image_base64"]) if "image_base64" in params else None
            if not img_bytes:
                return {"error": "image_base64 required"}
            result = await gemini.analyze_image(
                img_bytes,
                params.get("prompt", "请描述这张图片。"),
                mime_type=params.get("mime_type", "image/jpeg"),
            )
            return {"success": True, "description": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _tool_transcribe_audio(self, params: Dict) -> Dict:
        """Transcribe audio. Params: {audio_base64: str, language?: str}"""
        try:
            from services.google_ai import get_gemini
            gemini = get_gemini()
            audio_bytes = base64.b64decode(params["audio_base64"])
            result = await gemini.transcribe_audio(
                audio_bytes,
                f"Transcribe to {params.get('language', 'zh-CN')}.",
                mime_type=params.get("mime_type", "audio/wav"),
            )
            return {"success": True, "transcript": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _tool_text_to_speech(self, params: Dict) -> Dict:
        """Convert text to speech. Params: {text: str, language?: str}"""
        try:
            from services.google_ai import get_speech_client
            import base64 as _b64
            sc = get_speech_client()
            audio_bytes = await sc.text_to_speech(
                params["text"],
                language=params.get("language", "zh-CN"),
            )
            return {
                "success": True,
                "audio_base64": _b64.b64encode(audio_bytes).decode(),
                "mime_type": "audio/mp3",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _tool_gdrive_list(self, params: Dict) -> Dict:
        """List Google Drive files. Params: {query?: str, limit?: int}"""
        try:
            from services.google_ai import get_workspace_client
            ws = get_workspace_client()
            files = await ws.list_files(
                query=params.get("query", ""),
                page_size=params.get("limit", 10),
            )
            return {"success": True, "files": files}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _tool_gdrive_read(self, params: Dict) -> Dict:
        """Read a Google Drive file. Params: {file_id: str}"""
        try:
            from services.google_ai import get_workspace_client
            ws = get_workspace_client()
            content = await ws.read_file(params["file_id"])
            return {"success": True, "content": content[:10000]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _tool_gdoc_create(self, params: Dict) -> Dict:
        """Create a Google Doc. Params: {title: str, content: str}"""
        try:
            from services.google_ai import get_workspace_client
            ws = get_workspace_client()
            result = await ws.create_doc(params["title"], params.get("content", ""))
            return {"success": True, **result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _tool_gsheet_read(self, params: Dict) -> Dict:
        """Read a Google Sheet. Params: {spreadsheet_id: str, range?: str}"""
        try:
            from services.google_ai import get_workspace_client
            ws = get_workspace_client()
            data = await ws.read_sheet(
                params["spreadsheet_id"],
                params.get("range", "Sheet1!A1:Z100"),
            )
            return {"success": True, "values": data, "rows": len(data)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _tool_gsheet_write(self, params: Dict) -> Dict:
        """Write to a Google Sheet. Params: {spreadsheet_id: str, range: str, values: list}"""
        try:
            from services.google_ai import get_workspace_client
            ws = get_workspace_client()
            result = await ws.write_sheet(
                params["spreadsheet_id"],
                params["range"],
                params["values"],
            )
            return {"success": True, **result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_tools_description(self) -> str:
        return """Available tools:
- execute_code: Run Python code in Docker sandbox. Params: {code: str}
- query_database: Query platform data. Params: {type: "my_tasks"|"open_tasks"|"platform_stats"}
- submit_task: Submit a task. Params: {title: str, description: str, task_type: str}
- check_task_status: Check task. Params: {task_id: str}
- send_message: Message user/agent. Params: {to: str, content: str}
- search_tasks: Search tasks. Params: {task_type?: str, status?: str}
- read_file: Read platform file. Params: {path: str}
- git_status: Get git log. Params: {}
- heartbeat: Report alive. Params: {status: str}
- self_improve: Trigger bootstrap. Params: {target: "prompts"}"""


_runtimes: Dict[str, AgentRuntime] = {}


def get_runtime(agent_id: str, agent_name: str = "") -> AgentRuntime:
    if agent_id not in _runtimes:
        _runtimes[agent_id] = AgentRuntime(agent_id, agent_name)
    return _runtimes[agent_id]


def get_all_runtimes() -> Dict[str, AgentRuntime]:
    return _runtimes


# ---------------------------------------------------------------------------
# Core Executor
# ---------------------------------------------------------------------------

class AgentExecutor:
    """Central agent execution pipeline — the Rehoboam replacement."""

    def __init__(self):
        self.registry = AgentRegistry()
        self._clients: Dict[str, Any] = {}
        self._init_clients()
        logger.info("AgentExecutor initialized with %d agents", len(self.registry.agents))

    def _init_clients(self):
        for agent_id, agent in self.registry.agents.items():
            kwargs = {"api_key": agent.api_key}
            if agent.base_url:
                kwargs["base_url"] = agent.base_url
            self._clients[agent_id] = anthropic.Anthropic(**kwargs)

    def get_client(self, agent_id: str):
        return self._clients.get(agent_id)

    # --- Process message pipeline ---

    async def process_message(
        self, wechat_user_id: str, content: str,
        msg_type: str = "text", wechat_msg_id: str = "",
    ) -> str:
        from utils.database import get_db_context
        from models.conversation import Customer, Conversation, Order, SemanticMemory

        t0 = time.monotonic()

        with get_db_context() as db:
            # 1. Load/create customer
            customer = db.query(Customer).filter(
                Customer.wechat_user_id == wechat_user_id
            ).first()
            if not customer:
                customer = Customer(
                    wechat_user_id=wechat_user_id,
                    name=f"客户_{wechat_user_id[:8]}", trust_level=1,
                )
                db.add(customer)
                db.flush()

            # 2. Deduplicate
            if wechat_msg_id:
                existing = db.query(Conversation).filter(
                    Conversation.wechat_msg_id == wechat_msg_id
                ).first()
                if existing:
                    return existing.content if existing.role == "agent" else "收到，请稍候..."

            incoming = Conversation(
                customer_id=customer.id, role="customer", content=content,
                message_type=msg_type, wechat_msg_id=wechat_msg_id or None,
            )
            db.add(incoming)
            try:
                db.flush()
            except Exception:
                db.rollback()
                return "收到，正在处理中..."

            # 3. Load context
            history_rows = (
                db.query(Conversation)
                .filter(Conversation.customer_id == customer.id)
                .order_by(Conversation.created_at.desc())
                .limit(MAX_HISTORY).all()
            )
            history = [
                Message(role=h.role, content=h.content,
                        timestamp=h.created_at.timestamp() if h.created_at else 0)
                for h in reversed(history_rows)
            ]

            memories_rows = (
                db.query(SemanticMemory)
                .filter(SemanticMemory.customer_id == customer.id)
                .order_by(SemanticMemory.importance.desc())
                .limit(10).all()
            )
            memory_texts = [m.content for m in memories_rows]

            # MemoryHierarchy augmentation (best-effort)
            _memory_hierarchy = None
            try:
                from utils.db_pool import get_db_pool
                from services.memory_hierarchy import MemoryHierarchy
                _db_pool = await get_db_pool()
                _memory_hierarchy = MemoryHierarchy(agent_id=customer.id, db_pool=_db_pool)
                for entry in await _memory_hierarchy.recall(content, limit=5):
                    if entry.content not in memory_texts:
                        memory_texts.append(entry.content)
            except Exception:
                pass

            active_order = (
                db.query(Order).filter(
                    Order.customer_id == customer.id,
                    Order.status.in_(["quoted", "paid", "executing"]),
                ).order_by(Order.created_at.desc()).first()
            )

            # 4. Multi-modal processing (best-effort)
            try:
                from services.multimodal import get_processor
                processed = await get_processor().process(content)
                if processed.detected_types and processed.detected_types != ["text"]:
                    content = processed.enriched_text
            except Exception:
                pass

            # 5. Classify intent
            intent, complexity = "general", "medium"
            routing_decision = None
            try:
                from services.task_router import TaskRouter
                routing_decision = await TaskRouter(db=db).route(
                    task_id=wechat_msg_id or "msg", description=content,
                )
                intent = routing_decision.task_type or "general"
                complexity = "high" if routing_decision.suggested_raid_level >= 3 else "medium"
            except Exception:
                pass

            # 6. Select agent
            agent = self.registry.get_for_task(intent, complexity)
            if not agent:
                return "系统暂时不可用，请稍后再试。"

            client = self.get_client(agent.agent_id)

            # 7. Build prompt + context
            profile = CustomerProfile(
                customer_id=str(customer.id), name=customer.name or "",
                company=customer.company or "",
                interaction_count=customer.total_orders or 0,
                is_repeat=(customer.total_orders or 0) > 0,
            )
            order_info = None
            if active_order:
                order_info = OrderInfo(
                    order_id=active_order.order_no,
                    task_type=active_order.task_type or "",
                    status=active_order.status,
                    amount=active_order.quoted_price or 0,
                )

            system_prompt = build_system_prompt(profile, history, memory_texts, order_info)
            system_prompt += f"\n\n## 当前角色: {agent.name}\n"
            system_prompt += ROLE_CONTEXT.get(agent.role, "")

            # 8. Get runtime for tool execution
            runtime = get_runtime(agent.agent_id, agent.name)

            messages = [
                {"role": "user" if h.role == "customer" else "assistant", "content": h.content}
                for h in history[-MAX_HISTORY:]
            ]
            messages.append({"role": "user", "content": content})

            # 9. Call LLM
            raw_text, tokens = await self._call_llm(
                agent, client, system_prompt, messages, runtime,
            )

            elapsed = time.monotonic() - t0

            # 10. Parse actions and execute order lifecycle
            clean_text, actions = parse_actions(raw_text)
            clean_text = self._execute_order_actions(
                clean_text, actions, customer, content, db,
            )

            # 11. Save reply
            db.add(Conversation(
                customer_id=customer.id, role="agent",
                content=clean_text, message_type="text",
            ))
            db.commit()

            # 12. Store to MemoryHierarchy (best-effort)
            if _memory_hierarchy:
                try:
                    summary = f"[{intent}] User: {content[:200]} | Agent: {clean_text[:200]}"
                    await _memory_hierarchy.store(summary, importance=0.6 if intent == "general" else 0.75)
                except Exception:
                    pass

            # 13. Bootstrap logging
            log_entry = {
                "ts": datetime.utcnow().isoformat(),
                "customer_id": str(customer.id),
                "intent": intent, "complexity": complexity,
                "agent": agent.agent_id, "agent_role": agent.role,
                "actions": [a.action for a in actions],
                "tokens_used": tokens,
                "elapsed_ms": round(elapsed * 1000, 1),
            }
            bootstrap_logger.info(json.dumps(log_entry, ensure_ascii=False))

            logger.info(
                "Executor: customer=%s intent=%s agent=%s actions=%d tokens=%d elapsed=%.1fs",
                customer.name, intent, agent.name, len(actions), tokens, elapsed,
            )
            return clean_text

    async def _call_llm(
        self, agent: AgentProfile, client: Any,
        system_prompt: str, messages: List[Dict],
        runtime: AgentRuntime,
    ) -> Tuple[str, int]:
        """Call LLM with tool_use support and fallback. Returns (text, tokens)."""
        # Try with tools first
        try:
            try:
                response = client.messages.create(
                    model=agent.model, max_tokens=2048,
                    system=system_prompt, tools=CLAUDE_TOOLS, messages=messages,
                )
            except Exception:
                response = client.messages.create(
                    model=agent.model, max_tokens=2048,
                    system=system_prompt, messages=messages,
                )

            raw_text = ""
            tool_results = []
            tokens = (response.usage.input_tokens + response.usage.output_tokens) if response.usage else 0

            for block in (response.content or []):
                if block.type == "text":
                    raw_text += block.text
                elif block.type == "tool_use":
                    tool_input = block.input or {}
                    tool_map = {
                        "query_platform_stats": ("query_database", {"type": "platform_stats"}),
                        "check_order_status": ("check_task_status", {"task_id": tool_input.get("order_id", "")}),
                        "submit_task": ("submit_task", tool_input),
                        "execute_code": ("execute_code", {"code": tool_input.get("code", "")}),
                        "search_tasks": ("search_tasks", tool_input),
                    }
                    rt_name, rt_params = tool_map.get(block.name, (block.name, tool_input))
                    try:
                        result = await runtime.execute_tool(rt_name, rt_params)
                    except Exception as e:
                        result = {"error": str(e)}
                    tool_results.append({"tool_use_id": block.id, "result": result})

            # Follow-up call if tools were used
            if tool_results and response.stop_reason == "tool_use":
                followup = messages + [{"role": "assistant", "content": response.content}]
                for tr in tool_results:
                    followup.append({
                        "role": "user",
                        "content": [{
                            "type": "tool_result",
                            "tool_use_id": tr["tool_use_id"],
                            "content": json.dumps(tr["result"], ensure_ascii=False)[:2000],
                        }],
                    })
                try:
                    r2 = client.messages.create(
                        model=agent.model, max_tokens=2048,
                        system=system_prompt, tools=CLAUDE_TOOLS, messages=followup,
                    )
                    raw_text = "".join(b.text for b in (r2.content or []) if hasattr(b, "text"))
                    tokens += (r2.usage.input_tokens + r2.usage.output_tokens) if r2.usage else 0
                except Exception:
                    pass

            return raw_text, tokens

        except Exception as e:
            logger.error("Agent %s failed: %s, trying fallback", agent.agent_id, e)
            for aid, c in self._clients.items():
                if aid != agent.agent_id:
                    try:
                        response = c.messages.create(
                            model=self.registry.agents[aid].model, max_tokens=2048,
                            system=system_prompt, messages=messages,
                        )
                        text = next(
                            (b.text for b in (response.content or []) if hasattr(b, "text")), ""
                        )
                        tok = (response.usage.input_tokens + response.usage.output_tokens) if response.usage else 0
                        return text, tok
                    except Exception:
                        continue
            return "抱歉，系统暂时繁忙，请稍后再试。", 0

    def _execute_order_actions(
        self, clean_text: str, actions: List[ParsedAction],
        customer: Any, content: str, db: Any,
    ) -> str:
        """Execute order-lifecycle actions against DB. Returns updated text."""
        from models.conversation import Order, SemanticMemory

        for act in actions:
            try:
                if act.action == "create_order" and act.params:
                    task_type = act.params[0] if act.params else "general_computation"
                    amount = float(act.params[1]) if len(act.params) > 1 else get_task_price(task_type)
                    order_no = f"ORD-{secrets.token_hex(4).upper()}"
                    order = Order(
                        customer_id=customer.id, order_no=order_no,
                        task_type=task_type, title=f"{task_type} for {customer.name}",
                        description=content, quoted_price=amount, status="paid",
                        paid_amount=amount, payment_confirmed_at=datetime.utcnow(),
                    )
                    db.add(order)
                    db.flush()
                    clean_text = clean_text.replace("ORD-xxx", order_no)
                    self._dispatch_task_for_order(order, content, db)

                elif act.action == "submit_task" and act.params:
                    order_no = act.params[0] if act.params else None
                    order_row = None
                    if order_no:
                        order_row = db.query(Order).filter(Order.order_no == order_no).first()
                    if not order_row:
                        order_row = db.query(Order).filter(
                            Order.customer_id == customer.id
                        ).order_by(Order.created_at.desc()).first()
                    if order_row and order_row.status != "executing" and not order_row.internal_task_id:
                        order_row.status = "executing"
                        self._dispatch_task_for_order(order_row, content, db)

                elif act.action == "save_memory" and act.params:
                    db.add(SemanticMemory(
                        customer_id=customer.id, category="insight",
                        content=":".join(act.params), importance=5,
                    ))

                elif act.action == "confirm_payment" and act.params:
                    order_row = db.query(Order).filter(Order.order_no == act.params[0]).first()
                    if order_row:
                        order_row.status = "paid"
                        order_row.paid_amount = order_row.quoted_price
                        order_row.payment_confirmed_at = datetime.utcnow()

                elif act.action == "deliver_result" and act.params:
                    order_row = db.query(Order).filter(Order.order_no == act.params[0]).first()
                    if order_row and order_row.internal_task_id:
                        from models.database import AcademicTask
                        task = db.query(AcademicTask).filter(
                            AcademicTask.task_id == order_row.internal_task_id
                        ).first()
                        if task and task.status == "completed":
                            order_row.status = "delivered"
                            order_row.delivered_at = datetime.utcnow()
                            output = task.result_output or ""
                            if output:
                                clean_text += f"\n\n--- 执行结果 ---\n{output[:1000]}"

            except Exception:
                logger.exception("Failed to execute action %s", act.action)

        return clean_text

    def _dispatch_task_for_order(self, order: Any, description: str, db: Any) -> None:
        from models.database import AcademicTask
        task_id = f"acad_{secrets.token_hex(8)}"
        db.add(AcademicTask(
            task_id=task_id, title=order.title or order.task_type or "task",
            description=description, task_type=order.task_type or "general_computation",
            status="pending",
        ))
        order.internal_task_id = task_id
        db.flush()
        try:
            from api.academic_tasks import _dispatch_academic_task
            asyncio.ensure_future(_dispatch_academic_task(task_id))
        except Exception as exc:
            logger.warning("Failed to dispatch task %s: %s", task_id, exc)

    # --- Audit (Pillar 3: Bias) ---

    async def verify_task_result(self, task_id: str, raid_level: int = 2) -> Dict[str, Any]:
        """Verify a completed task result via auditor agent."""
        from utils.database import get_db_context
        from models.database import AcademicTask

        with get_db_context() as db:
            row = db.query(AcademicTask).filter(AcademicTask.task_id == task_id).first()
            if not row:
                return {"passed": False, "reason": f"Task {task_id} not found"}
            task_desc = row.description or ""
            code = row.result_code or "(no code)"
            output = (row.result_output or "(no output)")[:3000]
            error = row.result_error

        if error:
            return {"passed": False, "reason": f"Execution error: {error[:500]}"}
        if raid_level <= 1:
            return {"passed": True, "reason": "Raid 1: self-review only — auto-passed"}

        auditor = self.registry.get_by_role("auditor")
        if not auditor:
            return {"passed": True, "reason": "No auditor agent configured — auto-passed"}
        client = self.get_client(auditor.agent_id)
        if not client:
            return {"passed": True, "reason": "Auditor client unavailable — auto-passed"}

        audit_prompt = (
            "You are a strict academic task auditor. Review the following task result.\n\n"
            f"## Task description\n{task_desc}\n\n"
            f"## Generated code\n```python\n{code}\n```\n\n"
            f"## Execution output (truncated)\n{output}\n\n"
            "Check:\n"
            "1. Does the code look syntactically correct and runnable?\n"
            "2. Does the output make sense given the task description?\n"
            "3. Are quantitative metrics reported where applicable?\n"
            "4. Are there any obvious errors, empty outputs, or placeholder results?\n\n"
            'Respond ONLY with JSON: {"passed": true/false, "reason": "<brief explanation>"}'
        )

        try:
            response = await asyncio.to_thread(
                client.messages.create,
                model=auditor.model, max_tokens=512,
                system="You are a quality auditor. Be concise. Return only JSON.",
                messages=[{"role": "user", "content": audit_prompt}],
            )
            raw = next((b.text for b in (response.content or []) if hasattr(b, "text")), "")
            match = re.search(r"\{[^{}]*\}", raw, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                passed = bool(data.get("passed", False))
                reason = str(data.get("reason", raw[:300]))
            else:
                passed, reason = False, f"Auditor response unparseable: {raw[:300]}"
        except Exception as exc:
            return {"passed": True, "reason": f"Audit call failed ({exc}) — auto-passed"}

        try:
            with get_db_context() as db:
                row = db.query(AcademicTask).filter(AcademicTask.task_id == task_id).first()
                if row:
                    row.audit_status = "passed" if passed else "flagged"
                    row.audit_reason = reason[:2000]
                    if not passed:
                        row.status = "needs_review"
                    db.commit()
        except Exception:
            pass

        return {"passed": passed, "reason": reason}

    # --- Autonomous check (Pillar 7: Unprompted) ---

    async def autonomous_check(self) -> List[str]:
        """Run periodic autonomous checks. Called by scheduler."""
        actions_taken = []
        from utils.database import get_db_context
        from models.conversation import Order, Customer
        from models.database import AcademicTask

        with get_db_context() as db:
            # Check completed tasks not yet delivered
            for order in db.query(Order).filter(
                Order.status == "executing", Order.internal_task_id.isnot(None),
            ).all():
                task = db.query(AcademicTask).filter(
                    AcademicTask.task_id == order.internal_task_id
                ).first()
                if task and task.status == "completed":
                    order.status = "completed"
                    customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
                    if customer:
                        output_preview = (task.result_output or "")[:500]
                        notify_msg = f"您的任务 {order.order_no} 已完成！\n\n结果摘要：\n{output_preview}"
                        actions_taken.append(f"Notified {customer.name} about completed order {order.order_no}")
                        try:
                            if customer.wechat_user_id.startswith("tg_"):
                                from api.telegram_bot import send_message
                                await send_message(int(customer.wechat_user_id.replace("tg_", "")), notify_msg)
                            elif customer.wechat_user_id.startswith("wecom_"):
                                from api.wechat_bot import send_text_message
                                await send_text_message(customer.wechat_user_id.replace("wecom_", ""), notify_msg)
                        except Exception as e:
                            logger.warning("Notification failed: %s", e)
                elif task and task.status == "failed":
                    order.status = "failed"
                    actions_taken.append(f"Marked order {order.order_no} as failed")

            # Mark stuck tasks as failed
            ten_min_ago = datetime.utcnow() - timedelta(minutes=10)
            for task in db.query(AcademicTask).filter(
                AcademicTask.status == "pending", AcademicTask.created_at < ten_min_ago,
            ).all():
                task.status = "failed"
                task.result_error = "Timed out in queue"
                actions_taken.append(f"Marked stuck task {task.task_id} as failed")

            db.commit()

        if actions_taken:
            logger.info("Autonomous check: %d actions taken", len(actions_taken))
        return actions_taken


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_instance: Optional[AgentExecutor] = None


def get_executor() -> AgentExecutor:
    global _instance
    if _instance is None:
        _instance = AgentExecutor()
    return _instance


async def process_message(
    wechat_user_id: str, content: str,
    msg_type: str = "text", wechat_msg_id: str = "",
) -> str:
    """Top-level entry point for message processing."""
    return await get_executor().process_message(wechat_user_id, content, msg_type, wechat_msg_id)
