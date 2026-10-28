# OPS_STATE · 具身数采线单一真相源(2026-07-21 更新)

> 变更协议:先改本文件再开工。每条"真值"必须可独立复核(出处=测试/URL/报告/git)。

## 一、当前目标(用户 7/17 拍)
Phase 0 样板间:先从 **任务 001** 选出一个三天可完成的单任务样板；spec 到手后按 EGO/UMI 任务协议打包交付。**信号 #1 = 对方书面反馈;拿不到 = 回炉,不建基地。**

## 二、真值(全部可复核)
| 项 | 状态 | 复核方式 |
|---|---|---|
| qc_judge v0(7 规则) | ✅ 15 测试全绿 | `python -m unittest discover -s tests` |
| LeRobot v3 适配器 + 通用审计 CLI | ✅ | `python scripts/audit_lerobot.py <root>` |
| 真实审计 ×2 | ✅ pusht 0%/44.2% · aloha 0%(无标签)/98% | `docs/audit/` 可复跑 |
| 内部作战地图(9 页签+3 交互) | ✅ 已部署 | fde.nautilus.social/embodied/(fde 账号)|
| 外发能力册(生成式面板+2 DEMO+速算器) | ✅ 已部署,敏感词 grep=0 | /embodied/public/ |
| 外发/内部页面结构 | ✅ 已收敛为 3 入口 | /embodied/ 内部地图 · /embodied/public/ 唯一外发能力册 · /embodied/team/ 团队工作台;旧 /partner/ 只 301 跳转 |
| pilot_day3_core_v1 单样板闭环 | ✅ 已接入,不扩量 | pass@5=5/5 · repeat=100% · E-D=96%; 只证明最小闭环,不代表规模化能力已成立 |
| 任务 001 选择器与设备决策 | ✅ 已接入内部地图/团队台 | 八项硬门+100分评分+三类买方设备路径；等待实际 spec 选定唯一任务 |
| EGO/UMI 最小采购与组装 SOP | ✅ v0 已沉淀 | 两套 EGO 先行、1–2 套 UMI 原型后置；大件本体等客户验证路径 |
| Paris HTML 生成式 demo | ✅ 已并入外发页 | /embodied/public/ 下「Paris HTML 实时生成导览 Demo」; HTML 生成式演示,不是游戏客户端 |
| 讲解速记卡(三数字三故事+五个凭什么) | ✅ | docs/biz/pitch-cheatsheet.md |
| 商务弹药(两份一页纸+spec 问询清单) | ✅ 草案 | docs/biz/onepager-*.md |
| 飞轮实转记录 | 2 圈(pusht 阈值 confound / 沙盘 R4 误判) | git log 7/17 |
| 团队工作台(人类感知层) | ✅ 已部署 | /embodied/team/ —— 本文件+打法+审计的网页渲染,单一来源永不漂移 |
| **外部真实信号** | **0 个** | 诚实:一切仍是地图不是领土 |

## 三、分工(人 × agent)
- **用户(唯一的人)**:要 spec(智元/觅蜂、灵心巧手)/ 按《任务 001 选择清单》选定一个样板 / 政府与高校通道 / 一切对外签字拍板。
- **AI 侧(本框+子 agent)**:软件全包。队列:①飞书 ERP(FDE S1-S3 引擎换内容,人侧协作面)②培训考核系统 ③训练场运营方案模板 ④生成式 UI LLM 版(架构已备,等拍板要不要上 API key)。
- **调研**:一律派 agent 走 `workflows/research-agent-template.md`(硬约束防挂死),结论沉淀回 nautilus-core docs/research/ 并同步相关页面。

## 四、验证门(军令状,不达不进下一阶)
Phase 0:客户书面反馈 → Phase 1:首月按合格小时全额结算+毛利正 + 上手天数/月流失率立基线 → Phase 2:第二基地免驻场达标。

## 五、Parking(冻结,写明解冻条件)
五目设备定义文档(等样板包验证)· 生成式 UI LLM 版(等用户拍 API key 上云)· 训练场运营标投标(等标出现,模板先备)· 档位 A 3D 世界漫游 demo(等 Phase 0 后有余力)· 蒸馏/平台线(另一条业务,不混)。

## 六、节奏
- 每次 session 结束:真值表有变→更新本文件;新打法→沉淀进 workflows/;行情数字>30 天→触发月度复跑(见 workflows/research-agent-template.md 附录)。
- **本文件或 workflows/ 或审计有变 → 必须同步部署到团队工作台**(命令见 workflows/deploy-runbook.md「团队工作台同步」节)——否则人类感知层就是旧的,等于没有。
- 人类的信息入口只有两个:**/embodied/team/(看状态与打法)+ 飞书(将来领活干活)**。不要求任何人读 repo。

## 七、网页结构红线(7/21 复盘后冻结)
- `/embodied/` = 内部作战地图。它是参谋部,保留 9 页签结构,不能替换成外发页。
- `/embodied/public/` = 唯一外发能力册。以 Fable5 旧页为主,新增内容只能进入已有插槽,不能另起一套口径。
- `/embodied/partner/` = 旧链接兼容层,只允许 301 到 `/embodied/public/`,不得维护实体页面。
- `/embodied/team/` = 团队工作台。所有 SOP、速记、状态、证据通过 `docs/*.md` 渲染,让团队不用读 repo。
- 新增页面前先问:能否合并到这三类入口?不能解释清楚的,默认不建。
- 页面声明完成前必须至少验证:无凭证 401、有凭证 200、Content-Type 为 HTML、关键文本 grep、JS 语法、Chrome 截图。涉及按钮交互的,必须单独验证或明确写出未验证。
