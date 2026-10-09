# rerank 层激活评估(2026-10-10 · R446 · E1 读数工程化的决策档)

> 结论先行:**本机 daemon 暂不激活生产 rerank**——CPU 延迟实测不过预算;E1-TUNE 0.8333 过门读数的工程落地需 GPU 宿主,三路径列下候拍板。

## 一、骨架盘点 [实测,复用旧实物]

daemon.py v2.3.0 已内置完整 rerank 层,非新工程:
- 开关 `COMPASS_PROD_RERANK=1`(默认 off);候选深度 `COMPASS_RERANK_CANDIDATES`(默认 30);
- 模型 bge-reranker-v2-m3(与 E1-TUNE 实验同款,判据同源);lazy singleton+lock+fail-soft(失败回退 dense);
- 当年 benchmark 在档:bge-m3+reranker → P@5 0.86→0.92 / MRR 0.685→0.855;
- 本机权重已备:HF 缓存 2.2GB 完整(snapshots/953dc6f6)。

## 二、激活四前提核对

| 前提 | 状态 |
|---|---|
| 1 骨架实现 | ✅ daemon v2.3.0 在役 |
| 2 权重在位 | ✅ 本机 HF 缓存 2.2GB / A100 /root/vdf/models 双端 |
| 3 判据过门 | ✅ E1-TUNE v1:v2 干净工作集组合管线 R@1 0.8333/R@5 0.8333 |
| 4 **延迟预算** | ❌ **本机无 GPU,CPU 实测不过(下)** |

## 三、延迟实测 [实测,本机 CPU]

| 配置 | 实测 |
|---|---|
| CrossEncoder 加载(一次性) | 67s |
| rerank 8 candidates | **3.44s/查询** |
| rerank 30 candidates(生产默认) | **7.64s/查询** |

对照预算:recall 端到端需 <3s(当前 bge alone 1.9s)——**任何 candidates 配置都超预算,本机激活否决**。硬激活=每条 recall 5-9.5s,用户可感知劣化(今晚 hook 提速的成果会被一次性吃掉)。

## 四、三路径(候拍板)

| 路径 | 内容 | 成本 | 判 |
|---|---|---|---|
| a GPU 宿主(建议) | daemon rerank 走 A100(模型已在位):daemon 加 remote-rerank 通道(9876 协议扩展 action=rerank,A100 起轻量 rerank 服务接 GPU) | 1-2 天工程 | GPU 实测 A100 上 rerank 30 cand 预计 <300ms |
| b 轻量模型 | bge-reranker-base(4× 快,CPU 8cand≈0.9s?) | 需重测精度(E1 判据重跑) | 精度 trade-off 未证,不default |
| c 边际触发 | 仅 dense top1-top5 分差小于阈值才触发 rerank(多数查询免付延迟) | daemon 工程改造+阈值调参 | 精度收益打折,候 a 落地后再评估 |

## 五、建议时序

开业周(10/13-19)不动作(rerank 非开业阻塞件);10/18 排期位按工作台排期 v1 评估路径 a;E1-TUNE 读数与判据档作为 a 落地后的验收判据(零新判据)。

## 六、证据层

- 骨架/开关/benchmark 注释:daemon.py L108-127/234-291 直读 [实测];
- CPU 延迟:本机实测(sentence_transformers CrossEncoder fp32 CPU) [实测];
- A100 预估 <300ms:[推断](A100 GPU bge-reranker 典型性能,upgrade_path=路径 a 落地时实测);

—— compass · rerank 激活评估 · 2026-10-10 凌晨
