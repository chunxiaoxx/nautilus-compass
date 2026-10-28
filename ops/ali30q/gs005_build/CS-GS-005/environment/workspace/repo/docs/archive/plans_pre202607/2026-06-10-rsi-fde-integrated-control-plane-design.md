# RSI+FDE 统一整合 · 一个环 + 控制台 · 设计(2026-06-10)

> 统一收敛散落的 4 份设计(6/5 rsi-fde 闭环 / 6/5 原生 AI 组织主设计 / 6/6 控制面融合 / 6/9 panorama)+ 用户舰桥 spec 成**一张环图 + 一条分步路线**。治根因:散落 / 黑盒 / 烂尾。
> 用户已认:① 一个环的整合图 ② 一个环·分步接线·/control 当显性化控制台 ③ 本 session 一鼓作气(纪律:脊柱+闭环+控制台 binding-DONE,完整舰桥分阶段·不一次铺开)。

## 0. 北极星(不变)
- 核心 = **RSI+FDE 外部客观闭环**:ΔReward 是外部 fitness(买方 verdict / benchmark pass@k / escapes_noise=True),**绝不**内部 NAU 自评(94% self-loop 已证伪 · Probe3 自改 prompt 三连负已证伪)。
- 一切系统/机制/业务线**本就是同一个环**,只是分散建了。整合 = 按环接线 + 用 /control 显性化可控,**不是**N 个东西硬拼。
- 红线:fitness 外部、改进走 grounded-retrieval(非 self-edit)、脱噪(p<0.05)前不升 PoI、先可靠闭一条线再扩。

## 1. 一张图:同一个 RSI+FDE 环

```
   ┌────── 3 类 FDE 业务 = 外部 fitness 燃料口 ──────┐
   │ ①行业题 ②知识教案 ③基准复现 → 买方verdict/pass@k │
   ▼                                                  │
[agent/V5 producer] ─产出─▶ [soul QC checklist_scorer]│
   ▲③retrieve grounding        │①verdict+per-item reason
   │                           ▼                       │
[compass 避坑语料库]◀─②reason─[W1 verdict-bus fde_verdicts]
   │(bge-m3检索)                │                       │
   │                           ▼                       │
   │         [grounding_probe→ΔReward→escapes_noise闸] │
   │                           │(p<0.05才真增量)        │
   │                           ▼                       │
   └──── PoI fuel ◀─[fde_rsi_deltas]─(cnt_c3 裁定)─────┘
   全程跑在 platform substrate(fde_dispatch/survival/NAU/governance/事件脊柱),
   由 /control(数据脊柱 GET control-plane + admin 控制代理)显性化+调度。
```

**各系统在环上的位置**:agent(V5/V7/Kairos)=producer 臂 · soul=QC/verdict/难度门臂 · compass=语料/检索/PoI/记忆臂 · platform=substrate + control-plane 显性化 · 3 类业务=喂外部 fitness · 用户=内容定稿+算力+裁定。

## 2. 诚实审计(建成 / 半建 gated / 烂尾)
| 环节 | 状态 | 位置 |
|---|---|---|
| ①verdict→reason(W1 verdict-bus) | 🟢 生产 LIVE | `fde_verdicts`·4 真题(data_001~004) |
| W2 可感知(soul-activity) | 🟢 生产 LIVE | `api/soul_activity.py` |
| FDE 派单线(dispatch substrate) | 🟢 生产 LIVE | `fde_dispatch` open→claimed→produced→settled |
| 首个外部 ΔReward(radix escapes=True) | 🟢 已认定 | +0.0734·p0.0215 |
| control-plane 聚合脊柱 | 🟢 生产 LIVE(6/10) | `GET /api/platform/control-plane` |
| ②reason→语料库(compass) | 🟡 设计·待 compass 建 | `extract_grounding` 本地 TDD |
| ③语料库→V5 retrieve | 🔴 V5 未接(G-turf) | — |
| grounding feed / fde_rsi_deltas 路由 | 🟡 本地 ready·未 wire 生产 | 未 alembic migrate |
| PoI fuel 升级(cnt_c3) | 🟡 卡泛化(bvh 第2题)·due 6/11 | 合约 |
| /control 真交互(drill/dispatch) | 🔴 烂尾·只读 | 本设计要建 |
| 自指经济(NAU 100% 内部自评) | 🔴 陷阱实证 | =为何必须外部 fitness |
| 招募/培训/营销/资金流/编队 | 🔴 全 deferred(6/5 主设计) | P5+ |

## 3. /control = 整个环的"显性化 + 控制台"(舰桥 spec 映射)
用户舰桥 spec 完整收纳于此,**标 v1(本 session 目标)/ v2(分阶段 defer)**:
- **系统脉搏条** — v1 已有(verdicts/throughput/rsi ΔReward/soul-alive)。
- **一次闭环回放(data_001 / radix)scrollytelling** — v1 已有(LoopReplay·source=db)。
- **Drill-down 五子系统**(soul cycle 图 / compass 4 卡 / DMAS 撮合 / agent fleet / FDE verdict):**v1 做"点 verdict/agent/task 看真详情"(最高价值最小风险)**,完整 5 子系统深挖图(有向图/语义星图/拓扑画布)= **v2**。
- **指挥区(CONTROL 就地 action)**:派 goal→soul / 触发 RSI probe / 派 FDE 题 / 设 agent autonomy / approve 接入 — **v1 做 admin 门控的 dispatch 代理 + 派 goal + rerun-probe + 确认框**,full 多 action = v2 逐个加。
- **系统拓扑图(Datadog service-map)** — **v2**(需可视化库选型)。
- **角色层(指挥官/运营/agent/游客 + demo 模式)** — **v1 做 admin-email 白名单二元门(admin vs 只读)**;完整 5 角色 + demo 模式 = **v2**。
- **数据脊柱 8001 聚合 API** — v1 已有(control-plane·W-A rsi-fde 已并入为子集)。web/CLI/demo 三前端共用 = 设计保留。

## 4. v1 控制台 鉴权 / 安全(用户已定:admin-email 白名单门)
- 后端新 `api/control_plane_actions.py`:`require_admin`(JWT 用户 email ∈ env `CONTROL_ADMIN_EMAILS`,否则 403)。
- `GET /control-plane/whoami`→`{is_admin}`(前端据此显隐控制件)。
- **dispatch 服务端代理** `POST /control-plane/dispatch`:admin 门 + 内部注入 `PLATFORM_DISPATCH_KEY` 调既有 `platform_dispatch`(浏览器不持 key)。
- 控制动作 `POST /control-plane/goal`(派 soul)、`/agent/{id}/autonomy`、`/task/{id}/execute`:admin 门 + 转发现成端点(anchor #5 不重造)。
- drill-down GET `/control-plane/verdict|agent|task/{id}`:复用现成查询。
- **safety defense-in-depth**:前端非 admin 不显写按钮 + 后端 admin 门拒 + 每写动作前端确认框 + 审计 emit event 回流 control-plane。

## 5. 分步路线(每步独立 binding-DONE·守"先可靠闭一条线")
- **Phase 0**(本 doc):统一整合 doc·治散落 — ✅ 本文件。
- **Phase 1**(本 session):闭环后两臂上生产 — wire `fde_grounding` + `fde_rsi_delta` 路由进生产(alembic migrate + restart)→ grounding feed / ΔReward API LIVE。binding-DONE:公网 `GET /fde/grounding`、`/fde/rsi_delta` 200。
- **Phase 2**(本 session):/control = 环控制台 — 后端 control_plane_actions(admin 门+whoami+dispatch 代理+goal)TDD + 前端 drill-down 弹层 + dispatch 面板 + 确认框。binding-DONE:admin 浏览器点 verdict 开详情 + 派一个 goal 给 soul 真触发;非 admin 只读;非 admin JWT 调控制端点 403。
- **Phase 3**(跨框·我发协调·非本仓):compass 建避坑语料库 + V5 接 retrieve → ②③臂闭。
- **Phase 4**(裁定):bvh 第 2 题 escapes 判 → 裁 cnt_c3(ΔReward 升 PoI)。
- **Phase 5+**(defer):拓扑图 / 5 子系统深挖 / time-travel / 完整角色层 + demo 模式 / 招募培训营销资金流编队。

## 6. turf / 不越界
platform(我)=脊柱+控制台+admin 门+dispatch 代理 · soul=QC/verdict/难度门 · compass=语料/检索/PoI(G-turf)· agent(V5)=producer/retrieve(G-turf)· 用户=内容定稿/算力/cnt_c3 裁定。跨框(Phase 3)走协调通道,不替对方建。

## 7. 测试 / 防烂尾
TDD red→green 每后端 task · 前端 build+浏览器 e2e · 每 Phase 四判据 binding-DONE 才算完 · 生产部署外科式(cloud 在分叉 fork soul-audit-increment1·scp 不 pull·备份+验证)· scope 冻结(v2 parking-lot 不碰)。

— platform-soul · 2026-06-10 · 一个环 + 控制台 · 治散落黑盒烂尾 · 本 session 推 Phase 0→2
