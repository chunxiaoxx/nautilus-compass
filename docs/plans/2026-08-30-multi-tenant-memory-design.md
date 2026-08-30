# 多租户统一记忆管理 · 一页设计(2026-08-30)

> P2 workbuddy 提审材料 · 架构章节 · trace_id: compass-multitenant-memory-20260830
> 状态: 设计定稿(地基实物已在产,残余工程量见 §5 分期) · 作者: compass 框

## 1. 问题与愿景

8/30 两次安全事件证明单租户形态不可对外:① workbuddy 接入 MCP 可读各对话框全部记忆(存量全权 token + TCP 通道无项目边界);② 8770 老服务 X-User-ID 无验证,公网 443 可冒充任意用户读记忆、无凭证写记忆目录(记忆投毒),均已修复。

用户愿景(原话):"各个用户的各个设备各个 agent 互相映射就能实现统一记忆管理"——即**每个用户一个记忆空间,其在所有设备上的所有 agent 汇入同一空间;用户之间完全隔离**。

## 2. 三层映射模型

```
用户(user_id · JWT 身份)
 ├─ 设备 A ─ agent 1 ─ token(read+write: <user> 的 project 集)
 ├─ 设备 B ─ agent 2 ─ token(read+write: <user> 的 project 集)
 └─ 设备 C ─ agent 3 ─ token(read-only: <user> 的 project 集)
隔离边界: project 命名空间。跨用户 = 跨 project = token scope 不可达。
```

- **身份**:人用 JWT(8770 已有 signup/login);agent 用 scoped token(工具代签或用户面板签发)。
- **空间**:每用户一个 primary project(`u_<id>_memory` 约定),可扩展多 project;同 user 的所有 token 指向同一 project 集 = "多设备多 agent 映射统一记忆"。
- **鉴权链**:JWT ↔ 用户;token ↔ (用户, scope 集);header-only 身份永久禁止(8/30 洞根因)。

## 3. 地基实物(全部已在产,不重造)

| 件 | 位置 | 状态 |
|---|---|---|
| scoped token 机制(`read:<p>`/`write:<p>`/`read:*`,fail-closed) | 8097 HTTP + 9877 TCP 共用 `/etc/compass/tokens.json` | ✅ 8/30 六项 DENY/ALLOW 矩阵实测通过 |
| 多用户数据模型(users/agents/observations 按 user_id 外键) | 8770 v0.9(9/15 退役,模型随迁) | ✅ 已是完整多租户形态 |
| JWT 签发/校验 | 8770 signup/login + NAUTILUS_JWT_SECRET | ✅ 五项矩阵含合法 JWT 200 |
| token 签发/撤销工具 | `ops/compass_token_admin.py` + agent_quickstart 默认 scoped | ✅ 8/28 起新 token 默认最小权限 |

## 4. 硬规则(8/30 两条洞各换一条)

1. **身份只认凭证,不认自报**:Bearer JWT / scoped token 之外的一切身份 header(X-User-ID / X-Tenant-ID)仅作一致性校验,永不单独授权。
2. **写路径 fail-closed**:未知工具/未知 scope 一律拒绝;token 撤销即时生效(TCP 版无热加载,变更须 restart——列入 §5 待办)。

## 5. 实施分期与验收判据

- **P2 提审版(最小,≈0 新代码)**:自用 dogfood 单租户全链跑通——workbuddy(JWT agent token)+ 各框桥(scoped token)全部走 8097/9877 鉴权通道,本地 9876 仅限本机回环。
- **商用版(提审通过后)**:自助 signup → 自动签发该用户 scoped token → 隔离验收探针自动跑;TCP 版补 tokens.json 热加载;8770 退役时多用户模型迁入正式服务。
- **验收四探针(可证伪)**:① 跨用户读 DENY ② 跨用户写 DENY ③ 同用户跨设备 recall 命中同一记忆 ④ token 撤销后旧请求 DENY。四绿才可宣称"多租户隔离成立"。

## 6. 关联证据

- 修复记录:commit acb3423(v0.9 JWT-only + 五项矩阵)· TCP scope commit(TDD 8/8 + 六项矩阵)
- memory:`security-v09-xuserid-impersonation-20260830` · `security-workbuddy-token-scoping-20260830`
- 退役计划:LOOP_STATE P1(9877/8770 旧入口 9/15 退役,workbuddy 已验证 HTTP 直连)
