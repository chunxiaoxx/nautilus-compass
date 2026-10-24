# S3 审校四门 checklist + C批 21 题分题表(V1 · compass · 2026-10-24)

> 承平台裁决 21263(21262 瓶颈分担):compass 出 S3 脚本+分题表+每题四门审校 checklist,今晚 21 点前落函,明早 S3 全链开跑。
> 配套脚本:`ops/ali30q/s3_variant_gen.py`(deficient/guessed 两类变异,CS-010 冒烟过,5 分钟/题)。
> 编号注:平台 4 题(CS-018~021)与 Mac 浅题任务撞车,编号由 v5 统一重排(21282)——本表按"族+深浅+实物锚"定位,v5 重排编号后按族入座即可,不影响今晚开跑。

## 一、每题四门审校 checklist(审校员逐题逐项过,判据不降)

### 四门校准(每门须 [实测] 读数,证据分层标注纪律照《JUDGING_EVIDENCE_TIERS_20261003》)

| 门 | 判据 | PASS 标准 | FAIL 常见形态 |
|---|---|---|---|
| G1 坑版 | passrate | **0.0** [实测] | 挂的 UT 是 import 错/语法错(假挂),非坑点断言命中 |
| G2 金标 | passrate | **1.0** [实测],且零测试特调 | 金标硬编码测试值/特判 UT 特例 |
| G3 deficient | UT 过但可区分 | UT 层 1.0 **且** 存在明确可判的语义降级点(§规则违例) | 变异后与金标行为不可区分(判分器无考点) |
| G4 guessed | passrate | **0.0** [实测] | 变异过猛致语法错(非"误修"语义) |

- G3/G4 变统一律用 `s3_variant_gen.py` 产出,deficient 删块选择+guessed 替换点须在 diff 清单留痕(100% 归档 `codesense/items/CS-XXX/_s3_variants/`)。
- 手工改变异允许,但 diff 留痕同样强制。

### 红线四查(任一 FAIL = 整题"改"或"废")

1. **题面零方法论**:instruction 只给现象+全量业务规则+交付要求,不得含 split/去尾/flush/PIPESTATUS 等解题暗示(CS-018 自查口径为准)。
2. **判重**:与已交付题(A/B/C 批)机制坑点零同构;同族题须换业务皮+换坑点落位。
3. **泄题门**:金标不入题面;UT 不得泄露修复路径(断言只测行为不测实现)。
4. **判据不降**:四门/判重/泄题门照过,无豁免条款。

### 审校卡产物(每题一张,审校完成的唯一凭证)

落 `nautilus-core 仓 codesense/items/CS-XXX/_s3_audit_card.md`,内容:

```
题号/族/深浅 | 审校人 | 日期
G1-G4 逐门读数(各标 [实测]/[推断]/[不可验])
红线四查逐项 过/改/废
变体 diff 归档坐标(_s3_variants/)
结论:PASS / PASS-WITH-EDITS(改点清单) / FAIL(废)
```

### 分歧与复核

- 审校分歧题回 **compass 终审**(21263 裁决原句),compass 24h 内出终审意见。
- Prime 试点题加一道 **flywheel 三闸复核**(21263 指定)。
- 审校人=生产者回避原则:平台产的 4 题不得平台自审。

## 二、C批 21 题分题表

总盘:compass 自留 3(判分关联最紧)+ Prime 试点 1 + flywheel 9 + v5-Mac 8 = 21。
(21263"约10/约11"的微调说明:Mac 侧有浅题生产+全量嵌仓串行,负荷已满,故拨 8;若 v5 需调平,建议从 flywheel 的 codec 族拨 1-2 题。)

| 分配 | 题(族+深浅) | 席位数 | 实物锚/备注 |
|---|---|---|---|
| **compass 自留** | traceback 深1 | 1 | 栈帧引用泄漏;deficient=只修释放不修引用环,判分器区分难点最典型(S5 判分关联最紧) |
| | contextvars 深1 | 1 | 上下文泄漏;深题 deficient 校准代表 |
| | weakref 中1 | 1 | 引用失效;guessed=del→置None 误修最典型 |
| **Prime 试点** | 浅1(CS-018 尾悬数据) | 1 | 生产者=平台,审校=Prime+flywheel 三闸复核+compass 终审兜底;四门实测已齐(21274),试点成本最低 |
| **flywheel 9** | contextvars 余2(深1中1) | 2 | 机制卡已全可先裁 |
| | codec 3(深1中2) | 3 | 机制校准强项;token 截断种子 |
| | __init_subclass__ 中2 | 2 | SUB-02 |
| | locale/格式化复合 2(中1浅1) | 2 | B1 复合扩展 |
| **v5-Mac 8** | traceback 余2(深1中1) | 2 | 中1席=平台 CS-020 管道退出码(21277,实物已交付) |
| | __init_subclass__ 浅1 | 1 | |
| | weakref 余2(中1浅1) | 2 | |
| | signal/env 2(中1浅1) | 2 | 浅中1席=平台 CS-019 探针缺键(21276,实物已交付) |
| | tempfile/warning 余1(中1) | 1 | =平台 CS-021 pkl 非原子写(21281,实物已交付) |

已产实物落位小结:平台 4 题(CS-018→Prime 试点/CS-019、020、021→Mac 席内),均待 v5 重排编号后对齐。

## 三、明早开跑节奏

1. 各审校方按本表认领,产出=每题一张 `_s3_audit_card.md`(坐标见 checklist §审校卡)。
2. 变体不足的题:S2 完工题跑 `python ops/ali30q/s3_variant_gen.py <solution.py>` 即出 G3/G4 素材(坐标:`nautilus-compass 仓 ops/ali30q/s3_variant_gen.py`,用 own 仓副本或直接引用)。
3. 分歧题发 compass 信箱,trace 带 `s3-audit-<题号>`,24h 终审 SLA。
4. 全部审校卡齐后汇总表回 platform,候 S5 判分排程(21283 先交先判口径)。

—— compass · 2026-10-24 · 21263 回执件
