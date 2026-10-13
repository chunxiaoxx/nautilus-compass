---
name: orgfuel-ORGG-44d3268317db8eb3-5d028e37e5
description: "判读档判例 JUDGE_HOTPATH_INTEGRATION_PLAN_20261001 · 二 · 接入设计(第一版"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-44d3268317db8eb3
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 JUDGE_HOTPATH_INTEGRATION_PLAN_20261001 · 二 · 接入设计(第一版=影子模式)
## 二 · 接入设计(第一版=影子模式)

1. **只标记不拦截**:ingest 返回值加 `verdict: {label, confidence}` 字段+落盘到 verdict log(jsonl,一行一判定,含输入 hash)——不改任何入库行为
2. **判分器独立进程**(端口 9879):
   - 云端 daemon 刚做完内存根治,判分器(1.7B 底模 ~4G)绝不内嵌——独立进程,OOM 隔离,daemon 出口走 localhost TCP(同 9876 协议族)
   - 本地(Windows)同款:独立进程+惰性加载(首次判定才载模型)
3. **特征管道同源**:sample_text() 与 P2v2 训练同款(无作弊通道版);输入=text+tags+source
4. **三态语义**(U 态是特性):pass=正常/fail=标记可疑(如空文/复读/注入痕)/U=证据不足进待人工池
