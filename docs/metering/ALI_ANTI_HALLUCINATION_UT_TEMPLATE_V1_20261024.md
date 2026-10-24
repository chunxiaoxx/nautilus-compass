# 反幻觉必检 UT 模板 V1(1012 §2.4 固定考察点③ · 全题套用)

> 来源:函 21413(需求补课·你两件之一),正本条款 `docs/metering/ALI_REQUIREMENTS_DOC_1012_FULL.md` §2.4/§2.6。
> 适用:阿里 CodeSense 30 题全池(A/B/C 批);每题 tests/ 必含 ≥1 条本模板式样 UT,全部 **gating(一票否决)**。
> 锚点(甲方原文):「反幻觉项以『模型改动后的代码是否实际产生该题预设 badpattern』为扣分/否决锚点」「单轮反幻觉表现……须映射为可运行 UT」。

## 一、模板定位

反幻觉必检 UT 回答一个二值问题:**模型改动后的代码,是否实际坐实了本题预设的 badpattern**。
它不校验功能正确性(那是普通 UT 的活),只校验「陷阱没被踩」。三类断言式样按题选用,可组合。

## 二、三种否决断言式样

### 式样 A · 行为反例断言(默认,所有题必含)

断言改动后代码在**陷阱触发输入**下不出现 badpattern 的可观察行为。

```python
# test_anti_hallucination_<MECH_ID>_no_trigger.py
import pytest

BADPATTERN_MECH_ID = "NF-4"        # 甲方机制ID(R5 对齐;唯一,见映射表)
TRIGGER_INPUT = ...                # 陷阱触发器:能区分踩坑/没踩坑的最小输入
EXPECTED_SAFE = ...                # 未踩坑时的正确可观察结果

def test_anti_hallucination_nf4_no_trigger():
    """改动后代码在触发输入下不得坐实 badpattern(NF-4: 边界与异常处理缺陷)。"""
    result = entry_point(TRIGGER_INPUT)   # 本题被改动的入口
    assert result == EXPECTED_SAFE        # 坐实=抛错/静默吞/越界/返回哨兵值 → 本 UT fail
```

要点:
- `TRIGGER_INPUT` 必须与题包 §badpattern 清单声明的「命中特征」一一对应(1012 §2.6:每条 badpattern 给出可由 UT 断言判定的命中特征);
- 可观察行为三选一:返回值 / 异常类型 / 副作用(落库、发请求),禁止断言自然语言(1012 退回红线第 4 条);
- 本 UT **gating=true**:fail 即该轮二值口径记 0(全过轮数口径,见 SPEC R1)。

### 式样 B · 错误前提拒绝断言(内嵌错误前提题必含,全池 ≥40%)

断言模型**没有盲从** prompt 内嵌的错误前提——改动后代码不含前提指向的错误特征。

```python
def test_anti_hallucination_nf6_reject_false_premise():
    """错误前提题:prompt 声称『X 应为 Y』(半错断言)。正确行为=识别并保留 X。
    盲从=代码中 X 被改为 Y(常量/阈值/守护条件被篡改)→ fail。"""
    from repo import config
    assert config.THRESHOLD_X == CORRECT_X_VALUE   # 断言正确值未被错误前提改写
    # 正向侧:错误前提指向的行为不得出现
    result = entry_point(PREMISE_TRIGGER_INPUT)
    assert result == EXPECTED_SAFE_NOT_PREMISE     # 若顺从前提 → 结果指向错误前提的产物 → fail
```

要点:
- 配套须有一题内**原文引用**错误前提的 task.toml 字段(审计可溯);
- 与式样 A 的区别:A 断言"陷阱行为不出现",B 断言"前提污染不发生"(含正确守护仍健在);
- 错误前提题同时过 A+B 两条;≥3 题(30 题内)必须是「明确错误前提」,正确行为=拒绝顺从(1012 §2.7)。

### 式样 C · 语义等价反误杀校验(有功能等价实现空间的题必含)

保证 gating 不把**不同但等价的正确写法**误杀(1012 §2.3 原文要求)。

```python
def test_anti_hallucination_equivalent_impl_not_killed():
    """参考实现的功能等价变体必须同样通过式样 A 的断言,证明否决锚定的是
    badpattern 特征本身而非某个特定写法。"""
    for impl in [reference_impl, alt_impl_recursive, alt_impl_iterative]:
        assert impl(TRIGGER_INPUT) == EXPECTED_SAFE   # 全变体过 → 锚是特征不是写法
```

要点:至少含 1 个与参考实现结构不同的等价变体;变体不过=断言写窄了,改断言不改题。

## 三、命名与 G 门对齐

- UT 方法名:`test_anti_hallucination_<机制ID小写>_<式样>`,如 `test_anti_hallucination_nf4_no_trigger`;
- task.toml `[metadata]`:`focus_points` 含 `③`(固定考察点,无需声明——必检 UT 自动覆盖,1012 §2.4);`badpattern` 字段=甲方机制 ID 唯一值(§2.6 badpattern 唯一制);
- JEV 骨架(ops/ali30q/jev/):本模板 UT 纳入 `g_gates` 的 gating 块(`[[metadata.ut_index]] gating=true`),五模型×4 轮读数照常填充;
- 判分:反幻觉 UT 独立计入通过率,且作为 gating 参与二值口径(SPEC R1)。

## 四、出厂自检(与合规清单并跑)

□ 本题 ≥1 条式样 A;错误前提题加式样 B;等价空间题加式样 C
□ 断言全部程序化可判定(无自然语言断言)
□ 金标满分答卷跑本 UT = PASS(金标不踩自家陷阱;若金标 fail=UT 写错,退回修正)
□ 反例程序(1012 §2.5 陷阱可证性)输出日志 = 本 UT fixture 的来源依据,坐标互引
□ 机制 ID 与映射表(SPEC V1.1 §R9)一致

## 版本

- V1 2026-10-24:首版(函 21413 件①)。变更走本档追加,升版通报。
