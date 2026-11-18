# INC_20261118 · R564 更正：R563「bge-m3 本地化」候拍板项前提不成立 + 唯一残余地雷定位（daemon 本地 fallback）

> 日期：2026-11-18 00:15–00:52 EST（R564）
> 上游档：`INC_20261118_HF_NFS_CACHE_ROOTCAUSE.md`（R563）
> 本轮性质：**更正一条已进候拍板清单的误判** + **定位到 R563 修法未覆盖的唯一残余地雷**
> 本轮**零生产改动**（未改 plist / 未改插件 daemon.py / 未改 symlink / 未碰记忆卡 / 未动他线未提交文件）

---

## 一、更正：R563 的「bge-m3 本地化」候拍板项是误判，应撤而非执行

R563 留下的候拍板项原文：**「bge-m3 本地化（8400 embed server 因常驻内存而活·一旦重启将同样卡死·约 2.2GB 同法 SSH 拉）」**。

本轮三条现场实测证明其**前提不成立**：

| # | 证据 | 实测方式 |
|---|---|---|
| 1 | `bge-embed/embed_server.py:11` = `MODEL_DIR = os.path.expanduser("~/bge-embed/models/bge-m3")`；第 21–22 行 `AutoTokenizer.from_pretrained(MODEL_DIR)` / `AutoModel.from_pretrained(MODEL_DIR)`；**全文无 `huggingface` / `HF_HOME` / `snapshot_download` 引用** | `grep -nE` 实读源码 |
| 2 | 该本地目录在位且**完整**：4.3GB；含 `pytorch_model.bin` 2,271,145,830B、`tokenizer.json` 17,098,108B、`tokenizer_config.json`、`sentencepiece.bpe.model`、`special_tokens_map.json`、`config.json`、`modules.json`、`1_Pooling/`（无 `vocab.txt`——bge-m3 用 sentencepiece，不需要） | `ls -la` + 逐文件存在性实测 |
| 3 | `GET /health` → `{"status":"ok","device":"mps","model":"bge-m3","port":8400}`；`POST /embed` → **0.03s / dim=1024** | curl + urllib 实打 |

**结论**：8400 embed server **全程不读 HF 缓存、不读 NAS**。它不是「靠常驻内存侥幸活着」，而是**模型本来就在本地盘**。

⇒ R563 的两个推断均不成立：
- 「一旦重启将同样卡死」→ **不成立**（重启后从本地盘加载，无 NAS 依赖）。
- 「拉 2.2GB 到本地」→ **无作用**（拉了也没有任何代码路径会去读它）。

**该候拍板项应从清单中撤销**，不是「待执行」。若照 R563 原文执行，会在数据卷 96% / avail 18Gi 的前提下白占 2.2GB。

---

## 二、真正的残余地雷：daemon 的**本地 fallback** 路径（R563 修法未覆盖）

R563 修的是 reranker 侧（8401 → 本地 `~/.cache/hf-local`）。**另一条路径仍在同一坏子树上**：

```
daemon plist（实读 ~/Library/LaunchAgents/com.nautilus.compass-daemon.plist）
  COMPASS_EMBED_PROXY = http://127.0.0.1:8400      ← 嵌入走 8400（本地模型，安全）
  COMPASS_RERANK_REMOTE = 127.0.0.1:8401            ← 重排走 8401（R563 已修）
  HF_HUB_OFFLINE = 1
```

**fallback 链（源码坐标）**：

| 位置 | 行为 |
|---|---|
| `daemon.py:740-760` `get_embedder()` | proxy 已设 → `_ProxyEmbedder`（8400）；docstring 明确「proxy 不可达时抛异常，**由调用侧 fallback 本地**」 |
| `daemon.py:765-774` | fallback 落到 `SentenceTransformer(EMBEDDER_MODEL, device=device)` |
| `daemon.py:592-597` `EMBEDDER_MODEL` | `~/.cache/modelscope/hub/models/BAAI/bge-m3` **若存在**用它，否则用 **HF repo id `"BAAI/bge-m3"`** |

**实测关键一环**：`~/.cache/modelscope/hub/models/BAAI/` **不存在** ⇒ fallback **必然**走 HF repo id ⇒ 解析到
`~/.cache/huggingface/hub/models--BAAI--bge-m3` → 该 symlink 现指向 **NAS**（`~/mnt/nas-work/model-cache/huggingface/hub/models--BAAI--bge-m3`）。

**实测关键二环**（本轮对 bge-m3 子树独立复现，与 R563 在 reranker 子树报的现象同型）：

| 操作 | 实测结果 |
|---|---|
| 读 `refs/main` | **12.15s 超时（阻塞）** |
| 列目录 | **5.09s `InterruptedError`（EINTR）** |
| `snapshots/*` glob | 5.73s 返回 **空列表** |
| 读 safetensors 头 1MB | 5.01s **找不到文件** |

⇒ **一旦 8400 掉线 / 代理不可达，daemon 的本地 fallback 会重演 R562/R563 同一个 `open()` 永久阻塞**
（30s deadline 到期后二次重试更久）。这是当前**唯一剩余的同类地雷**，R563 的修法不覆盖它。

---

## 三、候选修法（候用户拍板·本轮零执行）

### A 零字节改指（推荐）
把 `~/.cache/huggingface/hub/models--BAAI--bge-m3` 从 NAS 改指**本地已有模型**，构造 HF 布局 shim：

```
~/.cache/huggingface/hub/models--BAAI--bge-m3/
├── refs/main          # 文件，内容为 "main"
└── snapshots/main -> /Users/chunxiao.wang/bge-embed/models/bge-m3   # symlink
```

⇒ `SentenceTransformer("BAAI/bge-m3")` 在 `HF_HUB_OFFLINE=1` 下直接命中本地权重，**不复制 2.2GB**。

- 验证法：① `HF_HUB_OFFLINE=1 python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-m3')"`（带超时）② `launchctl kickstart -k gui/$UID/com.nautilus.compass-daemon` ③ 跑一次 MCP recall
- 风险：改坏 HF cache 布局会让 daemon 启动 eager-load 失败（被 `daemon.py:1782` 的 try/except 吞掉→lazy 重试）⇒ **变更前须备份原 symlink 目标**

### B 一行 env
plist 增 `ZMM_EMBEDDER_MODEL=/Users/chunxiao.wang/bge-embed/models/bge-m3`（绝对路径，绕开 HF 解析）⇒ 需改 launchd plist + 重启 daemon。
（A 改本机缓存；B 改生产配置；两者都需授权。）

### C SSH 拉 2.2GB（R563 原方案）
**可行但冗余**：本地已有 4.3GB 同款模型，拉第二份纯浪费磁盘（当前数据卷 96% / avail 18Gi）。仅在 A/B 都不被采纳时才需要。

---

## 四、NAS 侧根因仍未定位（框外）

本轮独立复现 NFS 子树读阻塞（readdir EINTR + refs/main 阻塞），与 R563 的现象同型。服务端数据完好（R563 实测 SSH 直连秒回）⇒ 故障在 **NFS/SMB 协议路径**，属 `INFRA_BASELINE` 责任域（compass 框外），需 NAS 侧排查。

---

## 五、本轮值守面（全部现场实测）

| 面 | 读数 |
|---|---|
| 信箱 compass | **0** 未读 |
| RED 窗口 `check --to platform` | **219 封**（与 R563 持平·最新仍 id100729 ×85·**零增量**） |
| Gmail | 401 → 直刷 REFRESH_OK 3599s → 全量口径 7d **53 封**（R563 记 59·-6 出窗）/ 未读 **32** 持平 / 草稿 **35** 封零新 / **最大 internalDate 11-18 02:09Z（IFTTT 营销）早于 R563·零新商务函零新面孔** |
| mentions | 5 条全旧（最新 11-02） |
| notifications | 45 条全旧（最新 11-13） |
| genesis | 5 家（1/1/0/1/2）零 REPLY |
| dev.to | 30 文 · 有评论 2 篇（6+2）全旧 |
| a2a-x402#198 | 仍 1 条（alanwang100 11-09）·草稿 SLA 过期候用户硬闸 |
| CI | compass **44228981191**（= R563 head 6731f4af）success；core 43558665734 success |
| 本地 HEAD | = origin/main = 6731f4af，零领先 |
| daemon / watchdog / 哨兵 | 9876 ok / exit0 / exit0 **recall_hit=11** |
| recall 端到端 | **MCP recall 实打可用**（R563 修复持续有效） |
| GATE0 | **PASS** |
| 快筛 | CS-513 过；CS-512/514/515/516/517/518 不过 = 历轮全同 |
| 管道三件 | exit0 |
| 矩阵 | mtime 仍停 10-30 09:42 |
| S0 池 | 两仓分支 404 退役态 |
| 记忆库 | **1424 张**（session_auto 883 + distill 309 + session_非auto 40 + 主题 191 + MEMORY.md 1）⇒ **噪声 1232 = 86.5%**（R561 的 86.7% 基本持平；24h 内新/改 19 张 = distill 13 + 主题 6） |
| 磁盘 | 数据卷 96% avail 18Gi（≥10Gi alarm 线） |

---

## 六、教训

- **「拉一份模型到本地」不是通用药**：先确认**谁真的读那个路径**。R563 修的是 reranker；bge-m3 那条是按推测列的，实际无人读。
- **fallback 路径是修复的盲区**：主路径修好后，fallback 往往还指着同一个坏根因——**修复必须把 fallback 也纳入检查清单**。
- **共享插件的失败模式要按「读路径」列，不按「组件名」列**：本轮把 R563 的「bge-m3 一项」拆成「8400 主路径（本地，安全）/ daemon fallback（NAS，坏）」两行，误判即刻暴露。
