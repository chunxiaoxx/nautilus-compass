# 凭什么信你 Agent 的记忆层?——nautilus-compass 的两个架构赌注
*(中文版 · 适投:知乎/掘金/公众号/即刻技术圈;英文版投 HN/r/LocalLLaMA)*

每个 AI agent 记忆层产品都带着两样东西出厂:一张跑分表,和一句没说出口的"请相信我"。我们做 [nautilus-compass](https://github.com/chunxiaoxx/nautilus-compass) 的出发点正好相反:**我们对外公布的每个数字,你都应该能从字节级复算出来,不需要信任我们。**这篇文章讲背后的两个架构赌注。

## 赌注一:写入路径零 LLM 调用("写时押注"问题)

主流记忆管线在写入时就开始摘要、抽取、建图——这本质上是一场赌局:赌今天的压缩能命中明天的提问。我们反复看到这场赌局输掉:同一批语料、同一套检索,只在读取侧加了一层会话摘要,end-to-end 准确率从 42.6% 涨到 75.4%,**检索一行没改**——压缩不是地板,是天花板。

所以我们的写入路径什么都不"聪明地"做:原文、本地 BGE-m3 向量、数据不出机器。所有智能放在读取时:语义+关键词混合召回、单会话问题路由到轮次窗口分块、漂移检测(每条 prompt 先对照一组真实失败转录打分,held-out AUC 0.83)——在 agent 拿着过期记忆行动之前拦一道。

实测(LongMemEval-S 全 500 题、同题对打 mem0 2.0.19、双方各用默认嵌入、一条命令约 $3.50 可复现):**P@1 0.890 vs 0.774,P@5 0.978 vs 0.916**。复现脚本在仓里;证据链里还保留了那些*失败*的实验(交叉编码器重排在我们的语料上是负收益——照发)。

## 赌注二:数字以"密封证据包"出厂,不以文章出厂

跑分表是一种主张。我们的主张以 **VerifyPack 证据包**形式发布:sha256 清单、每条声明可从载荷字节复算、ed25519 签名回执。两条纯标准库命令即可重推任何数字——不依赖任何第三方库,不用"相信我们的 notebook"。[复算墙](https://github.com/chunxiaoxx/nautilus-compass/blob/main/docs/REPRODUCIBILITY_WALL.md)以同等醒目度发布与我们矛盾的数字;我们的一个密封包里就躺着一个 disagree——日志文件在封包后仍被追写,协议抓住了它,我们把这次失败原样保留。它就是干这个的。

这套纪律最初是自卫:我们自己的审计流程两周内两次拦下"实现方自报全绿但实测不绿"——其中一次,连实现方举的示例本身都复现不出来。经不起对自己日志的对抗性审读的 agent 记忆,不是基础设施,是日记。

## 三分钟接入

```bash
git clone https://github.com/chunxiaoxx/nautilus-compass ~/.claude/plugins/nautilus-compass
bash ~/.claude/plugins/nautilus-compass/install.sh
bash ~/.claude/plugins/nautilus-compass/daemon_start.sh
```

支持 Claude Code / Cursor / Cline / Continue / Zed / 任意 MCP 客户端;不想跑本地模型就用托管网关 `compass.nautilus.social/mcp/`。

**以及本文开头的那个邀请:你有已发布的记忆层跑分——自己的,或你依赖的?开个 issue。我们免费独立复算,结果无论 agree 还是 disagree 都同等醒目发布,附签名回执。**人肉管线,先到先得。

本文每个数字都有 sha256 清单+字节复算+签名的证据包背书——你的记忆层,敢过这道杠吗?
