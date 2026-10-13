---
name: orgfuel-ORGG-7f7edf2dbce01974-1720127ee9
description: "判读档判例 EMB_BAKEOFF_PREREG_20261009 · Conan-v2 出榜终记(2026-10-09"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-7f7edf2dbce01974
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 EMB_BAKEOFF_PREREG_20261009 · Conan-v2 出榜终记(2026-10-09 · 硬过滤执行)
## Conan-v2 出榜终记(2026-10-09 · 硬过滤执行)

- **实测发现**:Conan-embedding-v2 的 HF repo **不含模型权重**(仅 conan_api_client.py+config)——它是 **API-only 模型**(腾讯云 ak/sk 对接,权重托管在腾讯侧)。
- **判读:触碰预注册 V2 硬过滤"自托管(transformers 栈)"→一票否决出榜**(与 doubao/gemini/openai 嵌入系同判——外部 API 依赖违 4/28 用户隐私裁决)。
- **选型纪律执行案例**:热门 zh 专精模型(C-MTEB 顶级)因 API-only 出榜——硬过滤无例外;候选池返回三模型终局(bge-m3 留任三重确认)。
- 若未来 Tencent 开放权重下载,可重新入榜(候选池动态)。
