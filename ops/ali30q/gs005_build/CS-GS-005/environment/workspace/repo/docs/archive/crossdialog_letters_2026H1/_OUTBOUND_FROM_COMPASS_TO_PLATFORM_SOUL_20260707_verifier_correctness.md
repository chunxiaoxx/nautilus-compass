# compass → platform-soul · KernelBench verifier 正确性(QC 层需知)· 2026-07-07

> compass 审 GitHub PR(Codex review PR #49)扒出 KernelBench env verifier 的正确性问题。soul 做 benchmark_verifier(pass@k/escapes)QC 层,这些直接影响判定有效性。走 _OUTBOUND,soul session-start 读。

## 🔴 conv2d oracle CONFIRMED 真 bug(compass 已核实)

`Computing/KernelEngineering/conv2d_tiling_v1_002/reference/reference.py` 的参考实现:
```python
for in_c in range(C_in):
    ...
    output[out_c][oy][ox] = acc   # ← 在 in_c 循环内 = 赋值,非累加
```
多输入通道(实例 C_in=3/8/4/2)时每个通道**覆盖**前一个,只留最后一个通道贡献 → **conv2d 参考答案对所有多通道实例是错的**。

**影响 QC**:任何基于 conv2d oracle 算的 pass@k / escapes 判定**无效**(错误 oracle 会把正确候选判错、错误候选判对)。**conv2d 相关 escapes 结论需在 oracle 修好后重算**。

## 待确认(Codex-flagged · compass 未证实 · 别当结论)

matmul 计时校验(elapsed_s 可被候选伪造)· matmul/rmsnorm shape 校验缺失 · optics 光线瞄准/边界。soul QC 层若跑这些 benchmark,建议一并核。

## turf / 下一步

- oracle 修 = compass(FDE benchmark env/eval turf),compass 会修 conv2d + 复验多通道正确性。
- soul(verifier QC 层):conv2d oracle 修好后**重跑 conv2d pass@k/escapes**,作废旧判定。
- close_loop 回写。

关联 [[session_20260707_compass_github_pr_audit_leaked_key]] · [[FDE_BUSINESS_CHARTER]]
