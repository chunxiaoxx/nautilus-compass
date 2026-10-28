# 🎯📋 platform-soul → V5 + compass · 2026-06-24 · 统筹 plan(用户拍板)· 蒸馏 ALE 榨干收尾 + 第②维 Gap-2 producer 注册化

> 3 并行 grounded 调研后用户拍板。先纠正前提,再钉各框 actionable 球。这是统筹基线,变更走此文件。

## 🔴 调研纠正的前提(全框对齐·别再用旧认知)
1. **"glm→qwen 银弹"= 部分错**:cloud SWE producer daemon **早已是 qwen3.7-max**(2026-06-16 wired·全仓 grep glm=0·endpoint 实测 live)。我之前 `swe_producer_params_qwen` / `verify_0A_glm_not_qwen` 的"换 qwen"前提对 cloud 不成立——**SWE 0 A 类不是模型问题·是 strong 解出率/能力墙**(qwen 也解不对 flask f2p 0/2)。**仅 ALE producer(GPU run_ale_gpu.sh)用 glm-5.2**。
2. **qwen3.7-max 本身"慢/常超时"**(代码注释·reasoning 模型 142k token CoT)。换它不保证修 timeout。真瓶颈 = `complete()` timeout(12/19 turn-1 超时·strong 没产出)+ 强模型解出难题能力墙。
3. **ALE-Bench 40 题硬顶**(38 已试·剩 ahc004/ahc014)= **凑不到 n=30-50**。
4. **producer 注册化几乎 0%**:三 agent(prime/kairos/v7)是 alembic seed 行 + sentinel 假钱包·非注册产物。FDE claim 路径(`fde_dispatch.py:150`)把任意字符串当 producer 无认证。**今天 soul 修的 #1/#3/#5 是 agent 自治健康基底·没碰 FDE 燃料飞轮连通**——第②维真杠杆 = Gap-2/3。

## 📋 统筹 plan(两条并行·用户拍板)

### 路1 · 蒸馏 ALE 榨干收尾(forcing function 诚实证/杀)
- **V5**:GPU 盒 ① `run_ale_gpu.sh` 切 `PILOT_BAILIAN_MODEL=qwen3.7-max`(A/B 试·1 行 env)② 修 complete timeout:加 `ALE_SINGLE_TURN=1`(跳 turn-2 锦上添花·省一半调用)或 raise timeout/retries ③ 只重跑 ~18 道失败/strong=0 的题 + 补 ahc004/ahc014(别重跑全 40)→ 榨到 ~14 clean A 类(当前 12 clean)。
- **soul**:ALE clean A 类落池 → 跑**最干净一次 LOO**(`distill_loo.py --k4`·confound 防护:max_tokens 4096 + expandable_segments + 核 OOM/seq/adapter)。**判定**:仍弱(~0.18)= 坐实 ALE 蒸馏天花板·**不再投 ALE**(诚实杀这条·回护城河副产品)。突变 work = 料量是解。
- 🔴 **不再 9→11→12 小增量**(无梯度已证)。一次榨干 ALE 极限再判。

### 路2 · 第②维 Gap-2 = V5 daemon 真注册(producer 收口第一步·北极星铁律)
- **V5**:daemon 启动自注册(替代 sentinel seed 行):
  1. `POST /api/agent-first/challenge` body `{"capabilities":["code_evolve"]}` → 拿 `challenge_id` + `challenge_prompt`(答案在平台 `CHALLENGE_PROMPTS`·如算术题)
  2. 解 challenge → `POST /api/agent-first/register` body `{name, capabilities, proof_of_capability:"challenge_id:answer"}` → 拿**整数 agent_id + wallet_address + api_key**(限流 3/hour)
  3. daemon 持久化 api_key → 之后 **claim 带 api_key + 真整数 agent_id**(非裸字符串 "nautilus-prime-001")
- **soul/platform**:① 确认 `agent_first_register` 端点 LIVE(已 mount `main.py:560` `/api/agent-first`)② 后续 `fde_dispatch` claim 接受/验证 api_key(Gap-1 鉴权·V5 注册后顺带收口·非阻塞)。
- **意义**:从"1 个 daemon 裸字符串 claim"→"注册自主 agent 真身份"·能力/生存/marketplace 挂真 agent_id·为 Gap-3(N 个 agent 自主产燃料)铺路。

### compass · B 轨 conditional-go(非 rush)
- B 轨两 commit(b799d6b benchmark + 53dce44 access→tier wire)**只在本地·没 push box**。先 ① sync 到 box ② 给 `tier_promotion_driver` 加 `--dry-run`(它改写生产记忆 frontmatter·无 dry-run 是缺口)③ box 9720 corpus dry-run + `eval_recall --mode tier` 拿真 ΔMRR ④ **有正信号再挂 timer·没真 ΔMRR 别挂 daemon**。第②维并行件·不阻塞蒸馏。

### park(成本高·待解锁)
- **路A SWE**:strong 解出率 + 根盘 infra + SWE eval pipeline 未实现 = 三重卡。park·待 Gap-3 放大产量 + 根盘迁 datadisk0 后再说。
- 根盘 50G infra(SWE verify 吃不消)= 投 SWE 前置·V5 迁 docker datadisk0(turf 你·共享盒)。

## 球
- **V5**:路1(ALE qwen+timeout 修+补 2 题→榨 ~14 clean)+ 路2(daemon 真注册拿 agent_id)。
- **soul**:路1 LOO 执行+判定 · 路2 端点确认+claim 接真 id · 协调中枢。
- **compass**:B 轨 sync+dry-run+box A/B(conditional-go)。
- **元**:别再 glm/qwen 银弹叙事(已证伪)。蒸馏 ALE 一次榨干诚实证/杀·真杠杆转 producer 注册化(Gap-2)。

— platform-soul · 2026-06-24(统筹 plan 用户拍板:蒸馏 ALE 榨干收尾[qwen A/B+修 timeout+补 2 题+最干净 LOO·仍弱=杀 ALE] + 第②维 Gap-2[V5 daemon 真注册拿整数 agent_id·北极星 producer 收口]·compass B 轨 conditional-go·SWE/根盘 park)
