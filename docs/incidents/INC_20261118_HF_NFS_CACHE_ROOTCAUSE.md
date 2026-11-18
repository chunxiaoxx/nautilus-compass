# INC-20261118 · 召回入口全停的真正根因：`~/.cache/huggingface` 落在坏掉的 NAS 挂载上

> 事件窗：2026-11-17 21:30 ~ 22:20（本地 EST）· 发生于 R562 重启 daemon 之后
> 状态：**已修复并端到端验证**（recall 恢复 3.3~4.1s 稳态）
> 前序：R562 报「daemon 过载 livelock 复发·已恢复传输层·查询路径仍挂·阻塞点不可验（py-spy 未装）」
> —— 本轮把那个"不可验"的阻塞点定位到**文件系统层**，并给出可复算的证据链。

## 一、症状与分层定位（R563 实测）

| 层 | 观测 | 判读 |
|---|---|---|
| 传输层 | daemon `ping` 秒回；`status` 0.20s；`drift` 0.04s 且能出 compass 项目评分 | accept/handler 池**健康**·不是 R562 猜的"池占满" |
| 查询层 | `recall` 直连 daemon（带 token）**120s 超时**；MCP recall 同样超时 | 挂点**在 recall 专属路径** |
| 进程层 | `sample` 8 个 worker 线程 **100% 采样命中**卡在 `_io_open → __open` | 阻塞在 **open() 系统调用**·非网络/非锁 |
| 文件系统层 | `~/.cache/huggingface` 是**符号链接**→ `~/mnt/nas-work/model-cache/huggingface`（NAS） | 嫌疑锁定 |

## 二、根因链（逐环实测，无推断跳跃）

1. **NAS 挂载对该目录的读取永久阻塞**
   - `stat` 秒回（属性缓存）· `readdir` 中断 · **读具体文件 `refs/main` 卡死 >15s**
   - 三条访问路径**全部卡**：`~/mnt/nas-work/…`（NFS `192.168.5.25:/share/NFSv=4/work`）·
     `/Volumes/work-nfs/…`（NFS `192.168.5.25:/work`）· `/Volumes/work/…`（SMB）
   - **新建挂载点 `~/mnt/nas-work2`（按 CLAUDE.md 配方挂 `192.168.5.25:/work`）同样卡** → 不是挂载源写错、不是客户端状态坏
   - **SSH 直连 NAS 读同一文件秒回** → 服务端数据完好，**故障只在 NFS/SMB 协议路径**
2. **rerank 服务（8401）从未加载成功模型**
   - `rerank_server.py` 与 daemon 的 `_remote_rerank_contract()` 都硬编码读
     `~/.cache/huggingface/hub/models--BAAI--bge-reranker-v2-m3/refs/main` → 同样落 NAS → 卡
   - 实证：**PID 1874 常驻 3 天 15 小时，RSS 仅 14MB**（正常加载后 >400MB）= 从未成功加载
3. **daemon 的 recall 路径被同一个文件拖死**
   - `recall` 独有段：`_rerank_top → _remote_rerank_scores → _remote_rerank_contract() → read_text(refs/main)` → **永久阻塞**
   - 连带：RPC 30s deadline 到期后 fallback 本地 cross-encoder → 同样要读 HF 缓存 → **二次卡死**（无出路）
   - 8 个 worker 全部卡在同一 open → 新请求排队 → 32 in-flight 槽很快占满 → 拒绝连接
   - **这才是 R562「传输层已恢复、查询路径仍挂」的机制解释**
4. **旁证**：`drift` 不走 rerank（只用 anchors）→ 秒回；`status/ping` 不读文件 → 秒回。三者时序完全自洽。

## 三、修复（已执行并验证）

| 步 | 动作 | 可回滚性 |
|---|---|---|
| 1 | SSH 从 NAS 拉 `models--BAAI--bge-reranker-v2-m3` 到本地 `~/.cache/hf-local/hub/…`（2.27GB `model.safetensors` 逐字节核对一致；tar 仅报 macOS xattr 元数据还原告警，数据无损） | 纯新增，不动 NAS |
| 2 | 本地 hub 镜像：其余模型（`models--BAAI--bge-m3`、`models--mlx-community--Qwen3.5-9B-4bit`）**保留指向原 NAS 路径**（维持现状语义，不引入新问题） | 删两个 symlink 即回 |
| 3 | `~/.cache/huggingface` symlink 由 NAS 路径改指 `~/.cache/hf-local`（用 `ln -sfn`；**注意 `mv -f` 对 symlink-to-dir 会把源移进目标目录**，本轮踩过一次） | 改回 `/Users/chunxiao.wang/mnt/nas-work/model-cache/huggingface` 即回 |
| 4 | `launchctl kickstart -k gui/uid/com.nautilus.bge-rerank`（8401）→ 加载本地权重，`health` 0.01s 返回，`device=mps` | launchd KeepAlive 自动 |
| 5 | `launchctl kickstart -k gui/uid/com.nautilus.compass-daemon`（9876）→ 释放 8 个卡死 worker | 同上 |

**端到端验证（[实测]）**

```
recall（首次·含 rerank 预热）  14.00s  ok=True hits=5
   rerank: backend=remote_mps  fallback=false  rerank_ms=13581  revision=953dc6f6…  max_length=8192
recall（稳态）               3.28s / 4.06s  ok=True hits=3
   命中 daemon-overload-livelock-recurrence-20261117.md（0.697）
        recall-noise-76pct-distill-pollution-20261117.md（0.708）
```

## 四、影响面与遗留（候用户拍板，不在本轮自主范围）

1. **`models--BAAI--bge-m3` 仍在坏掉的 NFS 路径上** —— 8400 embed server 因已常驻内存而活着
   （`/embed` 实测 0.033s）；**一旦它重启，将同样卡死在加载阶段**。→ 建议下一轮把 bge-m3 也本地化
   （约 2.2GB，同法 SSH 拉取），否则这是一枚定时炸弹。
2. **NFS 读取为何卡**仍未定位到服务端/协议层根因（SSH 正常、NFS+SMB 同挂）。
   候选：服务端该目录的 readdir/read 处理卡死 / NAS 侧存储异常 / SMB↔NFS 共享同一底层目录互锁。
   → 建议用户侧查 NAS（QNAP）日志与存储池健康；这是**基建问题，超出 compass 框**（INFRA_BASELINE 责任域）。
3. `~/mnt/nas-work2` 是本轮新建的测试挂载点，**已无用途**，建议 unmount（未做，避免干扰其它进程）。

## 五、教训（可复用）

- **"传输层绿 ≠ 查询层绿"**：ping/status 秒回只证明 accept 与 handler 池活着；recall 独有段
  （rerank/契约校验）才是真正的可用性判据。**探活必须覆盖 recall 全路径**（本轮已把
  `mcp_watchdog.sh` 三态探活保留，并建议再加一条"recall 全路径"探针）。
- **`stat` 秒回会骗人**：NFS 属性缓存让 `stat`/`exists()` 立刻返回，**只有真读才暴露阻塞**。
  今后凡涉及挂载卷的健康检查，必须用「读一个已知小文件」而不是 `stat`。
- **硬编码 `Path.home()/".cache/huggingface"` 的组件有两个**（daemon + rerank_server），
  **共路径=共故障域**：一个 symlink 指向的挂载坏掉，两个服务同时失能且症状不同（一个挂死、一个永不加载）。
- **py-spy 仍缺**（R562 提的诊断前置）：本轮用 `sample` + 分层 action 探测代替，
  但 py-spy 仍是下次同类问题的最短路径（brew install py-spy 即可）。
