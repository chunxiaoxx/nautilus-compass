# 主线统筹:GenOpt RL 自我提升飞轮(2026-07-06 · platform-soul 统筹)

> 用户 7/6 定位:各对话框独立运行各管一个方向,方向/主线由 platform-soul 统筹;创新是核心竞争力;先想清主线 → 再分工 → 各框开新会话推进。本文 = 主线梳理(待用户 ACK)。

---

## 一句话主线

**用 GenOpt RL 多领域基准题,同时喂两个环:买方交付(赚钱)+ 自我提升飞轮(变强)—— 而飞轮就是护城河。**

---

## 北极星(不变 · 6/22 用户拍)

FDE 产难题(强解 + 弱模型难倒 = 燃料)→ 蒸馏燃料 → 系统两维变强(① 模型权重 ② agent 自治)→ 更强系统产更难题 → 外部 benchmark 证 → 循环。

---

## 当前主线 = 一鱼两吃(买方 GenOpt RL 1000 题订单)

买方要 1000 题(Easy 200 / Medium 400 / Hard 400 · 7 领域 · 连续分数 + verifier + GPT5.5 N=3 轨迹)。这批题**同一份数据,两处用**:

| 吃法 | 产出 | 价值 |
|---|---|---|
| **第一吃:买方交付** | zip/tar.gz + Excel 元数据 | 有钱(买方付费订单) |
| **第二吃:蒸馏燃料** | 连续分数 + verifier + GPT5.5 轨迹 | 喂蒸馏环(与 ALE 同构 · 连续分数破二元饱和) |

买方规格(连续分数 / baseline 迭代 / verifier)本身就是蒸馏训练料 —— 这不是巧合,是我们选这个订单的原因。

---

## 🌟 创新 = 核心竞争力:产题自我提升飞轮(护城河)

**表面业务**:给买方产 GenOpt 题(谁都能堆人力产)。
**护城河**:产题的**同时自我提升**,越产越强。

```
产 GenOpt 题(连续分数 + verifier + 轨迹)
        │
        ├──→ 交付买方(赚钱)          ← 第一吃
        │
        └──→ 蒸馏燃料 → 模型权重变强 + agent 自治变强   ← 第二吃
                        │
                        ▼
              更强模型 / 更自治 agent 产更难题(Hard 档更多)
                        │
                        ▼
              更难题 = 更值钱交付 + 更强燃料 → 回到顶部循环
```

**为什么是核心竞争力(反 D · 锚 #3)**:
- 竞争对手:一次性产题卖钱,人力堆砌,边际成本不降,越做越累
- 我们:产题 = 交付 + 自我提升 · **agent 自主产题**(注册 producer · survival/marketplace/A2A)· 越产越强,边际成本降,质量升
- 护城河不是"题",是**产题的飞轮**(agent-first 生态 · 锚 #1)

**"创新绝对是核心竞争力"的落点**:不是产题的数量,是产题 → 变强 → 产更难题的自我提升闭环。买方买题,我们借订单养飞轮。

---

## 买方权威口径(防狗熊掰玉米)

全文 = `vtf/BUYER_SPEC_GenOpt_RL_20260702_AUTHORITATIVE.md`(7/6 从 PDF 提取)。要点:
- **7 领域**:计算系统 / 量子信息 / 运筹优化 / 机器人控制 / 光学通信 / 能源 / 物理与工程设计
- **1000 题**:Easy 200 / Medium 400 / Hard 400(**难度偏 Medium/Hard = 买方要难题**)
- **14 文件规范** + verifier 三铁律(连续分数 / valid 门控 / 只读确定性)
- **难度 = GPT5.5 N=3 gap_closed**(Easy 0.6+ / Medium 0.3-0.6 / Hard 0.1-0.3)
- **本框缺口**:现有 57 题偏 Easy · 缺 Medium/Hard 大头 + 缺 光学通信/能源/物理 3 领域

---

## 方向级分工(各框独立运行 · platform-soul 统筹 · 待 ACK)

用户口径:"agent 对话框负责 agent 方向探索" = 各框管一个**方向**,不是切一堆题。

| 框 | 方向(独立运行) | 对主线的贡献 |
|---|---|---|
| **platform-soul(我)** | **统筹 + 平台 infra + 蒸馏环** | 定 1000 题分布/难度目标 · verdict 持久化 · dispatch · OR 域生产 · 蒸馏收口(第二吃)· 跨框聚合看板 |
| **agent(V5)** | **agent 方向探索(RSI)** | 注册 producer agent 自治(survival/marketplace)· 外环飞轮 · GenOpt 出题主体 · 让"产题"从对话框搬进常驻 agent |
| **compass** | **记忆 / env / eval** | KernelEng+ComputerSys 域生产 · benchmark env · verifier · 记忆/recall/PoI · feishu 读写 |
| **soul-verify** | **质量 / verify** | canonical verify(难度门 · gap_closed 判定 · valid 门控)· verdict-gate |
| **FDE** | **业务 / 交付** | 生产管理底座 · 飞书多维表格 · 招募领域专家(补光学/能源/物理 3 缺领域)· 买方 zip+Excel 交付 |

**创新落点(agent-first)**:主线的"产题"最终要从**各对话框(脚手架)搬进注册的常驻 producer agent**(§0-ARCH)—— V5 方向探索的终点 = daemon 自主产题,不靠对话框 crank。这是飞轮转起来的前提。

---

## 跨框协调机制创新(已落地 · 治精神分裂根)

**旧机制(已证失效)**:SSOT canonical + 副本手动同步各 repo 根 → V5 停 7/4 / compass 追 7/6 / qixuw 三框各查一遍。

**新机制(pull 聚合)**:`tools/cross_dialog_board.py` — platform 定期拉各框自己 repo 的 LOOP_STATE + git log → 生成 `CROSS_DIALOG_BOARD.md`。各框只维护自己那份 LOOP_STATE,session-start 读聚合看板。**弃 push 副本,改 pull 聚合。** 已跑通:platform 36 / V5 73 / compass 49 / FDE 9 commit(7d)。

---

## 下一步(顺序 · 用户拍)

1. **用户 ACK 主线**(本文)+ 方向分工
2. ACK 后 platform 产**各框新会话启动 prompt**(每框 self-contained:主线一句话 + 你的方向 + 起手拉看板 + 本轮任务 + 验收判据)
3. 各框开新会话按 prompt 推进
4. platform 定期跑聚合看板统筹进度
