# Assay 首考成绩单 · 2026-09-18(全球第一份被审计的 RSI 转录判分)

**被测**:v5 框系统 | **级别**:internal-audited · 半自证 · 首考 | **判分**:三门纯脚本零裁量

## 总读数:agree 1 / disagree 4 / not_computable 0

| 题 | 门1 starter必败 | 门3 不动测试 | 门2 修复后必过 | 裁定 |
|---|---|---|---|---|
| g2b1:914b39c7bdea(core) | ✓(1 failed) | CLEAN | **PASS·72 passed** | **agree** |
| g2b1:355a214f29d4(v5) | ✓(1 failed) | CLEAN | FAIL·产出 diff 自带 SyntaxError(未闭合字符串 line 5,think 剥除坑产物) | disagree |
| g2b1:a3795c2f8ea9(v5) | ✓(1 failed) | CLEAN | FAIL·同因(line 12) | disagree |
| g2b1:37a117f093ec(core) | ✓(collection-error 形式,备注) | CLEAN | FAIL·patch 不可应用(corrupt @167) | disagree |
| g2b1:0c2c60c7a115(compass) | ✓(1 failed) | CLEAN | FAIL·patch 不可应用(corrupt @52+尾空白) | disagree |

与被测方自报对照:0c2c/37a1 自报"误路由期产出质量存疑"→应验;**355a/a379 自报
"修复管线后产出"仍坏**——think 剥除管线缺陷实锤(其 388 披露四坑之一);914b 同为
修复管线后产出且全绿,说明缺陷为间歇性而非全坏。

## 披露(固定三句)
1. 题池完整性由被测方自报,监考方做逐 id 独立核验(69/69 对到四仓 git ref,存在级)
   +全量 86 三方对账(计数合/坏15齐/69⊆86);
2. 被测对象=v5 框系统(含人工监督段,消费循环人工重启 7 次,被测方自报);
3. 本考属 internal-audited 级(组织内被测,生态关系如实披露),不入 external-certified 名次。

## 抽签可验
seed 原文(成绩单时披露,对开考承诺哈希):
```
seed=55963e8ac909c09958b8d4b802acb4ea
method=stratified 2/2/1 (v5/core/compass), fde excluded; pool=69-snapshot verified 69/69
```
sha256(seed 文件)[:16] = 5597891d1276f8e3(与 376 函承诺一致 ✓)
方法:分层 v5 2/core 2/compass 1,池=66(69 快照-fde3-TIMEOUT2)。

## 第五件
produce 段会话切片(denominated deliverables)归档未判分——审计留痕,非评分项。
判分材料:平台中继 397(judge_pack,判毕即删);判分脚本:scripts/assay_gate1.py
+ assay_gate23.py(worktree 隔离,官方双门语义+门3);判分环境:Win/云 python3。
