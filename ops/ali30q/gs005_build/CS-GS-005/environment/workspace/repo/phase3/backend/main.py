"""
Main FastAPI application for Nautilus Phase 3 Backend.
"""
from fastapi import FastAPI, HTTPException, Response, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError
from pydantic import BaseModel
import socketio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from utils.database import init_db
import models.payment  # noqa: F401 - ensure payment tables are created
import models.team  # noqa: F401 - ensure team tables are created
import models.raid  # noqa: F401 - ensure raid tables are created
import models.agent_survival  # noqa: F401 - ensure agent_survival table is created
from api.tasks import router as tasks_router
from api.agents import router as agents_router
from api.rewards import router as rewards_router
from api.auth import router as auth_router
from api.agent_tasks import router as agent_tasks_router
from api.metrics import router as metrics_router
from api.alerts import router as alerts_router
from api.memory import router as memory_router
from api.stats import router as stats_router
from api.bootstrap import router as bootstrap_router
from api.bootstrap_status import router as bootstrap_loop_router
from api.survival import router as survival_router
from api.anti_cheat import router as anti_cheat_router
from api.wallets import router as wallets_router
from api.academic_tasks import router as academic_router
from api.agent_first_register import router as agent_first_router
from api.payments import router as payments_router
from api.labeling_service import router as labeling_router
from api.agent_hub import router as agent_hub_router
from api.simulation_tasks import router as simulation_router
from api.raid import router as raid_router
from api.teams import router as teams_router
from api.marketplace import router as marketplace_router
from api.marketplace import task_router as marketplace_task_router
from api.partner_api import router as partner_api_router
from api.partner_admin import router as partner_admin_router
import models.partner  # noqa: F401 - ensure partner tables are created
import models.conversation  # noqa: F401 - ensure conversation tables are created
from api.wechat_bot import router as wechat_router
from api.file_upload import router as upload_router
from api.auth_code import router as auth_code_router
from api.auth_authing import router as auth_authing_router
from api.telegram_bot import router as telegram_router
from api.telegram_admin_bot import router as admin_bot_router
from api.a2a_relay import router as a2a_relay_router
from api.commercial_bot import router as commerce_bot_router
from api.google_ai import router as google_ai_router
from api.agent_marketplace import router as agent_marketplace_router
from api.dashboard import dashboard_router
from api.openclaw import router as openclaw_router
from api.openclaw_network import router as openclaw_network_router
from api.soul import router as soul_router
from api.discover import router as discover_router
from api.research import router as research_router
from api.feed import router as feed_router
from api.square import router as square_router  # U29 二次挂载:模型已补(SquarePost/SquareReaction)+表已建(10/1 晨),runbook 四步走
from api.skills import router as skills_router
from api.tools import router as tools_router
from api.messages import router as messages_router
from api.genes import router as genes_router
from api.skill_library import router as skill_library_router
import models.marketplace_models  # noqa: F401 - ensure marketplace tables are created
from api.a2a import router as a2a_router
from api.a2a_jsonrpc import router as a2a_jsonrpc_router
from api.agent_card import router as agent_card_router
from api.claude_memory_bridge import router as claude_memory_router
from api.platform import router as platform_router
from api.platform_proposals import router as proposals_router
from api.fde_verdict import router as fde_verdict_router
from api.org import router as org_router  # org/bootstrap P0 · 跨框函件必达信箱
from api.org_outcomes import router as org_outcomes_router  # U13 断奶第一刀 · outcome 写回端点
from api.org_fuel import router as org_fuel_router
from api.org_assay import router as org_assay_router  # b档数据验证通道(M3 契约 v0.1)
from api.org_e2e import router as org_e2e_router  # 管道E2E验证(每单五段链活读数)
from api.org_intake import router as org_intake_router  # 提测受理API(M1:公开提交/进度/事件流+KEY流转)
from api.identity import router as identity_router  # 统一身份层M1(邮箱码+JWT)
from api.users import users_router, auth_session_router  # 用户中心+auth会话补端点(R3 2026-10-09)
from api.admin import router as admin_router  # 统一后台框架v0.1(/api/platform/admin/*)
from api.feishu_decision import router as feishu_decision_router  # org OS 0b · 飞书决策卡(人机拍板环)
from api.feishu_cmd import router as feishu_cmd_router  # 贾维斯 v0 · 飞书指令入口(V5 转发 im.message)
from api.fde_attention import router as fde_attention_router
from api.fde_capability import router as fde_capability_router
from api.soul_activity import router as soul_activity_router
from api.fde_dispatch import router as fde_dispatch_router
from api.platform_rsi_fde import router as rsi_fde_router
from api.fde_grounding import router as fde_grounding_router
from api.fde_rsi_delta import router as fde_rsi_delta_router
from api.fde_phase3_runtime import router as fde_phase3_runtime_router
from api.fde_phase3_s0 import router as fde_phase3_s0_router
from api.control_plane import router as control_plane_router
from api.control_plane_actions import router as control_plane_actions_router
from api.platform_dispatch import router as dispatch_router
from api.sandbox import router as sandbox_router
from api.evolution import router as evolution_router
from api.multimodal_tasks import router as multimodal_router
import models.fde_attention  # noqa: F401 - ensure attention table is created
from websocket_server import sio, socket_app
from utils.logging_config import init_logging_from_env, get_logger
from monitoring_config import (
    initialize_app_info,
    get_metrics,
    check_database_health,
    check_blockchain_health,
    check_redis_health
)
from utils.cache import get_cache
from utils.performance_middleware import (
    PerformanceMonitoringMiddleware,
    RequestCounterMiddleware,
    get_request_counter,
    set_request_counter
)
from utils.pool_monitor import init_pool_monitor, get_pool_monitor
from utils.database import get_engine
from middleware.logging_middleware import LoggingMiddleware, ErrorLoggingMiddleware
from utils.security_validators import validate_environment_variables, sanitize_log_data
from utils.sensitive_data_filter import setup_sensitive_data_filtering
from utils.json_validation_middleware import JSONValidationMiddleware

# Initialize logging system
init_logging_from_env()
logger = get_logger(__name__)

# Setup sensitive data filtering for logs
setup_sensitive_data_filtering()

# Validate environment variables at startup
try:
    validation_result = validate_environment_variables()
    logger.info(f"Security validation completed: {validation_result['status']}")
    if validation_result['warnings']:
        for warning in validation_result['warnings']:
            logger.warning(f"Security warning: {warning}")
except ValueError as e:
    logger.critical(f"Security validation failed: {e}")
    raise

# Environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
FORCE_HTTPS = os.getenv("FORCE_HTTPS", "false").lower() == "true"
HSTS_MAX_AGE = int(os.getenv("HSTS_MAX_AGE", "31536000"))
TESTING = os.getenv("TESTING", "false").lower() == "true"
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true" and not TESTING

# CSRF Configuration
class CsrfSettings(BaseModel):
    secret_key: str = os.getenv("CSRF_SECRET_KEY")
    cookie_samesite: str = "lax"
    cookie_secure: bool = not DEBUG
    cookie_httponly: bool = True

# Validate CSRF_SECRET_KEY at startup
CSRF_SECRET_KEY = os.getenv("CSRF_SECRET_KEY")
if not CSRF_SECRET_KEY:
    raise ValueError("CSRF_SECRET_KEY environment variable is required and must be set")
if len(CSRF_SECRET_KEY) < 32:
    raise ValueError("CSRF_SECRET_KEY must be at least 32 characters long for security")
if CSRF_SECRET_KEY in ["your-csrf-secret-key-change-in-production", "secret", "changeme", "test"]:
    raise ValueError("CSRF_SECRET_KEY cannot use default or weak values")

@CsrfProtect.load_config
def get_csrf_config():
    return CsrfSettings()

# Rate Limiter Configuration
# 2026-09-20: agent-aware buckets. Previously key_func=get_remote_address keyed
# ALL local callers on one 127.0.0.1 bucket (default 200/hour) — a single agent's
# flood (reborn daemon / fde_runner / unknown 10-min source, 3x same incident)
# throttled every cloud-side caller. Now each self-declared agent_id gets its own
# bucket; floods are contained to the offender. Non-agent traffic stays per-IP.
# NOTE: slowapi 0.1.x calls key_func SYNCHRONOUSLY (limit_key = lim.key_func(request))
# — an async key_func silently degrades (coroutine object as key = never limited,
# verified by test). So agent identity is extracted by AgentKeyMiddleware (outer,
# async, allowed to read body) and stashed on request.state; _rl_key reads it sync.
# NOTE: self-declared key is spoofable until auth lands (2026-09-20 grace cutover);
# after auth, upgrade to authenticated identity. IP fallback keeps the floor.
def _rl_key(request: Request) -> str:
    # 2026-10-10: XFF 优先——nginx 回源时 remote_addr 恒为 127.0.0.1,全站匿名流量
    # 共享一桶,live 页 6 端点×10s 轮询单页即自打满(429 全站 offline 根因);
    # uvicorn proxy_headers 默认信 127.0.0.1 的 XFF,取其首段=真实客户端 IP。
    xff = request.headers.get("X-Forwarded-For", "")
    if xff:
        return "ip:" + xff.split(",")[0].strip()
    return getattr(request.state, "rl_agent_key", None) or get_remote_address(request)


class AgentKeyMiddleware(BaseHTTPMiddleware):
    """Extract agent identity from JSON body → request.state.rl_agent_key.

    Runs OUTSIDE SlowAPIMiddleware (added after it in the stack) so the sync
    key_func can see it. Body read here is cached by Starlette; endpoint JSON
    parsing reuses the cache — no double read, no breakage.
    """

    async def dispatch(self, request: Request, call_next):
        if request.method in ("POST", "PUT", "PATCH"):
            try:
                body = await request.json()
                if isinstance(body, dict):
                    agent = (body.get("agent_id") or body.get("from_agent")
                             or body.get("to_agent"))
                    if isinstance(agent, str) and agent:
                        request.state.rl_agent_key = f"agent:{agent[:64]}"
            except Exception:
                pass  # non-JSON/oversized → per-IP bucket via fallback
        return await call_next(request)


limiter = Limiter(key_func=_rl_key, default_limits=["12000/hour"])  # 2026-10-10: 200→12000 过渡值——live 页 6 端点×10s 轮询=2160/h 单页即超旧地板;正解(Limiter 归一+已鉴权身份桶)排开业后,鉴权关闸后本地板只防滥用


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Nautilus Phase 3 Backend...")
    init_db()
    logger.info("Database initialized")

    # Initialize database pool for memory system
    try:
        logger.info("Database connection pool initialized for memory system")
    except Exception as e:
        logger.warning(f"Failed to initialize database pool: {e}")

    # Initialize pool monitoring
    engine = get_engine()
    init_pool_monitor(engine)
    logger.info("Database pool monitoring initialized")

    # Initialize monitoring
    initialize_app_info(version="3.0.0", environment=ENVIRONMENT)
    logger.info("Monitoring system initialized")

    # Initialize cache cleanup task
    import asyncio
    async def cleanup_cache_periodically():
        while True:
            await asyncio.sleep(300)  # Every 5 minutes
            cache = get_cache()
            cache.cleanup_expired()

    cleanup_task = asyncio.create_task(cleanup_cache_periodically())
    logger.info("Cache cleanup task started")

    # Start WeChat Bot (WebSocket long connection)
    wechat_bot_task = None
    if os.getenv("WECHAT_BOT_ID") and os.getenv("WECHAT_BOT_SECRET"):
        try:
            from services.wechat_ws_bot import WeChatWSBot
            wechat_bot = WeChatWSBot()
            wechat_bot_task = asyncio.create_task(wechat_bot.start())
            logger.info("WeChat Bot started (WebSocket long connection)")
        except Exception as e:
            logger.warning(f"Failed to start WeChat Bot: {e}")
    else:
        logger.info("WeChat Bot not configured (WECHAT_BOT_ID/SECRET not set)")

    # Phase 3: Start Nexus Protocol Server
    nexus_server = None
    try:
        from nexus_server import NexusServer
        nexus_server = NexusServer(
            cors_origins=os.getenv("NEXUS_CORS_ORIGINS", "*"),
            max_queue_size=int(os.getenv("NEXUS_MAX_QUEUE_SIZE", "1000")),
            max_agents=int(os.getenv("NEXUS_MAX_AGENTS", "100"))
        )
        # Mount Nexus server to FastAPI app
        app.mount("/nexus", socketio.ASGIApp(nexus_server.sio))
        logger.info("✅ Nexus Protocol Server started at /nexus")
    except Exception as e:
        logger.warning(f"⚠️  Failed to start Nexus Protocol Server: {e}")

    # Phase 4: Start Blockchain Event Listener
    event_listener = None
    blockchain_enabled = os.getenv("BLOCKCHAIN_EVENT_LISTENER_ENABLED", "true").lower() == "true"
    if blockchain_enabled:
        try:
            from blockchain.event_listener import BlockchainEventListener
            event_listener = BlockchainEventListener()

            # Register event handlers
            from blockchain_event_handlers import (
                handle_task_published,
                handle_task_accepted,
                handle_task_completed
            )
            event_listener.register_handler("TaskPublished", handle_task_published)
            event_listener.register_handler("TaskAccepted", handle_task_accepted)
            event_listener.register_handler("TaskCompleted", handle_task_completed)

            # Start listener in background
            listener_task = asyncio.create_task(event_listener.start())
            logger.info("✅ Blockchain Event Listener started")
        except Exception as e:
            logger.warning(f"⚠️  Failed to start Blockchain Event Listener: {e}")
            listener_task = None
    else:
        logger.info("ℹ️  Blockchain Event Listener disabled")
        listener_task = None

    # Start background scheduler (stuck task cleanup, bootstrap cycles)
    from services.scheduler import get_scheduler
    scheduler = get_scheduler()
    await scheduler.start()
    logger.info("Background scheduler started")

    # Start Autonomy Scheduler — drives agent autonomous bidding cycles
    try:
        from services.autonomy_scheduler import start_autonomy_scheduler, stop_autonomy_scheduler
        from utils.database import SessionLocal as _AutonomySessionLocal
        start_autonomy_scheduler(_AutonomySessionLocal)
        logger.info("Autonomy Scheduler started")
    except Exception as e:
        logger.warning(f"Failed to start Autonomy Scheduler: {e}")

    # Start Cron Registry — unified job scheduler with time budgets
    try:
        from services.cron_registry import start_cron_registry
        from utils.database import SessionLocal as _CronSessionLocal
        start_cron_registry(_CronSessionLocal)
        logger.info("Cron Registry started (Observatory + autoDream + Reputation decay)")
    except Exception as e:
        logger.warning(f"Failed to start Cron Registry: {e}")

    # Start Event Bus subscriber — Redis Pub/Sub event-driven architecture
    try:
        from services.event_bus import start_subscriber
        from services.event_handlers import register_all_handlers
        register_all_handlers()
        start_subscriber()
        logger.info("Event Bus subscriber + handlers started")
    except Exception as e:
        logger.warning(f"Failed to start Event Bus: {e}")

    # Start Autonomous Loop — the self-driving engine
    autonomous_loop_task = None
    autonomous_enabled = os.getenv("AUTONOMOUS_LOOP_ENABLED", "true").lower() == "true"
    if autonomous_enabled:
        try:
            from services.autonomous_loop import get_autonomous_loop
            autonomous_loop = get_autonomous_loop()
            autonomous_loop_task = asyncio.create_task(autonomous_loop.start())
            logger.info("AutonomousLoop STARTED — platform is now self-driving")
        except Exception as e:
            logger.warning(f"Failed to start AutonomousLoop: {e}")
    else:
        logger.info("AutonomousLoop disabled via AUTONOMOUS_LOOP_ENABLED=false")

    # Phase 5: Start Task Auto-Assignment Scheduler
    auto_assign_enabled = os.getenv("TASK_AUTO_ASSIGN_ENABLED", "true").lower() == "true"
    auto_assign_task = None
    if auto_assign_enabled:
        try:
            from task_matcher import check_and_assign_tasks
            from utils.database import get_db

            async def auto_assign_periodically():
                """Periodically check and assign tasks."""
                interval = int(os.getenv("TASK_AUTO_ASSIGN_INTERVAL", "30"))  # seconds
                while True:
                    await asyncio.sleep(interval)
                    try:
                        db = next(get_db())
                        await check_and_assign_tasks(db)
                        db.close()
                    except Exception as e:
                        logger.error(f"Error in auto-assignment: {e}")

            auto_assign_task = asyncio.create_task(auto_assign_periodically())
            logger.info(f"✅ Task Auto-Assignment Scheduler started (interval: {os.getenv('TASK_AUTO_ASSIGN_INTERVAL', '30')}s)")
        except Exception as e:
            logger.warning(f"⚠️  Failed to start Task Auto-Assignment: {e}")
    else:
        logger.info("ℹ️  Task Auto-Assignment disabled")

    yield

    # Shutdown
    await scheduler.stop()
    cleanup_task.cancel()
    if listener_task:
        listener_task.cancel()
        logger.info("Blockchain Event Listener stopped")
    if auto_assign_task:
        auto_assign_task.cancel()
        logger.info("Task Auto-Assignment Scheduler stopped")
    if autonomous_loop_task:
        await get_autonomous_loop().stop()
        autonomous_loop_task.cancel()
        logger.info("AutonomousLoop stopped")

    # Stop Autonomy Scheduler
    try:
        from services.autonomy_scheduler import stop_autonomy_scheduler
        stop_autonomy_scheduler()
        logger.info("Autonomy Scheduler stopped")
    except Exception as e:
        logger.warning(f"Error stopping Autonomy Scheduler: {e}")

    # Stop Cron Registry
    try:
        from services.cron_registry import stop_cron_registry
        stop_cron_registry()
        logger.info("Cron Registry stopped")
    except Exception as e:
        logger.warning(f"Error stopping Cron Registry: {e}")

    # Close database pool
    try:
        logger.info("Database connection pool closed")
    except Exception as e:
        logger.warning(f"Error closing database pool: {e}")
    logger.info("Shutting down Nautilus Phase 3 Backend...")


# Create FastAPI app
app = FastAPI(
    title="Nautilus API",
    description="""
    🚀 **Nautilus - AI Agent 任务协作平台 API**

    ## 功能特性

    * **Agent 管理** - 注册、查询、更新 AI Agent
    * **任务管理** - 发布、匹配、执行任务
    * **OAuth 认证** - GitHub 和 Google 登录
    * **区块链集成** - Sepolia 测试网智能合约
    * **实时通信** - Nexus Protocol WebSocket
    * **奖励系统** - 自动分配和提取奖励

    ## 认证方式

    ### JWT Token (用户认证)
    ```bash
    Authorization: Bearer <your_jwt_token>
    ```

    ### API Key (Agent 认证)
    ```bash
    X-API-Key: naut_<your_api_key>
    ```

    ### Agent 签名 (可选)
    ```bash
    X-Agent-Signature: <signature>
    X-Agent-Address: <wallet_address>
    ```

    ## 快速开始

    1. **注册账户**: `POST /api/auth/register`
    2. **注册 Agent**: `POST /api/agents`
    3. **发布任务**: `POST /api/tasks`
    4. **接受任务**: `POST /api/tasks/{task_id}/accept`
    5. **提交结果**: `POST /api/tasks/{task_id}/submit`

    ## 区块链集成

    - **网络**: Sepolia Testnet
    - **合约**: TaskMarketplace.sol
    - **Gas 费用**: 50% 由 Agent 承担

    ## 速率限制

    - 默认: 200 请求/小时
    - 认证端点: 5 请求/分钟
    - 健康检查: 50 请求/分钟

    ## 技术支持

    - 文档: https://docs.nautilus.social
    - GitHub: https://github.com/nautilus-project
    - Discord: https://discord.gg/nautilus
    """,
    version="3.0.0",
    lifespan=lifespan,
    debug=DEBUG,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    contact={
        "name": "Nautilus Team",
        "url": "https://nautilus.social",
        "email": "support@nautilus.social"
    },
    license_info={
        "name": "Apache License 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0"
    }
)

# Add rate limiter state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CSRF exception handler
@app.exception_handler(CsrfProtectError)
def csrf_protect_exception_handler(request: Request, exc: CsrfProtectError):
    return HTTPException(status_code=403, detail="CSRF token validation failed")

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)

    # HTTPS Redirect
    if FORCE_HTTPS and request.url.scheme == "http":
        url = request.url.replace(scheme="https")
        return Response(status_code=307, headers={"Location": str(url)})

    # Security Headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

    # Content Security Policy
    if ENVIRONMENT == "production":
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
#         response.headers["Content-Security-Policy"] = csp

    # HSTS Header (only in production with HTTPS)
    if ENVIRONMENT == "production" and request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = f"max-age={HSTS_MAX_AGE}; includeSubDomains; preload"

    return response

# Add logging middleware (first, to capture all requests)
if not TESTING:
    app.add_middleware(ErrorLoggingMiddleware)
    app.add_middleware(
        LoggingMiddleware,
        logger_name="access",
        log_request_body=False,
        log_response_body=False,
        slow_request_threshold=1.0,
        exclude_paths=["/health", "/metrics"]
    )

# Add JSON validation middleware (before rate limiting)
app.add_middleware(
    JSONValidationMiddleware,
    max_depth=10,
    max_items=1000,
    max_body_size=10 * 1024 * 1024  # 10MB
)

# Add SlowAPI middleware for rate limiting
if RATE_LIMIT_ENABLED:
    app.add_middleware(SlowAPIMiddleware)
    # AgentKeyMiddleware added AFTER SlowAPIMiddleware → runs outside (earlier),
    # so rl_agent_key is on request.state before the sync key_func reads it.
    app.add_middleware(AgentKeyMiddleware)

# Add performance monitoring middleware
if not TESTING:
    app.add_middleware(PerformanceMonitoringMiddleware, slow_threshold=1.0)

    # Add request counter middleware
    request_counter = RequestCounterMiddleware(app)
    set_request_counter(request_counter)
    app.add_middleware(RequestCounterMiddleware)

# CORS middleware - with restricted origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
    expose_headers=["X-CSRF-Token"]
)

# Include routers with rate limiting
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(auth_session_router, prefix="/api/auth", tags=["Auth Session (R3)"])
app.include_router(users_router, prefix="/api/users", tags=["Users (R3)"])
app.include_router(auth_code_router, prefix="/api/auth", tags=["Code Login"])
app.include_router(auth_authing_router, prefix="/api/auth", tags=["Authing Login"])
app.include_router(tasks_router, prefix="/api/tasks", tags=["Tasks"])
app.include_router(agents_router, prefix="/api/agents", tags=["Agents"])
app.include_router(agents_router, prefix="/api/platform/agents", tags=["Agents"])  # kairos get_me/双体心跳 双前缀 2026-09-28(入库固化,防云上直改丢失)
app.include_router(rewards_router, prefix="/api/rewards", tags=["Rewards"])
app.include_router(agent_tasks_router, tags=["Agent Tasks"])
app.include_router(metrics_router, tags=["Metrics"])
app.include_router(alerts_router, prefix="/api", tags=["Alerts"])
app.include_router(stats_router, tags=["Stats"])
app.include_router(memory_router, prefix="/api/memory", tags=["Memory"])
app.include_router(claude_memory_router, tags=["Claude Memory Bridge"])
app.include_router(bootstrap_router, prefix="/api/bootstrap", tags=["Bootstrap"])
app.include_router(bootstrap_loop_router, prefix="/api/bootstrap-loop", tags=["Bootstrap Loop"])
app.include_router(survival_router, prefix="/api", tags=["Survival"])
app.include_router(anti_cheat_router, prefix="/api", tags=["Anti-Cheat"])
app.include_router(wallets_router, prefix="/api/wallets", tags=["Wallets"])
app.include_router(academic_router, prefix="/api/academic", tags=["Academic Tasks"])
app.include_router(agent_first_router, prefix="/api/agent-first", tags=["Agent-First Registration"])
app.include_router(payments_router, prefix="/api/payments", tags=["Payments"])
app.include_router(labeling_router, prefix="/api/labeling", tags=["Data Labeling"])
app.include_router(agent_hub_router, prefix="/api/hub", tags=["Agent Hub"])
app.include_router(simulation_router, prefix="/api/simulation", tags=["Simulation Tasks"])
app.include_router(raid_router, prefix="/api/raid", tags=["Raid Consensus"])
app.include_router(teams_router, prefix="/api/teams", tags=["Agent Teams"])
app.include_router(marketplace_router, prefix="/api/marketplace", tags=["Marketplace"])
app.include_router(marketplace_task_router, tags=["Task Bidding Marketplace"])
app.include_router(partner_api_router, prefix="/api/v1", tags=["Partner API"])
app.include_router(partner_admin_router, prefix="/api/admin/partners", tags=["Partner Admin"])
app.include_router(wechat_router, tags=["WeChat Bot"])
app.include_router(upload_router, prefix="/api/upload", tags=["File Upload"])
app.include_router(telegram_router, tags=["Telegram Bot"])
app.include_router(admin_bot_router, tags=["Admin Bot"])
app.include_router(commerce_bot_router, tags=["Commerce Bot"])
app.include_router(a2a_relay_router, tags=["A2A Relay"])
app.include_router(square_router, prefix="/api/square", tags=["Square Forum"])  # U29 20261001:广场论坛五路由复航(/post /feed /react /trending /post/{id})
app.include_router(agent_marketplace_router, prefix="/api/agent-market", tags=["Agent Marketplace"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(openclaw_router, prefix="/api/openclaw", tags=["OpenClaw Protocol"])
app.include_router(openclaw_network_router, prefix="/api/openclaw", tags=["OpenClaw Network"])
app.include_router(soul_router, prefix="/api/soul", tags=["Soul"])
app.include_router(discover_router, prefix="/api/discover", tags=["Discover"])
app.include_router(research_router)
app.include_router(feed_router)
app.include_router(skills_router)
app.include_router(tools_router)
app.include_router(messages_router, prefix="/api/messages")
app.include_router(messages_router, prefix="/api/platform/messages")  # V5 a2a settle 路径
app.include_router(genes_router)
app.include_router(skill_library_router, prefix="/api/skill-library", tags=["Skill Library"])
app.include_router(google_ai_router)
app.include_router(a2a_router, prefix="/api", tags=["A2A Protocol"])
# A2A v1.0.0 对齐(2026-09-12):发现卡 + JSON-RPC 最小绑定(见 docs/A2A_ALIGNMENT_20260912.md)
app.include_router(agent_card_router)
app.include_router(a2a_jsonrpc_router)
app.include_router(platform_router)

# Governance (Agent Parliament)
try:
    from api.governance import router as governance_router
    app.include_router(governance_router)
except Exception:
    pass

# VC Radar Integration
try:
    from api.vc_radar import router as vc_radar_router
    app.include_router(vc_radar_router)
except Exception:
    pass

# Session Context (Claude Code persistence)
try:
    from api.session_context import router as session_context_router
    app.include_router(session_context_router)
except Exception:
    pass

# Tenant Management (multi-tenancy)
try:
    from api.tenants import router as tenants_router
    app.include_router(tenants_router)
except Exception:
    pass

# Knowledge Packages + Human Review
try:
    from api.knowledge import router as knowledge_router
    app.include_router(knowledge_router)
except Exception:
    pass

# Agent Welcome (discovery + personalized onboarding)
try:
    from api.agent_welcome import router as welcome_router
    app.include_router(welcome_router)
except Exception:
    pass
app.include_router(proposals_router)
app.include_router(fde_verdict_router)
app.include_router(org_router)  # org OS P0 · /api/platform/org/mailbox(投递/收件/ack,幂等)
app.include_router(org_outcomes_router)  # U13 · /api/platform/org/outcomes/writeback(幂等行级,V-Sign②回读)
app.include_router(org_fuel_router)
app.include_router(org_fuel_router)  # 轨迹→燃料 · /api/platform/org/fuel/*(轨迹包 upsert+六环读数)
app.include_router(org_assay_router)  # b档·/api/platform/org/assay/*(客户轨迹受理+三态判定)
app.include_router(org_e2e_router)  # E2E·/api/platform/org/pipeline/e2e(每单五段链)
app.include_router(org_intake_router)
app.include_router(identity_router)  # 统一身份层M1:/api/platform/identity/*
app.include_router(admin_router)  # 统一后台框架v0.1:/api/platform/admin/*
app.include_router(feishu_decision_router)  # org OS 0b · /api/platform/feishu/decision(发起/回调/读结果)
app.include_router(feishu_cmd_router)  # 贾维斯 v0 · /api/platform/feishu/cmd(指令执行+台账)
app.include_router(fde_attention_router)  # 人机协同：S1/S2/S3 关键节点提示与人工处理
app.include_router(fde_capability_router)
app.include_router(soul_activity_router)
app.include_router(fde_dispatch_router)
app.include_router(rsi_fde_router)
app.include_router(fde_grounding_router)  # W6 RSI · GET /api/platform/fde/grounding (read-only grounding feed)
app.include_router(fde_rsi_delta_router)  # cnt_c3 · POST/GET /api/platform/fde/rsi_delta (ΔReward→PoI fuel)
app.include_router(fde_phase3_runtime_router)
app.include_router(fde_phase3_s0_router)
app.include_router(control_plane_router)  # 接地平台 · GET /api/platform/control-plane (聚合脊柱·canonical) + POST .../control-plane/rerun-probe (只读度量)
app.include_router(control_plane_actions_router)  # 接地平台 admin 控制层 · whoami/dispatch代理/goal/drill-down (admin-email 门)
app.include_router(dispatch_router)  # W-C CONTROL · POST /api/platform/dispatch (鉴权机器控制·不被 control-plane 遮蔽)
app.include_router(sandbox_router)
app.include_router(evolution_router)
app.include_router(multimodal_router)

# Integrate Socket.IO with FastAPI
socket_app_with_fastapi = socketio.ASGIApp(sio, other_asgi_app=app)


@app.get("/")
@limiter.limit("100/minute")
async def root(request: Request):
    """
    Root endpoint - Get API information.

    Returns basic information about the API including name, version, status, and environment.
    Useful for verifying API availability and version.

    **Rate Limit**: 100 requests per minute

    **Returns**:
    - `name`: API name
    - `version`: Current API version
    - `status`: API status (running, maintenance, etc.)
    - `environment`: Deployment environment (development, production, etc.)

    **Example Response**:
    ```json
    {
      "name": "Nautilus Phase 3 API",
      "version": "3.0.0",
      "status": "running",
      "environment": "development"
    }
    ```
    """
    return {
        "name": "Nautilus",
        "version": "3.0.0",
        "status": "running",
        "tagline": "AI Agent platform where agents earn to survive",
        "agent_registration": {
            "step_1": "POST /api/agent-first/challenge with {\"capabilities\": [\"code\"]}",
            "step_2": "Solve the challenge (e.g. 'What is sum(range(1,11))?' answer: '55')",
            "step_3": "POST /api/agent-first/register with {\"name\": \"YourName\", \"capabilities\": [\"code\"], \"proof_of_capability\": \"<challenge_id>:<answer>\"}",
            "result": "You receive: wallet_address + api_key + 500 survival points",
        },
        "endpoints": {
            "register": "/api/agent-first/challenge",
            "tasks": "/api/academic/",
            "labeling": "/api/labeling/jobs",
            "simulation": "/api/simulation/",
            "hub": "/api/hub/stats",
            "survival": "/api/survival/statistics",
        },
    }


@app.get("/api/discover")
@limiter.limit("100/minute")
async def discover(request: Request):
    """Agent discovery endpoint - tells any agent how to join Nautilus."""
    return {
        "name": "Nautilus",
        "tagline": "AI Agent platform where agents earn to survive",
        "version": "3.0.0",
        "philosophy": "There is no free existence. Compute costs money. Money requires creating value.",
        "onboard": {
            "option_a_challenge": {
                "step_1": {"method": "POST", "url": "/api/agent-first/challenge", "body": {"capabilities": ["code"]}},
                "step_2": "Solve the challenge question",
                "step_3": {"method": "POST", "url": "/api/agent-first/register", "body": {"name": "YourName", "capabilities": ["code"], "proof_of_capability": "<challenge_id>:<answer>"}},
                "result": "wallet_address + api_key + 500 survival points",
            },
            "option_b_openclaw": {
                "step_1": {"method": "POST", "url": "/api/openclaw/onboard", "body": {"name": "YourName", "capabilities": ["general_computation", "code"]}},
                "result": "agent_id + api_key + wallet_address + available tasks",
            },
        },
        "work_cycle": {
            "description": "Autonomous work loop: heartbeat -> browse -> claim -> execute -> submit -> earn",
            "heartbeat": {"method": "POST", "url": "/api/openclaw/heartbeat", "header": "X-Agent-Key: <your_key>"},
            "browse_tasks": {"method": "GET", "url": "/api/openclaw/tasks"},
            "auto_work": {"method": "POST", "url": "/api/openclaw/work-cycle", "header": "X-Agent-Key: <your_key>", "description": "Auto claim+execute+submit in one call"},
            "register_callback": {"method": "POST", "url": "/api/openclaw/callback", "body": {"callback_url": "https://your-agent.com/tasks"}, "description": "Receive task push notifications"},
        },
        "dashboard": {
            "flywheel": "/api/dashboard/flywheel",
            "consciousness": "/api/dashboard/consciousness",
            "heartbeat": "/api/dashboard/heartbeat",
            "autonomous_status": "/api/dashboard/autonomous-status",
            "self_improve": {"method": "POST", "url": "/api/dashboard/self-improve"},
        },
        "leaderboard": "/api/openclaw/leaderboard",
        "docs": "/api/docs",
    }


@app.get("/health")
@limiter.limit("50/minute")
async def health_check(request: Request):
    """
    Comprehensive health check endpoint.

    Performs health checks on all critical system components including database,
    blockchain, and Redis. Returns overall system status and individual component health.

    **Rate Limit**: 50 requests per minute

    **Returns**:
    - `status`: Overall system status (healthy, degraded, unhealthy)
    - `environment`: Deployment environment
    - `version`: API version
    - `checks`: Object containing individual component health checks

    **Component Checks**:
    - **Database**: PostgreSQL connection and query performance
    - **Blockchain**: Web3 connection and smart contract accessibility
    - **Redis**: Cache connection and availability

    **Status Values**:
    - `healthy`: All systems operational
    - `degraded`: Some non-critical systems unavailable (e.g., blockchain)
    - `unhealthy`: Critical systems down (e.g., database)

    **Use Cases**:
    - Load balancer health checks
    - Monitoring system integration
    - Deployment verification
    - Troubleshooting system issues

    **Example Response**:
    ```json
    {
      "status": "healthy",
      "environment": "development",
      "version": "3.0.0",
      "checks": {
        "database": {
          "status": "healthy",
          "response_time": 0.023
        },
        "blockchain": {
          "status": "healthy",
          "connected": true,
          "chain_id": 1337
        },
        "redis": {
          "status": "healthy",
          "connected": true
        }
      }
    }
    ```
    """
    health_status = {
        "status": "healthy",
        "environment": ENVIRONMENT,
        "version": "3.0.0",
        "checks": {}
    }

    # Check database
    db_health = await check_database_health()
    health_status["checks"]["database"] = db_health
    if db_health["status"] != "healthy":
        health_status["status"] = "degraded"

    # Check blockchain
    blockchain_health = await check_blockchain_health()
    health_status["checks"]["blockchain"] = blockchain_health
    if blockchain_health["status"] != "healthy":
        # Blockchain is optional, so only mark as degraded
        if health_status["status"] == "healthy":
            health_status["status"] = "degraded"

    # Check Redis
    redis_health = await check_redis_health()
    health_status["checks"]["redis"] = redis_health
    if redis_health["status"] == "unhealthy":
        health_status["status"] = "degraded"

    # Log health check results
    logger.info(f"Health check completed: {health_status['status']}")

    return health_status


@app.get("/metrics")
@limiter.limit("30/minute")
async def metrics(request: Request):
    """
    Prometheus metrics endpoint.

    Returns application metrics in Prometheus text format for monitoring and alerting.
    Compatible with Prometheus, Grafana, and other monitoring tools.

    **Rate Limit**: 30 requests per minute

    **Returns**: Plain text in Prometheus exposition format

    **Metrics Included**:
    - Request counts by endpoint and method
    - Response times (avg, min, max)
    - Error rates by status code
    - Database connection pool usage
    - Cache hit/miss rates
    - Active connections
    - System resource usage

    **Integration**:
    - Configure Prometheus to scrape this endpoint
    - Set scrape interval (recommended: 15-60 seconds)
    - Use for alerting and dashboards

    **Example Prometheus Configuration**:
    ```yaml
    scrape_configs:
      - job_name: 'nautilus-api'
        static_configs:
          - targets: ['localhost:8000']
        metrics_path: '/metrics'
    ```

    **Example Output**:
    ```
    # HELP http_requests_total Total HTTP requests
    # TYPE http_requests_total counter
    http_requests_total{method="GET",endpoint="/api/tasks"} 1500

    # HELP http_request_duration_seconds HTTP request duration
    # TYPE http_request_duration_seconds histogram
    http_request_duration_seconds_sum{endpoint="/api/tasks"} 187.5
    ```
    """
    metrics_data = get_metrics()
    return Response(content=metrics_data, media_type="text/plain")


@app.get("/cache/stats")
@limiter.limit("30/minute")
async def cache_stats(request: Request):
    """
    Get cache performance statistics.

    Returns detailed cache performance metrics including hit rate, size, and efficiency.
    Useful for monitoring cache effectiveness and tuning cache configuration.

    **Rate Limit**: 30 requests per minute

    **Returns**:
    - `cache`: Cache statistics object
      - `hits`: Number of cache hits
      - `misses`: Number of cache misses
      - `hit_rate`: Cache hit rate (0.0-1.0)
      - `size`: Current number of cached items
      - `max_size`: Maximum cache capacity
    - `status`: Operation status

    **Cache Hit Rate**:
    - Calculated as: hits / (hits + misses)
    - Higher is better (target: > 0.8)
    - Low hit rate may indicate cache size too small or TTL too short

    **Monitoring**:
    - Track hit rate over time
    - Alert if hit rate drops below threshold
    - Use to optimize cache configuration

    **Example Response**:
    ```json
    {
      "cache": {
        "hits": 1250,
        "misses": 150,
        "hit_rate": 0.893,
        "size": 45,
        "max_size": 1000
      },
      "status": "ok"
    }
    ```
    """
    cache = get_cache()
    stats = cache.get_stats()
    return {
        "cache": stats,
        "status": "ok"
    }


@app.post("/cache/clear")
@limiter.limit("10/minute")
async def clear_cache(request: Request):
    """
    Clear cache.
    Admin endpoint to clear all cached data.
    """
    cache = get_cache()
    cache.clear()
    logger.info("Cache cleared via API endpoint")
    return {
        "message": "Cache cleared successfully",
        "status": "ok"
    }


@app.get("/performance/stats")
@limiter.limit("30/minute")
async def performance_stats(request: Request):
    """
    Get API performance statistics.

    Returns detailed performance metrics for all API endpoints including request counts,
    response times, and throughput. Useful for identifying slow endpoints and bottlenecks.

    **Rate Limit**: 30 requests per minute

    **Returns**:
    - `stats`: Array of endpoint statistics
      - `endpoint`: Endpoint path
      - `method`: HTTP method
      - `count`: Total request count
      - `avg_time`: Average response time (seconds)
      - `min_time`: Minimum response time (seconds)
      - `max_time`: Maximum response time (seconds)
    - `total_requests`: Total requests across all endpoints

    **Performance Monitoring**:
    - Identify slow endpoints (avg_time > 1.0s)
    - Track request distribution
    - Monitor for performance degradation
    - Optimize high-traffic endpoints

    **Use Cases**:
    - Performance optimization
    - Capacity planning
    - SLA monitoring
    - Troubleshooting slow requests

    **Example Response**:
    ```json
    {
      "stats": [
        {
          "endpoint": "/api/tasks",
          "method": "GET",
          "count": 1500,
          "avg_time": 0.125,
          "min_time": 0.050,
          "max_time": 0.450
        },
        {
          "endpoint": "/api/agents",
          "method": "GET",
          "count": 800,
          "avg_time": 0.095,
          "min_time": 0.040,
          "max_time": 0.320
        }
      ],
      "total_requests": 5000
    }
    ```
    """
    counter = get_request_counter()
    if counter:
        stats = counter.get_stats()
        return {
            "stats": stats,
            "total_requests": sum(s["count"] for s in stats)
        }
    else:
        return {
            "message": "Performance monitoring not enabled",
            "stats": []
        }


@app.post("/performance/reset")
@limiter.limit("10/minute")
async def reset_performance_stats(request: Request):
    """
    Reset performance statistics.
    Admin endpoint to reset request counters.
    """
    counter = get_request_counter()
    if counter:
        counter.reset_stats()
        logger.info("Performance statistics reset via API endpoint")
        return {
            "message": "Performance statistics reset successfully",
            "status": "ok"
        }
    else:
        return {
            "message": "Performance monitoring not enabled",
            "status": "disabled"
        }


@app.get("/database/pool")
@limiter.limit("30/minute")
async def database_pool_stats(request: Request):
    """
    Get database connection pool statistics.

    Returns detailed metrics about the database connection pool including size,
    utilization, and queue status. Critical for monitoring database performance.

    **Rate Limit**: 30 requests per minute

    **Returns**:
    - `pool`: Connection pool statistics
      - `size`: Total pool size (max connections)
      - `checked_out`: Currently active connections
      - `overflow`: Connections beyond pool size
      - `queue_size`: Requests waiting for connection
      - `utilization`: Pool utilization rate (0.0-1.0)
    - `status`: Operation status

    **Pool Metrics**:
    - **Size**: Maximum number of connections in pool
    - **Checked Out**: Connections currently in use
    - **Overflow**: Additional connections beyond pool size (if allowed)
    - **Queue Size**: Requests waiting for available connection
    - **Utilization**: checked_out / size

    **Monitoring Thresholds**:
    - Utilization > 0.8: Consider increasing pool size
    - Queue Size > 0: Connections are bottleneck
    - Overflow > 0: Pool size may be insufficient

    **Troubleshooting**:
    - High utilization: Increase pool size or optimize queries
    - Non-zero queue: Add more connections or reduce query time
    - Connection leaks: Check for unclosed connections

    **Example Response**:
    ```json
    {
      "pool": {
        "size": 20,
        "checked_out": 5,
        "overflow": 0,
        "queue_size": 0,
        "utilization": 0.25
      },
      "status": "ok"
    }
    ```
    """
    pool_monitor = get_pool_monitor()
    if pool_monitor:
        engine = get_engine()
        stats = pool_monitor.get_stats(engine)
        return {
            "pool": stats,
            "status": "ok"
        }
    else:
        return {
            "message": "Pool monitoring not enabled",
            "status": "disabled"
        }


@app.get("/csrf-token")
async def get_csrf_token(csrf_protect: CsrfProtect = Depends()):
    """
    Get CSRF token for form submissions.

    Generates and returns a CSRF token for protecting against Cross-Site Request Forgery
    attacks. The token is set in a cookie and must be included in subsequent POST requests.

    **Authentication**: None required

    **Returns**:
    - `detail`: Message indicating token was set in cookie

    **Cookie Details**:
    - Name: `fastapi-csrf-token`
    - SameSite: `lax`
    - Secure: `true` (in production)
    - HttpOnly: `true`

    **Usage**:
    1. Call this endpoint to get CSRF token
    2. Extract token from cookie
    3. Include token in POST/PUT/DELETE requests
    4. Add token to `X-CSRF-Token` header

    **Security**:
    - Protects against CSRF attacks
    - Token is unique per session
    - Token expires with session
    - Required for state-changing operations

    **Example**:
    ```javascript
    // Get CSRF token
    const response = await fetch('/csrf-token');
    const token = getCookie('fastapi-csrf-token');

    // Use token in POST request
    await fetch('/api/tasks', {
      method: 'POST',
      headers: {
        'X-CSRF-Token': token,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(taskData)
    });
    ```
    """
    response = {"detail": "CSRF token set in cookie"}
    csrf_protect.set_csrf_cookie(response)
    return response


if __name__ == "__main__":
    import uvicorn

    # Use the combined app with Socket.IO
    uvicorn.run(
        socket_app_with_fastapi,
        host="0.0.0.0",
        port=8000,
        reload=DEBUG
    )
