# 🔴 distill 污染 · 方案 A 离线预演 + 库内噪声口径修正（R561 · 2026-11-17）

> 承接：`RECALL_NOISE_QUANTIFIED_20261117.md`（R560 首次量化召回侧损害）·
> `DISTILL_FREEZE_DISPROVEN_20261117.md`（R559 证伪卡）·
> `DISTILL_BACKFILL_STILL_LIVE_20261117.md`（R558）· `DISTILL_LIVE_BACKFILL_RISK_20261116.md`（R557）。
>
> **R561 的定位**：R560 把损害**量化**了，但没有回答用户拍板时要问的那句话——
> **「改成方案 A 之后，召回窗口会变成什么样？」** 本轮给这张**离线预演表**（零生产改动、零生产动作），
> 并修正 R560 的**库内噪声占比口径**。
>
> 结论标签：读数 **[实测]**（现场实物 + daemon 实时查询 + 本地复刻实算）；因果判定标 [推断] 处已注明。
> **本轮零生产动作**：未 bootout launchd、未改 plist、未改 `recall.py`/`daemon.py`、未删/未移任何记忆卡、
> 未碰他线 4 个未提交文件（`extract_sample.py`/`publish_to_memory.py`/`p3_delta.py`/`fuel_intake.py` 保持 ` M`）、
> 未代推他线提交、未提交他线 untracked 新件（`export_fuel_candidates.py` + 3 新测试）。

---

## 一、一句话结论

**方案 A（两条召回路径同加前缀闸）的收益是结构性的、确定的，不需要实测估计**：
加闸后 **hook 索引 494→188 条、daemon 索引 1417→189 条，两个窗口的噪声都归零**，
而主题卡供给 **188 张 ≥ top30**，⇒ 加闸后每个 top30 窗口**必然全是主题卡**。

同时修正 R560 一处口径：库内噪声占比不是 84.0%，是 **86.7%**（R560 把 40 张 `session_*` 流水卡误计入"主题卡"）。

---

## 二、库内噪声占比：口径修正 [实测]

`~/.claude/projects/-Users-chunxiao-wang-Projects-nautilus-compass/memory/`（**1418** 个 .md，含 MEMORY.md）：

| 类别 | 张数 | 占比 | 说明 |
|---|---|---|---|
| `session_auto_*` | 883 | 62.3% | 会话流水蒸馏卡，frontmatter `distilled: auto`，**无 `drift:` 字段** |
| `distill-*` | 306 | 21.6% | 蒸馏纪要卡，304/306 description 是模板句，**全部未经语义复核** |
| `session_*`（非 auto） | 40 | 2.8% | **🔴 R560 口径错在此处**：被算进了"主题卡"，实为会话流水卡 |
| 纯主题卡 | 187 | 13.2% | 人工/agent 撰写的主题档案 |
| `MEMORY_archived_*` | 1 | 0.1% | 60 天以上归档索引 |
| `MEMORY.md` | 1 | — | 索引本体 |

- **噪声合计 1229/1418 = 86.7%**（R560 口径 1188/1416 = 84.0% ⇒ **低估 2.7pp**）。
- 40 张 `session_*` 中 **38 张无 `drift:` 字段**、2 张被 30 天归档衰减 drop；仅 **2 张 `drift:red`** 曾进过 hook 索引。

---

## 三、两条召回路径的**精确账**（离线复刻 · 零生产改动）[实测]

复刻 `recall.py:1443-1455` 的两条闸（`session_` 前缀闸 + 30d 归档衰减闸）实算：

| 路径 | 现状索引 | 现状噪声 | 方案 A 加闸后索引 | 加闸后噪声 | 主题卡供给 |
|---|---|---|---|---|---|
| **hook 路径**（会话启动注入 `recall.py`） | **494** 条（主题 188 + distill 306） | **61.9%** | **188** 条 | **0%** | 188 ≥ 30 ✅ |
| **daemon 路径**（MCP recall 实际服务 `daemon.py:1044-1049`） | **1417** 条 | **86.7%**（1229/1417） | **189** 条（含归档 1） | **0%** | 189 ≥ 30 ✅ |

**自洽校验**：R560 记 hook 索引 492（当时库 1416），本轮库 +2（distill +1、主题 +1）⇒ 494，**与复刻值完全对上**，
说明复刻方法与 R560 同源可信。

**为什么"噪声归零"是结构性结论而非估计**：daemon 的 top30 是从索引里取相似度最高的 30 条；
加闸后索引里**只剩主题卡**，主题卡 188 张 > 30 ⇒ 任何查询的 top30 **必然全为主题卡**，不存在"补不满"的情形。

### 方案 A 的三条副作用（诚实列出）[推断]

1. **hook 路径的"会话流水"能力归零**：hook 索引里本来就只剩 306 张 distill 卡被当作噪声，
   但 `session_auto_*` 883 张是被 hook 闸主动 drop 的（设计如此）。方案 A **不改变**这一现状，只把 distill 也 drop 掉。
2. **daemon 路径将从 1417 条索引掉到 189 条**：检索召回面**显著收窄**，冷门查询可能返回低分主题卡（仍是主题卡，不会漏主题）。
3. **存量 1229 张噪声卡仍留在库里**（方案 A 只挡召回，不清库）⇒ 库内 86.7% 的噪声占比**不因方案 A 而改善**，
   只有方案 B/C（清存量 + 停写入）才动这个数。

---

## 四、召回损害复算：R561 对拍 R560（两小时后）[实测 · daemon 实时查询]

同一批 8 条日常查询 × top30 = 240 候选位，token 直连 `127.0.0.1:9876`：

| 查询 | R560 噪声 | R561 噪声 | 首张主题卡位次 |
|---|---|---|---|
| 磁盘 空间 清理 ENOSPC 告警 阈值 | 83% | 83% | 1 |
| 对外发送 硬闸 审稿 草稿 不外发 | 93% | 93% | 1 |
| 阿里 30 题 产线 快筛 判据 矩阵 跑批 | 60% | 60% | 1 |
| Gmail 未读 差集 口径 遮蔽 | 70% | 70% | 1 |
| **distill 回填 旧会话 正式记忆库 污染** | **97%**（唯一主题卡@第 22 位） | **93%** | **1** |
| 平台信箱 OGE 状态 回函 SLA 逾期 | 83% | 83% | 1 |
| 值守轮 渠道 巡检 留痕 纪律 | 67% | 66% | 1 |
| 矩阵 phase2 解锁 出题 产线 | 57% | 56% | 1 |
| **合计** | **183/240 = 76.2%** | **182/240 = 75.8%** | — |

**读法（这才是本轮真正的决策信息）**：
- R560 的量化卡 `recall-noise-76pct-distill-pollution-20261117.md` 本身进了库，成为一张主题卡，
  把「distill 回填」那条查询的唯一主题卡**从第 22 位顶到第 1 位**，总噪声从 183 → 182（**−1 位 = −0.4pp**）。
- ⇒ **「靠多写主题卡去对冲污染」这条自助路径的速率是 1 位/轮（0.4pp/轮）**；
  而同期 distill 每 2 小时继续灌 1 张噪声卡（见第五节）。
  **两条路速率对不上 ⇒ 自助路径杯水车薪，真正的解法只能是闸门（方案 A/B/C）。**

---

## 五、🔴 distill 续写第 7 张（证伪后仍灌 · 结论继续成立）[实测]

`runtime/scratch_distill_pilot_20261104/incremental_stats.jsonl`：

- **353 行**（R560 为 352，+1）：`published` **272**（R560 为 271，+1）/ `review` 78（持平）/ `failed` 1（持平）。
- 最新已发布卡 **`distill-bed43658-74f7-48d4-ab80-ad0bd29c7b1a`**（源会话 mtime **2026-10-19 23:35:32 = 28.8 天前**）。
- **published 中源会话 >7d 占比 = 272/272 = 100.0%**（272 张全部可定位，最老 8.2d、最新 28.8d）。
- 库卡 1416 → **1418**（+1 distill +1 主题卡）。

⇒ R559「freeze 被证伪」结论**继续成立**；R560 的三方案仍是唯一出路。

---

## 六、候用户拍板（本轮把选项从"描述"变成"带数字的表"）[实测]

| 方案 | 改动面 | 召回窗口噪声 | 库内噪声占比 | 未决前提 |
|---|---|---|---|---|
| **A 只堵召回** | `recall.py` + `daemon.py` 各加一条前缀/状态闸（**`daemon.py` 属 nautilus-compass 共享插件 ⇒ 影响所有框**） | 494→188 / 1417→189 条，**噪声 0%** | **86.7% 不变**（存量仍留库） | 是否授权 compass 改共享插件 |
| **B 只堵写入** | bootout `com.nautilus.distill-incremental` + 落账工作区 4 文件 | 不变（噪声卡仍进窗口） | 停灌后不再增 | ~2000 旧会话是否本应进正式库 |
| **C 同时** | A + B + 清 1229 张存量 | **0%** | 降到 13.3% | 同上 + 清库是否获授权（不可逆） |

**本轮给出的新增决策信息**：①A 的收益是**确定的 0% 噪声**，不是估计；②A **不清库**，86.7% 这个数不动；
③"多写主题卡"的自助路径速率 **0.4pp/轮**，对不上污染增速 ⇒ 不能当作替代方案。

**本轮零生产动作**：未 bootout、未改 plist、未改 `recall.py`/`daemon.py`、未删未移任何记忆卡。

---

## 七、复算方法（本卡全部读数的取数方式）

```bash
# 库内构成（口径修正后的四分类）
python3 - <<'PY'
import pathlib, collections
mem = pathlib.Path.home()/".claude/projects/-Users-chunxiao-wang-Projects-nautilus-compass/memory"
g = collections.Counter()
for f in sorted(mem.glob("*.md")):
    n = f.name
    if n == "MEMORY.md": g["MEMORY.md"] += 1
    elif n.startswith("distill-"): g["distill"] += 1
    elif n.startswith("session_auto"): g["session_auto"] += 1
    elif n.startswith("session_"): g["session_other"] += 1   # 🔴 R560 漏了这一类
    elif n.startswith("MEMORY_archived"): g["archived"] += 1
    else: g["theme"] += 1
print(g, "噪声=%.1f%%" % (100*(g["distill"]+g["session_auto"]+g["session_other"])/sum(g.values())))
PY

# hook 闸门复刻（方案 A 收益表）
#   闸① recall.py:1447  f.name.startswith("session_") and drift != "red"  → drop
#   闸② recall.py:1452  age_days > 30 and not want_archived and startswith("session_") → drop
#   实算：索引 494 条（主题 188 + distill 306）→ 加 distill 闸后 188 条，噪声 0%

# daemon 实时查询（召回损害复算）
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

# distill 续写计数
wc -l runtime/scratch_distill_pilot_20261104/incremental_stats.jsonl   # 353 行
```

**证据坐标**：daemon 实时查询（本卡第四节全部读数）· `recall.py:1443-1455`（两条闸门原文）·
`~/.claude/plugins/nautilus-compass/daemon.py:1044-1049`（`get_memory_entries` 无前缀闸）·
`~/.claude/projects/-Users-chunxiao-wang-Projects-nautilus-compass/memory/`（ls + 逐卡 frontmatter 实读）·
`runtime/scratch_distill_pilot_20261104/incremental_stats.jsonl`（353 行：published 272 / review 78 / failed 1）
· 库内 1418 张卡逐张 mtime/前缀统计（脚本实跑，非目测）。
