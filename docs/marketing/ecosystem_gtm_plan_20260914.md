# 生态嵌入 GTM 系统性方案(2026-09-14 · 深度调研版)

> 定位:与「内容+直邮」线并行的**生态嵌入线**——让产品长进别人的分发树(目录/技能生态/周报),而非继续买渠道曝光。
> 判据对齐反剧场主尺:成功=**可验证采用信号**(技能卡被安装、PR 被 merge、star 斜率变化、外来复现请求),不是发帖数。
> 全部动作均可由 compass 框推进,用户只做拍板与账号动作。

---

## 一、五层目标矩阵(调研后画像)

| 层 | 目标 | 规模/活跃 | 入口与动作 | 优先级 |
|---|---|---|---|---|
| L1 垂直列表 | awesome-ai-memory(XiaomingX) | 172★·8/7 仍推·9 PR 排队 | PR 进「§1 聚合记忆层」表格(Mem0/Zep/Letta 同列);收录标准宽松:链接真实+描述符合官方定位 | 🔴 本周 |
| L1 周报 | 阮一峰 weekly | ~25 万读者/每周 | issue 自荐(无模板;社区惯例:【开源项目】+名称+一段话+链接);Memory-Palace 先例(#9651) | 🔴 本周 |
| L2 技能生态 | OpenClaw(389k★)+ WorkBuddy(指南仓 2.9k★·今日仍推) | 极活跃 | **SKILL.md 技能卡**(OpenClaw 与 WorkBuddy 同格式即插);投放:WorkBuddyGuide PR + awesome-openclaw-skills-zh PR + OpenClaw discussions | 🔴 下周 |
| L3 中间件 | new-api(QuantumNous,48k★) | 每日活跃 | 不提记忆叙事;提**记忆 token 观测**小 issue(per-key 记忆注入 token 统计)——我们 judge 网关真实用例 | 🟡 两周后 |
| L4 大厂闭源 | 豆包工作伙伴(字节) | 无公开仓/无插件入口 | 暂缓;等 L1/L2 打出案例后走开放平台或人脉通道 | ⏸ 观察 |

**关键调研发现**:OpenClaw 的技能=SKILL.md(Markdown+YAML frontmatter,name/description 必填),**是提示文档不是可执行插件**——制作成本低(半天);WorkBuddy 官方兼容同一格式(.skill 三分钟安装),一卡两用。

## 二、叙事资产库(五张牌 × 证据锚点)

| 牌 | 一句话 | 证据锚点(全部可验) | 适用受众 |
|---|---|---|---|
| 1 省 token | 写入零 LLM 调用=记忆写入 0 token;读侧按问题类型给最小检索单元(turn 级块≠整会话) | 架构文档;LongMemEval-S P@5 0.978(sealed) | 工程社区/网关用户 |
| 2 组织记忆 | 多 agent 共享一库:跨 agent 合约+scoped 多租户;治「个人提效、组织无感」(WorkBuddy 企业版公开痛点正对口) | 自家 4 框 dogfood 一库运行 130 天 | 企业向/大厂 |
| 3 长期个人记忆 | 130 天 771 commits 的记忆库,语义召回随时可查 | 记忆目录 56 条实存 | 个人用户 |
| 4 记忆胶囊 | agent B 直接继承 A 的解题经验(FAIL→PASS 实录) | D2 实验记录 | AGI 叙事受众 |
| 5 共创 AGI | 「智能=压缩+验证」,验证层是公共品 | 战略文档 | **仅 README 愿景段,不进 issue/PR** |

统一差异化钩子(所有场合收尾句):**「我们对外公布的每个数字都是 sha256 清单+字节可复算+签名的证据包——你的记忆系统敢这样做吗?」**

## 三、技能卡设计(nautilus-compass.skill)

```
SKILL.md(frontmatter: name=nautilus-compass-memory; description=Local-first agent memory via MCP — zero LLM calls at write time, typed retrieval at read time)
正文三段(中英双语):
 1. 何时用:会话记忆跨天保留/多 agent 共享事实/防重复犯错(drift)
 2. 如何接:MCP endpoint(本地 daemon 三命令 或 hosted 自助)·三分钟
 3. 如何验:两条 VerifyPack 命令+公钥(把验证能力直接做进技能=差异化)
```

## 四、执行排期

| 时点 | 动作 | 谁 |
|---|---|---|
| 本周 | awesome-ai-memory PR(§1 表格行,半小时) | compass 框(fork+分支就绪后 PR 若被反滥用拦→用户一键) |
| 本周 | 阮一峰 weekly 自荐 issue(中文一段话+链接) | compass 起草→用户过目发 |
| 下周 | 技能卡制作+WorkBuddyGuide PR+awesome-openclaw-skills-zh PR+OpenClaw discussions 帖 | compass |
| 两周后 | new-api 记忆 token 观测 issue | compass 起草 |
| 持续 | 豆包观察;punkpeye merge 后跟进 Glama 页流量 | 值守 |

## 五、红线(不可让步)

1. 技能卡/issue 正文=使用文档不是广告;「共创 AGI」不出口,只在 README
2. 对外数字一律出自 sealed 集(81.6% 等不可复算数不出口)
3. 大厂闭源不冷邮轰炸;被拒的渠道不二次纠缠(wong2 教训)
4. 每个动作完成后在 community_engagement_log.md 记台账,48h 无回响不追发
