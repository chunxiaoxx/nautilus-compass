# jev-trust 域 2 结果:code-patch-behavior(2026-09-22 · 协议见 PROTOCOL.md)

**任务**:读 Python 函数的修复 patch,判"这次调用的行为会变吗"(返回值/异常)
**仪器**:PyPI jev-trust 0.1.0 · jev-latest · n=120(6 模式×20,seed=20260922,正例 37)· 133s · 0 错误

## 读数(全量无剔除)

| 指标 | 值 | 域 1 对比 |
|---|---|---|
| accuracy | **0.925** | 1.000 |
| Brier | **0.0575** | 0.0055 |
| ECE(top-label) | **0.1343** | 0.0466 |
| C = 1 − ECE | **0.8658** → FACE_VALUE | 0.9534 |

**域间差 −8.8pt**:同一模型相邻两域(patch 语义理解 vs 异常事实判断),
C 从 0.9534 掉到 0.8658,accuracy 掉 7.5pt——校准货币的域特异性又一实证,
且这次难度梯度是我们自己设计的。

## 分模式准确率(错在哪)

- boundary / default / offbyone / rename:**20/20 全对**
- **nonecheck 16/20**(`b != 0` vs `b` 的 None 语义)
- **typeconv 15/20**(str 拼接 vs 直接相加,输入类型决定)

错的集中在「语义等价性判断」——正是 v5 修复判定域的核心难点。
ECE 0.134 说明置信偏高于实际(92.5% 准确但自报更满)。

## 判据对账

1. 口径与 jev_trust.calib 一致,独立手算四指标**精确一致** ✅
2. 工件:decision_set.json(sha256 见 stats.json)+ session.jsonl + .sig + pubkey 全在 ✅
3. 验签 **VALID** ✅
4. 全量无剔除(errors=0)✅
5. 如实报告 ✅

**判据 GREEN · 待非实现者复算**(新鲜会话按 PROTOCOL.md 重放)

## 边界

- 合成短函数(≤6 行),无多文件/无副作用/无上下文依赖;
  真实 v5 修复场景(带测试套件、更长 diff)难度更高,本读数是下界参照
- n=120 未算置信区间;nonecheck/typeconv 单模式仅 20 题
- 域 1/域 2 同日同模型版本,域间差是任务难度差的净读数

## 复算方法

同域 1:`pip install jev-trust`,verify_log 三元组 + session.jsonl 手算重放。
