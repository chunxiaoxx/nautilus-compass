# fact_status 覆盖率报告(E1 首件 · 2026-10-09 · R417)

> 来源:MEMX 效用表首跑抓出的缺口。纯报告零改写——修复=人工核验批量补标注(M5 纪律:daemon 不自动改写)。

- 总条目:161;fact_status 缺失:**93** 条(57%);
- 缺失原因:三件套上线(9/9)前的老条目无此字段;
- 影响:recall 带出空标注→归因算子 B 类误判面扩大(昨日实测 2 例);
- 修复建议:按 batch 人工核(每小时 ~40 条),核后补 `fact_status: measured|inferred|heard` 一行至 frontmatter;
- 候选清单如下(全列):

- [ ] _NODE_nautilus-compass.md
- [ ] aegis-compass-competitor-20260907.md
- [ ] arm-a-summary-layer-pass-20260903.md
- [ ] assay_gate_test.md
- [ ] benchmark-naming-licensing-20260902.md
- [ ] cheap-tier-close-and-watcher-20260904.md
- [ ] compass-daemon-pylibs-rootcause-20260830.md
- [ ] compass-roadmap-20260907.md
- [ ] convergence-state-snapshot-20260809.md
- [ ] convergence-state-snapshot-20260821.md
- [ ] d13-judge-retry-verdict-20260831.md
- [ ] d14-abstention-verdict-20260902.md
- [ ] daemon-9876-watchdog-rootcause-20260908.md
- [ ] daemon-auth-and-hf-offline-20260901.md
- [ ] devto-operations-20260908.md
- [ ] e2e-context-fix-and-tr-diagnosis-20260828.md
- [ ] emb-bakeoff-bge-stays-20260925.md
- [ ] feedback-ark-coding-plan-not-metered-api.md
- [ ] gmail-verify-production-20260906.md
- [ ] gpu-651799-expiry-incident-20260831.md
- [ ] gpu-e2e-rootcause-chain-20260829.md
- [ ] gpu-instance-reuse-not-rent.md
- [ ] gpu-old-disk-restart-20260903.md
- [ ] hud-multiview-crosstalk-fix-20260901.md
- [ ] inbox-agent-round-20260831.md
- [ ] industry-ilya-ssi-continual-learning-20260822.md
- [ ] launch-sprint-status-20260905.md
- [ ] license-modified-mit-20260904.md
- [ ] lmev2-first-full-baseline-20260830.md
- [ ] lmev2-judge-401-envvar-pitfall.md
- [ ] lmev2-pipeline-smoke-proven-20260830.md
- [ ] lmev2-three-knives-tuning-20260830.md
- [ ] lmev2-upstream-attribution-20260902.md
- [ ] memory-audit-seven-operators-20260907.md
- [ ] minimax-coding-plan-provider.md
- [ ] no-jargon-user-correction-20260829.md
- [ ] p1-host-migration-http-20260906.md
- [ ] p2-submission-terms-review-20260830.md
- [ ] p2v2-lora-milestone-20260930.md
- [ ] paper-roadmap-history-20260904.md
- [ ] propagation-layer-order-20260904.md
- [ ] pypi-311-published-20260906.md
- [ ] security-v09-xuserid-impersonation-20260830.md
- [ ] security-workbuddy-token-scoping-20260830.md
- [ ] session-contract-dogfood-bridge-20260822.md
- [ ] session-contract-fuel-loop-deploy-20260822.md
- [ ] session-contract-fuel-loop-live-20260822.md
- [ ] session-contract-gold-replication-20260822.md
- [ ] session-contract-l4a-distill-20260822.md
- [ ] session-contract-recall-usefulness-20260823.md
- [ ] session_00b61b64.md
- [ ] session_20260715_backend_502_coreLive_override_incident.md
- [ ] session_20260715_cloud_box_health_audit.md
- [ ] session_20260716_biomysterybench_P1_pipeline.md
- [ ] session_20260716_biomysterybench_scaffold.md
- [ ] session_20260716_eval_recall_v230_rerun.md
- [ ] session_20260717-0301_B理论沉淀CHARTER-0B.md
- [ ] session_20260717-0313_合约兑现SSOT同步V5.md
- [ ] session_20260717-0335_SSOT副本探针已上线.md
- [ ] session_20260717-1259_cloud-BGE过载召回全拒.md
- [ ] session_20260718-0925_compass价值实测-SSOT三方矛盾.md
- [ ] session_20260718-1132_reinforce修复-合约核销0718.md
- [ ] session_20260718-1142_差异化层-0-000是错尺子非无信号.md
- [ ] session_20260718-1201_drift护城河实测0-92-不需ARK.md
- [ ] session_20260722-0853_FDE表单校准事件.md
- [ ] session_20260722-1251_client-auto-reconnect-shipped.md
- [ ] session_20260722-1251_MCP-TCP-auth-landed.md
- [ ] session_20260722-1251_server-status-endpoint-added.md
- [ ] session_20260722-1251_TLS-demo-observation-one.md
- [ ] session_20260722-1251_TLS-demo-observation-two.md
- [ ] session_20260722-1257_client-auto-reconnect-shipped.md
- [ ] session_20260722-1257_MCP-TCP-auth-landed.md
- [ ] session_20260722-1257_server-status-endpoint-added.md
- [ ] session_20260722-1257_TLS-demo-observation-one.md
- [ ] session_20260722-1257_TLS-demo-observation-two.md
- [ ] session_20260807-0050_fde三期独立仓结构性变更.md
- [ ] session_20260807-2111_闭环收敛状态-fuel-loop唯一闸门.md
- [ ] session_20260822-1918_tribal-compass-daemon-port.md
- [ ] session_20260822-1918_tribal-feishu-select-id.md
- [ ] session_20260822-1918_tribal-utf8-explicit.md
- [ ] session_20260823-0912_goalmode-heartbeat-alert.md
- [ ] session_20260823-0935_goalmode-heartbeat-alert.md
- [ ] session_20260823-1031_tribal-windows-node-rename-epe.md
- [ ] session_20260824-1047_云桥MCP接不上求诊.md
- [ ] session_20260824_N4云容量体检三连根因.md
- [ ] session_9c3b69dc.md
- [ ] session_b2b522dd.md
- [ ] session_income_flatline_rootcause_20260824.md
- [ ] session_v3_launch_closure_20260824.md
- [ ] sota-eval-day-20260827.md
- [ ] test-security-stability-20260902.md
- [ ] week-review-20260927-1003.md
- [ ] zhihu-publisher-ready-20260927.md

## batch-1 修复记录(2026-10-09 · 效用表优先级 top3 已核补)

按效用表 B 类归因命中优先:daemon-9876-watchdog-rootcause(实测 349s 锚)/lmev2-upstream-attribution(纠偏事件实证)/arm-a-summary-layer-pass(500 题对照实测)——三条均为亲历实测记录,补 `fact_status: measured`(原创者核,非自动改写)。余 90 条按 batch 推进,高频命中优先。

## batch-2 修复记录(2026-10-09 · 16 条已核补)

measured×15(实测读数/事件记录类)+inferred×2(_NODE 聚合节点/assay_gate_test 测试桩)。累计已核:batch-1×3+batch-2×16=19 条;覆盖率 missing 93→74。剩余 74 条按同模式分批推进(b2 续:convergence 前段/通信类/竞品类……)。
