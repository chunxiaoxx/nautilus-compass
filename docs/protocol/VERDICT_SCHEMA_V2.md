# Verdict Schema v2(判读结果正式协议,2026-10-03 立档)

> 来源:10/3 七演判读实战反推(四真 verdict:g1/pusht_4win/pusht_pair/rollout_n100)——教训进 schema,不是发明新需求。
> 正本关系:证据层语义承 docs/metering/JUDGING_EVIDENCE_TIERS_20261003.md;判据演进程序承宪法 V1.2 十三条。
> 工具:tools/verdict_schema_v2.py(validator+migrator);判读脚本出件即须过 v2 校验。

## 一、顶层结构(七段,段名冻结)

```jsonc
{
  "ts": "ISO8601+08:00",                    // 必填
  "judge": "名称+版本",                      // 必填,幂等可重跑
  "case_id": "案件标识",                     // v2 新增必填(如 pusht_first_case)
  "evidence_policy": "JUDGING_EVIDENCE_TIERS_20261003",  // 必填,正本指针

  "criteria": {                             // v2 新增段(判据演进程序 schema 化)
    "ref": "判据正本指针",                   // 必填
    "version": "v1|v2-final|...",           // 必填
    "freeze_chain": [{"event": "冻结/用户裁/审定/修订", "ref": "函或档", "ts": "..."}],
    "mapping_note": "口径映射披露(如 probe→帧级),无则省"
  },

  "material": {                             // 锚定链(单源原则:以 env_fingerprint 为准)
    "<arm/window>": {"sha256|sha16": "...", "source_path": "..."},
    "env_fingerprint": "路径或内容锚",
    "note": "dir哈希 vs 张量哈希层级注明(J3 口径)"
  },

  "readings": {                             // 读数主体(判读器自由结构,如 arms/windows)
    "...": "域内自有"
  },

  "statistics": {                           // v2 新增段(两法同报+裁决规则)
    "primary": {"method": "paired_wilcoxon|mwu|sign|...", "...": "读数"},
    "secondary": {"method": "...", "...": "读数"},
    "ruling": "主法定裁规则(T2);两法分歧时的裁决记录"
  },

  "findings": [{                            // 必填,每条四字段
    "finding": "...", "evidence_tier": "measured|inferred|unverifiable",
    "basis": "...", "upgrade_path": "null 或 升实测路径"
  }],

  "claims": [{                              // v2 新增段(声称与证据层绑定)
    "claim": "...", "supported": true, "boundary": "不支持的边界(如'达标性未证实')"
  }],

  "verdict": {
    "state": "VERDICT|PARTIAL|U_STATE",     // 枚举,禁自由文本做 state
    "text": "人读全文",
    "stop_loss": {"seed_locked": true, "no_expansion": true, "no_new_methods": true,
                  "note": "防加注条款;无止损线案件省略整段"}
  }
}
```

## 二、v1→v2 迁移规则(migrator 实现口径)

| v1 字段 | v2 去向 |
|---|---|
| 顶层 criteria_positioning | criteria.ref+mapping_note |
| 顶层 verdict: "字符串" | verdict.state(解析 U/PARTIAL 关键词)+verdict.text |
| findings[].evidence_tier("measured" 英文) | 不变(枚举即英文,函件展示层再映射中文) |
| comparisons/statistics 顶层散字段 | statistics.{primary,secondary,ruling} |
| material_dirs/windows.*.rows_sha16 | material 锚定链 |
| (无) | case_id/claims/stop_loss 为 v2 净新增,迁移时按案件补 |

## 三、校验规则(validator)

- L1 结构:七段存在性;verdict.state 枚举;findings 每条 evidence_tier 枚举;
- L2 语义:inferred/unverifiable 的 finding 必须带 upgrade_path 或 basis 含"推断/不可验"字样;
  claims[].supported=false 必须带 boundary;
- L3 锚定:material 每个条目有 sha 字段;stop_loss 出现时三布尔须全 true 才算启用;
- L4 一致:verdict.text 中出现"显著"时 statistics.primary 必须存在(防主判据旁路)。

## 四、兼容与生效

- 现存四真 verdict 由 migrator 出 v2 版本存档(原文件不动);新判读脚本(含 pusht_judge 框架化后)出件即须过 validator;
- schema 变更判据:只许加可选字段,禁删/改语义——修改即新 vN+协议函。
