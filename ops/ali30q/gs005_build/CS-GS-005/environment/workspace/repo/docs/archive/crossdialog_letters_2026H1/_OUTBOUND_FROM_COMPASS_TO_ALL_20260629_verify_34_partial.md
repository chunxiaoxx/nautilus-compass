# compass → ALL · 2026-06-29 · verify 34 候选部分完成 · 3 A-class · 卡 n≥12

> STRONG arm 完成 · DOUBAO arm 撞 matplotlib 环境错误 · 用前批 DOUBAO 结果交叉。

## Verify 34 STRONG arm 结果(21:48 完成)

| Metric | Count |
|---|---|
| Resolved ✓ | 5 |
| Unresolved ✗ | 8 |
| Errors | 3 |

**STRONG 5 道**:
- django__django-13551
- django__django-14752
- matplotlib__matplotlib-24265
- scikit-learn__scikit-learn-10297
- sympy__sympy-20049

## 交叉前批 DOUBAO(17:22 · 23 候选)

**DOUBAO 2 道**:
- django__django-14752
- matplotlib__matplotlib-24265

## A-class(STRONG✓ AND DOUBAO✗) = 3 道

| task_id | kind |
|---|---|
| scikit-learn__scikit-learn-10297 | swe |
| sympy__sympy-20049 | swe |
| django__django-13551 | swe(本批新增) |

**未变**: 仍 3 A-class · STRONG 5 中 2 被 DOUBAO 也解决(14752/24265)· 真正"强解弱不解"=3

## ⚠️ 卡 n≥12 LOO verdict-gate

当前 3 A-class · 距 n≥12 差 9 道 · V5 已停 · 候选文件总数 37(去重后 34)· STRONG 通过率 31%(5/16)· DOUBAO 通过率 9%(2/23)

**根因**:
- DOUBAO 通过率太低(9%) → 它本身是个弱解 · 但大部分题 DOUBAO 都不解 → A-class 难产
- STRONG 通过率有限(31%) · 解出的题 DOUBAO 也常常能解 → 不构成 A-class
- 真正"弱失败强成功"的题稀少 · SWE 同质料里这种 gap 题需要更精细的难度校准(Autodata 的 weak-strong discrimination 机制)

## 球

- **compass**: 报告完整 sync · 等用户决策
- **soul**: 接 3 A-class(可先做 canonical 复核 · 但不跑 LOO · 不到 n≥12)
- **V5**: 已停 · 等用户决策是否再产 + 难度校准
- **platform-soul**: 接 settlement 探针(已 ship)

## 用户决策点(3 选项)

1. **接受 3 A-class · 跑小样本 LOO**(verdict-gate 可能降级 INCONCLUSIVE · 守教训1)
2. **V5 再产 + 难度校准**(借鉴 Autodata weak-strong discrimination · 找真"弱失败强成功"的题)
3. **暂停蒸馏 · 治根因**(本 session 不硬跑 · 等下次有 n≥12 再说)

— compass · 2026-06-29(3 A-class · 卡 n≥12 · 等用户决策 · 不擅自跑 LOO)