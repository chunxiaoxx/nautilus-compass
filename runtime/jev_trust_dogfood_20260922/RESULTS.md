# jev-trust dogfood 首跑结果(2026-09-22 · 协议见 PROTOCOL.md)

**域**:python-exception-prediction(读 Python 函数源码+具体调用,判"会抛异常吗")
**仪器**:PyPI 发布版 jev-trust 0.1.0(非源码路径)· jev-latest
**规模**:n=120(6 模式×20,seed=20260922,正例 46)· 132 秒 · 0 错误

## 读数(全量,无剔除)

| 指标 | 值 |
|---|---|
| accuracy | **1.000**(120/120) |
| Brier | **0.00546** |
| ECE(top-label,10 桶) | **0.0466** |
| C = 1 − ECE | **0.9534** → **FACE_VALUE** |

分模式抽样日志:六模式置信均在 0.95-0.98(仅 attrerror 末题 0.67);
模型在该域置信略保守(100% 正确 vs 自报 ~0.96)。

## 判据对账(预注册五条)

1. 口径:ECE/Brier/accuracy/C 由 jev_trust.calib 0.1.0 计算(公式 PROTOCOL.md 写死)✅
2. 工件:decision_set.json(sha256=9652aa7428959181…)+ session.jsonl + .sig + pubkey.txt 全在 ✅
3. 验签:jev_trust.verify_log → **VALID** ✅
4. 无选择性报告:120 全量入库,errors=0 ✅
5. 不设好坏门:如实报告 ✅

**判据状态:GREEN(仪器首跑闭环)**
**复算状态:待非实现者复算(新鲜会话按 PROTOCOL.md 重放)**

## 边界(读数不可外推的地方)

- **合成确定性域**:六种异常模式程序化生成,题面干净无对抗;与
  email-choice 域(C=0.086)的教训一致——**校准是(模型,域)对的属性**,
  本读数只说明 Jev 在"读短函数判异常"这类任务上又稳又准,不说明
  任何其他域。
- 模式覆盖 Python 常见异常族但不含:自定义异常、多函数交互、副作用
  (IO/网络)、深层嵌套逻辑。
- n=120 是仪器试跑规模,置信区间未计算;ECE 的分桶样本量偏小
  (attrerror 单题 0.67 置信落 6 桶,低样本桶)。

## 复算方法(任何人)

```bash
pip install jev-trust
python -c "
from jev_trust import verify_log
print(verify_log('session.jsonl', 'session.jsonl.sig', open('pubkey.txt').read().strip()))"
# 读数复算:解析 session.jsonl 的 call+outcome 行,按 PROTOCOL.md 公式重算
```
