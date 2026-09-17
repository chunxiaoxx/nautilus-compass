# HANDOFF 2026-09-17 · Glama hosted connector 提交(用户侧 2 击件)

> 背景:A 路=切 hosted connector(零构建)。自建 server 构建在 Glama 侧终态
> 失败(镜像/内省段),hosted 列表页不吃我们 Dockerfile——只吃端点。
> 昨日探针:https://compass.nautilus.social/mcp/ 未授权 initialize/tools/list
> 均 401(内省墙)。

## 提交步骤(glama.ai,需登录 GitHub 账号)

1. 打开 **https://glama.ai/mcp/connectors** → "Add MCP Server";
2. **Transport**:Streamable HTTP · **URL**:`https://compass.nautilus.social/mcp/`;
3. **Auth**:API Key/Bearer——先去 https://compass.nautilus.social/signup 控制台
   建 **scoped 只读 token**(仅 memory 读权限,别用全权);
4. 名称/描述:Nautilus Compass Memory · local-first agent memory via MCP
   (byte-recomputable, ed25519-signed receipts);
5. Source repo:github.com/chunxiaoxx/nautilus-compass(v3.2.0 · 344290b0);
6. 提交后看列表页:连接器页应有 tools 列表(凭 token 内省);
   若显示 "unable to introspect"/"?" → 走下面备选。

## 备选(仅当内省失败)

- nginx 改法(草案已在,生产变更需你明示批准):`/mcp/` 的 initialize+tools/list
  放行匿名(只暴露工具元数据,不暴露数据),tools/call 仍 401;
- 或提交时直接把 token 填进 Glama 表单(若表单支持,优先此路,零生产变更)。

## 验收(不预支)

- 列表页 tools 数 ≥1 且与我们 tools/list 一致;
- 质量评分:连接器同 TDQS,新上线可能是 "?",认领后 Request a re-sync
  (Admin 按钮,昨天已走过一遍流程);
- 隔日再看是否需补材料。

## 关联

- 技能卡 1.0.2 已 Pass(ClawHub);Glama server 页保留旧构建失败状态无妨,
  列表以 connector 为准;
- nginx 草案:docs(9/16 晚拟,未提交生产)。
