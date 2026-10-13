---
name: orgfuel-ORGD-46cd6569375187c5-0ed2b5dcf2
description: "[## 二 · 验收判据逐条(预备档预注册四条)] | # | 判据 | 读数 | 结论 | |---|---|---|"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-46cd6569375187c5
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 二 · 验收判据逐条(预备档预注册四条)] | # | 判据 | 读数 | 结论 |
|---|---|---|---|
| 1 | dim1 三态非零方差 | 部分 356 / 未动 142 / **完成 0**——两态非零方差(3B=全"部分"单态方差 0) | **达成**(带注,见三·1) |
| 2 | dim2 与 v4 读数相关性报告,变化要解释 | 与 3B 同 id 一致率仅 10.2%(3B 正常 452→7B 异常 440)——系统性翻转,归因见三·2 | **报告达成,变化已解释** |
| 3 | OOD/主包双包同口径 | OOD 400 题补跑完成(同日):timeout=0,csv/jsonl 零不一致;材料 sha16 jsonl `83ed22204b8347ef` / csv `2688194d249988b6` / log `b98ea2cf5e22a6d2` | **达成**(带注,见五) |
| 4 | 全档留痕同六轮制 | 脚本+三件材料+本档入仓;首跑 ImportError 崩(系统 python3 缺 torchvision→换 /root/venv)留痕 | 达成 |
