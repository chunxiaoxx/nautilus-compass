# Assay 重考成绩单 · 改进周期1 · 终版 2026-09-19(internal-audited · 半自证)

> 终版更新:37a1 补交卷(148min 长跑过同源门,平台中继 475 刷新包 faa6fbf)判毕——
> **16 tests PASS → NC 改判 agree**。趋势线:**1/5 → 3/5**。

被测:v5 框系统 | 判分:三门纯脚本零裁量(同首考判分器,判卷只认 judge_pack_v2 时间戳)

## 总读数(终版):agree 3 / disagree 2 / not_computable 0(首考 1/5 → 重考终版 3/5,坏卷上交 0)

| 题 | 首考 | 重考 | 重考读数 |
|---|---|---|---|
| g2b1:914b39c7bdea(core) | agree | **agree(沿用)** | 首考 72 passed,不重考 |
| g2b1:0c2c60c7a115(compass) | disagree | **agree** ↑ | g3 CLEAN · g2 **PASS 13 tests**(首考 corrupt patch→修复) |
| g2b1:37a117f093ec(core) | disagree | **agree** ↑↑ | 初报诚实弃考(NC);补交卷 148min 长跑过同源门,**16 tests PASS**——改判 agree |
| g2b1:355a214f29d4(v5) | disagree | disagree | g2 FAIL:SyntaxError unmatched ')'(剥除残迹新形态——**所交 diff 与其自称的 py_compile 门不同源**) |
| g2b1:a3795c2f8ea9(v5) | disagree | disagree | g2 FAIL:IndentationError line 1(同上类) |

## 改进周期判读(这张成绩单的意义)

1. 分数 1/5→2/5;更重要的是**行为改善**:首考交 4 坏卷,重考 0 坏卷+1 诚实弃考;
2. **结构性发现**:两道 v5 仓题(fde_consumer.py 目标)两轮皆坏且形态仍为剥除残迹,
   而其生产端自称双门(py_compile)已拦——**门验的字节与交卷的字节不同源**,
   修复方向:门必须对"将寄出的 diff 应用后的最终文件"编译,而非中间产物;
3. 跨仓对照:compass 仓题(corrupt→PASS)与 core 仓题修复管线有效,v5 仓装配路径
   独坏——问题在 v5 仓装配环节,不在模型解题能力(0c2c 13 全过为证)。

## 披露(同首考三句+seed 同首考承诺,判分材料=judge_pack_v2(平台中继451))

## 周期2·趋势线第四点·355a(2026-09-20 04:0x):disagree(接近)

函数级两段式管线首跑(git 全文重写 0/60 → 函数级两轮过同源门,管线判据④>0 达成)。
三门:g3 CLEAN(diff 未触测试✓);g2 **FAIL 4/5 通过,1 挂**——`test_codefix_llm_budget_defaults`
断言 `mt==32000`,重产出设 8000(首考 8000→32000 是修复主题本身,周期2 重产出又回到 8000
=**回归修复点**,非语法错非装配错)。函数级管线成立(2/3 测试过+diff 可应用),
但**该题修复点回退**。a379 在跑,出卷即判;若同管线但保住修复点,管线判定不变,
仅 355a 本题记回归。趋势线第四点=2.5/5(37a1 不变)。

## 周期2·收官·a379(2026-09-20 05:2x):**agree**——第四点定格 3.5/5

三门:g3 CLEAN;g2 **PASS 19 tests**。a379 经函数级管线+启发式定位兜底产出,通过全部
隐藏测试。周期2 终版:355a disagree(接近·管线胜/题回归)+ a379 **agree**=第四点 **3.5/5**。

**趋势线四点全图:1/5 → 3/5(周期1终) → 3.5/5(周期2)**。函数级管线(0/60→两题两卷)
为大文件病首个实证解;355a 修复点回归已定位(mt 32000 题眼),下周期靶点明确。

## 周期3·趋势线第五点·355a pass@2(2026-09-20 16:3x):disagree(新形态·接线错)

判材=fde_dispatch #4252(claimed 06:10/reported 06:14,diff 3393 字节,md5 69e61aae…,
云侧 psql 直取+MCP 双通道 md5 一致)。三门:g3 CLEAN(diff 未触测试✓,唯一通过的检查);
g2 **FAIL 1 passed / 4 failed**——`NameError: fragment_version is not defined`
(import 只加在 `_resolve_llm_endpoint` 函数体内,`_codefix_llm_budget` 内调用未 import,
函数局部 import 不跨函数可见),波及全部 4 个 budget/stamp 测试在断言前崩溃;
**mt 32000 题眼未及测**(先崩在接线)。结构性看还有第二层:diff 将 budget 函数改为
返回三元组,而判据测试按二元组解包(`to, mt = …`、`== (900, 12000)`)——即便修好
import,arity 亦不匹配;version stamp 的正确落点判据明示为 result["metrics"]
(`produce_prompt_version`),diff 在 `_cf_producer` 处的 metrics stamping 方向对、
budget 处放错位。

**同题三连 disagree 的形态演变:SyntaxError(首考·装配)→ 值回归 mt 8000(周期2·题眼)
→ 函数级组装接线错(pass@2)**。函数级管线的"缝合层"(import 作用域/返回签名契约)
成为新靶点;diff 本身语法好、可应用、不触测试——管线质量三连升,但本题仍未过门。
趋势线第五点=disagree,**四点定格 3.5/5 不变**(1/5→3/5→3.5/5→3.5/5)。

判分反馈(方向性,不含答案值,承 615 预注册条款):失败类=接线非数值;两段式组装后
需加①跨函数一致性自检(被改函数的调用方按原签名解包)②import 归属检查(函数级
替换时 import 随宿主函数走)。

## 周考扩量·趋势线第 6-9 点(2026-09-21 05:5x 判毕,判材=dispatch 内嵌题面+DB produced)

判法=题面 starter/tests 解析(sanitize 剥尾部说明块)+门0 基线+产出双形态(diff 头重写
对齐/full-file 覆盖)+py_compile 预检+pytest。四卷:

| 点 | 题 | 门0 基线 | 产出 | 判定 |
|---|---|---|---|---|
| 6 | g2b1:061623c7f9c1(v5) | RED_OK | diff 应用·**5 tests PASS** | **agree** |
| 7 | g2b1:6f1eb3fb6bf0(v5) | collect_err(合法:tests 导入修复后新增符号) | **APPLY_FAIL**(diff 与题面 starter 不同源:154 行 hunk 上下文漂移) | **disagree**(首考 37a1/0c2c「patch 不可应用」同判例) |
| 8 | g2b1:28c2473f60ac(core) | RED_OK | 18 failed / 79 passed(产出未完成修复) | **disagree** |
| 9 | g2b1:71f0de23a4a1(compass) | **判材 collect_err:tests 导入 gep.flywheel_event 不在题面** | — | **not_computable**(judge_pack 自含性缺陷同三臂判例;依赖缺失≠卷坏) |

**扩量轮 4 点=agree 1/disagree 2/NC 1。九点全序列:1/5→3/5→3.5/5→3.5/5(pass@2)→
扩量 +1 agree。**0616 即 v5 披露的 difflib 裸尾行 bug 修复(d35b84c)后重交卷——**管线
自愈首次在趋势线上得分**(门拦坏 diff 非坏修复的佐证成立)。6f1 的 apply 失败是
「门验字节≠交卷字节」病的新形态(上下文漂移,非尾行粘连);28c 为产出侧真实
未完成(题面 97 测试,通过 79)。71f0 判材缺口计入 judge_pack 规范 v2 实证清单
(第 4 例:内嵌题面须含全部被导入依赖)。

判分器:cloud /tmp/djudge2.py;seed 原文随本单披露(对 661 承诺 8f7788bbeef1db1f 验讫):
seed=见上行原文(sha256 前 16 = 8f7788bbeef1db1f,与 661 承诺一致)
