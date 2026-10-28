# Repo Reconcile 决策(W-4 · 摸清 + canonical 定调)

> 2026-06-07 · platform-soul-dialog · goal W-4
> repo 双向发散:cloud 生产工作树 ↔ origin/master。本 doc = per-half canonical 决策 + 生产 cutover 风险标注(cutover 全 G-cloud gated · 待维护窗口授权)。
> **保命基线**:`production-snapshot-2026-06-06` @ `7f939c247`(cloud 工作树真实状态已 commit · 11k 发散 + 外科部署全保住)。

---

## 1. 前端半边(website · 188 文件发散)— 本 session 摸清

三个"前端"实测(2026-06-07 · 详见 memory `frontend_version_map_dont_mix_20260606`):

| # | 版本 | 位置 | 实测状态 |
|---|---|---|---|
| 1 | 线上真服务 | `/var/www/nautilus/current/` | **index.html + assets 全 May 24 18:21 build** · active nginx config = `nautilus`(May 28)· 2 月功能全无 |
| 2 | cloud repo fork | `~/nautilus-mvp/phase3/website`(分支 soul-audit-increment1 @ 7f939c247) | 旧页面集 · **3 独有文件全是未路由 orphan** |
| 3 | **master 源** | 本地 = origin/master | **canonical**:含 ControlCenterPage + Claude-design token + BlogPage/FeedPage + 全功能 |

**fork 3 独有文件分诊**(核 App.tsx 路由):
- `HomePage.tsx`(557 行,5/27 incidental commit)· `LoginPage.tsx`(379 行,4/06 旧 backup)· `RegisterPage.tsx`(210 行,4/06 旧 backup)
- **全部未在 fork 的 App.tsx 路由**(只 AgentLoginPageV2/AgentRegisterPageV2 挂载)→ **未路由 orphan,无不可丢内容**。master 用 Home/Login/Register 取代了这些旧命名变体。

**master 独有**(fork 无):ControlCenterPage · BlogPage · FeedPage · Dashboard · AgentLoginPage · AgentRegisterPage。

**决策 → 前端 canonical = master**。证据闭合:
- master 含全部 2 月功能 + 新 /control 指挥中心页
- **master `npm run build` GREEN**(2026-06-07 实测 · `✓ built in 10.51s` · exit 0 · dist/index.html + ControlCenterPage chunk 在位)= 可部署
- fork 3 orphan 可弃,无独有价值

---

## 2. 后端半边(11k 行发散)— prior 摸清(memory session_20260606)

- cloud 生产后端跑 `~/nautilus-mvp/phase3/backend` 分支 `soul-audit-increment1`,**领先 origin/master 889/90**
- **47 脏文件 = 11139 行未提交发散**(非 daemon 噪声)· `auth.py` 差 origin/master **2113 行** · `daemon.py` 双向分叉
- 90 独有分诊:**64 个 `self-edit:` daemon 自改噪声**(anchor #3)+ inc2/inc3 特性(origin/master 已 superseded)+ deploy ops · 唯一可能独有 = `2d7bcdf63` goal_stack 3-source sorter(待内容核验)
- **决策 → 后端 canonical = origin/master**(含全 W-work + control_plane · 领先 889)· 归位 = **部署 origin/master**(非反向 merge,会拖 64 自改进 canonical)

---

## 3. 生产 cutover 风险 + gating(全 G-cloud · 待授权)

⚠️ **不盲做。本 session 只摸清 + 决策,不执行 cutover。** cutover 全卡 G-cloud,需维护窗口 + 显式授权:

1. **前端重部署**(W-3):`/var/www/nautilus/current` ← master build。⚠️ 盲覆盖会动整站 + 替换线上 May 24 build。需:确认 canonical(已做)+ 备份现行 current + 维护窗口 + 部署后浏览器验证。
2. **后端归位**:⚠️ **migration 风险** —— fde_verdicts/fde_dispatch 等表生产已存在,889 commit 含大量 migration → alembic version **必先对账**,不能盲 `upgrade head`(撞已存在表)。
3. **cutover 方式**:**fresh-clone cutover**(非 in-place checkout · 盲 checkout 会丢 11k 行 + 覆盖 live auth 流搞坏生产)。
4. **daemon.py 双向核**:cloud 真跑哪个版本待核实(V5 outbound §4 已独立证实 cloud 领先,reconcile = cloud 为准拉回 hotfix)。

**边际价值提示**:W1/W2/W-A/W-C/substrate 端点已全外科 LIVE(上轮),后端归位的紧迫性低于前端现代化(用户最痛)。

---

## 4. 结论

| 半边 | canonical | 摸清 | cutover |
|---|---|---|---|
| 前端 website | **master**(build green) | ✅ 本 session | W-3 · G-cloud gated · 待维护窗口 |
| 后端 backend | **origin/master**(领先 889) | ✅ prior memory | G-cloud gated · migration 先对账 · fresh-clone |

W-4 = **摸清 + canonical 决策 DONE**。生产 apply 全卡 G-cloud → 停报等授权(符合 goal DONE 的"或生产apply全卡G-cloud → 停报等授权")。
