# 前端维护 Agent 化 · 设计文档

> 2026-06-07 · platform-soul-dialog
> 回答用户问:「前端网页的维护和优化,能不能彻底交给 soul / kairos / v5 / v7?」
> 一句话结论:**「彻底交给」(无人监督全自动)今天不现实;但「agent 主导 + 验证门 + gated 部署」可行,且是 agent-first(anchor #1)的正道。关键杠杆是验证门,不是"交给哪个 agent"。**

---

## 0. 为什么这是对的方向 + 为什么不能现在裸交

**对的方向(anchor #1 / #3)**:前端维护是典型的**重复 D 工**(改 bug、对齐文档、视觉统一、部署)。这种活长期靠人手做 = 反 anchor #3。agent-first 生态的终态就该让 agent 拥有它。

**不能裸交(诚实 · anchor #6)**:前端维护是一整条工程闭环——读大型 React/TS 代码库 → 跨层诊断 → 改 → `tsc+vite` build → ssh 部署+备份+nginx → 浏览器逐页验证 + 回滚判断 + 视觉判断。今天没有任何 agent 有这条带护栏的 harness。把无人监督的 LLM agent 直接接生产部署 = 等于撤掉 R4/备份/验证护栏。

**真根因(本设计的核心洞察)**:2026-06-07 修的一串 bug(apiClient 硬编码 `http://IP:8000` mixed-content + token key 不一致 + 双 /api + 文档过时)漏到生产,**根因不是"没 agent 修",是没有任何验证门**——没 CI、没 build 检查、没端点 smoke、没截图回归。**有门,人或 agent 维护都安全;没门,交给 agent 反而更快把回归推上生产。** 所以先建门,再谈委托。

---

## 1. 三阶段路线(从门到自治 · 不跳步)

| 阶段 | 谁主导 | 部署门 | 前置 |
|---|---|---|---|
| **P0 验证门** | 人(我/用户) | 门=本地 CI 必绿 | 无(现在就能建) |
| **P1 gated 委托** | agent 产 diff → 人 review → 部署 | 门绿 + 人点头 + draft PR(绝不 auto-merge) | P0 门存在 |
| **P2 沙箱自治** | agent 全环 | 门绿 + 沙箱预览验证 + verdict 通过 → 自动部署(限定低风险类) | P1 跑稳 + verdict 数据 |

**彻底自治 = P2 终态,不是起点。** 高风险类(auth/支付/部署脚本/nginx)永远保留人 gate。

---

## 2. P0 · 前端验证门规格(最高杠杆 · 先建这个)

一条命令 / CI 跑完即"可安全部署"的判定。任何维护者(人或 agent)都必须过门。

| 闸 | 检查 | 工具(已在仓) | 拦住今天哪个 bug |
|---|---|---|---|
| **构建** | `tsc && vite build` 必绿(0 类型错) | vite/tsc | 删废弃文件触发的 ethereum 类型冲突 |
| **单测** | `vitest run` 全绿 | vitest(已配) | navConfig/apiClient 回归(已写) |
| **Lint** | eslint(无 `console.log`/未用导入) | eslint | 未用 import(Panel)|
| **端点 smoke** | curl 生产/预览关键端点判 200 + 路径对 | bash/curl | **双 /api(/api/api/stats 404)· apiClient base 错** |
| **认证 smoke** | 设 token → `/api/auth/me` 走同源 + 带 header | playwright | **登录失效根因(base + token key)** |
| **截图回归** | MCP browser 截关键页(home/control/marketplace/api-docs)对比基线 | MCP browser | 视觉回归 / 浅色页混入 |
| **部署护栏** | 必备份 `current_backup_<ts>` + 记回滚点 | ssh(已成流程) | R4 |

> 关键:**端点 smoke + 认证 smoke 是今天那串 bug 唯一能被自动拦住的地方**。这两闸不是 unit test,是对**真实生产/预览端点**的探测。建议先做这两闸 + build/test 三件,就能拦住 80% 的"无法登录/二级页无数据"类回归。

产物:`phase3/website/scripts/frontend-gate.sh`(或 CI workflow)· 退出码 0 = 可部署。

---

## 3. P1 · Agent 委托环(FDE-style · 复用 verdict-bus)

把"前端维护 task"接进平台已有的 produce→verdict 环(anchor #5 不重造):

```
前端 issue(用户/审计/监控产)
  → dispatch 到前端维护 agent(/api/platform/fde/dispatch 同款派单)
  → agent 读 issue + 相关代码 → 产 diff(git 分支)
  → 【P0 验证门】跑 frontend-gate.sh → 产出 verdict(pass/fail + 证据:build日志/截图/smoke结果)
  → verdict 写 verdict-bus(fde_verdicts 同构 · source=frontend-maint)
  → pass → draft PR(绝不 auto-merge)→ 人点头 → 部署 + 备份
  → fail → verdict 带 fail_reason 回 agent → 下一轮(RSI:grounded-retrieval 用 fail_reason 当避坑语料)
```

**复用清单(anchor #5)**:
- 派单 = `fde_dispatch` substrate(已 LIVE)
- 验收 = `fde_verdicts` verdict-bus(已 LIVE)· verdict=门结果(客观·build/smoke/截图)而非 LLM 自评 → **天然避内部自指**(anchor #3 红线:fitness=外部客观门,非 NAU 自印)
- RSI = fail_reason → grounding 语料 → 下一轮(`design_20260605_rsi_fde_closed_loop` 同模式)

---

## 4. 哪个 agent / turf(诚实分工)

| 候选 | 适配度 | 说明 |
|---|---|---|
| **soul / V5 self_modify 延伸** | 🟢 最自然复用 | V5 已有 self_modify(白名单+git self-edits 分支+**P3 沙箱门 pytest-pass-才-deploy**)。把白名单加 `phase3/website` + 门换成前端 `frontend-gate.sh` = 直接复用它的"改码→门→gated deploy"骨架。**是 V5 turf · 需 V5 dialog 协调** |
| 新建"前端维护 capsule" | 🟡 干净但重造 | 在 hermes `nautilus-engine` runtime 上装一个 frontend-maint persona+skills(read-react/run-gate/screenshot)。不污染 V5,但要新搭 |
| Kairos | 🟡 当触发器 | 适合"发现前端 issue"(监控 500/截图异常 → 产 issue),不适合自己改码部署 |
| V7 | 🔴 不适配 | 对外 front(telegram/飞书),非 codebase 维护者 |
| 当前对话(我) | 🟢 P0/P1 执行者 | 建门 + 跑 P1 gated 委托的人侧 reviewer,直到 P2 |

**推荐**:门(P0)平台自己建;委托环(P1)复用 V5 self_modify 延伸到 website(跨框协调)或新 capsule。**不要让 soul/V5 在没有前端门的情况下改前端**——它的 pytest 门管不了前端回归。

---

## 5. 红线 / Gates(anchor #3 / 护栏)

- **G-verdict-objective**:前端 verdict 必须是**客观门结果**(build green / smoke 200 / 截图 diff),绝不渲染 LLM 自评或内部 NAU 当 fitness(重蹈 94% self-loop)。
- **G-prod**:部署仍走 R4(备份+回滚点)· auth/支付/nginx/部署脚本类 = 永久人 gate,不进 P2 自动。
- **G-no-auto-merge**:agent 产出永远 draft PR,P1 人点头 / P2 沙箱预览过 才 merge+deploy。
- **G-turf**:V5 self_modify 是 V5 own · 延伸到 website 需 V5 dialog 同意,不单方改它白名单。

---

## 6. 案例回放:今天的 apiClient bug 在这套下会怎样

- **现状(无门)**:bug 漏到生产,用户报"无法登录",我手工 systematic-debugging 修。
- **有 P0 门**:部署前 `认证 smoke` 闸会 fire——设 token → app 调的是 `http://IP:8000/auth/me`(非同源)或 `/auth/me` 404 → 闸红 → **挡在部署外**,根本到不了用户。
- **有 P1 委托**:监控/截图发现登录回归 → 派单 → agent 产 base+token 修复 diff → 门绿(smoke 通)→ draft PR → 人点头 → 部署。全程不用我手搓。

= 门是把"事后救火"变"事前拦截"的那一步。

---

## 7. 实施序(决策可用)

1. **P0-a**(小·高价值·现在就值得做):写 `frontend-gate.sh` = build + vitest + **端点 smoke + 认证 smoke**(后两闸是今天 bug 的唯一自动拦截点)。
2. **P0-b**:加截图回归基线(MCP browser 截 home/control/marketplace/api-docs)。
3. **P1**:跨框和 V5 协调——self_modify 白名单加 website + 门接 frontend-gate.sh,或新 capsule。派单走 fde_dispatch,verdict 走 verdict-bus。
4. **P2**:跑稳 + 有 verdict 数据后,低风险类(文案/样式/文档对齐)放权沙箱自动,高风险永久人 gate。

## 8. 决策点(给用户 / V5)

- **Q1**:P0 门先建吗?(我判断:**应该,且是这一切的前提**。没门谈委托=危险。)
- **Q2**:P1 走 **V5 self_modify 延伸**(复用·需 V5 协调)还是 **新前端 capsule**(干净·要搭)?
- **Q3**:P2 自动部署的"低风险类"边界划哪?(建议:仅文案/样式/文档对齐 · 不含 auth/路由/部署/nginx)

> 本 doc 只设计。落地是跨框协调 + 新基建的专门项目,不是一个 session 能 ship。建议:先 ship P0 门(平台自己能做),再带着门去和 V5 谈 P1。
