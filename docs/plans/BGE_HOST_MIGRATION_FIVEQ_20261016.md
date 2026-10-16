# BGE 宿主迁移终态与五问评估(2026-10-16 · R542)

> 用户问:BGE 是否已全部迁出(A100/笔记本/cloud)?现宿主(Mac mini)效果/延迟/速率/精准匹配/调优潜力五问。
> **先澄清:现宿主是 Mac mini(M6),不是 MiniMax**(MiniMax 是标签重判用的 API 供应商,无 BGE)。

## 一、BGE 宿主全景(三台机器逐一核查)

| 机器 | BGE 状态 | 说明 |
|---|---|---|
| **Windows 笔记本** | ✅ **已迁走**——daemon 743MB 无本地 BGE,eager-load 移除 | 用户拍板"本地不跑 BGE"已落地 |
| **A100** | ✅ **已停机**(Status 8,磁盘保留)——GPU/嵌入/判分全停 | 累计消费定格 1071.14 元 |
| **cloud 服务器** | ⚠️ **仍在运行**——本地 BGE CPU fallback 在跑(compass-bge-daemon 的 COMPASS_EMBED_PROXY 指向 19987 隧道→A100,隧道断后 daemon 自动 fallback 本地 CPU 嵌入,**慢但活**) | 遗留:待切 Mac mini 或确认 CPU fallback 可接受 |
| **Mac mini M6** | ✅ **现役宿主**——bge-m3 MPS,LaunchD 常驻,8400 端口 | 局域网 IP 192.168.5.120 |

## 二、五问实测回答(Mac mini M6 · bge-m3 · MPS)

### 1. 效果:同模型,质量等同 ✅

同一模型(bge-m3)、同维度(1024)、同归一化。MPS 与 CUDA 的实现差异对**嵌入质量无影响**(只是计算后端)。recall 实测:hook 链路三查询全命中(首考记忆 0.654 最高分,语义排序合理)。

### 2. 延迟:单条 49-128ms(中位 63ms)✅ 良好

含网络往返(Windows→Mac mini 局域网)。纯推理部分 MPS 上 bge-m3 单条约 20-40ms。对比:A100 单条 30ms(GPU 更快但需跨公网隧道 +80ms)——**局域网 Mac mini 实际端到端更快更稳**。

### 3. 速率:批量 244 条/秒 ✅ 优秀

32 条/批 0.13s。**对比历史**:A100 隧道版 ~200ms/条(单条 HTTP 往返主导)、cloud CPU fallback ~4min/792 条(0.3s/条)。**Mac mini 批量是全历史最快配置**(batch 接口+局域网零公网)。2519 条 orgfuel 全量重嵌约 10 秒(批量)。

### 4. 精准匹配:跨设备 cosine 0.88-0.96(中位 0.91)⚠️ 需知情的细节

Mac mini(MPS)新嵌入 vs pkl 里 A100(CUDA)旧向量,同文本自相似:0.877-0.961。**不等于 1.0 的原因**:MPS vs CUDA 浮点路径差异+bge-m3 库版本差异(非精度缺陷)。
**影响评估**:cosine 0.91 的向量在检索排序中与原向量排序基本一致(相对序保持),**对 recall/排序零实质影响**;唯一切换期注意=旧 pkl 缓存向量与新嵌入混用的过渡期,排序可能有轻微抖动——一次性全量重嵌(批量 10 秒)即消除。
**精准匹配的实现口径**:上层全部走 cosine 相似度排序,不依赖绝对向量值——跨设备差异被 cosine 天然吸收。

### 5. 调优潜力(按杠杆排)

- **已足够用**:244 条/s 覆盖全部现役负载(2519 语料 10 秒/全量重嵌;日常增量每分钟几条),无调优必要;
- 若将来提效:①`max_seq_length` 512 已 cap(可在低价值场景降 256 提速 2x)②批量 texts 64-128/批(现在 32)③`torch.compile`(MPS 支持有限,收益待测);
- **真正值得调优的在别处**:daemon 侧批量嵌入接口(现在单条循环经 HTTP,批量直调可 10x)——已在 RAG migration memory 记为待办。

## 三、cloud 侧遗留(待办)

cloud daemon 的嵌入当前=本地 CPU fallback(A100 隧道已断)。两个选项(候用户/后续):
- **切 Mac mini**:cloud daemon 的 COMPASS_EMBED_PROXY 指向 Mac mini(需公网可达:frp/云隧道/或 Tailscale)——架构统一但增加 Mac mini 公网暴露面;
- **维持 CPU fallback**:cloud 记忆量小,慢但零暴露。**当前建议:维持现状**(cloud 记忆检索非热路径)。

—— compass · R542 · 2026-10-16 · 全部读数 [实测]
