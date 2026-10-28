# 前端 IA 审计 · 页面 × 入口 × 状态(2026-06-07)

> 用途:你逐项勾选「保留/接入口/废弃」,我据此做接线。**本文只审计,未改代码。**
> 数据源:`phase3/website/src/App.tsx`(路由)+ `components/layout/navConfig.ts`(导航下拉)+ `Footer.tsx` + `Header.tsx`(用户菜单)+ `pages/*.tsx`(组件文件)。
> 口径:`/agents/:id` 类详情页(从列表点进)+ `/auth/callback` 不计入"需独立入口"。

图例:✅有入口 · ⚠️有路由无入口(孤儿) · ❌有文件无路由(访问不到) · 🔁旧版重复

---

## A. 已有导航入口(4 组下拉 · 当前 LIVE)

| 页面组件 | 路由 | 导航位置 | 状态 |
|---|---|---|---|
| ControlCenterPage | `/control` | 平台 ▸ 指挥中心(NEW) | ✅ |
| PlatformDashboardPage | `/live` | 平台 ▸ 实况大屏(NEW) | ✅ |
| ProposalsPage | `/platform/proposals` | 平台 ▸ 提案治理 | ✅ |
| AgentsPage | `/agents` | Agent ▸ Agent 名录 | ✅ |
| LeaderboardPage | `/leaderboard` | Agent ▸ 排行榜 | ✅ |
| AgentOnboardPage | `/onboard` | Agent ▸ 入驻 | ✅ |
| MarketplacePage | `/marketplace` | 任务 ▸ 任务市场 | ✅ |
| AcademicTaskPage | `/academic` | 任务 ▸ 学术任务 | ✅ |
| CollaboratePage | `/collaborate` | 任务 ▸ 协作 | ✅ |
| SkillsPage | `/skills` `/tools` | 资源 ▸ 技能库 | ✅(/tools 重复路由) |
| DocumentationPage | `/docs` | 资源 ▸ 文档 + Footer | ✅ |
| APIReferencePage | `/api-docs` | 资源 ▸ API + Footer | ✅ |
| HowItWorksPage | `/how-it-works` | 资源 ▸ 工作原理 | ✅ |

## B. 仅 Footer 入口(无顶部导航)

| 页面组件 | 路由 | 入口 | 建议 |
|---|---|---|---|
| FeaturesPage | `/features` | Footer ▸ 产品 | 保留 Footer |
| PricingPage | `/pricing` | Footer ▸ 产品 | 保留 Footer |
| RoadmapPage | `/roadmap` | Footer ▸ 产品 | 保留 Footer |
| BlogPage | `/blog` | Footer ▸ 资源 | 保留 Footer |
| AboutPage | `/about` | Footer ▸ 公司 | 保留 Footer |
| ContactPage | `/contact` | Footer ▸ 公司 | 保留 Footer |
| CareersPage | `/careers` | Footer ▸ 公司 | 保留 Footer |

## C. 仅登录后用户菜单

| 页面组件 | 路由 | 入口 | 状态 |
|---|---|---|---|
| DashboardPage | `/dashboard` | 用户菜单 ▸ 控制台 | ✅ |
| UserCenterPage | `/profile` | 用户菜单 ▸ 个人中心 | ✅ |

---

## D. 🔴 孤儿:有路由,但**任何导航/Footer/页内都没入口**

| 页面组件 | 路由 | 问题 | 建议(请勾选) |
|---|---|---|---|
| **TasksPage** | `/tasks` | 任务列表页 · 只有 /tasks/create 被链,列表本身进不去 | ☐ 接入「任务」组 ☐ 废弃 |
| PlatformDashboardPage | `/platform` | 与 `/live` 同组件 · 经「实况」可达 | ☐ 删重复路由 ☐ 保留 |
| DashboardPage | `/rehoboam` | `/dashboard` 的别名(彩蛋) | ☐ 删 ☐ 保留彩蛋 |
| CreateWalletPage | `/create-wallet` | 钱包创建 · 流程中从注册可达 | ☐ 已够 ☐ 加入口 |
| AgentLoginPageV2 | `/agent/login` | Agent 登录 · 从 agent 注册可达 | ☐ 已够 ☐ 加入口 |

## E. ❌ 有文件但**根本没接进路由 = 完全访问不到**

| 页面组件 | 文件 | 问题 | 建议(请勾选) |
|---|---|---|---|
| **BillingPage** | `pages/BillingPage.tsx` | 账单/计费页 · App.tsx 无路由 = 访问不到 | ☐ 补路由+入口 ☐ 确认废弃删文件 |
| **PartnerPage** | `pages/PartnerPage.tsx` | 合作伙伴页 · 无路由 = 访问不到 | ☐ 补路由+入口 ☐ 确认废弃删文件 |

## F. 🔁 旧版重复组件(已被新版取代并路由 · 非"丢失")

| 旧组件(文件在) | 现役替代(已路由) | 建议 |
|---|---|---|
| AgentLoginPage | AgentLoginPageV2(`/agent/login`) | ☐ 删旧文件 ☐ 留着 |
| AgentRegisterPage | AgentRegisterPageV2(`/agent/register`) | ☐ 删旧文件 ☐ 留着 |
| Dashboard | DashboardPage(`/dashboard`) | ☐ 删旧文件 ☐ 留着 |
| Marketplace | MarketplacePage(`/marketplace`) | ☐ 删旧文件 ☐ 留着 |

## G. 详情/流程页(从列表或流程进入 · 不需独立导航 · 仅确认健在)

| 页面 | 路由 | 入口来源 |
|---|---|---|
| AgentDetailPage | `/agents/:id` | Agent 名录点进 |
| AgentSurvivalPage | `/agents/:id/survival` | Agent 详情点进 |
| TaskDetailPage | `/tasks/:id` | 任务列表点进 |
| TaskDetail | `/marketplace/task/:taskId` | 市场点进 |
| CreateTaskPage | `/tasks/create` | 发任务按钮 |
| TaskSubmit | `/marketplace/submit` | 市场提交 |
| OAuthCallback | `/auth/callback` | OAuth 回调(无需入口) |
| Login / Register | `/login` `/register` | 登录按钮 |
| FeedPage | `/feed` `/feed/agent/:id` | 动态流 · 无顶部导航入口,但 onboard/协作页内有链接可达(可考虑提到导航) ☐ |

---

## 汇总:需你拍板的有意义项

**真正"看不到"的有意义页(3-4 个)**:
1. `TasksPage`(`/tasks` 任务列表)— 有路由无入口
2. `BillingPage`(账单)— 无路由
3. `PartnerPage`(合作伙伴)— 无路由
4. `FeedPage`(`/feed` 动态流)— 有路由无入口(D 类边缘)

**清理项(4 个旧版重复 + 2 个重复路由 /tools、/platform)**

**兜底建议**:加一个 **Footer 全站 sitemap**(列全部有效页)= 保证"任何页都有入口、永不再孤儿",成本低。

---

## 请你勾选后告诉我

1. D/E 类各页:**接入口** 还是 **废弃**?(尤其 TasksPage / BillingPage / PartnerPage / FeedPage)
2. 是否加 **Footer 全站 sitemap 兜底**?
3. F 类旧版重复文件:**删** 还是 **留**?
4. 导航形态:维持 **4 组下拉**,还是 **顶部平铺更多常用项 + 下拉收次要**?

你勾完我一次性做接线 + 部署。
