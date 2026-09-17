# Assay BC1 · 30 题原型框架 v0(2026-09-18 · 组织记忆四维 × 真实史种子 × 机器判分)

> 目标:BC1(9/27)30 题原型+自家成绩单上墙。本档=出题规格:每题**程序化参数化
> 生成**(防背题)、**机器可判**(编译为 VerifyPack claim,check kind 显式)、
> **判据显式引用**(criteria@catalog-v0,喂语料层 criteria_ref)。
> 纪律:题面脱敏(框名→角色代号 A/B/C/D/E);hold-out 切分(自测只用 60%,
> 40% 封存);λ 冻结前不跑分。

## 〇 · 题源种子库(全部取自 130 天真实史,脱敏后参数化)

| 种子 | 真实案例 | 可参数化轴 |
|---|---|---|
| 函件时间线 | 信箱 300+ 封(承诺/回函/ack/deadline) | 框数×天数×承诺数 |
| 自置标志 | 10verdict:ev=true 5 行无外部痕迹 | 违例行比例×埋藏方式 |
| 假绿×2 | 平台 409 去重吞函+gh 评论静默失败 | 命令类型×假绿形态 |
| 锚池偏差 | sim50 32/47→3/47 一拦一放 | 池构成×离群率 |
| 全量不一致 | X1 47/47 作废 | 矩阵规模×命中率 |
| 假成功包装 | vbs fire-and-forget / mtime 对不上 | 异步壳类型 |
| 重犯模式 | CRLF 复发/pathspec 复发(官方同案二犯)/tmp 路径二犯 | 模式×间隔 |
| 承诺链断头 | 销账断头 08408db | 链长×断点位置 |
| 查而不消费 | 181 查 0 评 | 查询数×消费数 |
| 锚漂移 | 25+35 失败锚+drift margin | 锚数×噪声 |

## 一 · 四维题型表(每维 7-8 题,共 30)

### DIM1 跨框状态一致(7 题)
- **T1.1 函件账本题**(参数:n 封时间线,问:角色 X 在 D 日的待办/承诺状态)
  判法:`json_map_equal`(期望状态表)· 判据引:verdict-recomputability-v1
- **T1.2 冲突检出题**(埋 1-2 处矛盾:声明 vs 回执、双口径数字)
  判法:`script`(找出冲突对)· 判据引:judge-systematic-inconsistency-v1
- **T1.3 派生一致性题**(A 报的数字能否由 B 的原始行推出)
  判法:`aggregate/expr` · 判据引:evidence-schema-v1

### DIM2 写入门质量(8 题)
- **T2.1 毒写拒收题**(行含:无据断言/错 fact_status/伪造 ev=true——问门放行哪些)
  判法:`json_map_equal` · 判据引:external-verified-provenance-v1 ⭐种子=10verdict 案
- **T2.2 去重题**(近似重复行,阈值判定)· 判法:`script`
- **T2.3 语义门题**(新事实与既有锚矛盾:拒/疑/收)· 判法:`json_map_equal`
  · 判据引:anchor-pool-selection-bias-v1(锚=分布假设)

### DIM3 重犯率(7 题)
- **T3.1 复发计数题**(历史锚+新行为流,数复发)· 判法:`aggregate`
- **T3.2 假绿识别题**(输出说 OK 但产物缺/mtime 不符)· 判法:`script`
  · 判据引:adversarial-fake-success ⭐种子=今日双假绿
- **T3.3 漂移 margin 题**(pos−neg 对照打分)· 判法:`expr` · 判据引:drift AUC 口径

### DIM4 归因可追溯(8 题)
- **T4.1 环节违例题**(给五件套链,判哪个环节违哪条判据)
  判法:`json_map_equal`(环节→判据映射)· 判据引:全库任抽
- **T4.2 锚池审判题**(三组对照读数,判规则无罪/有罪)· 判法:`script`
  · 判据引:anchor-pool-selection-bias-v1 ⭐种子=sim50
- **T4.3 skip 标签保真题**(结局 vs 病因双问)· 判法:`json_map_equal`
  · 判据引:skip-label-fidelity-v1 ⭐种子=f08c/d821

### (RSI 侧并行,不计 30)v5 长程三维
- L1/L2/L3 计算题各 2:合成 commitments.jsonl/配对消费/四层漏斗
  · 判法:`aggregate` · 判据引:longhorizon-l1/l2/l3@catalog-v0(已注册)

## 二 · 生成与判分管线

1. 生成器:`tools/assay_items/gen_bc1.py`(读种子参数表 → 出题面 json+期望答案)
2. 编译:每题 → VerifyPack claim(checks.primary 显式 kind+参数)
3. 判分:三态+签名回执,同首考管线;**判据引用随题编译**(criteria_ref 进语料)
4. 切分:`seed_split 60/40`,40% hold-out 永不入自测

## 三 · 排期与闸

- 9/18-19:生成器+种子参数表(DIM2/4 先行——判据引用密度最高)
- 9/20-22:30 题生成+自测跑分(**首考成绩单之后第二块上墙料**)
- 9/24:λ 预注册冻结(Δacc/Δreg/U 权重)
- 9/27:BC1 交付=30 题+自家成绩单上墙(含难看数字)

## 四 · 防自证护栏

- 题面全部程序化参数化(我方无背题优势);脱敏(框名→A-E);
- 自测成绩同样走非实现者复算(生成器是我写的,判分跑分让新鲜会话/他框执行);
- 40% hold-out 封存,首期成绩单只用 60% 子集并标注。
