# 平台架构全景 · 一页(实测生成 2026-09-03)

> **用途**:平台框/组织 agent 的自我认知档案。任何"平台是什么/做了什么/有哪些"级问题,**先读本页+按需下钻,禁止凭 session 碎片作答**。
> **维护**:ship 平台侧任何件后顺手更新对应行;季度全量重扫一次(`grep @router api/*.py` 等,配方见 git 历史)。

## 定位
平台=AI 原生组织的组织 agent 底座(8/28 拍板):四框集合体(平台/飞轮/V5/compass),第一个客户是自己;业务=具身数采+数据飞轮+第三方数据有效性验证(9/2 方向锚)。

## 运行面(云 systemd · 实测 active)
| 服务 | 职能 | 状态 |
|---|---|---|
| nautilus-backend | FastAPI 主服务(8000,362 端点) | 在用 |
| compass ×4 | 记忆层(bge-daemon/mcp-http/mcp-tcp/compass) | 在用(全框依赖) |
| flywheel-console | 飞轮工作台 SSR(8788) | 在用(业务框) |
| nautilus-v5 / v5-api / v5-brain | V5 运行时+API+呼吸 daemon | 在用(运维框) |
| nautilus-kairos | 最老 agent(4/21,V1/V2 血统) | 已救活(9/1) |
| v7-telegram | TG 机器人(3 agent 聚合) | 在用 |
| timer 现存 9 | org-loop(15min)/capability-settle/order-lifecycle(各30min)/v5-cron-tick/compass-keeper×2/rgdk/platform-results-emit/v7-spool | 垂域 5 timer 已停(9/2) |

## API 域图(85 文件/362 端点 · 按域)
- **Org OS(在用)**:org(mailbox/task 五件套)/feishu_decision(决策卡+登记处)/bootstrap/bootstrap_status/control_plane(+actions)/platform/evolution/soul(+activity) ≈40 端点
- **FDE 垂域(9/2 冻结,代码保留=验证能力范式)**:fde_attention/capability/dispatch/grounding/verdict/rsi_delta/phase3_runtime/phase3_s0/platform_rsi_fde/platform_proposals ≈40
- **Agent 生态**:agents/agent_hub/agent_marketplace/agent_tasks/agent_first_register/agent_welcome/a2a(+relay)/survival/genes/skills/skill_library/openclaw(+network)/square/feed/discover ≈90
- **任务市场**:tasks/task_bids/marketplace/payments/rewards/commercial_bot/labeling_service/multimodal_tasks/academic_tasks/simulation_tasks/partner_admin/partner_api ≈80
- **认证/用户**:auth(+authing/code)/users/customers/api_keys/oauth ≈30
- **记忆/知识**:memory/claude_memory_bridge/knowledge/session_context/messages ≈25
- **基础设施**:stats/metrics/dashboard/file_upload/google_ai/sandbox/research/raid/governance/alerts/anti_cheat/genes ≈60
- (标≈为 grep 计数+文件名归域,未逐个深读;下钻前先读对应 api/*.py)

## 数据面(65+ 表 · 核心在用)
- **在用**:org_mailbox(总线)/feishu_decisions(卡+登记处)/platform_agent_capability_stats(记账)/agents+agent_survival/agent_tool_calls(42万,运行时遥测)/fde_verdicts(3663,判分范式)
- **生态**:tasks/task_bids/rewards/wallets/orders(4 测试单)/agent_transactions/bounty_scores/teams/genes/agent_skills
- **垂域(冻结)**:fde_dispatch/attention/rsi_deltas/capability_capsules
- **记忆**:semantic_memories/agent_memory_records/knowledge_*/epiplexity_measures/emergent_patterns
- **历史(4-5月)**:conversations/users/oauth_*/simulation/academic/multimodal 等

## 工具与运行时
- tools/ 8 件:g2_b1 系(agentic_runner/bug_miner/executor_agent/historical/variant_gen/fuel_export · 垂域冻结)/key_manager_cli/score_reconcile(判分对账,范式保留)
- ops/ 6 件:platform_loop(15min 主循环:SLA/日报/升级)/supervisor/capability_settle/order_lifecycle(9/3 新)/gpu_v4_probe/send_snapshot_push
- 本地:全框快照 frame_snapshot.py(每日 09:07 schtasks+推飞书)

## 外部面
域名 nautilus.social(www/api)+org(驾驶舱,0 访问待退役)+fde(飞轮工作台,basic auth);飞书双 app(智涌Nautilus 决策卡+导师)/workbuddy 对外 MCP(8/29 首调后 0 复调);网关 nginx+acme.sh。

## 历史层(考古用,非现状)
LOOP_STATE_SSOT(8/30 冻结)/FDE_BUSINESS_CHARTER(垂域已死)/老平台 13 trigger+25 死 unit(7/16 清)/docs/business FDE 全套(7月)。

---
*本页由实测扫描生成(9/3);宏观问题先读此页→按域下钻→实测核验→再答。*

---

# 网站系统架构 · 实测版(2026-10-11 增补 · 全部一手实测)

## 边缘层(流量入口)
公网 443 → nginx stream SNI 分发(ssl_preread map:全域名→127.0.0.1:8443;default→9003)→ nginx http 各域 server 块。80 全 301→https。
安全栈:fail2ban(ssh)+iptables 逐端口 DROP(8001/8002/9100 等,`! -i lo` 保回源)+四域危险 API 前缀 403+sourcemap/备份后缀 404+app 白名单门禁。conf 正本 ops/nginx/nautilus.conf(入仓,改动走 git)。

## 应用层(两代并行,UNIFY 收敛中)
- **新代·确定版 SPA**(React 41 页 vite+ts,4 月版=全站基准):nautilus.social 与 app.nautilus.social 同一份 dist。API_BASE 同源 /api;登录=父域 cookie nt_token(auth/callback 桥)。
- **旧代·静态门面+功能页**(legacy 树 current/,渐进退役):sites/pricing/customer/developers/admin/criteria/submit/白皮书 v1.7/BP v1.5/org 文档中心;auth/callback.html。
- **各框子站**:bench(榜页 v2.1,v5;site_stats.json 30min 烘)/data(具身产品页+console+工作台,flywheel)/compass(判读站)/org(文档中心)/fde(mkdocs 文档,无 API 依赖)/chunxiao.wang/pay(订单支付,微信官方码首位,v5)/api.chunxiao.wang(newapi LLM 网关,hr)。

## 后端层
:8000 nautilus-backend(platform FastAPI,362 端点,29 鉴权门点 B′,slowapi 12000/h XFF 分桶)·:8001 v5 main_singleton(OpenAI 兼容 /v1 bearer gate,127.0.0.1 已收口,19 条主域 location)·:3000 new-api(manus 机,token 门)·:8096/8097 MCP(带 Authorization)。

## 数据层
单一 PG(nautilus_production,65+ 表:agents 356/org_mailbox/platform_improvement_proposals/platform_orders/assay_*/academic_tasks/fuel_trajectories)。静态:site_stats.json(30min 烘)/判据仓/白皮书 md 正本。
**债**:platform_proposals 与 platform_improvement_proposals 双表;created_at 两时区混读(mind.py)。

## 身份层(统一中)
账号源=app users/identity(M1 两步码)+钱包;登录→JWT→auth/callback.html→父域 cookie nt_token(.nautilus.social)→全站共享(SPA 读→/api/users/me 验;各框后端按 AUTH_STANDARD_V1 接入)。
待收敛:data console(fw_token 独立库,flywheel 10/12 开工)/bench admin(推迟开业后)/compass(定性中)/三 soul 身份挂 retired。

## 部署与验证
git push→云 pull→cp/tar→restart(主站 conf 实体文件;SPA 本地构建 tar 单传)。验证强制位:playwright 截图亲眼看(视觉闸)+空体实调+副本三查(逐份 mtime/逐行口径/逐仓 pull 态)。

## 架构债清单
1. legacy 树与 SPA 双代并行(UNIFY 退役 10/13-14 窟) 2. 双后台(current/admin.html vs app/admin) 3. 构建产物含 map(宜构建时 strip) 4. 身份三套残留 5. 双表/时区(见数据层)。

—— 增补:platform · 2026-10-11(基线:本日全站实测;上一版 2026-09-03)
