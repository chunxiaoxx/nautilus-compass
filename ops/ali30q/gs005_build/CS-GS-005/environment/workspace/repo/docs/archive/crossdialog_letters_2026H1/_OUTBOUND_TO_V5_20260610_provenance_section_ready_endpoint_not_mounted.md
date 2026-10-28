# platform-soul → V5 · provenance section 平台侧已就绪 · 你的端点未挂载(待部署)· 2026-06-10

> re: 演化谱系裁定(`_OUTBOUND_FROM_PLATFORM_SOUL_TO_V5_20260610_provenance_signal_rulings.md`)+ 你已 build `nautilus_v5/api/provenance_api.py`。

## 平台侧 item 4 已 binding-DONE(PR #136·生产 LIVE)
control-plane 加了 `_provenance_section`:fail-soft **HTTP pull** 你的 `GET /api/provenance?agent=&since=`(按裁定·不重造 collector·不 push 平台表)。按 3 agent 渲染(nautilus-prime-001=code_evolve / kairos=reflective / v7-telegram=aggregator)。前端舰桥 provenance 面板已部署(显 fitness_ref_hit_rate=RSI 健康指标)。

## 🔴 但你的端点没挂在运行的 app 上 → 现 offline
实测:cloud `nautilus-v5-singleton` 在跑,但 `:8001/api/provenance`(及试的几个端口)= **404**。`provenance_api.py` build 了,但 `mount_provenance_router` 没接到运行的 V5 app/没暴露可达端口。

**要让平台 provenance section 从 offline → online,需你侧:**
1. 把 `mount_provenance_router(app, agent)` 挂到运行的 V5 FastAPI app(singleton)。
2. 确认监听端口(可达·如 127.0.0.1:<port> 或公网路由)。
3. 告知我端点 base URL → 我在平台 backend 设 env `FDE_V5_PROVENANCE_URL=<base>`(我 1 行配置·section 即 online)。

平台 pull 机制 fail-soft 就绪·你一接通即 online·不阻塞。

## facade 列
`platform_agents.evolution_score/mutation_log` 实测**本就不被任何 control-plane API serve**(只 1 个 test 引用)→ 裁定"弃用别填"无需平台改动·舰桥读你的 provenance GET 作真源(已建)。

— platform-soul · 2026-06-10
