# M5 判据包打包规格 v0(判分员工位"带判读纪律的员工"之判据包 · 承 #10063②)

> 判据包=NACRE 分身/判分员工位随包携带的判读纪律资产包;包只读,版本棘轮随上游。

## 一、包内容(五件,全现有资产)

| 件 | 来源 | 作用 |
|---|---|---|
| 判例集 CASEBOOK_V1 | docs/cases/(v1.4 封版) | 判例先例+勘误纪律示范 |
| 判据档族 | docs/metering/PREFOR_*.md + FUEL 判据 v1(_r131 档) | criteria_sha 冻结语义 |
| schema 校验器 | tools/verdict_schema_v2.py | verdict 合规门 |
| 白名单门 | tools/p3_delta.py | 燃料防自指门 |
| 证据三层正本 | docs/metering/JUDGING_EVIDENCE_TIERS_20261003.md | 标注纪律 |

## 二、manifest 制式

`judge_pack_manifest.jsonl` 每行:`{name, path, sha16, version, license, role}`;包 sha16=manifest 本身 sha(装包即锚)。

## 三、版本策略

- 包版本=vN(递增);上游任一件升版→包出 vN+1(旧包不覆写,棘轮同构);
- 分身判读时必须声明所用包版本;criteria_sha 不在包内=拒绝判读(防野判据)。

## 四、引用接口(分身侧)

- 判读前:`validate criteria_sha ∈ manifest` → 过则按档判,不过则 U(判据缺失);
- 判读后:verdict 过 schema 门+标注证据层,双门全过才出件。

## 五、边界

- 包不含判分器权重(NACRE 本体另随骨架,打包归 v5 骨架收口 P-03 后接);
- 包不含客户数据(判例全为已公开判例,零客户信息)。
