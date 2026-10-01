# Narrative-Drift Lint(`lint-report`)· 立项档 v1.0

> 2026-10-02 凌晨立项。触发实例:gtaras7 typesafe-jev #2(2026-10-01)。
> 一句话:**数据层干净、叙事层撒谎的报告,行业里每天都在产生;我们造一个把 VerifyPack 链条延长到叙事层的 lint。**

## 一 · 背景实例(为什么是现在)

2026-10-01 jev_cvscreen mini-report 事故,错误解剖定谳:

| 层 | 实物 | 状态 |
|---|---|---|
| 原始层 | jev_run_log.jsonl(40 行请求/响应) | ✓ 干净 |
| 提炼层 | jev_answers.json | ✓ 干净 |
| 聚合层 | measure_report.json(divergence_rows 等) | ✓ 干净 |
| **叙事层** | mini_report.md 散文 | **✗ 错误**:divergence 实为 2 行 unclear 弃权,散文臆造为 job_hopping↔lateral_moves 类别互换 |
| 下游 | commit message dda96982 | ✗ 同错传播 |

抓错方:外部评审者 gtaras7,靠**表格与散文的逻辑矛盾**(unclear 2/27 不可能同时是类别互换)定位。复算记录:`runtime/typesafe_jev_cvscreen/recompute_erratum_20261002.md`(9 项全绿,错误仅在叙事层)。

根因:预注册模板预设了"有趣结果"(divergence=主产出),散文被预期框架裹挟。**该错误类型(数据对/叙事错)无法被现有任何工具捕获**——VerifyPack 六命令(build/verify/receipt/check/keygen/export)全部止步于数据层。

## 二 · 定位

- **归属**:VerifyPack 第七命令 `lint-report`(tools/verifypack/),非新工具。三角色模型自然延伸:数据方 build → 验证方 verify → **叙事方(报告作者)lint-report** → 结算方 check。
- **对外名**:narrative-drift guard(宣传层),命令名 `lint-report`(实现层)。
- **纪律**:纯 stdlib(沿 v0.2 传统);SPEC 升 v0.4 附录段。

## 三 · 机制设计(声明式锚定,拒绝 NLP 猜测)

**核心决策:不解析自然语言语义。报告作者用声明式断言自证,lint 校验断言↔数据,并做关键词值域比对。**(全自动 NLP 抽取=脆+误报,违背本仓工具哲学)

三层结构:

1. **报告内锚点**:关键叙事句旁嵌 `<!-- vp:assert id=D1 -->`(HTML 注释,渲染不可见)。
2. **sidecar 断言文件** `report.assertions.json`,每条:
   ```json
   {"id": "D1",
    "kind": "enum_set",
    "source": "measure_report.json#/divergence_rows/*/pred",
    "expect": ["unclear"],
    "prose_scope": "D1 段落内",
    "vocab_all": ["job_hopping", "lateral_moves", "steady_growth", "unclear"],
    "severity": "hard"}
   ```
   断言两类:
   - `enum_set`:散文段落中出现的受控词表词汇,必须与 source 数据值域一致(**昨晚错误正中此门**:divergence 段出现 job_hopping/lateral_moves,数据值域={unclear} → RED)
   - `number`:散文数字 == source 重导出(复用 expr.py 受限求值器)
3. **lint 输出**:逐条 RED/GREEN + 行号 + 一句 diff 说明;exit code 非零=RED。锚点缺失/孤儿断言=soft 警告。

## 四 · 判据(预注册,开工先落,只许加严)

| # | 判据 | 线 |
|---|---|---|
| L1 | **昨晚事故回放 RED**:对勘误前版本(`git show dda96982:runtime/typesafe_jev_cvscreen/pack/mini_report.md`)配原 assertions 跑 lint,必须报出 divergence 叙事矛盾 | 抓得住 |
| L2 | 勘误后 v1.1(910bed22)同断言跑 lint,GREEN | 不误杀 |
| L3 | 数字复现:报告六个数字(92.6%/25/27/0.069/0.1378/2/27)从 measure_report.json 重导出逐位一致 | 数字门 |
| L4 | 误报控制:纯措辞改动(不动断言与数据)不报红;anchor 词表外词汇不触发 | 不扰民 |
| L5 | 端到端:jev_cvscreen pack 一条命令跑通,输出可入 receipt | 集成门 |
| L6 | 测试覆盖率 ≥80%(仓规) | 质量门 |

## 五 · 范围与非目标

**做**:enum_set 值域比对/number 复现/锚点与孤儿检查/exit code 协议。
**不做**(v1 明确出界):
- NLP 语义抽取/改写检测(脆)
- commit message 层校验(范围蔓延,记非目标)
- 跨报告一致性(多报告对照,留给 v2 视需求)
- 自动生成 assertions(作者必须手写——写作时的自证动作本身就是防裹挟程序)

## 六 · 工作量与排期

- 实现:0.5-1 天(lint 核心 ~200 行 + 断言样例 + tests)。
- 排期:10/2 白天死线四件后/10/26 M1 复盘前任一窗口;不抢明晨死线。
- 首个用户:本仓全部对外测量报告(jev_cvscreen/η 包/判分器门件)。

## 七 · 战略挂钩

- Report #3 素材链:工具是昨晚错误的直接产品化("error → product"),写作线可引用。
- 考场/认证轨:诚信计分的机械执法件——考生报告过 lint 才能上墙。
- 对外演示叙事:「我们的评审者抓到我们的错,我们当天勘误,然后把抓错的机制做成了工具」——验证机构护城河的一块砖。
