# 阮一峰周刊自荐文案(9/14 拟 · 待用户过目后发)

> 投稿方式:github.com/ruanyf/weekly 提 issue(无固定模板,社区惯例=【开源自荐】标题+介绍+链接)
> 参考先例:Memory-Palace 的 #9651(同为 OpenClaw 生态记忆插件)
> ⚠️ 红线自检:0.890/0.774 检索对打=evidence 文件+复现脚本在仓(非 sealed 包,文案如实分级);81.6% 不出口;无营销腔

---

**标题:【开源自荐】nautilus-compass:给 AI Agent 装上"可验证"的长期记忆**

**正文:**

项目地址:https://github.com/chunxiaoxx/nautilus-compass

一个人写了 130 天的开源 agent 记忆层(Modified MIT)。核心思路就两条:

**一、写入时不调 LLM。** 会话原文 + 本地 BGE-m3 嵌入,零抽取、零上云,记忆写入零 token 成本;智能全部放在读取侧——按问题类型路由检索单元(单会话用户型问题只取 turn 级小块,而不是塞整个会话),BM25+dense 混合检索。在 LongMemEval-S 全 500 题上,检索 P@1 0.890 vs mem0 2.0.19 的 0.774(同题同判据、各用默认嵌入,evidence 文件和复现脚本都在仓库里,复跑约 $3.50)。

**二、跑分做成"证据包"。** 对外公布的每个数字都是 sha256 清单 + 从字节可复算的 claim + ed25519 签名回执,clone 仓库跑两条命令即可验证,不需要信任作者。无法从包内字节复算的数字一律不进包,只做披露——因为判官网关静默故障把 14.2% 的题记成"答错"这类事故,我们自己抓到过五次,全部写进了协议文档(docs/REPRODUCIBILITY_WALL.md)。

支持 Claude Code / Cursor / Cline / Continue / Zed 一键接入(MCP),也有托管自助版。欢迎来验数字——推翻我们的结果,同样上墙。

---

## 发送备注

- issue 正文=上文正文;标题照上文标题
- 用户过目点头后:compass 框经 API 提 issue(gh token 可建 issue)
- 发出后 48h 观察是否被周刊收录(周刊每周五出);不收录不追发
