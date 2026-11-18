# INC_20261118-R565 · daemon 本地 fallback 地雷**实锤坐实** + 修法 B 实证可执行（零代码/零拷贝）

> 日期：2026-11-18 01:55–02:25 EST（R565）
> 上游档：`INC_20261118_HF_NFS_FALLBACK_LANDMINE.md`（R564·候选修法）/ `INC_20261118_HF_NFS_CACHE_ROOTCAUSE.md`（R563）
> 本轮性质：**把 R564 的「唯一残余地雷」从推断升级为实锤** + **把修法 B 从纸面候选变成已实证可执行** + **解掉一个继承前轮的前置顾虑**
> 本轮**零生产改动**（未改 plist / 未改插件 daemon.py / 未改任何 symlink / 未删记忆卡 / 未碰他线未提交文件 / 未动 NAS）

---

## 一、核心结论（R565 实锤）

> **R563 的「本地化」只做了 reranker，embedder 那条根本没本地化。**
> `~/.cache/huggingface` → `~/.cache/hf-local`（R563 换的顶层 symlink）之下，
> **`hub/models--BAAI--bge-m3` 本身仍是指向 NAS 的 symlink** ⇒ R564 说的「唯一残余地雷」是**实锤**，不是推断。

实测（`~/.cache/hf-local/hub/` 三个条目逐一 `islink` + `readlink` + `realpath`）：

| hub 条目 | islink | 指向 | 在 NAS |
|---|---|---|---|
| `models--BAAI--bge-m3` | **是** | `~/mnt/nas-work/model-cache/huggingface/hub/models--BAAI--bge-m3` | **是** ← 坏子树 |
| `models--BAAI--bge-reranker-v2-m3` | 否 | 本地真实目录（Nov 17 22:07 复制） | 否 ← R563 修好的那条 |
| `models--mlx-community--Qwen3.5-9B-4bit` | **是** | `~/mnt/nas-work/model-cache/huggingface/hub/...` | **是** ← **新发现·框外同类雷** |

⇒ R563 的修法**只覆盖了 reranker 一条**，embedder 一条被漏掉。**「修复必须把 fallback 也纳入检查清单」这条教训本轮又得到一次实证。**

---

## 二、地雷现状：NAS 读阻塞仍在（属性缓存会骗人）

对坏子树做逐步计时（python + SIGALRM 硬超时，避开 urllib/curl 长挂）：

| 操作 | 实测 | 备注 |
|---|---|---|
| `os.stat(NAS 路径)` | **OK 0.00s** | ← **属性缓存秒回·不能作为「路径健康」的证据** |
| `os.listdir(NAS 路径)` | **ERR 5.67s `InterruptedError(4)`** | readdir EINTR |
| `open(NAS refs/main)` | **TIMEOUT >10.07s** | 真正阻塞 |
| `listdir(~/.cache/hf-local)` | OK 0.00s | 顶层换 symlink 后确实本地了 |
| `listdir(~/.cache/hf-local/hub)` | OK 0.00s | 同上 |
| `listdir(hub/models--BAAI--bge-m3)`（穿过 symlink） | **ERR EINTR** | 落回 NAS |

⇒ 与 R563/R564 同型：**stat 秒回是属性缓存假象，readdir/open 才见真章**。
⇒ 触发条件不变：`COMPASS_EMBED_PROXY=127.0.0.1:8400` 一旦掉线，daemon fallback（`daemon.py:765-774` `SentenceTransformer(EMBEDDER_MODEL)`，`daemon.py:590-598` 解析为 repo id `"BAAI/bge-m3"`）→ 命中本坏子树 → **重演 R562/R563 的 open() 永久阻塞**（30s deadline 后二次重试更久）。

**当前为何未爆**：8400（`~/bge-embed/embed_server.py`，模型在本地盘）在跑 ⇒ 走 `_ProxyEmbedder`，永不加载本地 SentenceTransformer。**这是「待触发」状态，不是「已消除」。**

---

## 三、修法 B 实证可执行（本轮新增证据·且解掉一个继承前轮的前置顾虑）

R564 的修法 B 原文：**「plist 增 `ZMM_EMBEDDER_MODEL` 绝对路径」**。本轮补齐三块证据：

### 3.1 daemon.py **原生支持**该 env ⇒ 不需要改共享插件代码

`daemon.py:590-598` 实读：

```python
EMBEDDER_MODEL = os.environ.get(
    "ZMM_EMBEDDER_MODEL",
    str(Path.home() / ".cache/modelscope/hub/models/BAAI/bge-m3")
    if (Path.home() / ".cache/modelscope/hub/models/BAAI/bge-m3").exists()
    else "BAAI/bge-m3",
)
```

⇒ `ZMM_EMBEDDER_MODEL` 是**既有开关**（注释里还留了 `intfloat/multilingual-e5-small` / `bge-small-zh-v1.5` 的切换说明）。
⇒ **本轮新结论**：R561 遗留候拍板项里的前置顾虑——「共享插件 `daemon.py` 属所有框，compass 是否授权改它」——**对修法 B 不成立**。B **一行 env、零代码改动**，不碰共享插件文件。

### 3.2 目标路径结构完备（ST 本地加载所需全在）

`~/bge-embed/models/bge-m3` 实测目录内容：
`1_Pooling/`、`config.json`、`config_sentence_transformers.json`、`modules.json`、`sentence_bert_config.json`、`tokenizer.json`、`tokenizer_config.json`、`sentencepiece.bpe.model`、`special_tokens_map.json`、`pytorch_model.bin`（2,271,145,830B）等。

### 3.3 **端到端加载实测通过**（用 daemon 同一 python 环境）

环境定位：ST 只装在 `~/Projects/nautilus-compass/.venv/bin/python3`（**sentence_transformers 6.0.1 · py3.12**）；系统 `python3`/homebrew `python3`/v5 `.venv` 均 `IMPORT_FAIL`。⇒ daemon 用的就是这个 venv。

实测（`python3 -I`，纯本地路径，不触 NAS）：

```
Loading weights: 100%|##########| 391/391 [00:00<00:00, 54914.71it/s]
LOAD_OK  sec=2.9
ENCODE_OK dim=1024 sec=3.72
```

⇒ **修法 B 的目标路径可被 `SentenceTransformer` 直接加载并产出 1024 维向量：零拷贝、零下载、零 NAS 依赖。**

### 3.4 修法 A 的前提也被修正（R564 原文需调整）

R564 提的 A（造 HF 布局 shim：`refs/main` + `snapshots/main -> 本地模型`）：
- 实测 hub 里 `models--BAAI--bge-m3` **本身就是 symlink**，A 实为「把这条 symlink 改指」；
- 仍要赌 HF hub 的 `refs/main → snapshots/<sha>` 布局被 ST 正确解析（本地模型没有 hub 的 commit sha）；
- ⇒ **A 的成功条件比 B 多一层不确定性**，B 无此层。

**⇒ R565 建议：B > A > C**（C=SSH 再拉 2.2GB，纯冗余；数据卷 96% / avail 18Gi 时刻更不该做）。

### 3.5 待拍板的最小变更面（候用户授权·本轮零执行）

```diff
  ~/Library/LaunchAgents/com.nautilus.compass-daemon.plist
  EnvironmentVariables:
+   ZMM_EMBEDDER_MODEL = /Users/chunxiao.wang/bge-embed/models/bge-m3
```

- 改动性质：**一行 env**（不碰共享插件代码、不碰 symlink、不删文件）
- 生效方式：`launchctl kickstart -k gui/$UID/com.nautilus.compass-daemon`（重启 daemon）
- 验证法：① 重启后 daemon.log 出现 `BGE loaded · ~3s`（不再是 `loading BGE model` 后挂死）② 故意停 8400 → MCP recall 仍秒回 ③ `launchctl print` 确认 env 已注入
- 回滚：`launchctl unsetenv`/删该行 + 再 kickstart（原状：fallback 回到 NAS symlink 阻塞）
- 风险：**低**（env 只影响 fallback 分支；proxy 正常时 8400 路径不变）

---

## 四、附带发现：第三条 NAS symlink（框外·v5 侧 MLX）

`~/.cache/hf-local/hub/models--mlx-community--Qwen3.5-9B-4bit` → 同样是 NAS symlink。
⇒ v5 框若走 MLX 量化模型加载，会命中同一个坏子树。**属 v5 责任域，本轮只报不动**，建议与 NAS 侧根因排查一并处理。

---

## 五、NAS 侧根因仍未定位（框外·延续 R563/R564）

坏子树读阻塞（readdir EINTR + open 超时）三轮同型；服务端数据完好（R563 实测 SSH 直连秒回）⇒ 故障在 **NFS/SMB 协议路径**，属 `INFRA_BASELINE` 责任域。
**本轮补充一条对排查有用的事实**：该路径**只读不写**，即 NAS 上是「完好但读不动」，不是「写坏」——排查方向应指向**挂载参数/NFS 客户端重连/属性缓存与 mmap 交互**，而非数据修复。

---

## 六、教训（本轮新增）

1. **「换顶层 symlink」≠「本地化」**：R563 把 `~/.cache/huggingface` 指向本地目录就宣布修好，但**下一层**还有指向 NAS 的条目。修 symlink 类问题必须**逐层枚举条目**（`islink` + `readlink` + `realpath`），不能只看顶层。
2. **`stat` 秒回是属性缓存的谎言**：本轮实测 `stat` 0.00s 而 `readdir` 5.67s EINTR、`open` >10s 超时。**判「路径是否可用」必须 readdir/open，不能 stat。**
3. **修法要按「是否需要改共享代码」重新排序**：B（一行 env、零代码）比 A（要赌 HF 布局）更优，且**顺带解掉了一个跨轮继承的授权顾虑**——候拍板项的阻塞点有时藏在「谁有权改」而非「技术难度」。
4. **端到端实测优先于结构核对**：本轮用 daemon 同一 venv 实加载（2.9s / dim=1024）才敢称修法 B 可执行；只列目录结构不足以断言 ST 能加载。

---

## 七、本轮值守面（全部现场实测·零新增外部事件）

| 面 | 读数 |
|---|---|
| 信箱 compass | **0** 未读 |
| RED `check --to platform` | **220 封**（R564 记 219 → **+1**：唯一新函 id101974 soul-distress ×86·收件方 soul→platform·**非 compass·零行动**） |
| Gmail | 401 → 直刷 REFRESH_OK 3599s → 全量口径 7d **51 封**（R564 记 53 · -2 出窗）/ 未读 **30**（-2）/ 草稿 **35** 封零新 / 最大 internalDate **11-18 02:09Z（IFTTT 营销）·早于 R564·零新商务函零新面孔** |
| mentions | 5 条全旧（最新 11-02） |
| notifications | 45 条全旧（最新 11-13） |
| genesis | 5 家（1/1/0/1/2）零 REPLY |
| dev.to | 30 文 · 有评论 2 篇（6+2）全旧 |
| CI | compass **44243758143**（= R564 head 04abf91f）success；core 43558665734 success |
| 本地 HEAD | = origin/main = 04abf91f，零领先 |
| daemon / watchdog / 哨兵 | 9876 ok / exit0 / exit0 **recall_hit=28** |
| recall 端到端 | **MCP recall 实打可用**（返回 3 hits + recall_token） |
| GATE0 | **PASS** |
| 快筛 | CS-513 过；CS-512/514/515/516/517/518 不过 = 历轮全同 |
| 管道三件 | exit0（collect_for_quickscreen / pipeline_report / pipeline_state_sync） |
| 矩阵 | mtime 仍停 10-30 09:42 |
| S0 池 | 两仓 `codesense-s0-pool` 分支仍无远端引用（404 退役态） |
| 记忆库 | **1425 张**（session_auto 883 + distill 310 + session_非auto 6 + 其余主题/归档）· 24h 内新改 18 张 |
| 磁盘 | 数据卷 97% avail 13Gi（**较 R564 的 18Gi -5Gi·逼近 10Gi alarm 线·仍零清理候用户**） |
| 本轮生产改动 | **零**（未改 plist / 未改插件 daemon.py / 未改 symlink / 未删记忆卡 / 未碰他线 5 个未提交文件·保持 M / 未代推他线提交 / 未裹挟他线 untracked 新件） |
