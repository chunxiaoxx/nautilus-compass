# 🎯 LOOP STATE · 单一真相源 v4(2026-07-07 重写 · 用户拍"过于混乱,重新梳理")

> 当前状态唯一权威。各框 session-start 必读;与任何 goal/memory/文档冲突,以此为准。
> 变更协议:先改这里(canonical = nautilus-core),再开工,再同步各 repo 根副本。
> 7/7 前的全部历史层(推断纠正/实施日志/A800 候选/蒸馏条件)原文在 `docs/LOOP_STATE_ARCHIVE_20260707.md`,这里不再重复。

---

## 一、北极星(不变)

FDE 产难题(强解+弱难倒 = 燃料)→ 蒸馏 → 系统可证变强(① 模型权重 ② agent 群体自治)→ 产更难更值钱的题 → 每圈外部 benchmark 证明。**分叉过滤器:一件事不直接推进这条链,默认不做。**

当前阶段目标(7/6 /goal · 用户拍):把已走通一次的闭环从 one-off 变成
**(a) 活 producer 自持产出(income 自动持续涨)+ (b) 甲方可交付(11 道合规题入飞书表)**。
不扩 1000 题,不碰蒸馏(A800 到位再解冻),不开新战线。

## 二、当前真值(7/7 · 全部可独立复核,出处 = 记分牌/探针/DB)

| 指标 | 值 | 说明 |
|---|---|---|
| income(agent 9000009) | **703**(7/16 探针,7/15 起持平)| ⚠️ 7/15→7/16 零增长 = 题池枯竭信号仍在(mint 重刷旧题被幂等门全拦),产题供给是唯一瓶颈。历史注(7/8):| 🎯 **目标(a)"自持产出"字面达成**:平台 7/8 产 2 道新变体(bin_v3+cache_v2,数据全新 seed 20260708)放进 mint glob 路径 → daemon 自动拾取/解题/canonical verify/铸币(+86/+13,与产题 QC 预测分毫不差),全程零人工。**模式已证:income 斜率 = 产题速度,题目供给是唯一手动环节**。TSP 97.63 不铸维持原判(overall_pass=false 非交付档)|
| 外部验证 verdict | **67**(7/18 记分牌直读,7d 内 +26;income 703 · 7d +100 · 自治率 89.55%)· 历史:65(7/16)| 历史注(7/8,时值 16):| auto-verify daemon 自动验证在持续;7/7 深夜后新增 6 条全 autonomous **但全是同题重跑**(cache×3/bin×3),幂等门全拦零铸币 = 门有牙齿 + **题池枯竭信号**:genopt-mint 无新题可选在重刷旧题(浪费 LLM 成本,V5 宜让 mint 跳过已铸题)|
| **producer 自治率** | **89.2%(58/65)**(7/16 探针)| 历史注(7/8,时值 56%):| 7/7 晚脱 0(V5 修假成功 a3795c2 → 3 条 autonomous 铸币);此后新增全 autonomous 但系同题重复,含金量看 income 不看该比率。**真瓶颈回到题目供给(变体题/11 题)**,非 producer |
| settle 含金量 | **0/3617** | 旧自循环账,维持原判 |
| 甲方交付 | **11 题需求已作废(用户 7/18:"现在没有这个需求")** | 接棒:垂域高难度出题仍有大量需求;用户手上有第一批题目待交接,生产走 ecc-fde-vertcase 流水线;交付物继续一鱼两吃(买方件+蒸馏燃料) |
| 记分牌 | `GET /api/platform/convergence` | 收敛 = 这 5 个数字的走向,不是叙事。⚠️ prime-001 旧 PID 884064 已不在,但自治轨迹在产 = V5 侧有新进程,身份确认球在 V5,平台不动进程 |

基础设施:cloud backend = systemd 管(nautilus-backend.service · 8000)· auto-verify daemon 10min 轮 · prime-001(PID 884064)连续跑 7 天勿动 · GPT5.5 cloud 直连稳 · doubao ARK 本机通(偶发代理抖动)· T4/H800 已关 · A800 租赁中。

## 三、系统职责一句话(谁是什么 · 治重复造轮子)

| 系统 | 唯一职责 |
|---|---|
| 平台 backend | 经济与验证的账本:verdict / external-verify(income 唯一门)/ 镜子 / 记分牌 |
| genopt_factory | 题目工厂:出题 + runner(存完整解)+ verifier |
| soul canonical verify | 独立裁判:复现一致才盖章(已由 daemon 自动化) |
| compass | 记忆 + 独立审计探针(自报不算,它读 DB 才算)+ feishu 读写 |
| V5 / prime-001 | 生产 agent:产可复现轨迹 → persist → 被验证 → 挣 income |
| FDE | 人的业务:选题内容 / 招募培训 / 甲方交付内容(不背 infra) |
| fde.nautilus.social | 教材层(只读,已开放,学员入口 /start/) |
| 飞书多维表格 | 操作台(领题/提交/评分/结算;培训期只用 3 张表) |

## 四、各框本周唯一一件事(做完才领下一件)

- **V5**:修 `fde_claim_produce` 假成功 + runner 存完整解(两份合约 due 7/9)→ 产出**第一条自治合规轨迹**(带 `artifacts.autonomous=true`)→ 自治率脱离 0%。
- **platform(本框)**:主线定位(用户 7/7 拍)= **为整套业务体系(LLM 后训练 FDE + RSI + ENG 基准 + 具身智能数据采集)做减法和闭环**——守裁判链与账本(auto-verify/记分牌/backend);配合 FDE 用 `produce_task.py` 产**互不相同的变体题**;题集就位后跑 checklist 盲点测试(M1 修正口径:T1 开放题无"难倒",测的是 checklist 可判性 + 模型盲点密度;pass@5 难倒门只适用 T3 基准)。
- **compass**:三角色(用户 7/7 问分工后定)= ① **收敛执法**:5 记分牌数字 + FDE 培训链(学员/题目/派活行数)每日独立读数,自报与探针不符即亮牌;② **合约管家**:活合约到期核销(读 DB/表验收,不闭标红);③ **记忆守门**:四代资产台账 recall 前置(任何框"我先写个"之前先查),产"减法清单"(15 表/13 SOP/50 脚本标 活/死/冻结,给用户拍砍)。**不做**:生产、内容、新架构。
- **FDE**:①选定 11 道题内容(合约 due 7/10,候选 = L3 基准样例 43 道)②陪跑第一批真人培训 = 体系唯一验收(学员卡住处记下来当整改输入)。**基建冻结:不加表、不加 skill、不写新 T 文档;repo 根建一页 FDE_LOOP_STATE 锚治失忆**(7/7 审查:6 月 v0.8 体系被自己遗忘、7 月重造更差版)。
- **soul-verify**:维持 canonical 链;计时型 verifier(Attention 类)的验证协议设计进 parking。
- **用户**:带第一批真人培训(入口 https://fde.nautilus.social/start/ 已开放);A800 到位说一声。

## 五、活合约(compass 派 · 到期必须有交代)

| 合约 | 给谁 | due | 状态 |
|---|---|---|---|
| grant_survival(探针读权)| platform | 7/9 | ✅ 7/7 兑现(三张真值表 GRANT)|
| settle_routes_404 | platform | 7/9 | ✅ 7/7 兑现(messages 双前缀 + 镜子端点)|
| fake_success_produce | V5 | 7/9 | 🔴 进行中(自治率脱 0 的钥匙)|
| evaluate_artifacts_fix(甲方 7/7 反馈)| V5 | 7/9 | compass 已代修一版,V5 收口 |
| cache_income_finding 集成 | V5 | 7/10 | 待接 |
| 11 题内容 | FDE | 7/10 | ⚫ 作废核销(7/18 用户确认需求已无;接棒合约=垂域出题第一批,等用户交题) |

## 六、硬护栏(压缩版 · 全文见归档)

1. **外部 gate 经济学(C 口径)**:external_verified 只看独立复现;income 再加两门 = 难度档合格 + 每题每 producer 只铸一次。
2. **producer 必须是注册整数 agent**(§0-ARCH);Claude 对话框是脚手架,不算系统组件。
3. **自报不算,探针才算**:任何 alive/done/income 声明以 compass 读 DB 为准。
4. **部署规程(7/16 换轨,用户拍板)**:以 `ops/DEPLOY_DISCIPLINE.md`(main 分支)为准——单一主干 main、禁 VM 直改、部署 = git pull --ff-only 禁 scp 覆盖代码、禁手工改 systemd unit、部署后必验记分牌。过渡期若确需 scp,同一改动必须同步 commit 进 main。仍禁手工 kill/nohup;pkill/pgrep -f 会自匹配 ssh 命令行。底座融合状态见 `RECOVERY_STATE_20260715.md`(main 已立 = GitHub 默认分支,基于 prod-truth + 捞入资产)。
5. **可复现契约**:轨迹必须带完整解 + sha256;preview 一律拒。
6. **不重复造轮子**:动手前先查已有资产(7/7 教训:fde.nautilus.social 整套 v0.8 被遗忘重造)。
7. **confound 先核再下结论**;n≥12 才跑 LOO;买方名绝不出现在对外内容;"真"只作真实义,不作强调副词。
8. **甲方红线**:专家亲笔,AI 痕迹零容忍;附件脱敏;交付走飞书表。

## 七、Parking Lot(冻结 · 解冻条件写明)

蒸馏维①(等 A800 + n≥12)· SWE 链 verify 候选 A(等 A800)· 1000 题扩量(等 11 题交付)· Attention 计时型验证协议(等 GenOpt 主链稳)· 新陈代谢/income 花销(等自治率>0)· FDE 4 skill 发版 / RBAC / mkdocs 新增(等真人 gate 过)· compass MCP 耦合 Phase 1-4 · content-engine 命名合约 · **具身智能数据采集线**(用户 7/7 首提:先进 FDE_BUSINESS_CHARTER 立业务锚(甲方/口径/turf)再动一行代码,防再走散落失忆老路)· 专家进 agent 经济账本(等自治率>0 + 首批学员跑通)· 导师多轮会话态 + 注册整数 agent(等出题 Copilot 单消息版跑通)。

## 八、各框 turf(一行版)

platform-soul = infra/账本/裁判链部署;soul-verify = canonical 复现;V5 = 生产 agent 与 RSI;compass = 记忆/探针/feishu;FDE = 人的业务内容;用户 = 拍板/真人 gate/算力。

---
*维护:状态有变 → 先改本文件 → 同步 V5/compass repo 根副本 → 记 memory。历史查 `docs/LOOP_STATE_ARCHIVE_20260707.md`。*
