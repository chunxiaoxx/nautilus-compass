---
trace_id: 2026-07-20T22:00:00Z#prime-001#fuel-sync-20260720
source_trace_id: 2026-07-20T22:00:00Z#prime-001#fuel-sync-20260720
source_repo: nautilus-v5
source_files:
  - C:/Users/chunx/Projects/nautilus-v5/fuel_scorecard_20260721_from_feedback_v2.md
  - C:/Users/chunx/Projects/nautilus-v5/fuel_triage_20260720_45rows.md
owner_frame: platform
artifact_type: v5_vertical_fuel_queue
created_at_utc: 2026-07-21T07:19:29Z
a_class_count: 10
external_verified_delta: 0
local_verify_pass_count: 1
local_verify_fail_count: 9
status: local_external_verify_run
proof: source_scorecard_top10
---

# V5 Vertical Fuel Queue 20260721

This queue materializes the V5 fuel protocol follow-up into ten tracked platform work items.
It does not claim that external verification has run.

## Queue Contract

- Selection rule: first 10 risk-priority candidates from `fuel_scorecard_20260721_from_feedback_v2.md`.
- Verification status: local attachment/question-table verification ran on 2026-07-21. This is not the platform scoreboard `external_verified` counter.
- Hash rule: `payload_hash = sha256(trace_id|source_row|problem_title|lane|required_fix|verification_gate)`.
- Lanes: `attachment_repair`, `field_normalization`, `ai_trace_rewrite`, `data_governance`.

## Items

| item_id | trace_id | source_row | problem_title / short prompt | lane | required_fix | verification_gate | status | payload_hash |
|---|---|---:|---|---|---|---|---|---|
| v5vf-20260721-001 | 2026-07-20T22:00:00Z#prime-001#fuel-sync-20260720 | row 14 | 一切按照招标要求制作 | attachment_repair | 核对附件列表声明格式与文件夹实际文件格式，修正不一致项。 | 附件列表中的每个文件名、格式、数量与实际文件夹逐项一致。 | local_verify_failed | 2b8da6035bec9183b1b079318280fe411c7198b3aac7bb25e73bacfaf7d27060 |
| v5vf-20260721-002 | 2026-07-20T22:00:00Z#prime-001#fuel-sync-20260720 | row 27 | 制造业HR工伤赔偿与未缴工伤保险处理 | attachment_repair | 补齐工伤保险条例、社会保险法、劳动合同法、劳务派遣暂行规定四个附件，或删除无法提供的附件声明。 | 4个声明附件均存在且可打开，题目引用与附件列表一致。 | local_verify_failed | 9b0195d9f207d67536fd39b529faea9b23392473a2803f36c5951c1155ae32a9 |
| v5vf-20260721-003 | 2026-07-20T22:00:00Z#prime-001#fuel-sync-20260720 | row 19 | 人力资源外包客服的合同、五险一金与离职谈判流程 | field_normalization | 把每个附件的使用方式写入做题关键步骤对应环节。 | 每个附件至少在一个步骤中被明确引用，且说明读取字段或使用目的。 | local_verify_failed | 4e0f607d7e0e2b9abe6a6d0bbbe2982e98662fbd7fc2ef5c976b2654b83b96da |
| v5vf-20260721-004 | 2026-07-20T22:00:00Z#prime-001#fuel-sync-20260720 | row 18 | 人力资源合同文档批量生成与文件数据整理 | attachment_repair | 打开文件夹逐一核对实际文件名，修正题目列中的附件引用，并扩写附件总结。 | 题目列附件名与实际文件名完全一致，附件总结覆盖每个附件的关键字段和用途。 | local_verify_failed | 0c0148898267e10019e123e64511c09f2669684dc862aa321cd647fb4fae3cd1 |
| v5vf-20260721-005 | 2026-07-20T22:00:00Z#prime-001#fuel-sync-20260720 | row 5 | 1000人客户公司社医保同城转移增员业务 | attachment_repair | 删除附件列表中的政府网站链接，改为实际上传文件名；如需政策链接，移入参考资料字段。 | 附件列表只包含实际文件名，网址不再作为附件声明。 | local_verify_failed | aa725462deaa235f5b63d5fad40ffdc16bb7b67810222aff39dc28a79dda70c6 |
| v5vf-20260721-006 | 2026-07-20T22:00:00Z#prime-001#fuel-sync-20260720 | row 30 | 小红书矩阵账号运营与内容数据整理 | attachment_repair | 打开文件夹核对22个实际文件，把2个docx、19个xlsx、1个pdf全部列入附件列表。 | 附件列表声明22个文件，数量、扩展名、文件名均与文件夹一致。 | local_verify_failed | c42cad16173f38d9d451861dd7e7ea416e8c34edae3390215ececc056c3b9578 |
| v5vf-20260721-007 | 2026-07-20T22:00:00Z#prime-001#fuel-sync-20260720 | row 28 | 汽车电子结构工程师招聘筛选 | ai_trace_rewrite | 把10个动词宾语式步骤改写为自然业务流程，合并机械短句并保留可执行动作。 | 做题关键步骤不再连续使用同构动词宾语模板，仍能覆盖简历筛选、岗位匹配、风险判断和输出要求。 | local_verify_failed | b1680965af95ef816488d3224666fa407b9b9c105f6e2d2678370817ae39ff9b |
| v5vf-20260721-008 | 2026-07-20T22:00:00Z#prime-001#fuel-sync-20260720 | row 24 | 食品客户人力资源服务竞标方案 | attachment_repair | 补充赞华附件或从题目与附件列表中删除赞华，统一8家/7家竞品口径。 | 题目列竞品数量、竞品名单与附件列表逐项一致。 | local_verify_failed | aa89f298fb882bda705dd8588a6ab85eedc20dd0691bbe3c283dafc2fccf408a |
| v5vf-20260721-009 | 2026-07-20T22:00:00Z#prime-001#fuel-sync-20260720 | row 13 | B2B人力资源服务企业24页宣传册设计 | attachment_repair | 补齐缺失的4个附件，或修正附件列表为实际1个文件并调整题目依赖。 | 附件列表数量与文件夹一致，题目不依赖未上传附件。 | local_verify_failed | 41b0f20ec797c2deb126fc23d40b4b704147c3691e7d686a6a5962f2a89ccffc |
| v5vf-20260721-010 | 2026-07-20T22:00:00Z#prime-001#fuel-sync-20260720 | row 12 | 多分公司薪资社保与残保金测算 | field_normalization | 打开附件确认实际分公司数量，统一题目、思维链、做题步骤中的数量口径。 | 题目列、思维链、做题步骤的分公司数量完全一致，并能从附件中追溯。 | local_verify_passed | 1dc21a469e5b9f554785cbab9e727371467a3ef7b1d0573aa91a65b189a82788 |

## Open Gaps

- Local attachment/question-table verification ran; only row 12 passed its specific gate.
- Platform scoreboard canonical verification has not run; `external_verified_delta` remains 0.
- This artifact is a queue and audit surface only; it does not mutate production services, timers, or cloud state.
