# F-005 修复实弹验证账(2026-10-28 · 裁决22765 · 回执函22779)

## 5受影响题+对照(09:38 批,/tmp/f005_verify_20261028.log 存档)

```text

=== CS-003 09:38:00 ===
swap 4 文件: ['store.py→ephem/store.py', 'ingest.py→ephem/ingest.py', 'predict.py→ephem/predict.py', 'format.py→ephem/format.py']
same 1: ['__init__.py→ephem/__init__.py']
unresolved 0: []

=== 金标自检判定: score=0.0714 deterministic=True ===
GOLD-FAIL(疑似出题故障!)
workspace 已还原
exit=0
=== CS-004 09:38:02 ===
swap 3 文件: ['rounding.py→settlement/rounding.py', 'ledger.py→settlement/ledger.py', 'calc.py→settlement/calc.py']
same 0: []
unresolved 0: []

=== 金标自检判定: score=0.2143 deterministic=True ===
GOLD-FAIL(疑似出题故障!)
workspace 已还原
exit=0
=== CS-005 09:38:03 ===
swap 2 文件: ['counterparty.py→audit/counterparty.py', 'sampler.py→audit/sampler.py']
same 0: []
unresolved 0: []

=== 金标自检判定: score=1.0 deterministic=True ===
GOLD-PASS(题目有效,四模型全0=区分度真)
workspace 已还原
exit=0
=== CS-514 09:38:04 ===
swap 1 文件: ['parse.py→vrangen/parse.py']
same 0: []
unresolved 0: []

=== 金标自检判定: score=1.0 deterministic=True ===
GOLD-PASS(题目有效,四模型全0=区分度真)
workspace 已还原
exit=0
=== CS-515 09:38:04 ===
swap 1 文件: ['runner.py→verifier/runner.py']
same 0: []
unresolved 0: []

=== 金标自检判定: score=1.0 deterministic=True ===
GOLD-PASS(题目有效,四模型全0=区分度真)
workspace 已还原
exit=0
=== CS-513 09:38:04 ===
swap 1 文件: ['formatter.py→skillapi/formatter.py']
same 0: []
unresolved 2: ['manifest.py', 'variants/variant1.py']
GOLD-FAIL(F-005 解析歧义,禁止静默通过)
workspace 已还原
exit=2
```

## 单测实证(证伪探针后定谳:swap/import 正常,挂的是金标语义)
- CS-003 test_after_expiry_none: 墓碑 read(now=9) 应 None 实得 1
- CS-004 test_aggregate_mixed_amended: 修订单聚合 2520.00 应 2285.50

## G1 全量批(修复后 gold_check,逐题 600s 超时保护)

### 全量批账(10-28 10:17 收官,73 行账)

- GOLD-PASS 27: CS-002 CS-003B CS-005 CS-006 CS-009 CS-012 CS-013 CS-014 CS-015 CS-016 CS-017 CS-102 CS-104 CS-105 CS-205 CS-206 CS-207 CS-401 CS-402 CS-501 CS-503 CS-504 CS-505 CS-506 CS-514 CS-515 CS-516
- GOLD-FAIL·金标语义故障 20: CS-001 CS-003 CS-004 CS-007 CS-008 CS-011 CS-019 CS-020 CS-021 CS-022 CS-023 CS-024 CS-101 CS-103 CS-201 CS-202 CS-203 CS-512 CS-517 CS-G1
- GOLD-FAIL·解析歧义拒(待补标注,非出题故障) 23: CS-010 CS-301 CS-302 CS-303 CS-304 CS-305 CS-502 CS-507 CS-508 CS-509 CS-510 CS-511 CS-513 CS-518 CS-601 CS-G2 CS-G3 CS-G4 CS-G5 CS-G6 CS-G7 CS-G8 CS-SK11
- TIMEOUT 1: CS-204
- 异常 2: CS-018 codesense
- 附注[实测]: CS-008 solution=clean.py+golden.patch,clean.py 与 workspace 同文(same 跳过),patch 式解法 gold_check 不支持→G1 设计缺口(patch 型 item 需另立验法);items/ 下杂目录 codesense(1 项)混入批跑 rc=1;CS-018 未物化(无 workspace/repo)
- 附注[推断]: FAIL-UT 抽检 3/3 手动复现(CS-003/004/201),批跑非伪阳;歧义拒= fail-safe 设计行为,upgrade_path=补 docstring 模块标注后重跑
