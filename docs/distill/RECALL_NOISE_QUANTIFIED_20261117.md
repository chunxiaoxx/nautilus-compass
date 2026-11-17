# 🔴 distill 回填的**召回侧**污染实测（R560 · 2026-11-17）

> 承接：`DISTILL_FREEZE_DISPROVEN_20261117.md`（R559 证伪卡，证「选择面未收口」）+
> `DISTILL_BACKFILL_STILL_LIVE_20261117.md`（R558）+ `DISTILL_LIVE_BACKFILL_RISK_20261116.md`（R557）。
> 前三轮证的是**写入侧**（旧会话仍在灌入正式库）。**本卡第一次量化「污染已经造成的召回损害」**——
> 即污染不再是「将来会发生的风险」，而是**此刻正在发生的召回质量损失**。
>
> 结论标签：全部读数 **[实测]**（现场实物 + daemon 实时查询 + 逐封实拉）；因果判定标 [推断] 处已注明。
> **本轮零生产动作**：未 bootout launchd、未改 plist、未改 recall.py/daemon.py、未删/未移任何记忆卡、
> 未碰他线 4 个未提交文件。

---

## 一、一句话结论

**记忆库里 84% 是噪声卡；它们已经挤进召回窗口，把真正的主题卡挤出候选位。**
R559 说「余量 ≈1688 张 ≈141 天」是**未来**账；R560 补上**当下**账：**MCP recall 实际服务的 daemon 路径**，
30 个候选位里平均 **76.2% 被噪声占走**；最差的一条查询里 **29/30 位是噪声，首张主题卡被压到第 22 位**。

---

## 二、库内构成 [实测]

`~/.claude/projects/-Users-chunxiao-wang-Projects-nautilus-compass/memory/`（1415 个 .md，不含 MEMORY.md）：

| 类别 | 张数 | 占比 | 特征 |
|---|---|---|---|
| `session_auto_*` | 883 | 62.4% | frontmatter `distilled: auto`；mtime 全落 2026-10-18~10-23；**无 `drift:` 字段** |
| `distill-*` | 305 | 21.6% | frontmatter `origin: distill-pilot`；**99.7%（304/305）description 是模板句**「蒸馏纪要 <id> 蒸馏纪要 · <uuid>」 |
| 主题卡（curated） | 227 | 16.0% | 人工/agent 撰写的主题档案 |
| `MEMORY_archived_*` | 1 | 0.1% | 60 天以上归档索引 |

- **噪声合计 1188/1415 = 84.0%**。
- distill 卡里 **244/305** 带 `semantic_status: unreviewed_j1_only`，其余 61 张是 11-05 旧格式（无该字段）——
  ⇒ **305 张全部未经语义复核**进正式库。

## 三、两条召回路径，闸门覆盖不一样 [实测]

| 路径 | 代码位置 | 是否拦 `session_auto_*` | 是否拦 `distill-*` | 索引里噪声占比 |
|---|---|---|---|---|
| **hook 路径**（会话启动注入） | `recall.py:1447` 闸：`if f.name.startswith("session_") and drift_val != "red": continue` | ✅ 拦（全部无 `drift:` → drop） | ❌ **不拦**（文件名不以 `session_` 开头，闸根本不看它） | **62.0%**（492 条索引中 305 张 distill-* + 187 主题卡） |
| **daemon 路径**（MCP recall 实际服务，本轮所有 recall 调用都走这条） | `~/.claude/plugins/nautilus-compass/daemon.py:1044-1049` `get_memory_entries`：只 skip `MEMORY.MD`/`INDEX.MD`，**无任何前缀闸** | ❌ 不拦 | ❌ 不拦 | **84.0%**（全库 1415 张进索引） |

复刻 `recall.py` 闸实算：921 张被 `session_` 闸 drop（其中 883 张 `session_auto_*` + 38 张 `session_*`），
2 张被 30 天 `archived_at` 衰减 drop，**剩 492 条 = hook 自报 `entries 492`**（与实际注入输出一致）。
⇒ 主题卡只剩 **187 张**与 305 张 distill 卡竞争同一召回窗口。

## 四、召回损害量化 [实测 · daemon 实时查询]

token 鉴权直连 `127.0.0.1:9876`，8 条覆盖本框日常议题的查询 × top30 = 240 个候选位：

```
磁盘 空间 清理 ENOSPC 告警 阈值        curated  5  distill 25  sess  0   噪声 83%
对外发送 硬闸 审稿 草稿 不外发          curated  2  distill  2  sess 26   噪声 93%
阿里 30 题 产线 快筛 判据 矩阵 跑批      curated 12  distill  6  sess 12   噪声 60%
Gmail 未读 差集 口径 遮蔽               curated  9  distill  2  sess 19   噪声 70%
distill 回填 旧会话 正式记忆库 污染      curated  1  distill 25  sess  4   噪声 97%
平台信箱 OGE 状态 回函 SLA 逾期          curated  5  distill  0  sess 25   噪声 83%
值守轮 渠道 巡检 留痕 纪律              curated 10  distill 17  sess  3   噪声 67%
矩阵 phase2 解锁 出题 产线              curated 13  distill  2  sess 15   噪声 57%
──────────────────────────────────────────────────────────────
合计                                    curated 57  distill 79  sess 104  噪声 76.2%
```

**最尖锐的一条**（`distill 回填 旧会话 正式记忆库 污染`）：
top30 里 **29 张是噪声、只有 1 张主题卡**（`distill-live-uncommitted-code-20261116.md`），
**该主题卡被压到第 22 位**——即「问 distill 问题、拿到的前 21 条全是 distill 噪声卡」。
**这正是本轮最该被用户看见的一条**：污染最强的领域，恰恰是污染产物最能占据召回位的地方。

**机制 [推断 · 每一步都实测过]**：305 张 distill 卡 description 99.7% 是同一模板句
（「蒸馏纪要 <id> 蒸馏纪要 · <uuid>」），embedding 近似同向量 ⇒ 对任意查询都稳定给出 **0.546~0.599** 的相似度；
主题卡的匹配分跨度更大（实测 **0.542~0.709**）。**两条中低分段（0.54~0.60）完全重叠**：
最相关的主题卡确实排在最前（多数查询首个 curated 在第 1~3 位），但**中低分段是噪声的独占区**——
候选窗口只有 30 位，1188 张噪声以数量优势吃掉中后段，
**主题卡只要掉出这 30 位窗口就等于不存在**（`distill` 那条查询：唯一主题卡掉到第 22 位）。

## 五、修补方案（三选一 · 全部可逆 · 本轮均未执行）

### 方案 A：只堵召回侧（不动写入侧）— 推荐
在**两条**路径同时加同一条前缀/状态闸：
- `recall.py`：把 `startswith("session_")` 扩为 `startswith(("session_", "distill-"))`，
  且对 `distill-*` 额外要求 `semantic_status` 非 `unreviewed_j1_only` 才放行；
- `daemon.py:get_memory_entries`：加同款过滤（该文件属**共享插件**，改动影响面大于 `recall.py`，需谨慎）。

预期效果（按本轮读数推算，[推断]）：daemon 索引 1415 → 532，噪声占比 84% → 0；
hook 索引 492 → 187（纯主题卡）。**代价**：305 张 distill 卡的信息从召回面消失（文件仍在，可回滚）。

### 方案 B：只堵写入侧（不改召回）
按 R559 卡给的三选项执行：①仅 `launchctl bootout gui/$(id -u)/com.nautilus.distill-incremental`；
②停 + 落账 + 修完再开；③保持停用。
**代价**：已入库的 1188 张噪声卡**留在库里**，且 daemon 路径的 84% 噪声**不会改善**——
停写只止血，不治已发生的召回损害。

### 方案 C：A + B 同时做
先把 daemon 索引降到 532，再停写入 ⇒ 召回面干净且不再新增。
**代价**：一次性抹掉 305 张 distill 卡的召回可达性（需用户确认「这 305 张是否本应进正式库」——
R559 卡已列此未决前提）。

### 补丁（未应用 · 供审阅）
`recall.py:1447` 一行改法：
```python
# 现状：只拦 session_ 前缀 ⇒ distill-* 全量绕过
if f.name.startswith("session_") and drift_val != "red":
    n_dropped_noise += 1
    continue
# 建议（方案 A）：
if (f.name.startswith("session_") and drift_val != "red") or \
   (f.name.startswith("distill-") and drift_val != "red"):
    n_dropped_noise += 1
    continue
```
（`distill-*` 卡目前 **0 张**带 `drift:` 字段 ⇒ 该闸一加即全 drop，**等价于「只保留主题卡」**，
需与用户确认这 305 张的去留后再决定灰度方式。）

## 六、候用户拍板（与 R559 的三选项合并为四项）

1. **distill 写入侧**：R559 的三选项（①仅停 launchd ②停+落账+修完再开 ③保持停用）。
2. **distill 召回侧**：本卡方案 A/B/C（是否把 distill 卡移出召回索引）。
3. **未决前提（沿用 R559）**：~2000 个旧会话是否本应进正式记忆库？—— 这条不定，A/C 都只是权宜。
4. **共享插件边界**：`daemon.py` 属 `nautilus-compass` 共享插件，改它影响所有框 ⇒ 是否授权 compass 改。

## 七、复算方法（本卡全部读数的取数方式）

```bash
# 库内构成
ls ~/.claude/projects/-Users-chunxiao-wang-Projects-nautilus-compass/memory/*.md | wc -l   # 1416 含 MEMORY.md
# 召回损害：token 鉴权直连 daemon（9876）
python3 - <<'PY'
import socket,json,os,pathlib
tok=pathlib.Path.home().joinpath(".claude/.cache/compass_daemon_token").read_text().strip()
s=socket.socket(); s.settimeout(30); s.connect(("127.0.0.1",9876))
s.sendall((json.dumps({"action":"recall","query":"distill 回填 旧会话 正式记忆库 污染",
  "project":"-Users-chunxiao-wang-Projects-nautilus-compass","top_k":30,"token":tok})+"\n").encode())
buf=b""
while b"\n" not in buf:
    c=s.recv(65536)
    if not c: break
    buf+=c
recs=json.loads(buf.split(b"\n",1)[0]).get("recall") or []
print("noise/curated:",
  sum(1 for r in recs if os.path.basename(r["path"]).startswith(("distill-","session_auto"))),
  "/", sum(1 for r in recs if not os.path.basename(r["path"]).startswith(("distill-","session_auto"))))
PY
# 两条路径的闸门代码坐标
grep -n 'startswith("session_")' recall.py                      # :1447
grep -n 'mem_dir.glob("\*.md")' ~/.claude/plugins/nautilus-compass/daemon.py   # :1044
```

**证据坐标**：daemon 实时查询（本卡第四节全部读数）· `recall.py:1447` ·
`~/.claude/plugins/nautilus-compass/daemon.py:1030-1049` ·
`~/.claude/projects/-Users-chunxiao-wang-Projects-nautilus-compass/memory/`（ls + 逐卡 frontmatter 实读）·
`runtime/scratch_distill_pilot_20261104/incremental_stats.jsonl`（352 行：published 271 / review 78 / failed 1）。
