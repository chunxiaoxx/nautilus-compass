# MCP 目录提交材料包(9/8 夜备料 · B1)

> 四目录一 Discord,提交动作全部人工(账号/表单),本文=逐目录可贴内容。
> 数字照口径卡;连接串只给 hosted 端点(目录场景);本地安装指向 README。

## 通用提交包

| 字段 | 内容 |
|---|---|
| Name | nautilus-compass |
| Tagline | Local-first memory layer for AI agents — zero LLM calls at write time |
| Short desc | Open-source agent memory layer: verbatim local storage (BGE-m3), all intelligence at read time (utterance-type routing, BM25+dense RRF fusion, date anchoring). Beats mem0 head-to-head on LongMemEval-S full 500 (P@1 0.890 vs 0.774). Pre-action drift detection (AUC 0.83) + cross-agent contracts. Modified MIT. |
| Tags | agent-memory · long-term-memory · mcp · retrieval · bge-m3 · local-first · drift-detection |
| Hosted endpoint | https://compass.nautilus.social/mcp/ (open beta, self-serve signup at /signup) |
| GitHub | https://github.com/chunxiaoxx/nautilus-compass |
| Landing | https://compass.nautilus.social |
| PyPI | https://pypi.org/project/nautilus-compass/ |
| Logo | docs/marketing/deck_assets/(取已有品牌图) |

## 逐目录注意

### 1. Smithery(smithery.ai)
- 需 repo 内 server 定义(`smithery.yaml` 或 server.py 入口描述)——提交前要补一个配置文件;脚本安装命令:`pip install nautilus-compass && compass-mcp`
- 类别:Memory / Agent Tools

### 2. mcp.so
- 表单提交(name/url/description/tags);hosted URL 直填;附 GitHub 链接过审

### 3. PulseMCP(pulsemcp.com)
- 表单:server name/transport(streamable-http)/endpoint/tags/long description(用通用 Short desc 扩写一段)
- 特色字段:认证方式=Bearer token(self-serve signup)

### 4. Glama(glama.ai/mcp/servers)
- 提交 GitHub repo + 自动抓取;确认 README 顶部有 MCP server 安装段(已有 Quickstart)

### 5. Anthropic MCP Discord #showcase
- 一条消息(≤5 行):
  > nautilus-compass — local-first agent memory, zero LLM calls at write time. Head-to-head vs mem0 on LongMemEval-S full 500: P@1 0.890 vs 0.774, ~$3.50 to reproduce. Hosted open beta (self-serve) + local daemon + Reproducibility Wall. github.com/chunxiaoxx/nautilus-compass

## 提交节奏

Smithery 要补配置文件=唯一有代码动作的;其余四项纯表单,用户 30min 可全部提交完。建议 9/9 白天随值守间隙做。

---

## B2 附录 · awesome 列表 PR 草稿(9/9 凌晨备 · 每列表一 PR 一 entry,按字母序插入)

### 1. punkpeye/awesome-mcp-servers(最大列表)

Entry(插 Memory 分区,按字母序):

```
- [nautilus-compass](https://github.com/chunxiaoxx/nautilus-compass) 🔒 🖥️ 🍎 🪟 🐧 - Agent memory layer. Local-first, zero LLM calls at write time; retrieval intelligence (question-type routing, BM25+dense RRF) at read time. Pre-action drift detection + cross-agent contracts. Hosted beta available.
```

PR 标题:`Add nautilus-compass (memory)`
PR 正文:
> Adds nautilus-compass — an open-source agent memory layer (Modified MIT). Distinguishing traits: zero LLM calls at write time (verbatim local BGE-m3 embedding; free, lossless writes), all intelligence at read time. Ships an MCP server both as local daemon (stdio/TCP) and hosted endpoint. Full head-to-head benchmark evidence vs mem0 in-repo (~$3.50 to reproduce).

### 2. wong2/awesome-mcp-servers

Entry:
```
- [nautilus-compass](https://github.com/chunxiaoxx/nautilus-compass) - 🧠 Agent memory layer — zero LLM calls at write time, local-first (BGE-m3), read-side routing/hybrid retrieval, pre-action drift detection (AUC 0.83)
```

PR 标题同上;正文两句话即可(该列表较简)。

### 3. e2b-dev/awesome-ai-agents(agents 大列表,agent 工具分区)

Entry:
```
- [nautilus-compass](https://github.com/chunxiaoxx/nautilus-compass) - Open-source memory layer for AI agents. Local-first; beats mem0 head-to-head on LongMemEval-S retrieval (P@1 0.890 vs 0.774, full 500, scripts open).
```

### PR 纪律提醒
- 三个 PR 分三天发(9/9/9/10/9/11),同日三列表=模式相似易判 spam;账号用 chunxiaoxx
- 若某列表 CONTRIBUTING 有格式/分区要求,按它(先读再提)
- entry 描述与 README 首屏一致,不超额声明
