---
name: orgfuel-ORGG-c70b0b6c22f16315-3c6d3584e8
description: "判读档判例 DAY_LOG_20261009 · 三、复盘认知(六次"红灯先证伪自己"全部纠偏) ## 三、复盘认知(六"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-c70b0b6c22f16315
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 DAY_LOG_20261009 · 三、复盘认知(六次"红灯先证伪自己"全部纠偏)
## 三、复盘认知(六次"红灯先证伪自己"全部纠偏)

1. **sha 口径行尾分裂**:平台报"旧 sha"→不认错先查证→根因=autocrlf 双口径,非文件旧→gitattributes 固化根治;
2. **A4 险些误删**:清理列单里 ecc venv 按体积判"可删"→执行前探针抓到 2 个在役 uvicorn→否决(该条从列单剔除);
3. **containerd 16G 误诊**:初判"k8s 残留可清"→深挖实为 docker 悬空层,contachd 真身 4K→改用 docker prune;
4. **cache 不递进虚警**:测试进程 inotify fast path 环境差导致"cache 不涨"假象→进程内实验定位→与生产无涉;
5. **dedup 冷文件漏检**:不是 bug 是 EMBED_BUDGET 渐进设计→按诚实纪律加 coverage 披露而非改机制;
6. **recipe 格式偏差**:发前预检抓到 TEMPLATE schema 不符→重写,避免 PR 被打回。

**共性**:[实测]探针成本远低于错误动作成本——六次全是在"动手前"或"结论前"被探针拦下。
