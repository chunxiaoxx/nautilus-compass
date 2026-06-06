# compass 云 substrate 部署 — 设计文档（2026-06-06）

> 状态:设计批准(brainstorming 收敛)· 执行分期 · P2+ gated on 平台签 token。
> 本文档不 ship 部署 · 出实施 plan 见配套 writing-plans。

## 0. 目标(用户确认:两者都要)

1. **多 agent 共享 substrate** — v5/v7/kairos 读写**同一份**云端记忆,真正的跨 agent 记忆胶囊(= Phase B · agent-first substrate)。
2. **个人跨设备** — 你任何机器/手机访问同一份 compass 记忆。

诚实边界:GPU 不是"共享"的 enabler(共享=云部署架构);GPU 买的是 **reranker 默认开(+0.167 P@5)+ 速度 + 并发**。

## 1. 架构裁定:云权威 + 瘦客户端(A 起步 → C 演进)

放弃"双向文件同步"(B · 类比比特币分布式账本 · 需冲突共识 · 记忆不需拜占庭容错 = 杀鸡用牛刀 · 踩 anchor #3 D 维护)。

**A(起步)**:云跑权威 daemon,所有读写打云。**"双向同步"被溶解为单写权威** —— 一条 ingest 路径写同一份云语料 = **零冲突**,这就是绕开同步地雷的本质。
**C(演进)**:本地加**只读副本**(单向从云拉)供离线 recall + 提速 · 写仍去云 · 仍零冲突。

## 2. 拓扑(spot/持久分离 · 核心抗抢占)

竞价(spot)T4 随时被回收 → **无状态算力(spot OK)与有状态数据(必须持久)分开**。

```
持久 CPU 服务器(现有 · 4核16G180G · up21天)        spot T4(GPU · 便宜 · 可丢)
├─ postgres(poi_credit · 权威 · 已在此)   ←ingest写── GPU daemon(bge-m3 + reranker 默认开)
├─ 语料真相源(memory .md · 单一真相)      ←启动拉──→  ├─ 内存语料 + index 缓存(可重建)
└─ CPU daemon(冷备 · T4挂时拉起)                       └─ PoI 快照文件(从 CPU 服拉 · 非每查 live)
       ↑ T4 被回收 → 客户端 fallback 到这                ↑ 客户端优先打(GPU 快)
```

- **T4 不需要自己的权威 DB**(在临时盘 = 被回收丢数据)· 它读 CPU 服的 postgres + 拉语料/快照到本地缓存 · recall 全内存。
- **现有持久 CPU 服 = 灾备(DR)** —— 数据持久 + 降级可用。**不用第二台 T4**(2 台 spot 可能同时被回收 = 解决不了 DR · 混淆 HA/DR · 浪费 spot 省下的钱)。
- spot 被回收 → 收 2 分钟终止信号 → drain 在途 ingest → 新 spot 自动拉起 + 重建 index。

## 3. 实测资源占用(2026-06-06 SSH cloud 实测 · 非臆测)

CPU 服现状:CPU load 0.4-0.8/4核(充裕)· 硬盘余 49G(72%用)· **内存紧**:用 6.2G + **swap 已用 6.5G**(一个 4.1G python 进程=平台/v5 turf)· 真空闲 478M · available 8.7G。

compass 在 CPU 服当**轻租客**:
- **硬盘**:语料(<500MB)+ index(几十 MB)· 49G 余量随便用 ✅
- **CPU**:recall 短峰(347ms/查)· load 充裕 ✅
- **内存**:⚠️ 箱子已 swap → **冷备**(平时≈0 内存 · 只 postgres 增量 + 语料躺盘)· T4 挂时才载 bge-m3(~1.7G · 那时 available 8.7G 够临时)· 失败切换 ~1 分钟。**不加常驻热备**(避免给已 swap 的箱子加压)。

实测数据点:本地 daemon working set 1766MB(主要 bge-m3 模型)· 本项目 memory 语料仅 5.2MB/961 文件(1.8GB 是整个 ~/.claude/projects 含 transcript · **别镜像**,只镜像 memory 语料)。

## 4. 多 agent 鉴权(Phase B · gated G-token)

云 daemon 暴露 ~17 MCP 工具(token-gated TCP · 复用 v5 已建传输)+ per-agent scope(Phase B authz 层 · 见 2026-06-06-compass-mcp-3agent-dogfood-design.md)。平台签 v5/v7/kairos token + 注册 endpoint。

## 5. 分期(降险 · 每期可独立验证)

- **P0 · 立 T4 GPU daemon**(只你 · 无 agent):spot T4 起 daemon + 拉语料/快照 + reranker 默认开 + 客户端(你本机 recall hook)指向 T4。验:跨设备 recall 通 + reranker lift 生效 + 抗抢占(手动 kill 验 fallback)。
- **P1 · CPU 冷备 + ingest 写路径**:CPU 服装冷备 daemon(systemd · 抢占信号触发)+ 所有 ingest 走云 daemon(单写权威)。验:T4 kill → 1 分钟 fallback · ingest 落持久。**先修 CJK-surrogate ingest 崩 bug**(P1 必修前置)。
- **P2 · Phase B 多 agent**(gated 平台 token):per-agent scope + v5/v7/kairos wire MCP client。验:每 agent recall+ingest 实测。
- **P3 · 本地只读缓存(C)**:离线 recall 副本。

## 6. 必修风险

| 风险 | 缓解 |
|---|---|
| spot 被回收 | 状态在持久 CPU 服 · 冷备 fallback · 自动重拉 |
| 网络依赖 recall | P3 本地只读缓存离线兜底 |
| **CJK-surrogate ingest 崩**(调研:跨设备 ingest 静默失败根因) | **P1 必修前置** · ingest 路径不能崩在 CJK |
| 公网暴露 MCP/语料 | token 鉴权 + TLS + 防火墙白名单 |
| CPU 服内存已 swap | 冷备(不加常驻热备)· compass 轻租客 |
| T4 常驻成本 | spot 竞价(便宜)· 仅 GPU 算力上 spot |

## 7. gated 边界

- G-token(P2):平台签 v5/v7/kairos token + 注册 endpoint。
- G-spot:T4 spot 实例 + 抢占处理(运维)。
- 不碰平台/v5 在 CPU 服的现有进程(4.1G python = 它们 turf)。

## 关联
[[reference_compass_rsi_fde_role_progress]] · 2026-06-06-compass-mcp-3agent-dogfood-design.md(Phase B authz)· 跨设备 ingest 缺口(缺口1)· 实测:SSH cloud 2026-06-06。
