---
name: orgfuel-ORGQ-R168-95adb96146
description: "### R168 · 2026-10-05 09:4x-10:0x(用户拍"both_wrong 14 条人工复核"→语"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R168
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R168 · 2026-10-05 09:4x-10:0x(用户拍"both_wrong 14 条人工复核"→语料管线两缺陷实锤)
- **复核执行**(本地 split sha16 与 A100 一致先验;14 条题面抽全 `_r168_bothwrong_14.json`):截断假说修正——语料件 response 本身=200 字符(入库截断,原始 per_question response_raw 317-509 字符,579557d8 的 boxed 结论 309 字符全被砍)
- **两缺陷实锤 [实测]**:
  1. **A 型·截断缺陷(both_wrong 主因 11/14)**:语料构造 response[:200] 截断砍掉结论段,gold(官方 harness 全文判定)依据不可见于判读输入——lme"陷阱题"(真值=环境里不存在 X,正确行为=指出不存在)全灭;10 例 pass 判 fail+2 例 fail 判 pass 完美镜像=两代判读器对坏特征的一致系统性误读,非能力差
  2. **B 型·字段映射缺口(全仓 52/1454=3.6% 普查炸出)**:bc1 36+f15 8+t3 8 条各族原生结构(exam/audit_table、probe/rationale、case_id/sample_pack)未被导入器映射到通用键——判读器无题面盲判,gold 来源严肃(BC1 人工审计/T3 盲评/F15 三门)但输入空
  3. C 型·单轮化损失(rejudge 2 条):偏好链上下文丢失
- **修复建议三条带验收判据**(复核档 `_r168_bothwrong_audit.md`):①response 截断修复重导出 v1(验收=A 型 11 条复评 ≥7/11 转对)②字段重映射(验收=全仓零空题面)③rejudg
