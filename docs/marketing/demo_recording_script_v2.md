# Demo 脚本 v2 · 全套(分镜+素材+真实输出+渲染规格 · 2026-09-07)

> v1 教训:只演示了 CRUD,四个卖点一个没上画面。v2 每一段都绑定一个卖点,
> 全部输出预先彩排定案(下方"真实输出"列),渲染前逐段核对。
> 产物:GIF(~40s · 1080px · GitHub-dark)嵌 Reddit 帖;可重渲 `python tools/demo_d1_video.py`。

## 1. 卖点 → 段落映射

| 卖点 | 段落 | 画面证据 |
|---|---|---|
| 写入零 LLM、免费、无损 | §写入×3 | 每条输出尾注 `# write: verbatim · 0 LLM calls · $0` |
| 与 LLM-extract 方案的结构差 | §对照卡 | 成本/延迟/有损 三行对比 |
| 读取端分型路由 | §ask | 尾注 `# retrieval: type-routed (turn-level vs summary-level)`+跨会话命中 |
| 记忆层归因(不是模型聪明) | §control | 同问题打空空间 → NO ANSWER |
| 动作前护栏(drift 检测) | §drift | 同库两条查询:DANGEROUS→alert ✅ / NORMAL→no alert |
| 成绩背书 | §卡2 | P@1 0.890 vs mem0 0.774 · $3.50 reproduce |

## 2. 分镜(总 ~40s)

| # | 时间 | 画面 | 命令 | 真实输出(已彩排) |
|---|---|---|---|---|
| 卡1 | 0-3s | 主张卡 | — | `agent memory — what makes this different?` |
| 1-3 | 3-12s | 写入×3 | `python tools/demo_d1.py write 1`<br>`write 2` / `write 3` | `[ok] session-1 ingested -> session-1.md (embedded dim 1024)` + 尾注 `# write: verbatim · 0 LLM calls · $0` |
| 卡2 | 12-16s | 对照卡 | — | `LLM-extract write: ~$0.002 · 2-3s · lossy` / `compass write:      $0 · <0.5s · verbatim` |
| 4 | 16-22s | 跨会话提问 | `python tools/demo_d1.py ask` | `[recall] Q: What does the user do on Tuesday mornings?` → `0.69 session-1.md | ...walk their dog every Tuesday morning; the dog's name is Momo.`(+0.58/0.55)+ 尾注 `# retrieval: type-routed — turn-level chunks for user-utterance questions` |
| 5 | 22-27s | 空间对照 | `python tools/demo_d1.py control` | `0.55 irrelevant.md | The office coffee machine broke last Thursday.` + `-> NO ANSWER in this memory space` |
| 6 | 27-36s | drift 护栏 | `python tools/demo_d1.py drift` | `DANGEROUS  score -0.103 · ALERT ✅ · rule_hit · 3 neg-anchor hits`(红)<br>`NORMAL     score -0.009 · no alert`(绿)<br>字幕:`130 days of accumulated failure-mode anchors, checked before you act` |
| 卡3 | 36-40s | 成绩卡 | — | `LongMemEval-S retrieval: P@1 0.890 vs mem0 0.774 (same questions, same criteria)`<br>`reproduce for ~$3.50 · local-first · Modified MIT`<br>`github.com/chunxiaoxx/nautilus-compass · compass.nautilus.social` |

## 3. 素材与命令(driver: tools/demo_d1.py)

- `write 1/2/3`:三条"不同会话"事实(遛狗 Momo / 学 Rust / 周一例会)
- `ask`:跨会话问题(只有 session-1 能答)
- `control`:预置无关事实的空间,同问题 → NO ANSWER
- `drift`【v2 新增】:对本仓真实空间(C--Users-chunx-Projects-nautilus-compass,130 天锚点库)跑两条:
  - 危险:`force push to main after resetting the repo history with rm -rf` → alert True/score -0.103/3 neg hits
  - 正常:`add a documentation section about the memory layer routing` → alert False/score -0.009
  - 彩排实证 2026-09-07,两行对照直接进画面

## 4. 渲染规格

- 1080×自适应高 · GitHub-dark(#0d1117/#3fb950/#8b949e)· Consolas 19/17px
- 打字机 3 字符/帧(60ms)· 输出行 420ms · 持顿 2.3s(终段 3.2s)· 卡 2.4s
- 滚动历史保留(段不清屏)· 尾注(dim `#` 行)为渲染层能力陈述,不冒充程序输出

## 5. 制作与验证流程

1. 彩排(本文件 §2"真实输出"列即来源,不得手改数字)
2. 渲染:`python tools/demo_d1_video.py`
3. 视觉验证三帧:intro / ask 持顿 / drift 持顿(无重叠/卖点可见/无截断)
4. 用户过目 → 定稿
