# 宣发物料中枢 · Content Hub(2026-09-08 建档 · 发布日起维护)

> 单一入口:各渠道素材/时点/口径/状态。与 launch_plan 分工:那边管发布执行 runbook,
> 本档管**素材资产与多渠道复用**。传播顺序遵循五层拍板(英文业界→中文圈→论文→市场→大众)。
> dev.to API key 已验证可用(2026-09-08,me 端点通,账号有 9/4 发文史)——key 不入仓,
> 发布脚本从 env `DEVTO_API_KEY` 读。

## 1. 素材资产盘点(全部实物,状态 9/8)

| 资产 | 位置 | 状态 | 复用渠道 |
|---|---|---|---|
| Reddit 主帖 v3 | 20260904_launch_post_v3.md §A | ✅ 终检(数字三处一致) | Reddit 今晚;HN 首评素材 |
| 首评(94.4 口径战) | 同上 §13 | ✅ | Reddit;X |
| X thread 7 条 | 同上 §B | ✅ | X 今晚;微博/即刻可改编 |
| demo GIF v3.1 | deck_assets/demo_d1.gif(35s·循环) | ✅ 视觉验证 | Reddit 帖图;视频号原料;README 可嵌 |
| position paper | 20260904_architecture_position_paper.md | ✅ v1 待发 | 9/10 博客+HN |
| dev.to 适配版 | 20260905_devto_position_paper.md | ✅ front matter 齐 | 9/10 API 自动发 |
| 知乎答 | zh_zhihu_answer_20260905.md | ✅ 备料终检 | 9/15 周知乎 |
| 公众号技术文 | zh_wechat_tech_20260905.md | ✅ 金句卡 5 张 | 9/15 周 |
| V2EX 帖 | zh_v2ex_share_20260905.md | ✅ | 9/15 周 |
| 白皮书+深讲 PPT | whitepaper/pitch_deck_deepdive(40页) | ✅ | 视频配音底稿;路演 |
| 第二帖(LME-V2 卫生学) | 20260830_lmev2_post2_skeleton.md | 🟡 骨架,数字已定案 | Reddit 第二波 |
| paper2 | arXiv 提交中(9/7) | 🟡 等 ID | 全渠道权威背书;三处回填点位已定 |
| BGE 联动一页纸 | bge_liaison_onepager | ✅ | BAAI 触达(用户主导) |
| 仲裁栈/roadmap 中文叙事 | docs/plans/2026-09-07-* 系列 | ✅ | 创投/长线叙事素材(对外需脱密:组织内部件不外发) |

## 2. 渠道矩阵与时序

| 波次 | 渠道 | 动作 | 自动化 |
|---|---|---|---|
| 今晚 | Reddit/X | 主帖+首评+thread | reddit_watch 值守 |
| 9/9-10 | 值守+复算 | 评论区 24h 回复率 100% | — |
| **9/10** | dev.to | position paper 发布 | **API 可自动**(payload=devto 版,env key) |
| 9/10 | 个人博客 | 同文 | 手动 |
| 9/10-11 | HN | repo 直链+§14 首评 | 手动(错峰 48h) |
| 发布周 | MCP 目录×4+Discord | 目录提交 | 手动(用户账号) |
| **9/15 周** | 知乎/公众号/V2EX | 中文圈三件(错开 2-3 天) | 公众号有既有管线 |
| 9/15 周 | **视频号** | 见 §5 视频三档 | 录制用户,脚本已备 |
| 灵活 | Lobsters/Bluesky/Newsletter | 第①层反响好后 | 手动 |
| ID 到手 | r/MachineLearning+三处回填 | 论文讨论帖 | 模板已备 |

## 3. 统一口径卡(所有渠道不得偏离)

- 检索对打:P@1 **0.890 vs 0.774**(+11.6pt)/P@5 0.978/0.916/MRR 0.929/0.834,同题同判据各用默认嵌入
- e2e:**42.6→75.4%**(全 500)/81.6%(剔除断连 71),双口径并报
- LOCOMO 客场 0.644 vs 0.592;EverMemBench 44.4-47.3%
- drift AUC 0.83·p95<50ms;写入零 LLM;$3.50 复现;130 天 771 commits(603 agent)
- 叙事三句:写入时下注→地址空间决定遗忘→判分卫生学(概率世界共识)
- 链接四件:github.com/chunxiaoxx/nautilus-compass · compass.nautilus.social · pypi:nautilus-compass(3.1.2) · arXiv paper2(待 ID)
- 🔴 红线:不称"区块链式去信任"(只说 PKI 式信任最小化);不提组织内部件(信箱/框名);数字只引上列

## 4. 创投日报素材包(交创投日报框,按其工作流生产,compass 只供料不代写)

**故事钩(按传播力排序)**:
1. 一个人+agent 舰队 130 天 771 commits(603 次 AI 提交)做出开源记忆层,在公开基准上赢了拿了大钱的 mem0——「AI 原生组织」不是概念,是审计记录
2. 他们的竞争力藏在你看不见的地方:判分卫生学——他们抓了自己的 AI 判官 5 次静默失效,一次冤枉了 14% 的题;这个方法论成了论文(arXiv 提交中)
3. 新叙事:agent 时代的基础设施缺口不是记忆本身,是「仲裁」——谁验证 AI 记得对不对、数据值不值钱;他们押注这个位置(对标海外 Aegis Compass $20/mo 已验证付费意愿)
4. 竞品撞名三次的独立开源项目,怎么在巨头和融资玩家的缝里找位置(Modified MIT:自部署永久免费)

**数字卡**(照 §3,不另造);**素材文件指针**:§1 表+demo GIF+quote_cards(金句卡)。
**边界提醒**:创投日报 IP 是用户另一工作流(写作助手管线),本包只提供事实与素材;
公众号文按其自身宪法(七条铁律)生产;**对外不引用组织内部信件/框名/未公开产品线**。

## 5. 视频三档(视频号等)

| 档 | 时长 | 内容 | 底稿 | 动作 |
|---|---|---|---|---|
| A·hook | 15-30s | demo GIF 原样+3 行字幕 | demo_d1.gif | 直接合成,今晚可发 |
| B·产品实操 | 60-90s | 真终端跑 demo_d1.py 五命令(带字幕) | demo_recording_script_v2.md 分镜 | 用户录,Win+Alt+R |
| C·深讲 | 3-5min | 深讲 PPT 40 页配音精讲(挑 12-15 页) | pitch_deck_deepdive | 用户配音;脚本=页注已内嵌 |

优先级:B>A>C(视频号算法偏好 60-90s 实操);A 可当 B 的预告。

## 6. 待办

- [ ] dev.to 发布脚本(tools/devto_publish.py,env 读 key)9/9 前备好
- [ ] 创投日报素材包转交(用户或告知该框仓路径后投函)
- [ ] 视频 B 录制(用户,发布周)
- [ ] paper2 ID 到手→三处回填+全渠道背书升级
- [ ] 第二帖成文(LME-V2 卫生学,Reddit 第二波)
