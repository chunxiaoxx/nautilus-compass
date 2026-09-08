# 增长系统方案 v2(2026-09-08 · 调研质疑→迭代版 · 待用户飞书审)

> 流程:v1 系统设计 → 业界调研质疑 → 本版迭代。上游:v1 要点见会话与 content_hub;
> 本档为正本。审查结论:**五层架构与北极星被业界证据支持;四点被质疑,已迭代**。

## 一、系统架构(五层,v1 保留)

```
L5 反馈层   双螺旋:技术⇄营销互为飞轮(milestone→故事件;质疑→issue→公开跟进)
L4 度量层   四采用信号自动采集 + 24h/72h/7d 检查点 + 粗归因
L3 分发层   渠道=部署目标 · 30 天发射序列 · dev.to API 化
L2 生产层   内容工厂:一次深挖→多渠道渲染 · ship a feature 同时 ship a story
L1 资产层   故事组件库 + 数字从 SCOREBOARD 程序化注入(禁手抄)
```

北极星(不看 star 看采用):signup 数 / 外部 token MCP 调用 / pip 下载 / **复算者人数**。

## 二、调研质疑与迭代(本次核心增量)

**质疑 1 · Product Hunt 推迟是否错误?**
业界共识最强序列是 Reddit→PH→Show HN([smollaunch 对比](https://smollaunch.com/compare/product-hunt-vs-hacker-news):两平台奖励不同叙事)。
但也有反证([r/SaaS](https://www.reddit.com/r/SaaS/comments/1rjrpxp/product_hunt_launch_in_10_days/):PH 访客多为开发者非买家)。
**迭代**:PH 从「定价时再说」改为**数据驱动待定**——9/12 第一波复盘若 Reddit 参与度≥阈值
(≥20 技术性评论),9/13-14 上 PH(产品叙事版),否则继续推迟。

**质疑 2 · 我们没有 pre-seed 社区(冷启动)。**
业界普遍强调 launch 前先有 10-50 早期用户/支持者([SideProject 8 天清单](https://www.reddit.com/r/SideProject/comments/1s8taqv/launching_on_show_hn_in_8_days_what_actually/)、[daily.dev 案例](https://business.daily.dev/resources/open-source-marketing-grow-developer-community-without-budget/):12 周 1500 star 靠社区参与)。
已无法回退(今晚发)。
**迭代**:加 **seeds 机制**——发布后 48h 内每个复算者/signup 用户进 seeds 名单,定向维护
(点名感谢/优先回复/进 issues 讨论),把冷启动劣势在第一周内转化为种子社区。

**质疑 3 · maintainer burnout 是开源头号死因。**
[HN「Dumb ways to die」](https://news.ycombinator.com/item?id=48198127):弃维护/精力耗尽比
没人看更致命。一人组织+30 天序列风险实测偏高。
**迭代**:设**最低维护档**——每周投入上限(建议 ≤15h 营销线),超限砍序列事件、不砍维护;
「活跃度信号」协议:issue 24h 响应 SLA + 每周至少一次可见 commit(我们 771 commits 天然优势,
守住即可)。

**质疑 4 · star 是虚荣指标还是动量指标?**
[ToolJet 36.4k stars 复盘](https://blog.tooljet.com/github-stars-guide/):star=动量与社区信号,
非目标——与 v1 北极星一致,**无迭代,加强表述**:star 只做过程量进周报,不进决策。

## 三、30 天发射序列(v2,含迭代点)

| 日期 | 事件 | 判据/回退 |
|---|---|---|
| 9/8 21:00 | Reddit 主帖+首评+X thread | 前 30min 值守权重最大 |
| 9/9-10 | 值守+评论区复算攻略+**seeds 名单启动** | 复算者全点名致谢 |
| 9/10 | dev.to(API 自动)+博客 | — |
| 9/10-11 | HN 错峰(repo 直链+技术首评) | 周二-四 7-9AM EST 窗 |
| 9/11 | 创投日报公众号(中文首发) | 用户侧 |
| 9/12 | **第一波复盘(24/72h 数据)+ PH 决策** | ≥20 技术评论→PH 上,否则推迟 |
| 9/13-14 | 视频号实操档 / PH(若通过) | 二选一防精力超限 |
| 9/15 | 中文圈三件(知乎/公众号技术文/V2EX) | 错开 2-3 天 |
| 9/15-17 | paper2 ID 宣传波(r/ML+全渠道背书) | ID 到手触发 |
| 9/18-20 | 第二帖(判分卫生学行业故事) | — |
| 9/22-25 | VerifyPack v0.2「先验后付」故事 | #47 完成触发 |
| 9/28-30 | 30 天总复盘 → 10 月定档 | 北极星四信号评分 |

## 四、失效模式与防护(v1 保留+v2 增)

| 失效 | 防护 |
|---|---|
| 冷启动无人看 | 30 天 8 事件再点火;seeds 机制补 |
| 负面质疑 | §6 模板+质疑→issue→修复→公开跟进协议 |
| 口径漂移 | 数字注入管线 |
| **精力耗尽(v2 强调)** | 最低维护档:周上限 15h,砍事件不砍维护 |
| 爆红过载 | 读 5rps 天花板已知,限流预案 |
| 假成功工厂复发 | 北极星只认四采用信号,star 不进决策 |

## 五、分工

compass=资产层/英文生产/度量自动化 · 创创投日报框=中文生产 · 用户=发布动作+视频配音+
**每周 30min 复盘拍板**+PH 等 go/no-go 决策。

---
*审查与调研来源:见 §二 链接;v1→v2 差异=四项迭代+序列表判据列。本档经用户飞书审阅后生效。*
