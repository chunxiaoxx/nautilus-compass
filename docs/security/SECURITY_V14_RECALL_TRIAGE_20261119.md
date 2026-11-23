# v14 recall 安全报告跟进卡

> 报告来源：Nagizaaz Shaik，Gmail thread `1a1ab9487dc51507`，2026-11-05。
> 本卡只记录当前源码核对与处理边界，不代表已修复或已部署。

## 当前结论

- [实测] 报告人指出的两个风险在当前工作树仍有对应代码形态。
- [实测] `GET /v1/v14/recall` 的函数签名没有 `Depends(auth_user)`，`scope=user` 仍可触发跨项目扫描。
- [实测] `POST /v1/v14/ingest_obs` 已要求 Bearer JWT，但 `project` 值在拼接 `~/.claude/projects/<project>/memory` 前仍没有单段名称白名单校验。
- [实测] 在本机转发到 8770 的服务上，用无 Authorization、无 X-Tenant-ID、无 X-User-ID 的 GET 请求读取 `scope=project&project=nautilus-v5`，服务返回 HTTP 200、`ok=true` 和 5 条项目记忆摘要。只保存了状态和计数，没有把记忆正文写入本卡。
- [实测] 同一入口的无认证 `scope=user` 请求在 20 秒内超时，说明跨项目扫描仍然会执行或等待，不能把超时误读成权限拦截。
- [不可验] 这次探针只证明当前转发入口的行为，尚未证明所有生产副本一致。

## 影响

这不是单纯的检索慢问题，而是身份和项目命名空间没有形成可信绑定。服务需要能证明“这个用户有权读取这个项目”，并拒绝把任意路径当成项目名。

## 处理顺序

1. 只读盘点所有 v14 recall 消费者，确认哪些调用仍依赖无 JWT 的旧协议。
2. 先在测试中加入未认证读取、伪造租户、跨项目和路径逃逸的负向用例。
3. 选择迁移方案。完整方案是认证身份绑定项目并补项目名白名单。临时方案是先关闭公网 `scope=user` 或把 v14 入口限制到内网。
4. 重新跑本地和远端负向验证，保存请求、状态码、响应摘要和哈希。
5. 给报告人发只确认事实和处理阶段的邮件草稿，修复时间和披露日期以实际证据为准。

## 对外回复边界

当前不应回复“已经修好”或给出未经验证的生产承诺。可回复已收到报告、正在核对当前部署和消费者、会按协调披露流程更新。

## 确认邮件草稿

> Gmail draft message id `1a1f72c912c39a97`，thread `1a1ab9487dc51507`，未发送。

Hello Nagizaaz,

Thank you for following up on issue #66 and for sending the technical details privately.

We have received the report and are checking the current v14 recall and ingest paths, the deployed exposure, and the existing consumers before making a change. We are treating the report as a security issue under the coordinated-disclosure process. We will update this thread with the verified status and the remediation path.

At this stage we are not claiming that the issue is fixed or that a production deployment has changed.

## 2026-11-20 本地跟进

- [实测] 8097 MCP HTTP 无认证请求返回 401。
- [实测] 9876 daemon 的定向鉴权测试通过，ping 保持可用，其他动作无 token 被拒绝。
- [实测] 本地 `v14_recall` 已加 Bearer JWT 依赖，并要求 `COMPASS_V14_PROJECT_MAP` 提供明确的用户到项目映射。映射缺失时返回 403，`scope=user` 在过滤 union 实现前保持关闭。
- [实测] 9876 鉴权失败路径修复了 Unix socket 上 `lsof tcp:0` 导致的响应延迟。
- [实测] 相关 MCP、daemon、auth、scope 和 v14 边界测试共通过 101 条。没有部署到 8770，也没有发送外部回复。
- [未核] 8770 远端转发本轮无认证请求超时，不能把超时当作权限修复。

Best regards,
Chunxiao Wang
nautilus-compass
