# jev-trust 第二域实弹协议(预注册 · 2026-09-22)

> 域 2/自用 DCR:v5 代码修复域。上一域(python-exception-prediction,
> C=0.9534)是「读代码判事实」;本域升一级难度:「读 patch 判行为变化」。
> 仪器:PyPI jev-trust 0.1.0。判据口径与域 1 完全一致(PROTOCOL 同构)。

## 域定义

**code-patch-behavior**:给定一个短 Python 函数与其「修复」后版本,
问 Jev(noul)"打上这个补丁后,这次具体调用的行为会改变吗
(返回值不同或异常不同)"。模型必须理解补丁语义差异——
v5 修复判定场景的最小切片。

## 生成器(确定性)

- seed=20260922,n=120,六模式×20:
  1. off-by-one(range 边界移动/不动)
  2. 边界条件(> 与 >=,输入取边界值)
  3. None 检查差异(`b != 0` vs `b` 真值判定,b 可为 None)
  4. 默认值(dict[k] vs dict.get(k, 0))
  5. 类型转换(str 拼接 vs 直接相加,输入类型决定)
  6. 等价重排(纯重命名/格式,行为必不变——负例)
- 真值:机械——实际执行两版,比较 (返回值, 异常类型名);相同=0,不同=1
- 决策集 JSON 归档(含 sha256),正例约半

## 调用纪律

一题一请求,jev-latest,decide→record_outcome 真值流;内容零重试;失败如实记录。

## 判据(与域 1 逐字同构)

1. 口径写死:ECE 10 桶 top-label;Brier=mean((1−p_true)²);C=1−ECE;
   与 jev_trust.calib 0.1.0 一致,库/手算必须一致
2. 工件完备:decision_set.json+session.jsonl+.sig+pubkey 全入库
3. 验签 VALID
4. 全量无剔除(含 error)
5. 不设好坏门,如实报告

## 收工

RESULTS.md 全数字+边界;状态:**待非实现者复算**。
与域 1 构成「域对比」:同一模型相邻两域的 C 值差=域特异性又一实证。
