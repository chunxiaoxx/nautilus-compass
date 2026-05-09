# nautilus-compass v1.0.0 宣发交接包 · 给创投日报对话框

> **交接日期**: 2026-05-08 · **状态**: repo 已公开 · v1.0.0 stable 已 ship · 论文 arxiv 上传中
>
> 这是给创投春晓 / 创投日报 dialog 的宣发执行包。所有事实已锁、文案已写、渠道已分。
> 接收方: **直接拿这份文档作为入口** · 我已经在 paper/promo/ 下放好所有 ready-to-post 内容。
> 你的工作: 选时机、选渠道、按顺序发、收 metrics 反馈给我。

---

## 0 · 核心事实 (所有渠道一致 · 不可改)

```
项目:        nautilus-compass v1.0.0 stable
作者:        Chunxiao Wang (王春晓) · Yiluo Technology Co., Ltd.
邮箱:        chunxiaoxx@gmail.com
仓库:        https://github.com/chunxiaoxx/nautilus-compass (公开 · MIT)
SaaS:        https://compass.nautilus.social (305 用户)

跑分头号数 (锁定):
  LongMemEval-S n=500             56.6%   (v0.8 · 2026-05-04 锁)
  EverMemBench-Dynamic n=500      44.4%   (Run 1 · 2026-05-07)
                                  47.3%   (Run 2 · 2026-05-08 · n=497, 3 题 API skip)
                                  45.84%  (双 run 均值)
  vs MemOS 42.55                  +1.85 / +4.73 / +3.29 pts (Run 1/Run 2/mean)
  Drift 检测 AUC                   0.83 held-out · 0.92 in-set
  V4-pro full-500 (负结果)         56.4% (-0.2 vs v0.8 · 8× cost)
  复现成本                         ~$3.50 · LongMemEval 500 题
  Hook 延迟                        <50 ms p95

技术 (锁定):
  全栈 MCP A2A 协议: stdio + TCP + TLS + mTLS · 每 token RBAC + rate limit
  Merkle hash chain 完整审计链 · session_writer 写入即生效
  5 个用户级 slash command (/compass-{verify,drift,recall,search,status})
  6 个 MCP 客户端一键安装 (Claude Code/Desktop · Cursor · Cline · Continue · Zed)
  228 个 pytest 全过 · 0 flake · 0 regression
  Cross-judge replication: Gemini 2.5 Pro + DeepSeek V4-flash · κ=0.70

License:
  代码 MIT · Anchors CC0 · 双 license 物理隔离

论文 (即将上 arxiv):
  Paper 1: "Nautilus Compass: Black-box Persona Drift Detection for Production LLM Agents" · 19 页
  Paper 2: "Closing the Memory Recall Gap with Chinese LLMs ..." · 27 页 · 含 Gemini cross-judge
```

**绝对不要改的点**:
- 数字必须用 Run 1/Run 2 双值 · 不能只说 47.3 (cherry-pick) 也不能只说 44.4 (低估)
- 必须 honesty caveat 一句: "Gemini 2.5 Pro 跑得 28% · 双 judge 都有 bias"
- V4-pro 必须 mention 是负结果 · 不能藏起来
- 仓库公开 + MIT · 必提 (信任度核心)

---

## 1 · 现成的内容资产 (在 paper/promo/)

| 文件 | 用途 | 状态 |
|---|---|---|
| **`outreach_emails_2026-05-08.md`** · 8 封 | cold email 给学术圈 / 工具圈 VIP | ✅ 已写 · 8 封 Gmail drafts 已创建 (在 chunxiaoxx@gmail.com 草稿箱) |
| **`forum_refresh_2026-05-07.md`** | HN + Reddit r/MachineLearning + r/LocalLLaMA + Twitter thread | ✅ 已 refresh v3 + 1.0 |
| **`hackernews.md`** | HN show post 专用 | ✅ |
| **`papers_with_code_submission.md`** | PWC leaderboard 提交 (LongMemEval + EverMemBench) | ✅ 含双 run + leaderboard 表 |
| **`iclr_2026_workshop_submission.md`** | ICLR 2026 Workshop 投稿包 | ✅ (未 verify deadline · 你查 CFP) |
| `../news_v1_rc2_refresh.md` | 中文新闻稿 (技术媒体口径) | ✅ 已 refresh v3 + 1.0 |
| `../PRESS_KIT.md` | 通用 press 包 (logo / one-liner / facts / FAQ) | ✅ |
| `../BLOGPOST.md` | 长 blog post (中英混排) | ✅ |
| `../GITHUB_RELEASE.md` | GitHub Release 公告 (已用) | ✅ |

---

## 2 · 渠道分配 + 时序策略

**总原则**: arxiv ID 拿到后再开始公开 broadcast。在那之前,可以先做暖场 (closed circles)。

### Stage 1 · 暖场 (D 日: 即刻 · arxiv ID 还没下来时)

| 渠道 | 发什么 | 谁发 | 注意点 |
|---|---|---|---|
| 8 封 cold email | `outreach_emails_2026-05-08.md` 里的 4 封可发 (#1 Anthropic / #5 Charles Frye / #6 OpenAI / #7 LangChain+LlamaIndex) · 4 封 [TODO] 地址需先查 | 我 (chunxiaoxx) 自己点 Send | 发件用 chunxiaoxx@gmail.com · 不要批量 BCC · 一封一封发 · 间隔几小时 |
| 微信公众号 (创投春晓) | 改写自 `news_v1_rc2_refresh.md` · 中文 · 配图用 paper2_main.pdf 的 figure 1/2/3 | **创投日报对话框** | 标题别太硬技术 · 主推 "中国开发者论文 · 跑分超 MemOS · MIT 开源" 角度 |
| 知乎 | 同上 · 删掉公众号特有的引导关注语 | **创投日报对话框** | 个人号发 · 加 #LLM #AI Agent #开源 标签 |

### Stage 2 · 主推 (D+1 ~ D+3 · arxiv ID 已 live)

| 渠道 | 发什么 | 谁发 | 时机 |
|---|---|---|---|
| **Hacker News** | `hackernews.md` "Show HN" | 我 | 周二 / 周四 · 美西 8AM (北京晚 11) · 上 front page 概率最高 |
| **Reddit r/LocalLLaMA** | `forum_refresh_2026-05-07.md` 的 Reddit 段 (技术诚恳口径) | 我 | HN 发完 24h 后 |
| **Reddit r/MachineLearning** | 同上 · 强调 paper + benchmark | 我 | LocalLLaMA 后 12h |
| **Twitter thread** | 8 推 thread · 第 1 推主 hook · 第 2-7 推数字 · 第 8 推 GitHub URL | 我 (个人号) | HN 发完即推 |
| **PaperWithCode** | `papers_with_code_submission.md` 完整提交 LongMemEval + EverMemBench leaderboard | 我 | arxiv ID 到 24h 后 |

### Stage 3 · 持续 (D+7 ~ D+30 · 收 reaction · 持续输出)

| 渠道 | 发什么 | 谁发 |
|---|---|---|
| **微信公众号 (创投春晓)** 第 2 篇 | 深度技术稿 · drift 检测 + MCP A2A 协议解析 · 配 BLOGPOST 内容 | **创投日报对话框** |
| **小红书 / 抖音** | 短视频 · Demo 镜像 · 60 秒 walkthrough · "AI Agent 不再忘事" 角度 | **创投日报对话框** |
| **掘金 / 思否 / V2EX** | 中文技术社区精简版 · 引流 GitHub | **创投日报对话框** |
| **ICLR 2026 Workshop** (如果 deadline 还没过) | 投 short paper · 用 `iclr_2026_workshop_submission.md` 的精简版 | 我 |
| **HuggingFace Spaces demo** | 上线 hf_space/ 里的 Gradio demo · 让人立即试 | 我 (待 HF token) |

---

## 3 · 给创投日报对话框的具体执行清单

### 你 (创投日报 dialog) 做的事

#### A · 微信公众号长文 (优先级 P0)

```
源文件:    paper/news_v1_rc2_refresh.md (英文为主)
任务:     改写为中文公众号文 · 适配 创投春晓 风格
长度:     2000-3000 字 · 配图 5-8 张
图源:     paper/figures/fig1_architecture.pdf 等 · 也可截 paper/paper2_main.pdf 的 table
角度建议:  "中国开发者用 DeepSeek + BGE-m3 跑过 MemOS · MIT 开源 · 还附 2 篇论文"
钩子:     双 run 的诚实精神 (44.4 + 47.3 + Gemini 28% 都报) 是中国开源圈少见的 transparency
```

#### B · 知乎专栏 (P0)

```
任务:     从公众号文衍生 · 删公众号引导语 · 加知乎 tag
评论引导: "如果你是开发者用 Claude Code, 跑 install_to_agent.py 试试 · 60 秒接入"
```

#### C · 短视频 / 小红书 (P1 · 一周内出)

```
60 秒 demo:
  - 0-10s   "AI 长 session 后忘了你的规矩 · 这就是 drift"
  - 10-25s  装 plugin 的 GIF + slash command 演示
  - 25-45s  数字 56.6% / 47.3% 一闪而过 + GitHub URL
  - 45-60s  call-to-action: "开源 · 自己装 · MIT"

文案吸睛:
  - "我让 AI 自己拦住了它的老毛病"
  - "中国开发者写的 AI memory · 论文+代码同时开源"
  - "Cursor / Claude Code / Cline 都能用"
```

#### D · 跨平台运营 (P2 · 持续 30 天)

```
- 公众号 commenting / Q&A 回复
- 知乎私信 / 评论运营
- 小红书 / 抖音引流
- 周一 status: 发哪些 / 反馈如何 / 转化几人去 GitHub star · 同步给我
```

---

## 4 · 我 (OSS dialog · chunxiaoxx) 做的事

不重复你做的:

- 8 封 cold email Send (我自己点 Gmail 草稿箱)
- HN / Reddit / Twitter 英文圈子 (我个人号)
- arxiv 提交 + paper Q&A
- ICLR Workshop 投稿
- HuggingFace Spaces deploy (待 token)
- GitHub Issue / PR 处理
- 跑 demo / talk 邀请响应

**协作点**:
- 你公众号文出来后 · 我转发到 Twitter (英文圈子也看到)
- 我 HN 上后 · 你截图发到知乎 / 微博 (社会证明)
- 8 封 cold email 中如果有人回 (Anthropic / OpenAI 官方) · 我立刻告诉你 · 你做后续公众号 follow-up

---

## 5 · 关键 KPI · 你周一汇报给我

**Week 1 (D~D+7)**:
- 公众号阅读 / 在看 / 转发数
- 知乎专栏阅读 / 收藏 / 赞数
- 引导到 GitHub 的链接点击数 (UTM 标记 · 用 `?ref=weixin` `?ref=zhihu`)
- 引导到 https://compass.nautilus.social/signup 的注册数

**Week 2-4**:
- GitHub star 增长 / fork 数
- 微信公众号粉丝增长
- compass.nautilus.social 转化数 (Free → Pro)

**红线**:
- 任何渠道发出去后, 数字必须跟 §0 完全一致 · 改一个位都要先跟我 confirm
- 不能 cherry-pick 47.3% 不报 44.4% (会被 reviewer / 同行抓 cherry-pick · 信誉折损一次失全部)
- V4-pro 必报 (诚实 · 反差感 · 反而是宣发 hook)

---

## 6 · 我的承诺 (给你 buy-in)

- arxiv ID 拿到后 24h 内 · 我把所有 promo 文件里的 `[arXiv:TBD]` 占位替换成真 ID · 通知你重发更新过的内容
- 任何渠道有人提我们的项目 (HN comment / Reddit thread / Twitter mention) · 我转给你做 social proof 素材
- compass.nautilus.social 后端有 bug 影响演示 · 我 4h 内修
- 周一 status 我也写自己的 (OSS metrics / GitHub star / arxiv reads / cold email 回复率) · 双向同步

---

## 7 · 起步建议

**优先级最高**: 微信公众号长文 (你这边 P0)

可以**今天 (2026-05-08) 就开始写** · 不用等 arxiv ID:
- arxiv 部分写 "论文已上传 arxiv · ID 即将公布" 占位
- 等 arxiv ID 到了我立刻给你 · 你改 1 个字段重发不存在 · 直接发布即可

时机建议: **明天 2026-05-09 (周六) 上午 10 点** 推公众号 (周末上午阅读率高 · 加技术圈周末看长文习惯)。

我在等 arxiv 提交完 · 拿到 ID 第一时间通知你。

---

## 8 · 文档版本

- v1.0 · 2026-05-08 · OSS dialog (chunxiaoxx) seeds initial handoff
- 后续 OSS / 创投日报双向 PR 修订 · 在本文件 §8 追加版本号
