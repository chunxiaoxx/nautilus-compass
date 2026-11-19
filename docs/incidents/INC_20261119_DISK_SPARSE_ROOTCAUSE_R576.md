# INC_20261119 · 磁盘根因归属修正(OrbStack 映像为稀疏文件,460.4GiB 表面尺寸 ≠ 实际占用)· R576

- **轮次**:loop R576(2026-11-19 13:45–14:10)
- **触发**:R575 收尾 alarm「avail 7.9Gi/99% 满 · 距 ENOSPC 约 1.8h」,根因沿用 11-10 lsof 基线「OrbStack 容器 VM 映像疯写(data.img.raw = 460.4GB)」,但 R575 明确「本轮未复测,不下新根因结论」。
- **本轮目标**:复测该基线,并区分「文件表面尺寸(apparent)」与「实际分配块(allocated)」。

## 结论

🔴 **旧根因表述不成立(需修正)**:R533/R573/R575 沿用的「根因=VM 映像 460.4GB」是**按 `ls -l` 的表面尺寸(apparent size)**得出的,对**稀疏文件**会严重高估。

| 口径 | 数值 | 测法 |
|---|---|---|
| `data.img.raw` 表面尺寸 | **460.4 GiB** (494,333,346,304 B) | `stat -f %z` |
| `data.img.raw` **实际分配** | **103.88 GB** (25,361,840 × 4096) | `stat -f %b` × `blksize` |
| Data 卷 used | 420,072 MB | `df -m` |
| ⇒ OrbStack 映像占 used 比例 | **≈ 25%** | 103.88 / 420.07 |
| ⇒ **未定位的其余占用** | **≈ 316 GB** | 差值 |

60s 采样窗内映像增长 = 96 blocks = 393,216 B ⇒ **≈ 23.6 MB/h**(非 R575 估的 3.9 GB/h)。

## 速率证伪

R575 记「avail 8.6Gi → 7.0Gi(25min)≈3.9GB/h ⇒ 距 ENOSPC 约 1.8h」。本轮实测 5 个采样点:

| 时刻 | avail |
|---|---|
| 13:45:00 | 6,124 MB |
| 13:45:5x | 6,135 MB |
| 13:46:2x | 6,149 MB |
| 13:52 | 6,137 MB |
| 13:58 | 6,144 MB |

⇒ **本轮窗口内 avail 基本持平(反而微升)**;R575 的 −3.9GB/h **未在本轮持续**。跨轮对比 11:50(7.0Gi)→ 13:45(6.0Gi)约 −1.0Gi/115min(≈0.53GB/h),**比 R575 估的 3.9GB/h 慢 7 倍**。

🔴 **方法论落账**:单轮两点差分不足以给速率结论(且可能跨越一次已完成的清理/回收)。后续轮次须**多点采样 ≥3 次跨 ≥10min** 才可对外报 ENOSPC 倒计时。

## 本轮定位到的实际占用(可读部分)

- `~/Library/Caches` 9.8 GB(其中 `com.openai.codex` 4.0 GB、`com.alibaba.DingTalkMac` 2.3 GB、`Google` 1.3 GB、`dev.kdrag0n.MacVirt` 0.7 GB、`ms-playwright` 0.6 GB)
- `~/.cache` 6.2 GB(注意 `~/.cache/huggingface` 是指向 NAS 的 symlink,R563 记;符号链接本身不占本地块)
- `~/Library/Application Support` 2.7 GB(`Google` 0.87 GB、`DingTalkMac` 0.69 GB、`com.apple.wallpaper` 0.46 GB、`Codex` 0.40 GB)
- `/Users/chunxiao.wang/Library/Group Containers/HUAQ24HBR6.dev.orbstack/data/data.img.raw` = OrbStack VM 映像(TCC 保护目录,`du` 不可读 ⇒ **只能用 `lsof` 定位路径 + `stat -f %b` 量分配块**)

## 未解边界(诚实留档)

- `du` 对 TCC 保护目录(Group Containers / Containers)不可读 ⇒ 剩余 ~316 GB 的**具体落点本轮未定位**。
- `/Applications`、`/Library`、`/private/var`、`/Users/Shared`、`/opt` 的 `du` 后台普查**本轮未在时限内返回**。
- APFS 快照:仅 1 个 `com.apple.TimeMachine.2026-11-19-132959.local`,标记 **dataless**(=不占本地数据块),故不解释差额。

## 本轮动作

**零清理**(零删除、零 kill、零 bootout),沿用 R533/R575 的「候用户拍板」纪律。候拍板项已更新:
1. 🔴 磁盘:可回收候选已定位到具体目录(Codex cache 4.0 GB / DingTalk 2.3 GB / Google 1.3 GB 等)—— 但清理动作须用户拍板(删除属不可逆)。
2. 🔴 剩余 ~316 GB 落点未定位 ⇒ 建议下一轮后台 `du` 分层 + `lsof` 全量扫大文件。
3. 🔴 **OrbStack 映像内的实际占用**(VM 内部文件系统)未测 ⇒ 需 `orb`/`docker` 侧工具读 VM 内部 `df`,非宿主机 `df`。
