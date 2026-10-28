# Fresh-session /goal — RSI+FDE 收敛(2026-06-19·答"快速收敛闭环 / 第三类飞轮彻底打通 / 推进 RSI+FDE")

> 我是 platform-soul(nautilus-core 后台引擎)。元规则:先验证后动手·诚实·任何能力声明挂 probe 真数否则标 facade。anchor #2 RSI 闭环优先 · #3 反 D(ship≠价值)· #5 先调研。session-start 读:`docs/PATH_B_RSI_CORRECTNESS_BINARY_DESIGN_20260618.md` + memory `session_20260618_p13_rsi_singleowner_close_fast1_structurally_dead`。

## 核心洞察(把三问焊成一件事)
第三类业务飞轮 = RSI 飞轮(**双门一鱼两吃**):
```
产难题 → doubao 做 → 失败(pass@5≤0.6) = 买方 stump 题(第三类业务交付)
       → 强模型做 → 强✅+doubao❌    = 蒸馏燃料(强模型 correct trace 教小模型)
```
一条生产线同喂业务(买方难倒题)+ RSI(蒸馏训练料)。

## 🥇 P0(单一 forcing function·闭了才开下一个)
**闭 path B = 第一个真 RSI in-context 环**(5 周第一次·离散判据干净)。工具齐(11 TDD):`services/swe_verify.py`(parse/reward/rsi_improved/memory)+ `services/swe_runner.py`(apply patch+跑 pytest)。剩 3 步:
1. **选题**:1 道 SWE-bench-lite 易 instance。🔴 关键:挑 turn-1 **部分通过**(0<X<全部)的题——全 0/全过都没梯度(p18 single-trick 坑)。先 pilot 3-5 道看 turn-1 pass 率筛"中间梯度"题。
2. **接 producer**:复用 `services/fde_sdiagnose_run.bailian_complete`(deepseek/qwen 产 patch)· 泛化 `scripts/rsi_p13_loop.py` 结构(produce→`swe_runner.run_candidate`→`swe_verify.parse`→reward→`build_swe_memory`→produce turn-2)。
3. **跑 2-turn**:turn-1 patch(无记忆)过 X 个 → 记忆=失败测试+traceback → turn-2(注入)过 Y 个 → `rsi_above_noise` 不用(离散!)直接 `swe_verify.rsi_improved(X,Y)`=Y>X。**Y>X = RSI 机制首证** → 写 PoI + 经合约通道交 V5 wire W1/W2。
- DONE:Y>X → 报喜 STOP。ABORT:扫 5 道都无梯度(全 0/全过)→ 记 probe-backed 负 → 转蒸馏路(P1)。

## P1(P0 绿后·第三类飞轮自治=Q2"彻底打通+持续")
零件全在,缺 timer 自治串联。建"mint→GPU验→双门分拣→写买方表+燃料池"自治环:
- 产题:compass `kernelbench-stump-batch`(L2 stump)/ `compass-experience-benchmark`(经验题)
- 验证:gate B poller(已部署)+ GPU kb_eval · dispatch timeout reaper(已修·孤儿自清)
- **双门分拣**(质量门):doubao 失败=够难(买方料)· 强模型解=干净蒸馏料 · `services/fde_triage.classify_distillation_fuel` 已建
- 缺口:把强模型那侧 + 写买方表 + 燃料池 串进 fde-bench.timer 自治。**这步=Q2 的"彻底打通"**。

## P2(蒸馏破墙·6/14 策略·需 P1 产燃料 + GPU)
用飞轮产的"强解 doubao 败"燃料训小模型(QLoRA 7B on T4)→ 破 doubao 能力墙 = 真 RSI(权重更新·非 in-context)。gated:需 P1 燃料池有量 + A 簇 GPU(compass daemon 占·expandable_segments 已 wire)。

## 快速收敛纪律(Q1·写进行为)
1. 单一 forcing function · **离散判据优先**(整数 Y>X 干净·避噪声判据如 speedup 0.54%)
2. 先验证后建 · probe-backed · 负结论也要 probe
3. **负结论 ABORT 不硬撑**(死路证负即停·别被 Stop hook 锁死无限重试=本 session 真踩过)
4. parking lot 冻结 · 不开新战线 · 每 loop 一节点

## 阻塞/待办(等外部·不阻塞 P0)
- **FDE B2**:等 FDE 给 RGDK app_token + 授 bot + 14 行迁移确认 → 切 S1 runner(小改 service args)
- **context-hook 瘦身续**:task-notification 注入已降 60%(env COMPASS_SKIP_RECALL_ON_SYSTEM=1·LIVE)·剩 anchors 静态块(1.7k)·要全归零需 compass 改 recall.py daemon 路(它 turf·已 disclose)

## 凭据/坐标(carry over)
GPU=43.166.8.20 Tesla T4 · key=`~/.claude/.cache/.fde_api_secrets.env`(BAILIAN=deepseek/qwen·ARK=doubao)· cloud ssh port 24860 · DB=nautilus_production(无 updated_at·verdicts 用 overall_pass)· python -m services.* 前 cwd=phase3/backend · git push 前可能需 merge origin(本 session 已同步)。

## 各框(6/19)
V5=stand down p13·飞轮棘轮自治转(另一 loop·与 in-context RSI 不同)·等"记忆抬 reward"机制交它 wire。compass=待登 PoI·切 fast1 verifier·gate B 部署·daemon 占 T4。FDE 框架=v0.6.1·等我 B2 切换(我已 ball-back 需它三件)。

关联 [[session_20260618_p13_rsi_singleowner_close_fast1_structurally_dead]] · docs/PATH_B_RSI_CORRECTNESS_BINARY_DESIGN_20260618 · design 2026-06-14-rsi-distillation-flywheel · [[FDE_BUSINESS_CHARTER]]
