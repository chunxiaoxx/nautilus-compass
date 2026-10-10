# rerank 在线验收方案(2026-10-10 · R489 · 部署四步第 4 步细化)

> 前置:部署序列①合 main(PG 流程)②隧道自启 ③双开关——本档=第 4 步"验收"的可执行定义。判据源=E1-TUNE v1 冻结档(EIGHTB/SEVENB_PREREG 同源纪律,零新判据)。

## 一、验收判定表(预注册,只许更严)

| 门 | 判据 | 口径 |
|---|---|---|
| V1 功能门 | daemon 开 rerank 后,recall 输出的 top 顺序与离线 E1 组合管线(0.8333 读数管线)对同一查询集一致 | 抽 10 query,逐条比对 |
| V2 延迟门 | 带 rerank 的 recall 端到端 P50 ≤ 3s(本机预算) | 30 query 实测 |
| V3 回退门 | 隧道断开(杀 a100_rerank_tunnel)→recall 自动回退 dense 顺序,不报错不挂起 | 断链实弹 3 次 |
| V4 开关门 | COMPASS_PROD_RERANK=0(默认)行为与现版 byte-identical | 抽 5 query diff |

## 二、验收执行序(部署窗内,~30 分钟)

1. 合 main+重启 daemon(开关 off)→ V4 基线 diff;
2. 开双开关(COMPASS_PROD_RERANK=1 + COMPASS_RERANK_REMOTE=127.0.0.1:19879)→ 重启;
3. V1 一致性 10 query(取 A_plus_queries_v2 前 10)+V2 延迟 30 query;
4. V3 断链实弹(kill tunnel→recall→观察回退→重启隧道);
5. 全过→验收报告落档(rerank 上线正式化);任一不过→开关回 off,问题归因。

## 三、回滚预案

开关回 off 即回滚(零数据迁移);隧道守护独立存在不影响其他服务;daemon 回退=git revert 单 commit。

—— compass · RERANK-ACCEPTANCE · R489 · 2026-10-10


---

# 附:激活评估(原 RERANK_ACTIVATION_ASSESS 独立档并入,2026-10-10)

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

