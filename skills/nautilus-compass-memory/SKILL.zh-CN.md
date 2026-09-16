---
name: nautilus-compass-memory
description: AI 智能体的本地优先长期记忆(MCP)——写入时零 LLM 调用、读取时混合召回、带漂移检测防重复犯错。适用于:会话决策需要跨天保留、多智能体共享同一文件系统事实、或想要"同样的错误不犯第二遍"。所有对外数字随附 sha256 清单+字节复算+ed25519 签名证据包。
---

# Nautilus Compass Memory(中文版)

开源 AI 智能体记忆与可靠性层(Modified MIT)。写入路径零 LLM 调用——纯本地
BGE-m3 向量,数据不出机器;读取时做语义+关键词混合召回,另带漂移检测
(对照 25 正例 + 35 反例真实失败模式锚点集)。

支持 Claude Code / Claude Desktop · Cursor · Cline · Continue.dev · Zed ·
任意 MCP 客户端;本地 daemon 或云托管网关二选一。

## 一 · 何时用

任选其一:

- **记忆要活过会话**——过去会话里的决策、踩坑、配置、复盘,几天后相关时
  自动回到上下文。
- **多智能体/多对话框共享一个文件系统**——多个 agent 干同一个仓库,
  需要共享事实底座,而不是各记各的小本本。
- **同样的错误反复出现**——每次 prompt 先过漂移检测(对照真实失败锚点),
  在 agent 行动前拦截。

跳过:一次性任务无记忆依赖,或用户明确说不用历史上下文。

## 二 · 如何接(约 3 分钟)

### 方式 A · 本地 daemon(推荐)

```bash
git clone --branch v3.2.0 --depth 1 \
  https://github.com/chunxiaoxx/nautilus-compass ~/.claude/plugins/nautilus-compass
# 钉住已审计 commit——tag 若被动过则硬失败:
[ "$(git -C ~/.claude/plugins/nautilus-compass rev-parse HEAD)" = "344290b0bb252c4a28305d351bb18a7f177718be" ] || \
  { echo "commit 不符:审查过的代码 != 克隆到的代码——勿跑安装脚本"; exit 1; }
bash ~/.claude/plugins/nautilus-compass/install.sh        # 为 Claude Code 装钩子
bash ~/.claude/plugins/nautilus-compass/daemon_start.sh   # 启动 BGE-m3 daemon(每次开机一次)
```

其他 MCP 客户端(Cursor / Cline / Continue.dev / Zed / Claude Desktop),
自动检测+备份+写入其 MCP 配置:

```bash
python ~/.claude/plugins/nautilus-compass/scripts/install_to_agent.py
```

脚本会做什么(执行前请知悉): 下载本地嵌入模型、在 `~/.claude/settings.json`
注册钩子、改动各 MCP 客户端配置——每处改动前逐文件备份;卸载=删除
`~/.claude/plugins/nautilus-compass` 并还原备份。

PyPI 也有: `pip install nautilus-compass==3.2.0`(CLI + MCP server + A2A adapter)。

### 方式 B · 云托管网关(自助,免本地模型)

1. 注册 <https://compass.nautilus.social/signup>
2. 控制台创建 scoped token
3. 任意 MCP 客户端指向 `https://compass.nautilus.social/mcp/`
   (Bearer token · streamable-http · 用户级记忆隔离)

> 出域提示: 云托管=记忆内容与召回查询会发送到 compass.nautilus.social
> (用户级隔离);数据不能出本机请用本地 daemon(方式 A)。

### 装完得到什么

核心工具:`ingest_obs` · `recall` · `session_search` · `profile` ·
`drift_check` · `drift_history` · `feedback_log`(+10 个进阶)。Claude Code
斜杠命令:`/compass-recall` `/compass-verify` `/compass-drift`
`/compass-status` `/compass-search`。

> daemon 空闲后首次 recall 最长 ~90 s(模型冷加载);MCP 客户端会自动带
> 加长超时重试一次。

## 三 · 如何验(不信自报)

本项目差异点:对外公布的每条声明都封装为证据包——sha256 清单、声明从字节
可复算、ed25519 签名回执。两条命令验证,纯标准库,零第三方依赖:

```bash
git clone --branch v3.2.0 --depth 1 https://github.com/chunxiaoxx/nautilus-compass && cd nautilus-compass
[ "$(git rev-parse HEAD)" = "344290b0bb252c4a28305d351bb18a7f177718be" ] || { echo "commit 不符,中止"; exit 1; }
# 1. 全量复算(每条声明从字节复算,产出你自己的回执)
python -m tools.verifypack verify runtime/verifypack/arma_summary/pack \
  --out /tmp/my_receipt.json
# 2. 签名+摘要校验
python -m tools.verifypack check runtime/verifypack/arma_summary/pack \
  --receipt runtime/verifypack/arma_summary/pack/receipts/receipt.json \
  --pubkey f7554b8709b7fe36f5a63e7f76cf2a31f827aee5724ff8dd4f11772d1aa3e8be
```

想用**你自己的密钥**留判据?

```bash
python -m tools.verifypack keygen --out-dir .verifypack --name you
```

重跑 `verify`、签名、把回执发我们——独立复算优于自报;[复算墙](../../docs/REPRODUCIBILITY_WALL.md)
以同等醒目度公布与我们矛盾的数字。

---

## English version

**Nautilus Compass Memory** — local-first long-term memory for AI agents over
MCP. Zero LLM calls at write time (local BGE-m3 embeddings, no data leaves the
machine), hybrid semantic + keyword recall at read time, plus drift detection
against real failure anchors.

Connect: `git clone … && bash install.sh && bash daemon_start.sh` (local), or
the hosted gateway at `https://compass.nautilus.social/mcp/` (Bearer token).
Verify: two stdlib-only commands recompute every published claim from bytes and
check the ed25519 signature — see
[`SKILL.md`](SKILL.md) for the full English card.
