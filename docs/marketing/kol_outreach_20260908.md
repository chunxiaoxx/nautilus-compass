# KOL/团队发信计划(2026-09-08 · 发布夜起执行)

> 纪律(先读):每封个性化,禁群发密送;新地址每天 ≤5 封(Gmail 信誉);
> 数字照口径卡 v2;只邀请「复算/点评/试用」,不请托吹捧(不买量红线同源);
> 组织内部件(信箱/框名)绝不外提;对外一律 nautilus-compass 全名。

## 1. 目标分层与渠道状态

| 层 | 目标 | 渠道 | 状态 |
|---|---|---|---|
| 国际记忆同行 | mem0 | founders@mem0.ai(GitHub 官方) | 📝 信已定稿,**待 Reddit 链接回填后发**(9/9) |
| 国际记忆同行 | Zep | info@getzep.com(官方列出) | ✅ **已发 9/8 晚**(EverMemBench 39.97 钩子+邀请纠错) |
| 国际记忆同行 | MemOS/MemTensor | contact@openmem.net(论文页官方) | ✅ **已发 9/8 晚**(EverMemBench 42.55 钩子+架构对话邀请) |
| 国际记忆同行 | Letta(MemGPT) | letta.com/contact 表单+Discord(无公开邮箱) | 9/9 走表单 |
| 国际记忆同行 | Cognee | GitHub topoteretes/cognee(无公开邮箱) | 9/9 走 GitHub discussion |
| 国内媒体 | 机器之心 | content@jiqizhixin.com(投稿/报道,已验证) | ✅ **已发 9/8 晚** |
| 国内媒体 | 量子位 | ai@qbitai.com(官方投稿/爆料,已验证) | ✅ **已发 9/8 晚**(主题带【报道】) |
| 国内社区 | PaperWeekly | hr@paperweekly.site(投稿,已验证) | ✅ **已发 9/8 晚**(判官盲区方法向角度) |
| 国内社区 | Datawhale | opensource@datawhale.club(官网已验证) | 9/9 发(开源社区联合推广角度) |
| 国内大厂 | 字节(豆包/TARS/火山 Ark) | 无公开邮箱;火山 Ark 商务表单/GitHub bytedance org | 模板②(待用户自有渠道转发) |
| 国内大厂 | DeepSeek | 无公开邮箱;GitHub deepseek-ai | 模板② |
| 国内大厂 | 腾讯(混元/元宝) | 无公开邮箱;腾讯云合作/GitHub Tencent-Hunyuan | 模板② |
| KOL 个体 | 苏剑林/张俊林等 | 知乎私信/微信公众号留言(非邮件) | 9/10 起,模板③压短版 |

> 9/8 发送台账:5 封(机器之心/PaperWeekly/Zep/MemOS/量子位)——达到「新地址每天 ≤5」上限,mem0 与 Datawhale/Letta/Cognee 排 9/9。发送通道=飞轮 _gmail_send.py(REST 直发,Gmail message id 留档)。

## 2. 模板① · 国际记忆同行(EN,礼节通报+邀请复算)

> 用于 mem0(已建草稿)/Letta/Cognee/Zep(改称谓后走表单或 GitHub)

Subject: Head-to-head vs [tool] on LongMemEval-S — full evidence, would love your corrections

Hi [team],

I'm the author of nautilus-compass, an open-source memory layer (github.com/chunxiaoxx/nautilus-compass). We just published a head-to-head against [tool] [version] on r/LocalLLaMA, and wanted you to hear it from us first, with the evidence in hand.

Short version — identical questions, identical judge criteria, each system on its default embedder:
- LongMemEval-S (full 500): P@1 0.890 vs 0.774 · P@5 0.978 vs 0.916 · MRR 0.929 vs 0.834
- LOCOMO-10 (n=1986): P@1 0.644 vs 0.592

Our design bet: no LLM extraction at write time — verbatim local embedding, all intelligence at read time (utterance-type routing, BM25+dense RRF fusion, date anchoring). Failed experiments are published too, and everything reproduces from the repo for ~$3.50.

If any part of our setup misrepresents [tool] (wrong flags, outdated defaults, unfair comparison), we genuinely want to know — we'll correct the post and the repo. Also open to a joint benchmark exchange.

Respect for what you've built — this space needs more public, reproducible comparisons.

— chunxiao, author of nautilus-compass
github.com/chunxiaoxx/nautilus-compass · compass.nautilus.social

## 3. 模板② · 国内大厂(中文,邀请评估与合作)

主题:开源 agent 记忆层 nautilus-compass · 邀请评估与共建

[老师/团队] 您好,

我是开源项目 nautilus-compass 的作者(独立开发者,AI-agent 协作组织,130 天 771 次提交中 603 次由 agent 完成)。今晚在 r/LocalLLaMA 发布了与 mem0 2.0.19 的全量对打:

- LongMemEval-S 全 500 题:检索 P@1 0.890 vs 0.774(+11.6pt),三项全面领先;mem0 主场 LOCOMO(1986 题)0.644 vs 0.592
- 设计赌注:写入零 LLM(原文+本地嵌入),智能全在读侧(分型路由/混合检索/日期锚定)
- 判分协议、失败实验、复现脚本全部开源(复现约 $3.50);另有一篇「判官盲区/判分卫生学」论文在投(arXiv)

与贵方的相关性(按对象改一段):
- 字节:豆包/TARS 等 agent 产品与火山 Ark 的第三方记忆层生态位;可作 Ark 插件/工具评测合作
- DeepSeek:模型侧长上下文与记忆评测共建;我们开源的判分协议(harness+双口径)可直接用于第三方复算
- 腾讯:混元 agent 与腾讯云开发者生态;记忆层可作为开源组件接入

我们求的不是背书,是**评估与拍砖**:欢迎复算(全脚本开源)、欢迎指出不公之处、欢迎共建公开评测。若方向契合,也乐意探讨更深的合作。

GitHub: github.com/chunxiaoxx/nautilus-compass(双语 README)
落地页: compass.nautilus.social(托管版已开放自助注册)

— chunxiao · nautilus-compass 作者

## 4. 模板③ · 国内媒体/KOL(中文,求报道/点评)

> 已建草稿两封:机器之心(content@jiqizhixin.com)/PaperWeekly(hr@paperweekly.site)。
> KOL 个体(知乎/公众号)用此模板压短到 150 字内走私信。

主题:求报道/点评:一人+AI 舰队 130 天做出开源记忆层,500 题公开基准全面超过 mem0

编辑/老师好,

开源项目 nautilus-compass(agent 记忆层)今晚在 r/LocalLLaMA 发布,与 mem0 2.0.19 全量对打:LongMemEval-S 全 500 题检索 P@1 0.890 vs 0.774(+11.6pt),mem0 主场 LOCOMO 同样领先。设计赌注反直觉——写入不调 LLM,智能全在读侧;失败实验、判分协议、复现脚本($3.50)全部开源。另:全部判分靠自家 harness,我们抓到自家 AI 判官 5 次静默失效(71 题断连被误判),全部重判+双口径披露,这个方法论写成了论文(arXiv 在投)。130 天 771 次提交,603 次由 AI agent 完成(审计记录可查)。

素材包/数字出处/作者采访随时可给。唯一标准:数字经得起复现——欢迎复算。

GitHub: github.com/chunxiaoxx/nautilus-compass · compass.nautilus.social

## 5. 发送节奏

| 时间 | 动作 |
|---|---|
| 9/9 | mem0 草稿补 Reddit 链接后发;机器之心+PaperWeekly 发 |
| 9/9-10 | Letta/Cognee/Zep 走表单/GitHub(模板①) |
| 大厂三封 | 用户自有渠道转发(火山 Ark 表单/GitHub/内推),邮件渠道不存在不硬发 |
| KOL 私信 | 9/10 起,每天 ≤5 个 |
| 回复跟进 | 48h 未回不追发;有回复进 seeds 名单优先维护 |
