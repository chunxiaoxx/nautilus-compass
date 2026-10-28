---
trace_id: 2026-07-20T22:00:00Z#prime-001#fuel-sync-20260720
artifact_type: local_external_verify_report
created_at_utc: 2026-07-21T07:32:26Z
source_queue: C:/Users/chunx/Projects/nautilus-core/docs/embodied/v5_vertical_fuel_queue_20260721.md
source_feedback_xlsx: C:/Users/chunx/Downloads/大模型训练-问题反馈表_清理版_v2.xlsx
attachment_root: C:/Users/chunx/AppData/Local/Temp/claude/C--Users-chunx-Projects-nautilus-core/efea1144-0b71-4702-8732-646859f091b0/scratchpad/batch1/titi/大模型训练师-题目
local_verify_pass_count: 1
local_verify_fail_count: 9
external_verified_delta: 0
---

# V5 Vertical Fuel Local External Verification 20260721

This report verifies the first 10 vertical fuel candidates against the locally available Excel feedback sheet and the platform-dialog attachment workspace.

Important boundary: this is a local file-and-table verification pass. It is not the production scoreboard `external_verified` counter and it does not mint income.

## Summary

| result | count |
|---|---:|
| local verify passed | 1 |
| local verify failed | 9 |
| production external_verified delta | 0 |

## Evidence Inputs

- Feedback workbook: `C:/Users/chunx/Downloads/大模型训练-问题反馈表_清理版_v2.xlsx`
- Attachment workspace: `C:/Users/chunx/AppData/Local/Temp/claude/C--Users-chunx-Projects-nautilus-core/efea1144-0b71-4702-8732-646859f091b0/scratchpad/batch1/titi/大模型训练师-题目`
- Queue file: `C:/Users/chunx/Projects/nautilus-core/docs/embodied/v5_vertical_fuel_queue_20260721.md`

## Item Verdicts

| item_id | row | owner | gate | local verdict | evidence |
|---|---:|---|---|---|---|
| v5vf-20260721-001 | 14 | 李敏 | Attachment list names, formats, and counts match actual folder files. | failed | Actual folder has 10 files including the task workbook. The task workbook still lists symbolic attachment labels and final output only names `附件八-优化后的标书`, not the 9 actual attachment file names. |
| v5vf-20260721-002 | 27 | 李强 | Four declared law attachments exist and match the task. | failed | Available zip contains a different task package (`海运操作专员`/用工模式合规) and files for 外包协议、劳动法、劳动合同法、劳务派遣. It does not match the queue's manufacturing injury compensation problem or its required 工伤保险条例/社会保险法/劳动保障监察条例 gate. |
| v5vf-20260721-003 | 19 | 茅丹 | Every attachment is explicitly used in the task steps. | failed | Eight source files exist, but the task steps remain generic and do not bind each attachment to a specific step or field. |
| v5vf-20260721-004 | 18 | 肖兵 | Prompt attachment names match actual file names and summary covers each attachment. | failed | Actual folder has 25 files including nested groups. The task workbook still uses broad categories and includes a stale `file:///E:/...` reference; attachment summary is only generic category text. |
| v5vf-20260721-005 | 5 | 张亦欣 | Attachment list contains only actual uploaded file names, not URLs. | failed | The task workbook's `相关附件` field still contains government website URLs; the folder only contains the task workbook itself. |
| v5vf-20260721-006 | 30 | 宋斌斌 | Attachment list declares all 22 actual files with exact names and formats. | failed | Actual folder has 22 files. The task workbook summarizes two documents plus screenshot counts, but does not list all 22 exact file names. |
| v5vf-20260721-007 | 28 | 王雪影 | Steps no longer show rigid verb-object AI-trace pattern. | failed | The zip exists and has usable attachments, but the task output still uses numbered, template-like output descriptions; the rewrite gate is not cleared by file existence alone. |
| v5vf-20260721-008 | 24 | 单旻辰 | Competitor count and names are consistent across prompt and attachments. | failed | The task workbook's task text still says 8 competitors and includes 赞华, while the task summary says 7 competitors and the folder has 7 competitor files plus our company and client. |
| v5vf-20260721-009 | 13 | 朱进 | Attachment list matches actual folder or the prompt no longer depends on missing files. | failed | Actual folder has one material file plus workbook, but the task workbook still asks for VI manual, brand copy, AI logo source, and reference images. |
| v5vf-20260721-010 | 12 | 成鑫 | Branch/company count is confirmed from attachment and consistent in task/steps. | passed | `各分公司上一年度在职职工人数及年平均工资数据.xlsx` contains 50 company data rows; the task workbook consistently uses 50 companies in the relevant output requirement. |

## Interpretation

Only one candidate is ready to move forward as locally verified fuel under its current gate. The other nine still create useful training signal, but as repair tasks rather than accepted fuel: they teach attachment manifest discipline, exact evidence binding, and removal of template traces.

## Next Action

Do not mint these 10 as externally verified. Route the nine failed items back to repair, with row 12 eligible for the next canonical verification stage.
