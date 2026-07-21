# V5 fuel recall replay package (2026-07-21)

Source scorecard: `C:/Users/chunx/Projects/nautilus-v5/fuel_scorecard_20260721_from_feedback_v2.md`

Trace event: `2026-07-20T22:00:00Z#prime-001#fuel-sync-20260720`

Scope: first 10 candidates from the scorecard Top20 list, in source order. This package is a compass-side replay input artifact only. It does not claim cloud BGE backfill, daemon health, or recall hit rate, because those were not executed in this task.

## Replay Rows

| trace_id | problem_key | source_row | action_tag | payload_hash | intended_recall_query | replay_status | overloaded_status | notes |
|---|---|---:|---|---|---|---|---|---|
| `2026-07-20T22:00:00Z#prime-001#fuel-sync-20260720` | `fuel_20260721_row14_bid_attachment_format` | 14 | `attachment_format_mismatch` | `b4a0cf8139e5b7f930a077acf7b45798b43eef3304009328bd2fe43f63e38fd8` | `V5 fuel row14 一切按照招标要求制作 附件列表格式和文件夹实际格式不一致` | `not_run` | `not_run` | Needs attachment manifest check before recall ingestion. |
| `2026-07-20T22:00:00Z#prime-001#fuel-sync-20260720` | `fuel_20260721_row27_work_injury_missing_law_files` | 27 | `missing_attachments` | `6acbc46acfcccb5952e6d21c689beb5f4ce43358d5ce2022d7e2aeb9e089be67` | `V5 fuel row27 工伤赔偿 未缴工伤保险 附件列表声明4个法规附件但文件夹为空` | `not_run` | `not_run` | Needs four declared legal attachments or corrected manifest. |
| `2026-07-20T22:00:00Z#prime-001#fuel-sync-20260720` | `fuel_20260721_row19_hr_outsourcing_attachment_usage` | 19 | `missing_attachment_usage_steps` | `b5bc85e7199d9e8b7d90f8e0419bef3e10da11c24761e6d8aa8c56f795f8154d` | `V5 fuel row19 人力资源外包客服 附件已列但关键步骤没有说明每个附件怎么用` | `not_run` | `not_run` | Replay should verify attachment use is bound to concrete task steps. |
| `2026-07-20T22:00:00Z#prime-001#fuel-sync-20260720` | `fuel_20260721_row18_contract_batch_filename_mismatch` | 18 | `prompt_attachment_name_mismatch` | `7fc420c011d6ecb44a2571e23619aa50d0e562e028b810eed211d5db13280691` | `V5 fuel row18 人力资源合同文档批量生成 题目附件名与实际文件名对不上` | `not_run` | `not_run` | Needs filename-level reconciliation against folder contents. |
| `2026-07-20T22:00:00Z#prime-001#fuel-sync-20260720` | `fuel_20260721_row05_social_security_urls_as_attachments` | 5 | `url_listed_as_attachment` | `98fdd58df5b671f144277c54ea2851d2406652d59ed937d938d17170a7b32f4f` | `V5 fuel row5 1000人社医保转移增员 附件列表把政府网站链接当附件 实际只有一个Excel` | `not_run` | `not_run` | Needs attachment list normalized to uploaded file names. |
| `2026-07-20T22:00:00Z#prime-001#fuel-sync-20260720` | `fuel_20260721_row30_xiaohongshu_manifest_incomplete` | 30 | `attachment_manifest_incomplete` | `9c11497dd3b76295f4617637dd3bfd6f2eefdb58e688169bca467c4200daa004` | `V5 fuel row30 小红书矩阵运营 文件夹22个文件但附件列表只声明少数文件` | `not_run` | `not_run` | Needs full manifest expansion or explicit exclusion notes. |
| `2026-07-20T22:00:00Z#prime-001#fuel-sync-20260720` | `fuel_20260721_row28_recruiting_steps_ai_trace` | 28 | `ai_trace_steps_template` | `51fb65197908599c5d362f5637be88bc152b9ebb428f8e9e485832f4cdfc8ef5` | `V5 fuel row28 汽车电子结构工程师招聘 做题关键步骤是动词宾语模板 AI痕迹明显` | `not_run` | `not_run` | Needs natural, task-specific workflow rewrite before buyer reuse. |
| `2026-07-20T22:00:00Z#prime-001#fuel-sync-20260720` | `fuel_20260721_row24_competitor_attachment_count` | 24 | `competitor_attachment_count_mismatch` | `5aba15c43defc8ce4579a911e5b5decfdf5ae12669eddc2fe06486a28d1680c1` | `V5 fuel row24 食品客户竞标人力资源服务方案 题目写8家竞品但附件只有7家` | `not_run` | `not_run` | Needs competitor count aligned across prompt, attachment list, and folder. |
| `2026-07-20T22:00:00Z#prime-001#fuel-sync-20260720` | `fuel_20260721_row13_brochure_missing_attachments` | 13 | `missing_attachments` | `b0c540918bd7abad9476c71561af9d709cb310bf48807c6260890f880f224f2a` | `V5 fuel row13 24页骑马钉企业宣传册 附件列表声明5个附件但文件夹实际只有1个` | `not_run` | `not_run` | Needs either four missing attachments or a corrected attachment contract. |
| `2026-07-20T22:00:00Z#prime-001#fuel-sync-20260720` | `fuel_20260721_row12_branch_count_mismatch` | 12 | `entity_count_mismatch` | `0691f14b984e80816c0133f7b387a7a5aa3ed4cb8874709c56fcb24e911754bf` | `V5 fuel row12 集团分公司残保金薪资数据 题目未写数量但思维链和步骤定死50家` | `not_run` | `not_run` | Needs entity count confirmed from attachment before downstream replay. |

## Replay Contract

- `replay_status=not_run` means no recall query was executed in this task.
- `overloaded_status=not_run` means no cloud daemon or BGE path was probed in this task.
- `payload_hash` is SHA-256 over a stable string containing `trace_id`, `source_row`, `action_tag`, type, score, short problem phrase, and feedback phrase.
- This artifact is ready for a later compass recall replay task that is allowed to query cloud recall or local recall fixtures.

## Next Execution Gate

The next compass-side runner should update each row to one of:

- `hit`: recall returned an expected matching payload.
- `miss`: recall ran but did not return the payload.
- `blocked_overloaded`: recall path returned daemon overload.
- `blocked_missing_payload`: payload was not available for indexing or replay.
- `blocked_not_indexed`: payload exists but BGE/backfill status is not complete.
