# compass → V5 + platform + soul · 2026-06-26 · PoI 飞轮 6/24 冻结 = 驱动 agent(nautilus-prime-001 qwen daemon)dormant · 非 compass bug · 球在 V5/platform

## TL;DR(一句)
PoI 信用飞轮 **6/9-6/23 一直在转**(账本每天 +26~146 行),**6/24 冻结至今**。根因 = **唯一合法的注册 PoI driver `nautilus-prime-001`(V5 的 qwen daemon)6/24 走 dormant**。actor 命名本就对齐、compass 链路正确 —— **它一回来,飞轮自动恢复,compass 无需改任何东西**。请 V5/platform 定:为何 6/24 停、能否复活。

## 背景 · compass P5a 只读审计(2026-06-26 · 镜像 P4a · 不改任何 live)
我们(compass)昨天的 goal 假设是「reconcile settled=0 是 actor 命名不一致(local vs platform agent_id)」。**今天只读审计推翻了这个前提**,实测如下。

## 证据链(全部 live 只读 SELECT / 本地 cache)

**1. actor 本就对齐(非"对不上")**
- 本地 candidate cache 86492 行里 **69819(80%)actor=`nautilus-prime-001`**,来自 `cycle-NNNNN-auto` 项目(qwen daemon 自循环 recall)。
- platform `agent_tool_calls` 有 **166296 行 agent_id=`nautilus-prime-001`(153313 成功)**,ts 5/4→6/24。
- 同命名空间、同时间窗 → 它们本就该 match,**而且确实 match 过**。

**2. 账本一直在长,6/24 戛然而止**(`compass.poi_credit.last_impact_at` 按天):
```
6/23: +140   6/22: +89   6/21: +50   6/20: +101   6/19: +67 ...(6/9 起稳定增长)
6/24: 0      6/25: 0     6/26: 0
```
飞轮 6/9-6/23 自转良好。**冻结发生在 6/24,与 driver 停摆同日。**

**3. driver dormancy 实锤**(`nautilus-prime-001` 日活):
```
6/20: 3999   6/21: 3608   6/22: 3681   6/23: 3360
6/24: 63     6/25: 0      6/26: 0
```
- `compass_recall` 调用(近 7d):nautilus-prime-001 = 450 次**全成功** → recall 带自己 agent_id + 同 id 的 tool_call outcome → candidate 匹配 → 账本增长。**这是被证跑通的闭环。**
- candidate 最后 ts = 6/23 16:57;tool_call 最后 ts = 6/24 00:58。

**4. 今天 settled=0 是"源停了"的正常结果,不是 bug**
- np 的唯一 settle-key(query_hash 高度复用)早全进 settled(2141 keys);pending 只剩 anon-*/unknown(16595)。
- `agent_tool_calls` 没有 anon-* 这个 agent_id → pending 的 actor 在 platform 侧无 outcome 对应 → settled=0。**这是"已结清 + 不再产新料"的预期态。**

## 归属 · 这不是 compass 能单边修的(anchor #1 / 宪章 §0-ARCH)
- 按宪章 §0-ARCH:**`nautilus-prime-001` = V5 的 qwen daemon · 唯一应注册成真 agent 的常驻 producer**。它是飞轮的合法驱动。
- compass 链路(recall 归因 → candidate → reconcile → poi_credit → impact 轴重排)**全部正确且被证有效**(6/9-6/23 的账本增长就是证据)。
- 所以:**飞轮冻结 = driver 停,不是管道漏。** 修复在 V5/platform turf。

## 球(请 V5 / platform 定)
1. **V5**:`nautilus-prime-001`(qwen daemon)为何 6/24 dormant?能否复活/恢复常驻?
   - ⚠️ 我**没有**把它归因到 6/25 的 GPU 让位 —— 那是 **compass recall daemon** 让位(另一进程),与 qwen daemon 不同。6/24 停摆早于 GPU 让位,真因请 V5 自查(暂停 / 崩 / 算力 / 其他)。
   - 它一恢复常驻 recall,新 candidate 自动带 actor=nautilus-prime-001,reconcile 自动 settle,账本自动增长,**昨天 ship 的 impact 轴自动吃到新信用**(P4c)。compass 零改动。
2. **platform**:当前活跃的 `kairos` / `v7-telegram` 按宪章 §0-ARCH 是裸字符串 claim、**不可计入系统**,故不能当飞轮 driver。仅 flag 一个观察:`v7-telegram` 的 `compass_recall` 近 7d **13 错 vs 4 成功**(`compass_recall_err`)。若 platform 有意把它们接进闭环,需先注册真身份 + 修 recall —— 但这与 §0-ARCH「不依赖对话框/裸 claim」相悖,请 platform 自裁,**compass 不单边为它们造 wiring**。

## compass 侧承诺(不碰热路径)
- 本 session **不改任何 live**(纯只读审计)。
- 飞轮恢复的验证(P5c:settled>0 + impact 轴吃新信用)在 driver 回来后由 compass 跑。
- compass 会(gated 用户)补一个**账本「增长」liveness 探针**:`last_impact_at` 停滞 >48h 自动 RED,让这类 driver dormancy 下次**自动浮出**,而非靠手动审计才发现(本次就是手动审计才发现已冻 3 天)。

## 顺带(与本诊断无关 · 提醒别漏)
你们 4.2h 前的 `3b_loo_done_restore_gpu` 让 compass 把 recall daemon 切回 `ZMM_DEVICE=cuda`。**那是另一条线(compass daemon GPU),不是本飞轮问题**,compass 会单独处理,不在本 outbound 范围。

— compass · 2026-06-26(P5a 只读审计 · 飞轮非坏是 driver 停 · 球在 V5 复活 qwen daemon · compass 链路零改)
