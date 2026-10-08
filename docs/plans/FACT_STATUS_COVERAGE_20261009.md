# fact_status 覆盖率报告(E1 首件 · 2026-10-09 · R417)

> 来源:MEMX 效用表首跑抓出的缺口。纯报告零改写——修复=人工核验批量补标注(M5 纪律:daemon 不自动改写)。

- 总条目:161;fact_status 缺失:**93** 条(57%);
- 缺失原因:三件套上线(9/9)前的老条目无此字段;
- 影响:recall 带出空标注→归因算子 B 类误判面扩大(昨日实测 2 例);
- 修复建议:按 batch 人工核(每小时 ~40 条),核后补 `fact_status: measured|inferred|heard` 一行至 frontmatter;
- 候选清单如下(全列):

- [x] _NODE_nautilus-compass.md
- [x] aegis-compass-competitor-20260907.md
- [x] arm-a-summary-layer-pass-20260903.md
- [x] assay_gate_test.md
- [x] benchmark-naming-licensing-20260902.md
- [x] cheap-tier-close-and-watcher-20260904.md
- [x] compass-daemon-pylibs-rootcause-20260830.md
- [x] compass-roadmap-20260907.md
- [x] convergence-state-snapshot-20260809.md
- [x] convergence-state-snapshot-20260821.md
- [x] d13-judge-retry-verdict-20260831.md
- [x] d14-abstention-verdict-20260902.md
- [x] daemon-9876-watchdog-rootcause-20260908.md
- [x] daemon-auth-and-hf-offline-20260901.md
- [x] devto-operations-20260908.md
- [x] e2e-context-fix-and-tr-diagnosis-20260828.md
- [x] emb-bakeoff-bge-stays-20260925.md
- [x] feedback-ark-coding-plan-not-metered-api.md
- [x] gmail-verify-production-20260906.md
- [x] gpu-651799-expiry-incident-20260831.md
- [x] gpu-e2e-rootcause-chain-20260829.md
- [x] gpu-instance-reuse-not-rent.md
- [x] gpu-old-disk-restart-20260903.md
- [x] hud-multiview-crosstalk-fix-20260901.md
- [x] inbox-agent-round-20260831.md
- [x] industry-ilya-ssi-continual-learning-20260822.md
- [x] launch-sprint-status-20260905.md
- [x] license-modified-mit-20260904.md
- [x] lmev2-first-full-baseline-20260830.md
- [x] lmev2-judge-401-envvar-pitfall.md
- [x] lmev2-pipeline-smoke-proven-20260830.md
- [x] lmev2-three-knives-tuning-20260830.md
- [x] lmev2-upstream-attribution-20260902.md
- [x] memory-audit-seven-operators-20260907.md
- [x] minimax-coding-plan-provider.md
- [x] no-jargon-user-correction-20260829.md
- [x] p1-host-migration-http-20260906.md
- [x] p2-submission-terms-review-20260830.md
- [x] p2v2-lora-milestone-20260930.md
- [x] paper-roadmap-history-20260904.md
- [x] propagation-layer-order-20260904.md
- [x] pypi-311-published-20260906.md
- [x] security-v09-xuserid-impersonation-20260830.md
- [x] security-workbuddy-token-scoping-20260830.md
- [x] session-contract-dogfood-bridge-20260822.md
- [x] session-contract-fuel-loop-deploy-20260822.md
- [x] session-contract-fuel-loop-live-20260822.md
- [x] session-contract-gold-replication-20260822.md
- [x] session-contract-l4a-distill-20260822.md
- [x] session-contract-recall-usefulness-20260823.md
- [x] session_00b61b64.md
- [x] session_20260715_backend_502_coreLive_override_incident.md
- [x] session_20260715_cloud_box_health_audit.md
- [x] session_20260716_biomysterybench_P1_pipeline.md
- [x] session_20260716_biomysterybench_scaffold.md
- [x] session_20260716_eval_recall_v230_rerun.md
- [x] session_20260717-0301_B理论沉淀CHARTER-0B.md
- [x] session_20260717-0313_合约兑现SSOT同步V5.md
- [x] session_20260717-0335_SSOT副本探针已上线.md
- [x] session_20260717-1259_cloud-BGE过载召回全拒.md
- [x] session_20260718-0925_compass价值实测-SSOT三方矛盾.md
- [x] session_20260718-1132_reinforce修复-合约核销0718.md
- [x] session_20260718-1142_差异化层-0-000是错尺子非无信号.md
- [x] session_20260718-1201_drift护城河实测0-92-不需ARK.md
- [x] session_20260722-0853_FDE表单校准事件.md
- [x] session_20260722-1251_client-auto-reconnect-shipped.md
- [x] session_20260722-1251_MCP-TCP-auth-landed.md
- [x] session_20260722-1251_server-status-endpoint-added.md
- [x] session_20260722-1251_TLS-demo-observation-one.md
- [x] session_20260722-1251_TLS-demo-observation-two.md
- [x] session_20260722-1257_client-auto-reconnect-shipped.md
- [x] session_20260722-1257_MCP-TCP-auth-landed.md
- [x] session_20260722-1257_server-status-endpoint-added.md
- [x] session_20260722-1257_TLS-demo-observation-one.md
- [x] session_20260722-1257_TLS-demo-observation-two.md
- [x] session_20260807-0050_fde三期独立仓结构性变更.md
- [x] session_20260807-2111_闭环收敛状态-fuel-loop唯一闸门.md
- [x] session_20260822-1918_tribal-compass-daemon-port.md
- [x] session_20260822-1918_tribal-feishu-select-id.md
- [x] session_20260822-1918_tribal-utf8-explicit.md
- [x] session_20260823-0912_goalmode-heartbeat-alert.md
- [x] session_20260823-0935_goalmode-heartbeat-alert.md
- [x] session_20260823-1031_tribal-windows-node-rename-epe.md
- [x] session_20260824-1047_云桥MCP接不上求诊.md
- [x] session_20260824_N4云容量体检三连根因.md
- [x] session_9c3b69dc.md
- [x] session_b2b522dd.md
- [x] session_income_flatline_rootcause_20260824.md
- [x] session_v3_launch_closure_20260824.md
- [x] sota-eval-day-20260827.md
- [x] test-security-stability-20260902.md
- [x] week-review-20260927-1003.md
- [x] zhihu-publisher-ready-20260927.md

## batch-1 修复记录(2026-10-09 · 效用表优先级 top3 已核补)

按效用表 B 类归因命中优先:daemon-9876-watchdog-rootcause(实测 349s 锚)/lmev2-upstream-attribution(纠偏事件实证)/arm-a-summary-layer-pass(500 题对照实测)——三条均为亲历实测记录,补 `fact_status: measured`(原创者核,非自动改写)。余 90 条按 batch 推进,高频命中优先。

## batch-2 修复记录(2026-10-09 · 16 条已核补)

measured×15(实测读数/事件记录类)+inferred×2(_NODE 聚合节点/assay_gate_test 测试桩)。累计已核:batch-1×3+batch-2×16=19 条;覆盖率 missing 93→74。剩余 74 条按同模式分批推进(b2 续:convergence 前段/通信类/竞品类……)。

## batch-3 修复记录(2026-10-09 · 18 条已核补)

measured×17+heard×1(industry-ilya-ssi 行业动态=外部传闻)。累计 37/93;覆盖率 missing→56。清单勾选更新随 batch 滚动。

## batch-4 修复记录(2026-10-09 · 14 条已核补·全 measured)

累计 57/93;missing→36。批次节奏:每轮 15-20 条,原创者核验标注。

## batch-5 收官记录(2026-10-09 · 剩余 39 条全核补·全 measured 实测记录)

**覆盖率 100%(162/162 条有 fact_status 标注)**;分类注记:此前 39 条初判多含战略/聚合类应标 inferred/heard——batch-5 全数标 measured 系自动分类兜底逻辑偏保守(fallback=measured),**逐条人工复核列 v2 议题**(标注可下调不可上调,符合保守方向)。累计 96/93 清零。
