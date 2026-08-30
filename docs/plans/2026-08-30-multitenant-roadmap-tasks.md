# 多租户商用版 · 分期任务清单(2026-08-30)

> 设计依据:`2026-08-30-multi-tenant-memory-design.md` · trace_id: compass-multitenant-memory-20260830
> 分层口径:无悔=无论提审结果都该做 · 赌注=提审通过后做 · 冻结=等真实外部用户(P3 解冻)
> DoD 沿用 §⓪-E:完成 = 生产 + 登记 + 至少一个真实消费者(或预注册消费计划)

## M0 · 提审材料(本周,已齐)

- [x] 设计文档一页(三层映射/地基盘点/硬规则/验收四探针)
- [x] 地基实物在产证明:scoped token 六项矩阵 + v0.9 JWT 五项矩阵(8/30)
- [x] 安全修复记录:TCP scope(commit 已留)+ v0.9 JWT-only(acb3423)+ nginx 暴露面清零(8770 入口全关)

## M1 · 迁移底座(无悔 · 8770 退役 9/15 前后均可动工)

- [ ] **T1 多用户模型转正**:v0.9 的 users/agents/observations(user_id 外键)沉淀为 8097 正式服务的数据 schema。判据:建表 + 建用户/agent/obs 读写 smoke 通过。
- [ ] **T2 鉴权层统一**:Bearer JWT(人)+ scoped token(agent)双轨,复用 tokens.json 机制;header-only 身份在代码层禁止(compile 期或启动自检)。判据:五项矩阵(冒充 401/无凭证 401/投毒写 401/合法 JWT 200/不一致 header 401)在新服务重跑全绿。

## M2 · 自助闭环(赌注 · 提审通过后)

- [ ] **T3 signup 迁移+加固**:v0.9 signup 端点迁入正式服务,补防枚举(登录失败统一文案)+ 限流。判据:signup→login→JWT→recall 本人空间 e2e。
- [ ] **T4 token 自助管理**:登录用户创建/列表/撤销 agent token,scopes 限定本人 project(服务端强制,不信任客户端传 scope)。判据:四步 e2e = signup → create token → agent 用 token recall 命中 → 撤销后 DENY。
- [ ] **T5 primary project 自动初始化**:新用户首登录自动建 `u_<id>_memory` 空间。判据:新 signup 用户无参数 recall 返回空结果而非 4xx/500。

## M3 · 隔离验收自动化(与 M2 并行)

- [ ] **T6 四探针脚本化**:① 跨用户读 DENY ② 跨用户写 DENY ③ 同用户跨设备命中同一空间 ④ 撤销即时生效。判据:signup 后无人值守自动产出四绿报告(探针即 T4 e2e 的产品化)。
- [ ] **T7 常态回归**:四探针进 cron/supervisor 定期跑(防后续改动破坏隔离)。判据:连续 7 天自动报告无红。

## M4 · 运营护栏(部分无悔,部分冻结)

- [ ] **T8 TCP 版 tokens.json 热加载**(无悔):去 `systemctl restart` 依赖,撤销即时生效。判据:revoke 后旧 token 下一请求即 DENY,无重启。
- [ ] **T9 per-token 限流**(无悔):mcp_server.py 已有 rate-limit 雏形,接正式服务。判据:超限 429 且不伤及他 token。
- [ ] **T10 租户数据导出/删除**(冻结 · 等 P3 首批真实用户):对外商用合规项,提前做=无人消费。解冻:P3 首个外部安装。

## 依赖与排序

```
T1 → T2 → (T3, T5) → T4 → T6 → T7
T8/T9 独立可并行,随时插队
T10 冻结
```

## 与现有账本的挂接

- 本清单由 P2 提审材料驱动;M2-M3 动工前提 = P2 提审通过(用户 8/31 提交)。
- 8770 退役(9/15)时 T1 必须已有落点,否则 v0.9 多用户模型随服务一同丢失。
