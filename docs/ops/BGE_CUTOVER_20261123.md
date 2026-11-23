# BGE 切换 Mac mini + 检索池治理 · 变更记录(2026-11-23)

> 用户令:"批准,按顺序推进三件"(①BGE 切 Mac+关云 BGE ②蒸馏管线复活+接 9B ③C 项目检索池治理)。
> 本卡只记实测事实与遗留,不做未验证声明。

## 一、BGE 切换(完成,全链实测)

**架构**:云=门面+鉴权(v14 8770 / MCP 8097 → daemon 9876),嵌入推理=Mac mini(bge-m3,MPS,8400),链路=Mac→云反向 SSH 隧道(19988→8400),云 CPU BGE 降为惰性兜底(Mac 不可达时自动加载,恢复后 gc+malloc_trim 回收)。

**实测**:
- 向量兼容对拍:同文本 Mac MPS vs 云 CPU(镜像参数 512 截断)cosine=1.0(6 位小数)。
- daemon_v33 改造:`COMPASS_EMBED_PROXY` 配置时不再预载本地 BGE(`get_embedder` 加 `_ProxyFirstEmbedder` 代理优先分支);失败惰性加载本地;恢复后卸载。生产 sha `e9bba393…cebfd`。
- 稳态 RSS:2.3GB(本地常驻)→ 3.4MB(重启后实测)。
- 故障演练×3(拔隧道):Connection refused → "PROXY down → loading local BGE fallback"(13-22s 冷加载)→ 召回自愈(NACRE 查询 0.43s 3 命中)→ 隧道恢复 → "PROXY recovered → local BGE unloaded" → gc+malloc_trim 后 RSS 回收至 886MB(不加 trim 时残留 1.5GB)。
- 首笔查询超时说明:Mac 故障时第一笔召回可能撞 v14 层 15s 超时(本地冷加载 13-22s > 15s),第二笔起自愈——"三套超时互不知晓"的已知实例,治本方案在路线图 2.2/六-2。
- 入库:云 clone 提交 `b2c28456`(daemon_v33.py 首次入仓);本地仓 `bd138efd` 推送(GitHub)。生产哈希=仓内哈希 `e9bba393…`。

## 二、蒸馏管线复活 + 9B(完成,实测)

- 停摆根因:launchd 注册被移除(11/18 后);脚本本身完好——9B 接线早已内建(`llama-server` Qwen3.5-9B-Q4_K_M GGUF,端口 8765,自启自停)。
- 复活动作:`launchctl bootstrap` 重新注册(每 2h StartInterval)+ kickstart。
- 实测完整周期:`[incr] 1a7f257f review`——extract → 9B 压缩(13.3s)→ J1 锚点门 0.9(<0.95)→ 落复核队列,未自动入库(发布器强制复核回执+sha 读回绑定,门控按设计工作)。
- 注意:Mac 上现有两个 9B 服务并存(MLX 11435=本地价值环用;GGUF 8765=蒸馏自管)。合并是后续优化,未做。

## 三、C 项目检索池治理(机制完成,向量补齐收敛中)

- **归档层**:46,842 张 >30 天 session 卡移入 `memory/_archive/YYYY-MM/`(可逆 mv+manifest 46,841 行;首跑脚本 bug 1 张已移动未入 manifest:session_20260724-1036_cycle-14409-auto.md)。池根保留 8,965 张近 30 天卡+4 张手写卡(永不归档)。每周日 04:00 cron 自动归档(`ops/archive_old_session_cards.py --apply`)。
- **fill 顺序根修**:旧序=文件名序=最旧在前,300s 预算窗口永远嵌最旧的卡;改为 mtime 降序(最新优先),`_fill_order()`。
- **陈旧缓存键清理**:fill 时删除已移动/删除文件的缓存键(含 |chunks),`_pruned_n` 驱动 flush。实测 prune 7,882 键,pkl 598MB→546KB。
- **磁盘急救**:缓存目录 95 个 .tmp 尸体(10/9-11/23,合计 ~15GB)+ daemon.log 4.4GB 清除,磁盘 96%→84%。
- **隧道 wedged 修复**:Mac 本地嵌 0.02s、经隧道 2.7-10.6s → kickstart 隧道后 0.64-1.39s。
- **收敛期现状(如实)**:池内 8,970 张卡需重嵌(旧 pkl 向量属已归档老卡,已清),~0.8s/编码 → 数小时自然收敛;收敛完成前 C 项目召回在 fill 进行期可能撞 v14 15s 超时(fill 与请求互锁),收敛后 fill 秒级、召回恢复。fill 预算=每请求 300s,newest-first 保证最热卡先有向量。

## 遗留(候办)

1. 嵌入批量打捆(fill 逐条单呼→批量 POST),消除隧道 RTT 开销——v3.5.0 候。已挂临时 fill 加速器 cron(每 7 分钟触发一次填充,标注 `TEMP-FILL-ACCELERATOR-convergence-20261123`,池补齐后应移除)。
2. 隧道走 Tailscale 直连路径评估(当前 SSH over 公网)。
3. 故障期首笔超时:daemon 侧后台预热兜底模型或 v14 层部分结果语义(路线图六-2)。
4. Mac 双 9B 服务合并(11435 MLX / 8765 GGUF)。
5. daemon 日志轮转(daemon.log 无上限增长,今日 4.4GB)。
6. 云 clone 与 GitHub 的同步策略(本卡仅通过本地仓推送归档;云 clone 本地提交 b2c28456 未推)。

—— compass 审计席 · 2026-11-23 · 全部数字为当日实测
