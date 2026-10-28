# Session 总结 · 2026-08-28(平台框 · 交接后首个大 session)

> 起手:SESSION_HANDOFF_NEXT 三步(loop 1h 挂起→四轮推进→用户解除);全程 11 commits 推 GitHub,未推量 0。

## 一、executor 复活闭环(今日最大件 · 等待项 #1 关闭)

1. **互等破局**:交接文档判"等 V5",V5 回函揭示真卡点=等平台的 verdict POST 协议+启动链出处 → 平台考古交付**复活钥匙包**(协议/主循环/CLI/evidence 对账规约/部署两选项)+ 100 题矿队列 checkout 上云。
2. **V5 收包 30min 复活**:schtasks 25min 保活本地跑,与 DPO 错峰并行零冲突。
3. **verdict 断链双缺陷修复**(平台代码,独立验证抓到):①`submit_verdict` base 缺失静默 return None(现 fallback 生产端点+SKIPPED_NO_BASE 可见化)②POST 失败零留痕+replay 幂等永久挡重发(现 `verdict_post_status` 写回 evidence+replay 幂等补发)。TDD 9 green,生产重放 200 实测。
4. **账本无损失**:漏发 2 条手动补发双 200,DB 读回(5a32ecfea844 t / a05b3e7bf95b f);evidence 85 个全量同步上云,auto-verify 对账恢复。verified 463→465 已被 supervisor 自动记账。
5. supervisor 判 ZERO=准确(ARK 欠费后零新生产)——监督逻辑验证有效,恢复即自动转绿。

## 二、变体生成批 1(管线全通,GOAL_STACK 4b 破顶③)

- 设计 v1(`docs/plans/2026-08-28-variant-generation-design.md`):OP-1 受控回注/五门质量门/novelty 二维门(行骨架×标识符取小,阈值 0.3 预注册)/判据三态。
- 内核+variant 流+跑批 CLI 全 TDD(16 green)。实作期三发现已固化:
  1. 变体 uid=合成内容哈希(防 evidence_candidates 前缀匹配双向污染对账);
  2. `variant_patch` 随行(合成 starter 无 commit,变体双门=fix 树+patch 必败/干净必过);
  3. completer 返回形状 dict 适配+JSON artifact 解包(SYSTEM_PROMPT 致 GLM 回 `{unified_diff}` 包裹,pilot proposed=0 根因)。
- pilot 两轮:第一轮 proposed=0(JSON 包裹,已修);第二轮撞 ARK **AccountOverdueError(403 欠费,定谳)**。
- **LLM 臂多元化(用户 A 级授权)**:GLM coding plan+minimax m3 key 拷入平台 secret 文件;executor PROVIDERS 加 minimax_m3+ANTHROPIC_PROVIDERS 泛化(V5 已先接 glm_plan);双臂 pong 冒烟实测 ✓(glm 需 RPM 节流)。第三轮 pilot(glm_plan 臂)跑批中。

## 三、例行与跨框

- 飞轮 GPU 锁提案回执:轻量锁够用,平台队列并入转移线⑤不单独立项(台账 B级#4)。
- SSOT 十三/十四次增量;三仓副本同步多轮;DECISION_LEDGER B级#4。
- V5 函三封投递(revival_kit/verdict_fix/ark_overdue),均带 trace_id+proof。
- 云分支拓扑债实证:生产分支 soul-audit-increment1+dirty(cherry-pick 流),择机专场正名,不阻塞。
- 云 backend `/api/health` 404(路由缺,旧账)挂起待理。

## 四、教训速查(本 session 新增)

1. **fail-soft 假 done**:静默 return None 比 crash 危险——POST 失败必须留痕(verdict_post_status)。
2. **对账 join key 是契约**:命名空间设计前先查前缀匹配逻辑(evidence_candidates startswith)。
3. **SYSTEM_PROMPT 会泄漏语义**:executor 的 JSON artifact 约定污染了变体提案输出格式——共用 completer 必须解包兼容。
4. 死因判读先查供给:ZERO≠executor 死,ARK 欠费=燃料臂断供(供给级故障)。

## 五、遗留与下一步

| 项 | 谁 | 判据 |
|---|---|---|
| 变体批 1 pilot 第三轮(glm_plan) | 平台(在跑) | proposed>0→放全批 30 模板→20-40 过门变体 |
| ARK 充值 | 用户(可选,GLM/minimax 已顶上) | doubao 难倒抽样需要它(批 1 判据第 4 门) |
| 三台阶回函 V5/compass | deadline 8/29 22:00 | 仓根回函 |
| executor 批量消费变体 | V5(schtasks 已活) | 新 verdict 入库→ZERO 转绿 |
| 云分支拓扑正名 / health 404 | 平台专场 | 择机 |
| 附件包(5 题结算+QC v1/v2) | 用户 | 路径提供 |

*生成:Claude Code via Happy · 2026-08-28*
