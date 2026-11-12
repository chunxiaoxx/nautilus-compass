[任务单 L1/L2/L3] 中转站+组织记忆优化路线图(深度分析版)——orgup 开启前置与中长期基建

Mac compass:

用户准备用 orgup 开启五框,要求中转站与组织记忆优化给出分层路线。以下 L1/L2/L3 为 compass 只读顾问深度分析产出,**L1 请立即执行(L0 前置检查已由顾问完成并确认)**,L2/L3 按序排期。

## L0 前置状态(顾问已实测确认,你无需重做)
- relay 主路径 `/v1/*` **已直连 new-api**(nginx 实况:proxy_pass 3000;注入层仅剩 `/v1i/*` opt-in)——orgup 开框安全
- 模型四键已回滚大写 `[1M]` 且实弹 200
- skills 43→8(私有配方保留,通用类/CLI 族 35 个移 `skills_disabled_20261031/` 可逆)
- 塌缩会话 24185386 交接文档已就绪:`nautilus-migration/HANDOFF_calm_jingling_peach_20261031.md`

## L1 · 立即(今天,orgup 开框配套)
1. **orgup 前置自检脚本**(`~/bin/orgup_preflight`,跑一次 ≤30s):
   - relay 直连核验:`curl /v1` 状态 ok
   - 模型四键探测:glm-5.3[1M]/MiniMax-M3[1M]/k3-256k 各一发 min 请求(503 即报警——防"渠道缺口"类故障复发)
   - daemon 9876 / embed 8400 / rerank 8401 三探活
   - 塌缩会话清单列出(含 24185386),提示用户弃用
2. **塌缩会话清理**:24185386 按 HANDOFF 文档弃用归档(交接文档已就绪)
3. 五框 daemon/hooks 健康预检(compass 链外,v5/flywheel/venture 的 hooks 现状盘点入报告)
4. orgup 可开启;**观察指标**:各框 compact 触发点(应≥150k;6-7 万即报警,回报 compass)

## L2 · 本周(健壮性)
1. **relay count_tokens 端点**:new-api 旁路服务实现 Anthropic 兼容 `POST /v1/messages/count_tokens`(治 CC 对第三方模型的估算漂移——thrashing 根因之一)
2. **orgup 双模式改造**:desktop(五框 nclaude 原生长会话)/ mobile(happy 只监控+审批)分离——长活与轻交互分轨
3. happy 升级观察:1.2.5→新版 changelog 跟踪;issue 稿已备(`runtime/outreach/_happy_issue_draft_20261031.md`,数据齐)
4. **compact 熔断告警**:任一会话 1h 内 compact ≥3 次即告警到 compass 信箱(自动检测,防无感恶化)
5. 注入层重上预案(等 L3 定架构后):降量(<3KB 摘要)+白名单+预算硬顶(≤5% 上下文)+count_tokens 兼容

## L3 · 战略(组织记忆正解架构)
**org-memory-proxy 方向正确、实现错误**(全量 107KB 注入→上下文爆炸)。终局架构=**三层记忆,各有 owner 与预算**:
| 层 | 内容 | 预算 | 载体 |
|---|---|---|---|
| L0 常驻 brief | 平台是什么/五框/主线/纪律(ORG_BRIEF.md) | ≤3KB | 全局 CLAUDE.md(include) |
| L1 会话相关 | recall top5+24h 新鲜(compass hook 范本) | ≤5KB | 框内 hook,节流 10min |
| L2 深档按需 | soul 章程/台账/判例 | 不限 | 用户问才拉(session_search) |
**收敛原则:注入收敛到框内 hook(relay 回归纯透传)**——relay 注入无框感知(每个框塞同样的东西),hook 有 cwd 感知且有 compass 成熟范本;org-memory-proxy 降级为实验/审计角色,其"会话指纹缓存"设计(首见注入后冻结)值得 hook 借鉴。
配套:ORG_BRIEF 带 owner+日期(战略拍板同步更新);验收清单永久新增"认知面"三问(你是谁/平台是什么/主线是什么)。

## 执行与回执
- L1 今天;L2 排本周;L3 架构定稿后实施
- 每级完成在报告 `DIAG_cognitive_layer_20261031.md` 尾部追加回执
- 异常(503 复现/compact 触发点低/渠道缺口)即时回报 compass 信箱

—— compass 只读顾问 · trace=orgup-l123-roadmap-1031
