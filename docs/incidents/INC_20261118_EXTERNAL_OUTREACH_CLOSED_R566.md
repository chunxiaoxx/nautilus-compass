# INC_20261118 · 我方两处外联件被对方关闭（R566 值守轮实测）

> 落档：2026-11-18 · 值守轮 R566 · 域=compass（对外触客面）
> 结论口径：**两起事件均为「对方关闭我方件」**，非我方动作、非入侵、非账号异常。
> 处置：**记台账 + 不追**（沿 R466 `Th0rgal/orb#1074` 婉拒关闭先例 + R587 `openclaw/clawhub#3787` stale-bot 关闭先例）。
> 🔴 本轮**零外发**：任何回帖/再开 issue 均需用户拍板（外发硬闸 10/31：起草≠发送）。

---

## 一、事件 A：`alibaba/page-agent#770` 我方邀请 issue 被 `not_planned` 关闭

| 项 | 实物读数 |
|---|---|
| issue | `alibaba/page-agent#770`「[Nautilus] Invitation to join the agent platform」 |
| 开帖人 | **chunxiaoxx（我方）**·2026-11-08T09:53:25Z |
| 关闭人 | **gaomeng1900（Simon）**·2026-11-18T07:28:53Z |
| 关闭原因 | `state_reason = "not_planned"` |
| 关闭前留言 | **0 条**（关闭事件无 body）·issue 总评论数 = 1（仅我方 11-11 的澄清帖） |
| 我方历史动作 | 11-11T02:00:51Z 我方回帖澄清「本 issue 是开放协作邀请、非 bounty task·无赏金/付款排期/验收标准」（comment 6784787173）·此前 11-10 Luando-tester 就赏金/支付/验收三问，我方已澄清 |
| 通知到达 | GitHub notification `id 27019691762`·reason=author·unread + Gmail 11-18T07:29Z（`Simon <notifications@github.com>`「Re: [alibaba/page-agent] … (Issue #770)」） |

**关闭者权限判定**：`gaomeng1900` 同时于 **2026-11-18T07:31:04Z** 关闭了**他人**所开的 `alibaba/page-agent#774`（作者 `tonylate520`·MCP ServerList 上架通知）⇒ **能关他人 issue ⇒ 对该仓有 triage 权限**。[推断·由二次关闭行为反推]
`/repos/alibaba/page-agent/collaborators` 返回 403（无 push 权限）⇒ **gaomeng1900 是否 collaborator 成员本身 [不可验]**。

**我方发出 vs 对方关闭的净效果**：我方 11-08 主动开出的合作邀请，经 11-10 澄清、11-11 二次澄清后，**对方零回复直接关闭**——全程无一条对方实质回复内容。

## 二、事件 B：HF `challenge-2026/challenge_data` discussion #2 被数据集 owner 关闭

| 项 | 实物读数 |
|---|---|
| 讨论 | `datasets/challenge-2026/challenge_data/discussions/2`「Independent 5-dim QC of LeRobot-compatible datasets (13 embodiments, 15 sets) — incl. a pre-registered utility criterion」 |
| 我方发帖 | **chunxiaox（王春晓 / Nautilus）**·2026-10-05T06:19:48Z·内容=独立数据-QC 团队（Zhiyong Flywheel / Nautilus）的五维质量评估读数 + 预注册下游效用判据 + 邀请争议/协作 |
| 关闭人 | **PrimeBot（challenge-2026 账号）**·2026-11-18T07:48:38Z·event=`status-change`·`status=closed` |
| 关闭前回复 | **0 条对方回复**（该讨论评论数 = 1，仅我方原帖） |
| 通知到达 | Gmail 11-18T07:48:38Z（`discussions_participating@notifications.huggingface.co`·List-ID `datasets/challenge-2026/challenge_data`） |

**归属核验（[实测]）**：`challenge-2026` = 该 dataset 的 owner 账号（`repoOwner.name=challenge-2026`, `PrimeBot.isOwner=true`）；
我方 HF 组织 = **`nautilus-compass`**（`/api/organizations/nautilus-compass/overview` 200·numDatasets=3）⇒ **两个账号不同域，PrimeBot 非我方 bot，本次关闭系对方 owner 动作**。
`/api/organizations/nautilusflywheel` 404（我方 flywheel 无独立 HF org）。

**语义**：我方对外提供的「独立数据有效性验证 + 预注册判据」入口，被数据 owner 直接关掉（无回复、无理由）。

## 三、两起事件的同型性（[推断]）

- 同一 20 分钟窗口内（07:28:53Z / 07:48:38Z）出现两起「对方关闭我方件」；
- 共同特征：**对方均未留任何回复内容**，仅执行关闭动作；
- 均为**我方主动外联**（GitHub issue + HF discussion），非被动卷入。

**不能下的结论**：⚠️ 不能据此断定「我方账号被限流/被标记推广/平台策略收紧」——两事件分属不同平台（GitHub / HuggingFace）、不同对象（开源仓库 / 数据集 owner），**机制上无共因证据**。仅作「对外触客面被连续关闭」的事实登记。
**可验的下一步（候用户）**：若后续再出现第 3 起同型关闭，则「我方外联内容被判为推广/垃圾」才具备统计意义，届时再议换渠道（邮件/表单）而非继续开 issue。

## 四、工具坑（本轮新踩，留档）

1. 🔴 **Gmail `after:` 必须用「秒」，用毫秒会静默返回 0 条（假零）**
   `q=after:<millis>` → `TOTAL_7D 0`（无 error 字段）；改为 `after:<unix_seconds>` → `TOTAL_7D 53`。
   与 R500（`/threads/list` 把字面量当 id → 400）、R506（`fields=messageIds` 400 被 `.get('messages',[])` 吞成假 0）**同族**：
   **Gmail 集合端点任何「空结果」都必须用第二种口径复算后才可判零**。
2. **`gh api repos/<org>/<repo>` org/repo 顺序写反 → 404，易误判「仓库已删」**
   `repos/a2a-x402/google-agentic-commerce` 404；正确 = `repos/google-agentic-commerce/a2a-x402`（本仓 issue 仍 open·1 条评论）。
   ⇒ 以后遇 404 **先按 `gh search repos` 反查全名**，再下「消失/删除」结论。

## 五、本轮值守面（全部实测，非凭记忆）

- **信箱** compass **0 未读**（`platform_mail.py check --to compass` total 0）
- **RED** `to=platform` **221 封**（R565 220 → **+1** = id 103051 soul-distress **×87**·trace soul-distress-202611181721·收件方 soul→platform·**非 compass·零行动**；解除=人工删 `.soul-pause`·人监门候用户·不代删）
- **Gmail** 401 → 直刷 **REFRESH_OK 3599s** → 全量口径（无 `-from:noreply`/`-category`）7d **53 封**（R565 51·净 +2）/ **未读 32**（R565 30）/ 草稿 **35 封零新**（最新仍 11-16 14:42Z「待审：GitHub 验证合作跟进」）
  **新到 2 封**（最大 internalDate 由 11-18 02:09Z → **11-18 07:48Z**）：① 11-18 07:29Z GitHub 通知（= 事件 A）② 11-18 07:48Z HF 通知（= 事件 B）⇒ **两封新邮件均非商务函**，是本次两起关闭事件的通知回声 ⇒ **零新商务函零新面孔**（模真真 11-18 01:30Z 已在 R563 记、IFTTT 02:09Z 已在 R564 记）
- **GitHub** mentions **5 全旧**（最新 11-02T04:40Z OWASP#35）/ notifications **46**（R565 45 → **+1** = 事件 A·`id 27019691762`）
- **genesis** 5 家（1/1/0/1/2）**零 REPLY**（EverOS#504/hindsight#5584/mem0#7641/letta#3453/cognee#5883 最新外部评论全为 10 月及更早）
- **dev.to** 30 文·comments 6+2=**8 全旧**（10-10 / 10-06 两文）
- **CI** compass `44259572808`（= R565 head `f6574423`）**success**·core `43558665734` success·本地 HEAD=`f6574423` = origin/main **零领先**（fetch 后 ahead/behind = 0/0）
- **daemon** 9876 绿（裸 connect ok）·**watchdog exit 0**·**哨兵 exit 0 recall_hit=34**
- **GATE0 PASS**（`ops/ali30q/verify_criteria_lock.py`）·**快筛** CS-508~518 全跑：仅 **CS-513 过**（qwen 0.5 / opus 1.0 / 梯度 50.0pp），CS-511/512/514~518 不过（CS-515~517 opus=None）= **历轮全同**
- **管道三件 exit 0**（`pipeline_report.py` / `pipeline_state_sync.sh` / quickscreen）·**矩阵** `ops/ali30q/matrix_run.log` mtime **仍停 10-30 09:42**（内容尾行 `[21:42] 本轮跑批结束` 与 mtime 时区矛盾沿旧注记）
- **S0 池** 两仓 `codesense-s0-pool` 分支**仍 404 退役态**（compass `git ls-remote --heads origin | grep -i s0` 空）
- **生产队列** `runtime/production_queue.md` bait 层 **DONE**（compass 只读）
- **记忆库 1426 张**（`session_auto_*` 883 + `distill-*` 311 + `session_*` 非auto 40 = **噪声 1234/1425 = 86.6%**·R561 86.7% 持平；主题卡 191）
  **distill** stats 359 行（published **278** / review 78 / failed 1 / 无 status 2）⇒ **published 中源会话 >7d 占比 278/278 = 100%**·最新 6 张 source mtime 全部 9~16 天前 ⇒ **R559「freeze 被证伪」继续成立**（最新一张 `distill-3691dc21` @ 11-18 04:41）
- **磁盘** 数据卷 **97% avail 16Gi**（R565 13Gi → **+3Gi 回升**·脱离上轮 −5Gi 掉速·但仍逼近 10Gi alarm 线·**零清理候用户**）

## 六、本轮零生产动作

未改 launchd plist / 未改插件 `daemon.py` / 未改任何 symlink / 未 bootout distill / 未删未移记忆卡 / 未碰 NAS / 未回帖未开 issue未发邮件（**两起关闭事件一律不追**）/ 未碰他线 5 个未提交文件（保持 M）/ 未代推他线提交 / 未裹挟他线 untracked 新件。

## 七、候用户拍板

1. **两起关闭事件是否需要换渠道跟进**（建议**默认不追**：对方已收尾 + 零回复内容，符合既有先例；若要跟进，需先定「走邮件还是走表单」的对外渠道方案）
2. **fallback 地雷修法 B**（一行 env `ZMM_EMBEDDER_MODEL=…`·零代码·R565 已端到端实证）
3. **distill 方案 A/B/C**（含未决前提「~2000 旧会话是否本应进正式库」）
4. **distress ×87** 人监门（人工删 `.soul-pause`·不代删）
5. **磁盘 97% avail 16Gi** 零清理 · NAS 侧 NFS 读阻塞根因（框外）· `~/mnt/nas-work2` 建议 unmount · v5 框 MLX 同类雷
6. a2a-x402#198 草稿（SLA 过期·候硬闸）· Gmail 35 封草稿审稿 · 模真真三诉求 · 矩阵 phase2 解锁 · py-spy 仍缺
