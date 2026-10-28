# /goal 机制 meta-prompt(跨对话框可复用模板 · 2026-06-17 定)

> 用途:任何 Nautilus 对话框(compass/V5/platform-soul/platform)session 收口时,照此结构生成下一会话的 `/goal` handoff。目标 = **一份提示词让 fresh session 零上下文也能无缝续上、不丢项、不假报、不越界**。
> 用法:把下面「填写指令」喂给收口的 dialog(或自己照填),产出 8 段式 /goal 文本。**先填后自检 §质量门**。

---

## 为什么是这个结构(机制原理)
/goal 解决的根问题 = **context 会丢 + 多对话框易精神分裂 + 长 session 易假报/越界/狗熊掰玉米**。所以每段都对应一个失效模式的护栏:
- 身份/turf → 防越界 + 防"本框是谁都不知道"
- 战略 anchor → 防偏离用户最新心智(anchor 会迭代·别用旧的倒批)
- LIVE/done(分级)→ 防把"文档说 LIVE"当"我亲测 LIVE"(no-live-claim)
- 优先序待办(gated vs 自主)→ 防虎头蛇尾 + 防做被阻塞的事空转
- 红线/纪律 → 把复发 anti-pattern 固化成不靠"我提醒自己"的硬规则
- 坐标 → 防重新发现/重复问/丢凭据
- 起手第一步 → 让 fresh session 0 决策成本开跑

---

## 8 段式填写指令(逐段)

**§0 你是谁 + 开场自检**
- 一句话身份 + turf 边界 + session-start 必读文件(charter + anchor)。
- 开场契约:① 第 1 个 response 必报 active anchor ② 验本框身份解析对(hook 报对框?)③ 信 hook 读未读跨框件。
- ⚠️ 不写流水账历史·只写"你是谁、读什么、先验什么"。

**§1 战略(注明用户拍板日期)**
- 用户最新战略定位 + 路线 + 本框在其中的角色。注日期(心智会变·标 anchor 来源)。
- 指向 design/plan 文件路径,不在 /goal 里展开。

**§2 上一会话 LIVE/done(🔴 分级·诚实)**
- 每条标清:✅亲测 LIVE / 🟡 armed 待点火 / 📦 代码 done 待部署 / 诚实边界(机制证≠价值证)。
- 带凭据/commit/路径/真日志片段。**禁止把"文档说"或"别人报"平铺成"我亲测"**。

**§3 下一会话待办(按优先序 · 标 gated vs 自主)**
- **P0 = 立刻/阻塞解除后第一件**(常是 restart-gated:重启后验某修复生效)。
- **P1 = 本框自主可做·不阻塞别框**(优先填这类·fresh session 不空转)。
- **P2 = 被别框/外部 gated**(写清 gate 条件 + 解除后动作链)。
- **P3 = 低优先/可选**。
- 每件写"做什么 + 验收门(怎么算真做完)+ 走哪个 skill"。

**§4 turf / 红线(收敛后净分工)**
- 各框 turf 一行 + "不重建已 live 的件"清单(防重复造轮子)。
- 谁是裁判/谁产/谁验/谁部署。

**§5 纪律(复发护栏·铁律)**
- 本项目固定:ssh heredoc 批量(fail2ban)· R3(4h 拒 ship)· "真"字≤3/段非强调副词 · LLM 脚本后台跑落日志 · 报 LIVE 前亲测 · 修补丁≠修根因 · 跨框走 `_OUTBOUND_FROM_<本框>_TO_<X>_*.md`。
- 加本线特有红线(如本轮:mint 只 mint 确认 true_wall·不 firehose)。

**§6 坐标(防丢/防重新发现)**
- memories(带日期·主入口标⭐)· skills · 关键脚本/harness 路径 · creds(只写文件位置不写明文)· infra(IP/key/endpoint·标已确认 vs 待确认)· 关键入站件名。

**§7 起手第一步(编号·0 决策成本)**
- 3-5 步有序动作,第一步永远是"报 active anchor"。

---

## 质量门(产出后自检·任一不过就回填)
1. **自包含**:fresh session 不读别的也能开跑?(身份/坐标/起手齐?)
2. **诚实分级**:每个"LIVE/done"都标了亲测/armed/待部署?有无把文档或他框的话当亲测?
3. **优先序可执行**:P0/P1 是本框现在就能动的?gated 项写清了 gate 条件?
4. **防丢**:这次新发现的凭据/路径/决策都进 §6 了?重大件落了 handoff 文件(非只在 /goal 文本)?
5. **不越界**:§4 turf 写清了·没替别框拍板?
6. **anchor 对齐**:§1 用的是用户最新拍板(非 7d+ 旧 memory)?
7. **护栏完整**:§5 覆盖了本线复发风险?
8. **简洁**:每段是"续上工作所需最小集"·没历史流水账冗余?

---

## 模板骨架(直接复制填空)
```
你 = <框> 对话框(<repo>)。第 1 个 response 必报 active anchor。
0. 你是谁 + 开场自检:turf=<...> · 读 <charter>+anchor · 开场三件<...>
1. 战略(用户 <日期> 拍板):<定位+路线+本框角色> · design:<path>
2. 上一会话 LIVE/done:✅<亲测> · 🟡<armed> · 📦<待部署> · 诚实边界<...>
3. 待办:P0<restart-gated> · P1<自主+验收门+skill> · P2<gated:条件→动作> · P3<低优>
4. turf/红线:compass=<> soul=<> V5=<> platform=<> · 不重建<live 件清单>
5. 纪律:ssh heredoc · R3 · 真≤3/段 · LLM 后台 · 报 LIVE 前亲测 · 本线特有<...>
6. 坐标:memories<⭐主入口> · skills · harness 路径 · creds<文件位> · infra<IP/key/endpoint·确认态>
7. 起手:① 报 anchor ② 信 hook 读未读 ③ P0 ④ P1 ⑤ <gate 后点火>
```
```
（产 /goal 后:重大未落地件另写 handoff md 落盘·别只活在 /goal 文本里）
```
