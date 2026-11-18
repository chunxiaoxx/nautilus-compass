# INC_20261118 · 召回侧损害同口径复算(R567)·dev.to 应答深核坐实

> 轮次:R567(2026-11-18 09:00–09:30 EST)·性质:值守诊断轮·本轮零生产改动
> 上游:R560(首次实测 76.2%)· R561(口径修正 + 方案 A 预演)· R564/R565(fallback 地雷)· R566(外联关闭事件)

## 一、召回噪声:同 query 同口径复算(R560 原查询,免口径漂移)

R560 的做法是用 8 条 query × top30 = 240 候选位测噪声占比。本轮**不重跑 8 条**(时间预算 + 避免口径漂移),
改用 **R560 自己记下的"最尖锐一条"原 query 逐字复算**:

```
query = 「distill 回填 旧会话 正式记忆库 污染」  (R560 记录原文)
top_k = 30 · scope=project · project=-Users-chunxiao-wang-Projects-nautilus-compass
召回 token = rt_033027f154dfa05b
```

实测 top30 逐张点数(前缀判噪声,与 R561 口径一致):

| 类别 | 张数 | 位次 |
|---|---|---|
| 噪声(`distill-*` 空蒸馏纪要) | 25 | 3-22, 24-27, 29 |
| 噪声(`session_auto_*` 流水卡) | 2 | 28, 30 |
| 主题卡 | 3 | 1(`recall-noise-76pct`)、2(`distill-live-uncommitted-code`)、23(`MEMORY_archived_20261106`) |

- **本轮噪声占比 = 27/30 = 90.0%**
- R560 同 query:29/30 = 96.7%(唯一主题卡被压到**第 22 位**)
- R561 同 query:唯一主题卡顶到**第 1 位**(=R560 自己写的量化卡进了库)

**判读(不夸大)**:
1. 主题卡**可及性已恢复**(第 1、2 位连续三轮都在),R561 的"多写主题卡对冲"路径**在极尖锐 query 上确实见效**;
2. 但**噪声绝对占比仍在 90% 上下**——对照窗口满屏仍几乎全是 `蒸馏纪要 <uuid>` 空壳卡;
3. R561 已算过的账仍成立:主题卡供给速率(约 1 位/轮)追不上污染增速(每 2h 灌 1 张)
   ⇒ **自助路径杯水车薪·解法只能是闸门(方案 A/B/C 候拍板项)**,本轮不新增第三种主张。

## 二、库级噪声:逐张前缀统计(R561 修正后口径)

```
compass 项目 memory 目录 .md 总数 = 1430 张(R566 记 1426,+4)
  session_auto_*  883
  distill-*       314
  session_*       45
  其余主题卡/归档/MEMORY.md = 88
噪声 = 883 + 314 + 45 = 1242 → 1242/1429 = 86.9%
```

对照:R560 84.0%(口径错,把 40 张 `session_*` 算作主题卡)· R561 86.7% · R564 86.5% · R566 86.6% · **本轮 86.9%**
⇒ 噪声占比仍处高位,四条曲线在 86.5–86.9% 区间横盘,**未因"多写主题卡"而实质下降**。

## 三、distill 回填仍在写:published 280/280 全部来自 >7d 旧会话

`runtime/scratch_distill_pilot_20261104/incremental_stats.jsonl`(mtime 11-18 08:45,今天仍在写):

```
published = 280(R566 记 278,+2)· review = 78 · failed = 1
published 中 source_mtime 齐全者 = 280
其中源会话年龄 > 7d = 280 → 100.0%
  max_age = 29.4d · median = 29.1d · min_age = 9.5d
```

今日 05:00 后新增 2 张 distill 卡(06:43 `distill-71e13745`、08:45 `distill-628f538c`)——
**两张同样出自 9 天以上的旧会话**。

⇒ **R559「freeze 后仍发旧会话卡」的证伪继续成立**(第 N 次复算同向)。
⇒ 候拍板项③(distill 方案 A/B/C)所指向的损害**仍在持续累积**,不是历史遗留的静态存量。

## 四、dev.to 应答深核:R566 的"全旧"本轮升级为"已答且双答"

R566 只核到"30 文 6+2=8 全旧"(即评论条数无变化)。本轮**拉评论正文 + 两文正文尾部逐条对账**,
把"旧"细化为"已回应":

| 文章 | 外部评论 | 我方应答 | 位置 |
|---|---|---|---|
| 4805943「Your AI Agent Lies About Finishing Work」 | indiainfranotes(10-06,"transcript vs receipt")、devansh_kontey(10-08,BRYDGE 推广) | **已答** | 正文 **PS (2026-10-27)**:signed evidence packs + "implementer never grades their own work";BRYDGE=complementary layer·拒绝试用·保持独立 |
| 4825866「We quantized our AI judge」 | arhancanli、baumgaerben、mp6nfjxhrlxc(均 10-10) | **已答** | 正文 "**On receipts**(@indiainfranotes)"+"**@devansh_kontey**(BRYDGE)"两段完整回应 |

⇒ 两条评论**均已应答且给出可复算口径**,无遗漏、零新评论 ⇒ **本轮零外发**(外发硬闸)。
⇒ 教训补一条:**只核"条数没变"=未核到"是否已答"**;dev.to 的应答形态是"文内 PS/Addendum"而非评论区,
   必须拉正文尾部对账才能判完。

## 五、值守面读数(全实测)

| 面 | 读数 | 对比 |
|---|---|---|
| 平台信箱 compass | 0 未读 | 持平 |
| platform RED 窗口 | **222 封**(唯一新函 id103772 soul-distress ×88·trace soul-distress-202611181933) | R566 221 → **+1**(soul→platform,零 compass 行动) |
| Gmail | 401 → 直刷 REFRESH_OK 3599s → 2d 窗口 **19 封**逐封 sender 全甄 | 最大 internalDate 仍 11-18 07:48:38Z(R566 事件 B 通知)⇒ **R566 后零新到·零新商务函·零新面孔**;7d 未读 28 |
| GitHub mentions | 5 条全旧 | 持平 |
| GitHub notifications | 45 条,最新 11-13 | 全旧(无新) |
| 创世监视 | 5 家(1/1/0/1/2) | 零 REPLY |
| dev.to | 30 文·8 评论 | 见第四节·**已答坐实** |
| 外联件新评论 | a2a-x402#198 仍 1 条(alanwang100 11-09)· IHUI-AI#78 末条 10-13 · rsi-bench#4 末条 10-10 · mem0#7641 零评论 | 零新评论 |
| CI | compass 44279781204 success(=R566 head)· core 43558665734 success | 双绿 |
| daemon / watchdog / 哨兵 | 9876 绿 · exit0 · exit0 **recall_hit=44** | 全绿 |
| 快筛 | CS-508~518 仅 **CS-513** 过(qwen 0.5/opus 1.0/梯度 50.0pp) | 历轮全同 |
| 管道三件 | collect+verdict+report+sync 全 exit0 | 持平 |
| 阿里矩阵 | mtime 仍停 10-30 09:42 | 停摆维持 |
| 磁盘数据卷 | 97% · avail **14Gi**(R566 16Gi) | **-2Gi / 约 4h**·仍逼近 10Gi alarm 线·零清理候用户 |
| 记忆库 | 1430 张·噪声 86.9% | 见第二节 |

## 六、本轮零生产动作(边界声明)

未改 launchd plist · 未改插件 daemon.py · 未改任何 symlink · 未 bootout distill · 未删/未移记忆卡 ·
未碰 NAS · 未回帖 / 未开 issue / 未发邮件 / 未 PATCH dev.to · 未碰他线 5 个未提交文件(保持 M) ·
未代推他线提交 · 未裹挟他线 untracked 新件。

## 七、候用户拍板(延续 + 变更)

延续:①fallback 地雷修法 B(一行 env·零代码·R565 已实证)⭐ ②distill A/B/C(损害持续累积,见第三节)
③distress ×88 人监门(人工删 `.soul-pause`·不代删)④磁盘 97% avail 14Gi 零清理 + NAS 侧 NFS 读阻塞根因(框外)
⑤通道配额 ⑥a2a#198 草稿(SLA 已过期)⑦Gmail 35 封草稿审稿 ⑧模真真三诉求 ⑨矩阵 phase2 解锁 ⑩py-spy 仍缺

变更:本轮**不新增**候拍板项——dev.to 一项经深核证明已完成,原"dev.to 待回"类疑点消除。
