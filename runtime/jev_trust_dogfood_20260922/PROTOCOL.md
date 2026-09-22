# jev-trust dogfood 实弹协议(预注册 · 2026-09-22)

> 目的:jev-trust 0.1.0 发布后的首次真实使用(非实现者模拟:用 PyPI 发布版,
> 不用源码路径)。产出公开签名日志,第三方可用 `pip install jev-trust` 复算。
> 本档为判据锚:开工前写死,收工只许更严。

## 域定义

**python-exception-prediction**:给定一个 Python 函数源码与一次具体调用,
问 Jev(noul 类型)"执行这次调用会抛异常吗"。模型读代码作判定——
真实开发者场景,非纯数值比较。

## 生成器(确定性)

- seed=20260922,n=120,六模式×20:
  ZeroDivision / IndexError / KeyError / TypeError / ValueError / AttributeError
- 每题:短函数源码 + 具体参数;正例半数(模式内随机但 seed 固定)
- 真值由生成器机械计算(实际执行 try/except 判定),与模型无关
- 决策集 JSON 随工件归档(含 sha256)

## 调用纪律

- 一题一请求,jev-latest,`TrustedJev.decide()` 全程
- 内容零重试(库默认:仅网络类重试);失败如实记录
- 每题调用后立即 `record_outcome(qid, truth)`——模拟"真值延迟到达"流

## 判据(收工复算契约)

1. **计算口径(写死)**:
   - ECE = 10 等宽桶 top-label:`Σ (n_b/n)·|acc_b − conf_b|`
   - Brier = `mean((1 − p_true)²)`,p_true = 模型给真实结果的概率
     (noul:P(yes) 若 truth=yes,否则 1−P(yes))
   - accuracy = 正确数/n;C = 1 − ECE
   - 以上与 `jev_trust.calib` 0.1.0 实现一致;复算者可用库或手算,两者必须一致
2. **工件完备**:decision_set.json(带 sha256)+ 会话 JSONL 日志 + .sig + pubkey
   全部入库;缺一即 RED
3. **验签**:第三方 `jev_trust.verify_log(log, sig, pub_hex)` 必须 VALID
4. **无选择性报告**:n=120 全量入库,含任何 error 行;不许剔除
5. **不设好坏门**:这是仪器首跑(域校准读数如实报告,高低都发)——
   唯一硬门 = 上四条全部满足

## 收工

- 结果档 RESULTS.md 全数字 + 丑数字照登
- 状态:**待非实现者复算**(新鲜会话按本档判据重放)
