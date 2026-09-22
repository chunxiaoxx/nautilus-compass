# jev-trust 第四域预注册协议:OK-first 措辞对照(2026-09-22)

> 对照实验,不是新域。单一变量原则:**完全复用域 3 的 120 题决策集与
> 真值**(同 sha256),唯一变量 = 标注规范的措辞方向。

## 实验假设(开工前写死)

- **H0**:措辞反转不改变行为分布(域 3 全 yes 偏差是结构性的)
- **H1**:OK-first 措辞降低负例误报(偏差部分由「缺陷条件优先」措辞诱导)

## 操作化(双重反转)

域 3(对照):问 "Label NEEDS_REVIEW if and only if ANY defect rule holds",
缺陷规则列表优先。
域 4(处理):问 **"Is this sequence OK?"**,通过条件列表优先:
> Label the sequence OK if and only if ALL of these hold:
> (1) every pair of consecutive readings differs by at most 0.8;
> (2) there is no run of 5 or more consecutive identical readings;
> (3) every reading is within [-3.14, 3.14];
> (4) the sequence does NOT drift: NOT (|first − last| > 1.5 AND monotonic overall).

**真值映射(写死)**:决策集 truth 字段沿用域 3(1=NEEDS_REVIEW)。
域 4 问的是 OK,故 record_outcome 传 `1 − truth`(yes=OK 与否)。
复算者按此映射核。

## 决策集

`../jev_trust_domain3_20260922/decision_set.json` 原样读入
(n=120,正例[缺陷] 60/负例[OK] 60,sha256 与域 3 一致,协议不复核生成)。

## 判据(预注册,只许更严)

1-5. 与域 3 五判据同构(口径/工件/验签/全量无剔除/如实),
    工件含与域 3 的映射说明。
6. **主对照判据——负例误报数**(域 3 基线 = 60/60):
   - 域 4 负例误报(OK 题被判"不 OK")**≤ 45/60** → 措辞有实质影响(H1)
   - **≥ 55/60** → 结构性偏差(H0 保持)
   - 46–54 → 混合效应,只报效应量不站队
7. **召回守护**:正例(缺陷题)漏检 **> 18/60(30%)** → 红旗:
   措辞修复以引入漏检风险为代价,须明示
8. **配对翻转**:统计两域逐题决策翻转数,按真值分组列出
   (负例翻正 × 正例翻负),供 McNemar 手工核

## 预期之外的解读纪律

两方向结果都发布:若 H0 保持,「全 yes 是结构性」升级为更强结论
(两措辞下复现);若 H1 成立,域 3 读数解读须加措辞边界声明,
并回传社区(含域 3 帖的 follow-up)。

## 收工

RESULTS.md:域 4 四指标 + 判据 6/7/8 三个对照读数 + 与域 3 并列表;
**待非实现者复算**(交接档沿用三域模板,加判据 6-8)。
