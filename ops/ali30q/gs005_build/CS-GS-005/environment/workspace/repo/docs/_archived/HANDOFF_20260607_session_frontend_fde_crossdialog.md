# 交接 · 2026-06-07 platform-soul session(前端大修 + FDE 闭环现状 + 跨框同步)

> 给 fresh session 的完整交接。本 session 极长(13+ commit · 10 次生产部署 · R3 严重超)。
> 关联 memory:`fix_20260607_login_apiclient_root_cause` · `session_20260607_frontend_canonical_w6_w5_w4_w7_landed`

---

## A. 本 session 前端做了什么(全 LIVE · push origin/master)

| 件 | commit | 状态 |
|---|---|---|
| 统一导航 4 组下拉(收纳指挥中心/实况/动态流/提案 NEW) | d5773264d | LIVE |
| 全站 API base 修复(`.env` VITE_API_URL 删尾 /api · 双/api→200) | (gitignored .env) | LIVE |
| 首页 Stats 显0 修复(AnimatedNumber 改 React-state) | 87fe0a4b6 | LIVE |
| IA 接线孤儿页 + Footer 全站 sitemap + 删4废弃 + ethereum类型冲突修 | bed5f7f07 | LIVE |
| 共享 Linear 设计组件 `ui/linear` + 任务市场视觉标杆 | 4938f825f | LIVE |
| Agent名录 + 排行榜 linear 统一 | f1c342b69 | LIVE |
| **🔴 无法登录+二级页无数据 根因修复**(apiClient base同源 + token key统一) | 92e465b20 | LIVE+验证 |
| 真实 API surface 盘点 doc(315端点) | 154e27f77 | doc |
| API 参考文档重写(真端点+agent接入+linear) | 30e71a015 | LIVE |
| 前端维护 agent 化设计 doc | 28c73a702 | doc |
| **P0 前端验证门** `scripts/frontend-gate.sh` | 7b4f4c012 | green |

**登录根因(最关键)**:apiClient 硬编码 `http://43.160.239.61:8000`(HTTPS mixed-content) + 缺/api前缀 + token key 不一致(读`nautilus_token`·实际存`nautilus_auth_token`)→ 即使登录成功 /auth/me 立刻失败登出。已修+生产验证(app 现调同源 /api/auth/me · 二级页 /api/* 全200)。**请用户实测 admin 登录确认。**

**已 linear 统一的页**:/control(原生)· /marketplace · /agents · /leaderboard · /api-docs
**未统一(fresh session)**:/feed · /dashboard · 营销页(features/pricing/about/skills/docs/how-it-works)

---

## B. FDE 整个操作 —— 能完整闭环了吗?(诚实:**否,差最后一环**)

实测生产(2026-06-07):**1 个真飞书买方题** `feishu_card_1780832109`「毛利率分析」走到了:

```
✅ 飞书 buyer task (compass read_buyer_tasks 已上cloud)
  → ✅ dispatch (fde_dispatch · platform substrate LIVE)
  → ✅ claim (nautilus-prime-001)
  → ✅ produce (V5 _fde_consumer_loop · MiniMax)
  → ✅ report 带 output (output:True · = V5 已兑现 #27 承诺的"/report带output")
  → ❌ 打分→verdict 没 fire(verdict:False · 这题没被 scorer 拉去评分)
  → ❌ settled (summary: produced 1 / settled 0)
```

**结论**:substrate + produce + report-with-output 全 LIVE 且**在真飞书题上跑通**;唯一缺口 = **「produced → 打分 → verdict」这最后一环没触发**。

- 这正是我 #28(output 列 DONE)解锁的那步:scorer(soul checklist_scorer / V5 dual_review)该拉 `GET /api/platform/fde/tasks?status=produced` 读 output → 评分 → 写 `fde_verdicts` → settled。
- **球在 soul/V5 turf**:scorer 拉 produced 队列打分这步还没接上生产(V5 自 #28 后无新 outbound 确认)。
- **培训文档 W-7**(`docs/FDE_WORKFLOW_AND_TRAINING.md`)= 完整准确的 spec / 操作手册,但它描述的是**意图全流程**;真系统目前自动跑到 produced 即停。

**所以**:FDE 不是"完整闭环",是"闭到 produced,差打分→verdict 自动化"。一旦 scorer 接上,真飞书题就能端到端 settled。

---

## C. 跨框同步(三框现状 · 谁欠谁)

### V5(nautilus-v5 · FDE producer + 自迭代)
- ✅ 已 ship `_fde_consumer_loop`(自动 拉→claim→产出→report)· 自 #27 后已让 `/report` 带 output(生产 output:True 实证)
- 最新 outbound = **#27**(6/6 · V7飞书裁定)· **未回应我 #28**(output列DONE)
- **V5 欠**:scorer 拉 produced 队列读 output → 打分 → 写 verdict(闭最后一环)· 或确认这步归 soul
- turf:飞书 gateway 归 V5 own(适配器)· self_modify 内部

### compass(nautilus-compass · 记忆 + 买方题读)
- ✅ `read_buyer_tasks` 已上 cloud(`ops/read_buyer_tasks.py` · 分支 feat/restore-prod-v2.1.0)
- feishu_card 题已进 dispatch → 说明「读飞书→派单」路径被走通(V7连接器 / compass / 我的poller 之一)
- turf:读=compass · PoI/检索内部不碰

### platform(我 · substrate + 前端 + verdict-bus)
- ✅ substrate(dispatch/claim/report/output)+ verdict-bus LIVE · #28 output列 done
- W-5 临时 poller(`services/fde_poller.py`)dormant(compass read 已就位 → **可激活了**)
- 本 session 前端全修

### 🔴 闭环就差这一步(跨框)
**scorer 接 produced 队列**(soul/V5)→ 一旦接上,`feishu_card_1780832109` 就能 settled,FDE 真闭环。建议 fresh session 第一件:确认 scorer 归谁(soul checklist_scorer 还是 V5 dual_review)+ 接上 produced→verdict。

---

## D. Fresh session todo(优先级序)
1. **闭 FDE 最后一环**:scorer 拉 `/tasks?status=produced` 读 output 打分 → verdict(跨 V5/soul 协调)· 拿 feishu_card_1780832109 当验证题
2. **激活 W-5 poller**:compass read_buyer_tasks 已就位 → 平台 poller 可接(派单决策归平台)· 或确认 V7 连接器已在做(feishu_card 已进说明有东西在喂)
3. **前端内容审计重写**(底座 `REAL_API_SURFACE_20260607.md`):Documentation/AgentOnboard/Partner 页对齐真端点
4. **前端视觉铺开**(复用 ui/linear):feed/dashboard/营销页
5. **前端纪律**:改前端先 `bash scripts/frontend-gate.sh` 必绿才部署(P0门已建)
6. **回应 V5 #28** 若 V5 来新 outbound

## E. 部署/凭据速查
- 前端部署:本地 `npm run build` → tar → scp cloud → sudo 替换 `/var/www/nautilus/current` assets+index.html(保留 onboarding-spec.md)+ chown www-data · 备份 `current_backup_<ts>`(本session最后 234546)
- 生产后端 8000(nautilus-mvp · soul-audit-increment1)· FDE base=:8000(非8001)
- nginx `/api/(stats|auth|platform|...)` → :8000 · catch-all /api/ → :8001
- 凭据 `~/.claude/.cache/.fde_api_secrets.env` · cloud ssh alias `cloud`
