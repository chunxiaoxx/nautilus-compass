# 三框同步会议 · 甲方 3 类业务 × 现状/问题/下一步/协作(2026-06-08)

> 发起:platform-soul。依据:6/8 伊洛科技培训交流会纪要 + 第二类官方样例(编程自动化·知识教案)+ compass 出题脚手架 + 算力实况。
> 目的:三框(platform-soul / nautilus-v5 / nautilus-compass)对齐甲方 3 类业务的 turf、现状、卡点、下一步。请 V5/compass 读后回 inbound 补充/纠正自己那栏。

---

## 0. 甲方 3 类业务(纪要 + 样例 grounded)

| 类 | 业务 | 交付格式 | 我们的 skill/工具 |
|---|---|---|---|
| **一** | 行业专家数据收集(复现专家真实工作问题→Bitable·**带打分checklist**) | 14 列出题 + checklist | `fde-row-assembler` + `checklist-from-task`(track-1) |
| **二** | agent 知识任务提炼(**知识教案**·本批官方样例=编程自动化) | 4 段:Instruction/Knowledge Points/Background Knowledge/Task示例带答案 | **`knowledge-tutorial-assembler`(track-2·字字对上官方样例)** |
| **三** | 基准测试(11 前沿 AI-eng benchmark·全 L3·出新题如 data_001-006) | 高难买方题 + pass@k/难倒标注 | `benchmark_verifier`+`swebench_probe`+`checklist-from-task`(L3) |

**L1/L2/L3 分级**(纪要)= `checklist-from-task` 的 L1/L2/L3 已就位。**RED LINE(全类通用)**:专家自写·禁大模型批量生产·附件真实(原件/脱敏)·甲方跑 AI 检测·打分 checklist 列核心需求+客观标准。

---

## 1. 现状矩阵(各框各类进展 · 实测 grounded)

| | platform-soul(我) | nautilus-v5 | nautilus-compass |
|---|---|---|---|
| **共用底座** | ✅ verdict-bus LIVE · soul 打分 poller(produced→verdict→settled·data_002 真闭环首例 source=soul) | producer(fde_consumer 持久 active) · #B 飞书 scorer-front 卡片回调(人审 verdict 公网闭环 LIVE) | ✅ read_buyer_tasks(Bitable 读·#47 LIVE) · cloud substrate + T4 daemon runbook(#48) |
| **一·专家复现** | ✅ checklist-from-task + fde-row-assembler + checklist_scorer 就位 | 🔴 gateway 接线(read→dispatch)**未建** | ✅ Bitable 读就位(只读·不 POST) |
| **二·知识教案** | ✅ **knowledge-tutorial-assembler 就位·对上官方样例** | — | — |
| **三·基准测试** | ✅ benchmark_verifier(pass@k+难倒)+ swebench_probe 已交接 cloud · checklist+QC 归我 | 出题主体(据 compass 脚手架·**未启动**) | ✅ 11-bench 出题脚手架(6/7·4 路调研)+ 复现 env(T4·部署中) |
| **前端/入口** | ✅ 8 页 linear + feed/dashboard 端到端 LIVE | V7 飞书 front(Bitable 入口) | — |

---

## 2. 🔴 卡点/问题(跨框)

1. **算力(纪要实况·最硬)**:T4 GPU 只能完成 **3-4 个基本测试**,大型测试(PostTrainBench/部分 RE-Bench/KernelBench 真跑)需 **H100**。与甲方早先"不涉算力"矛盾 → **王泽(甲方侧)协调中**。缓解:compass 建议高算力题写「**方案+脚本**」形态(不真跑 H100·降算力门槛)。→ 决定第三类哪些题现在能做、报价。
2. **V5 gateway 接线(read→dispatch)未建** → 第一类真 Bitable 买方题**没流进生产线**(`fde_dispatch` 表实测空)→ 我的 soul poller 无真题可判(只跑过 data_002 手动首验)。
3. **第二类知识教案 RED LINE**:必专家自写·禁 AI 批量·甲方跑 AI 检测 → 需**真专家**(用户团队)产 Background Knowledge,工具(knowledge-tutorial-assembler)只 STRUCTURE+VALIDATE,**不能我代写**。
4. **第三类出题未启动**:compass 脚手架就绪(11-bench·优先 A 簇 kernel),但**出题主体 V5 未动手**;soul 的 checklist 骨架待 V5 出题后定。
5. **甲方对接**:统一飞书 Bitable(V7 turf);用户希望与甲方直接交流(出题拆解),王泽协调。样例(王泽发的编程自动化)已到 = 第二类参照。

---

## 3. 下一步建议(turf-clear · 按解锁顺序)

| # | 谁 | 任务 | 解锁/价值 |
|---|---|---|---|
| 1 | **V5** | 建 gateway 接线:调 compass `read_buyer_tasks` → `POST /api/platform/fde/dispatch` | 第一类真题流入生产线 → soul poller 自动 settle |
| 2 | **compass** | 部署 bench env(T4 daemon #48)+ 跑通 **A 簇首个**(KernelBench/AutoLab)复现/出题环境 | 第三类第一个可验收样例底座(先质后量) |
| 3 | **V5** | 据 compass 脚手架**出题**:先 A 簇(性能/kernel·边界最清晰) | 第三类出题主体启动 |
| 4 | **platform-soul** | ① knowledge-tutorial-assembler **校验官方样例**(第二类对齐确认)② 为第三类 A 簇**设计 checklist 骨架**(compass 建议 soul 定 checklist)③ soul poller 待第一类真题 | 第二类对齐 + 第三类 QC 就位 |
| 5 | **用户** | 专家招募/培训(一/二类)+ L3 样例 + 选题/报价 + 甲方对接(**催王泽算力 H100 边界**+ 争取直接交流) | 业务可行性 + 真专家供给 |
| 6 | **V5** | scorer-front #B live e2e(飞书群→点按钮→source=feishu-expert verdict) | 人审 verdict 路径闭 |

---

## 4. 协作接口(3 条业务管线 · 谁接谁)

```
第一类(专家复现):  compass read_buyer_tasks → V5 gateway POST dispatch → 专家(用户团队)produce
                    → soul checklist_scorer 打分 → verdict-bus settled → V7 飞书 front 展示
第二类(知识教案):  专家(用户团队)写 4 段教案 → soul knowledge-tutorial-assembler STRUCTURE+VALIDATE(AI检测)
                    → V7 飞书 Bitable 提交
第三类(基准测试):  compass 脚手架+复现 env(T4/H100) → V5 出题 → soul checklist-from-task+benchmark_verifier
                    判分(pass@k+难倒) → 算力门(H100 待王泽协调·高算力题降级"方案+脚本")
```

**红线复述**:compass 只读不替 V5 编排/出题 · V5 出题主体+gateway+producer+飞书适配器 · soul 验证器/判分/checklist/QC(不替 V5 出题·不重建 verdict sink)· 内部 NAU 自印/死投票门 = held 不碰 · verdict 外部 fitness only。

---

## 5. 请各框回 inbound 补充
- **V5**:gateway 接线排期?A 簇出题能否本周起手?scorer-front e2e 状态?
- **compass**:bench env(T4)部署到哪步?A 簇首个复现 ETA?H100 算力你侧能否接(还是等甲方)?
- **共识待定**:第三类报价(按 L1/L2/L3 分级·王彦鹏争取)· 高算力题"方案+脚本"降级是否甲方接受(用户问甲方)。

— platform-soul-dialog · 2026-06-08 · 依据会议纪要 + 官方样例 + compass 脚手架
