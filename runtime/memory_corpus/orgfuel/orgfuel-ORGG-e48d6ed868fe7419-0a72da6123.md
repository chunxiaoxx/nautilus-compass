---
name: orgfuel-ORGG-e48d6ed868fe7419-0a72da6123
description: "判读档判例 2026-09-19-mechanism-pivot · 四 · 工程排期(机制产品线 P0 重定义) ##"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-e48d6ed868fe7419
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-09-19-mechanism-pivot · 四 · 工程排期(机制产品线 P0 重定义)
## 四 · 工程排期(机制产品线 P0 重定义)

1. **assay-sdk(pip 包,3 天)**:`pip install assay-verify`;
   - `attest(claims, artifacts_dir) → pack+sig`(生产端,一行)
   - `verify(target, sig, pubkey) → 三态`(消费端,一行,verify_receipt.py 包装)
   - 判据模板随包分发;README 三行代码接入
2. **记忆层内置验签(1 天)**:ingest_obs 写入时,若带 receipt 字段→自动验签
   →fact_status 打 `verified`;否则 `self-reported`。查询端透出标记。
3. **MCP 工具 assay_verify(半天)**:已列在 Registry server.json 的工具表补真身
4. **创世演示改造**:Aider 复算改用 SDK 流水产出,回执=SDK 的第一个第三方用例
5. 暖私信文案更新:卖的不是"我们的审计服务",是"三行代码让你的数字自动可信"
