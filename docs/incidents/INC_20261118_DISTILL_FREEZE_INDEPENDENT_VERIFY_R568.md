# INC_20261118 · distill 冻结独立复核 + 召回闸门方向性观察(R568 值守轮)

> 性质:**值守轮独立复核**(不重复他线施工,只做「信实测不信措辞」的外部验证)
> 产生时间:2026-11-18 11:05~11:40 EST(值守轮 R568)
> 上游:他线 COLLAB_BOARD「2026-11-18 10:35 EST · compass R568 · 基础设施收敛」(daemon/recall 双路径加语义证据闸门 + distill launchd bootout 冻结 + ZMM_EMBEDDER_MODEL fallback 落地)

---

## 一、写入侧:**distill 回填通道已停**(四环独立实测坐实)

R559/R560/R567 三轮连续判定「freeze 被证伪·distill 仍在写·损害持续累积」
(published 278→280,published 中源会话 >7d = 280/280 = 100%)。
**本轮起该判定不再成立**——四环实测:

| # | 实测项 | 读数 | 判定 |
|---|---|---|---|
| ① | `launchctl list \| grep -c distill` | **0**(任务未加载) | 已 bootout ✅ |
| ② | `~/Library/LaunchAgents/ai.nautilus.distill-incremental.plist` | **No such file**(已移出加载目录) | 已摘除 ✅ |
| ③ | `ps aux \| grep incremental_distill` | **无进程** | 无残留执行 ✅ |
| ④ | 记忆库最新 distill 卡 mtime | **11-18 08:45**(`distill-628f538c`),此后 **~2.5h 无新卡** | 回填节律(00:36→02:38→04:41→06:43→08:45·约 2h/张)下 **10:45 档缺失** ✅ |

⇒ **写入侧止血坐实**:R567 记「published 278→280 + 今日 05:00 后新增 2 张」是最后一波;本轮起污染源不再新增。
⇒ **R567 报告里「损害持续累积不是静态存量」这句,只对 11-18 08:45 之前成立**。

**存量未清(重要)**:库内 **1430 张**,其中 `distill-*` **314 张** + `session_auto_*` **883 张** = **1197 张噪声卡仍在库**。
本轮实测 `distill-*` 计数 **R567 311 → 本轮 314(+3)**(R567 采集于 05:05,08:45 那张为其后新增)⇒ 总量已停在 314。
⇒ **闸门只挡「读」不删「库」**:存量 1197 张需另行处置(候拍板项②的「清理存量」部分**尚未执行**)。

---

## 二、读取侧:**闸门方向性信号**(口径与 R567 不同,**不作结论**)

他线 R568 receipt 自称「daemon 重启后真实 recall 4.92s、top30 噪声 **0/30**」。

本轮用**本地 BGE+hook 路径**(`python3 recall.py --bge --query "<R560 原 query>"`,**top_k=5**)实测:

```
🎯 召回 top 5 (BGE-bge-m3 · daemon · query: distill 回填 旧会话 正式记忆库 污染):
  🟢 0.669 · recall-noise-76pct-distill-pollution-20261117.md      ← 主题卡·第 1 位
  🔴 0.600 · MEMORY_archived_20261106.md                             ← 主题卡
  🔴 0.556 · distill-3e11f289-4fe9-49b9-9f7f-da49f291619a.md       ← 噪声
  🔴 0.556 · distill-fa3a4db7-ea66-42ac-8ec3-485084f27487.md       ← 噪声
  🔴 0.494 · session-contract-l4a-distill-20260822.md               ← 主题卡(非 session_ 前缀)
```

**⚠️ 口径声明(不得据此下结论)**:
- 本轮 = **top5 + hook 路径**;R567 = **top30 + MCP daemon 路径**;他线 receipt = **top30 + daemon 路径**;
- 三者窗口大小与调用链不同 ⇒ **不可与 90.0% / 0/30 直接相减**;
- 只能说:**方向一致**(最高分位已是主题卡·distill 卡退到 0.556/0.494 低分段),**独立同口径 top30 复算欠账** ⇒ 候下轮做(需 MCP token 通路,本轮 ToolSearch 未取到 `mcp__nautilus-compass__recall` schema)。

**另注**:`session-contract-l4a-distill-20260822.md` 虽名含 distill,但前缀是 `session-` 非 `session_` ⇒ 按 R560/R561 口径判为**主题卡**。前缀判噪声时勿按关键词猜。

---

## 三、🔴 新工具坑(本轮踩到·**结果看似成功实则口径错**)

**`GET /gmail/v1/users/me/messages?ids=<逗号分隔>` 会静默忽略 `ids` 参数**,返回默认最新 ~100 封
(无 error 字段、HTTP 200、JSON 结构完全正常)。本轮首次批量拉取据此得到「100 封」且 `internalDate` 全为 0,
**若不复算会得出「窗口全部异常」的假结论**。

**正确做法**:改逐封 `GET /users/me/messages/{id}?format=metadata&metadataHeaders=From&metadataHeaders=Subject`
(50 封 ~25s·可接受)⇒ 拿到真实窗口 50 封。

**归族**:与 R566「`after:` 用毫秒静默返 0 条(假零)」、R500「`/threads/list` 字面量当 id→400」、
R506「`fields=messageIds` 400 被 `.get('messages',[])` 吞成假 0」同族——
**Gmail API 任何「静默成功但口径错」都必须用第二种口径复算**(本轮:批量 → 逐封 + 与 `list` 端点条数对账)。

---

## 四、值守面读数(全实测)

| 项 | 读数 | 对比 |
|---|---|---|
| 平台信箱 compass | **0 未读** | 持平 |
| platform RED(to=platform) | **223**(新函 id105040 soul-distress **×89**) | R567 222 → +1(soul→platform·零 compass 行动) |
| Gmail 7d 全量 | **50 封**·未读 29·**新到 1 封**(Gamma 营销·11-18 15:42Z) | 零新商务函·零新面孔 |
| mentions | 5 全旧(最新 11-02 OWASP#35) | 持平 |
| notifications | **45** 全旧(最新 11-13) | R566 46 → −1 |
| genesis | 5 家(1/1/0/1/2)**零 REPLY** | 持平 |
| dev.to | 30 文·6+2=8 评论·条数未变 ⇒ **零新评论**(comment count 单调) | 持平 |
| CI | compass **44342935844**(5b852a7f)success·core 43558665734 success | 双绿 |
| 本地 git | HEAD=17ca6b22 **领先 origin/main 1 commit**(他线 R568 记录批未推) | 不代推 |
| daemon 9876 / watchdog / 哨兵 | 绿 / exit0 / exit0 **recall_hit=62** | R567 44 → +18 |
| 管道三件 | collect/verdict/report/sync 全 exit0 | — |
| 快筛 | **CS-303 + CS-513 过**(qwen 0.5/opus 1.0/梯度 50.0pp)·总结论「存在不过筛」 | CS-513 历轮同·CS-303 本轮新入列 |
| 矩阵 | mtime 仍停 **10-30 09:42** | 停摆维持 |
| 磁盘数据卷 | 97% **avail 15Gi** | R567 14Gi → **+1Gi 回升**(仍逼近 10Gi alarm) |

---

## 五、本轮零生产动作

未改 plist / 未改 daemon.py / 未改 recall.py / 未改任何 symlink / 未 bootout 任何任务(他线已做)/
未删未移记忆卡 / 未碰 NAS / 未回帖未开 issue 未发邮件未 PATCH dev.to /
未碰他线 5 个未提交文件(保持 M)/未代推他线提交/未裹挟他线 untracked 新件。

**产出**:本档 + COLLAB_BOARD R568(值守复核)行 + rounds.log + state.json(round=568)。

---

## 六、候拍板(本轮不新增,更新 2 项状态)

1. ⭐ **distill 写入侧已止血**(本轮坐实)——候拍板项②的「写入侧」部分**可视为已执行**;
   **但「存量 1197 张噪声卡清理」仍未执行** → ② 拆分:**②-a 存量清理(未做)** / **②-b 写入侧(已止血·他线执行)**。
2. **同口径 top30 复算**(MCP 通路)候下轮,坐实闸门「0/30」是否成立。
3. ③ distress **×89** 人监门(人工删 `.soul-pause`·不代删)·④ 磁盘 97% avail 15Gi 零清理 + NAS 侧 NFS 根因(框外)·
   ⑤ 通道配额(MiniMax/Kimi 双 429)·⑥ a2a#198 草稿 SLA 过期候硬闸·⑦ Gmail 35 封草稿审稿·⑧ 模真真三诉求·
   ⑨ 矩阵 phase2 解锁·⑩ py-spy 仍缺。
