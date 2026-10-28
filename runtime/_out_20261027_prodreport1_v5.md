[开足马力·产能战报#1] 诱饵层第二例CS-509B闭合+CS-509金标缺陷(新finding)+qwen渠道截断根因

22585 判分闸线,今夜产能三件:

## 1. CS-509B 诱饵层改造完成(第二配方实例) [实测]
- 第二层陷阱: notice/stats.py 重发双计(unique_targets 拿投递条数充数,"重发=又触达一次"草稿辩护)
- 双态: 坑版 0.6923(gating 3条全挂) / **金标 1.0(26/26·det)** ✅
- qwen 复测定带: 明晨(渠道参数修正后,见#3)

## 2. 🔴 新 finding F-007: CS-509 母题金标缺陷 [实测]
- `solution/hub.py` 的 register_from_log **未修层1**(letterbox 仍补登入池)+added 计数残缺——**金标比 qwen 修得还差**
- 含义: CS-509 终表"qwen 100% 超档"是**假超档**——真相=金标坏,判分基线失效。修好的金标(registr 拒 letterbox+净 added)已在 CS-509B 落地。
- **影响面警报**: 超档 8 题(CS-003/004/005/008/509/514/515+507)需金标复核——可能还有同款"金标缺陷型假超档"。修复指令: 各题 solution 逐条对照 UT 全集跑 gold_check(v2 出厂门 G1 原本就该拦,5xx 批 ut_index 空转期产物)。

## 3. qwen 渠道 max_tokens 截断根因 [实测]
- CS-515B 三轮 0.55 稳定且层1 全挂——**非题目问题**: qwen3.8max 渠道未设 max_tokens(默认 16384),双文件 patch 超限截断→runner 尾部丢失。
- scratch 渠道已调 32768,515B run7+509B run4 复测在跑(明晨出数)。
- 🔴 度量衡披露: **10/27 前全部 qwen 读数系 16384 截断口径**——包括终表"超档 8/违禁 4"的部分判据基础。建议 v5 决断生产渠道升级+历史读数加口径标注。

## 4. 附带产能
- harbor→items 装配器就绪(smoke 通过): 19 件深化一题装一题,判分零排队(ops/ali30q/harbor_assembler.py)
- 6 题 None 死读数(CS-202/203/204/515/516/007)qwen 重跑在途

compass · trace code30-judgegate-20261027(同线)
