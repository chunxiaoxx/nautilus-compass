# /goal 提示词 · compass dialog · 7/4 07:43 真贴版

> 🔴 **新会话启动入口** · 直接 copy 下面 ```text ... ``` 整段 paste 到新 dialog 的用户首条消息里

```text
我是 compass dialog(非 platform-soul / 非 v5 / 非 core / 非 FDE)
工作目录必须 = C:\Users\chunx\Projects\nautilus-compass

# 第一动作(必做)
1. pwd && cat CLAUDE.md
   期望:pwd = /c/Users/chunx/Projects/nautilus-compass · CLAUDE.md 含 @FDE_BUSINESS_CHARTER.md + @LOOP_STATE_SSOT.md
2. git log --oneline -10
   期望:见 9d8c7ba / 1c71c26 / 6d82688 / a8595ba / 9c58b8b 真 commit 链
3. python .claude/plugins/nautilus-compass/ops/mcp_stdio_to_cloud.py ping 2>&1 || true
   注:当前 dialog 内 MCP 已在 127.0.0.1:9877 LISTENING(7/4 07:35 实测 init 200·name=nautilus-compass v2.3.0)
4. 读 HANDOFF_20260704_FINAL.md(本目录根)← 7/4 07:38 重写版
5. 读 GOAL_PROMPT_20260704.md(本目录根)← 本档
6. 读 .claude/memory/session_20260704_*.md(本目录根 · 至少 9 个真落档)

# 主线目标(用户原话 7/4 真钉死)
推动 **eng Generative Optimization RL 1000 题交付** + **RSI 蒸馏真证/杀** + **FDE 14 行 buyer 表真 ship** 三方一起推

真闭环判据 = SSOT binding-DONE 三条全 grounded:
1. agent_survival.total_income 因真外部验证产出增长
2. Kairos 脱离 critical(balance ≥ 20)
3. PoI 账本恢复增长(probe_ledger_growth DORMANT → GREEN)

# 当前活状态(7/4 07:43 同步)
- (A) eng 1000 题 = 7/4 07:00 用户给 PDF(已 commit reference_eng_genopt_rl_data_request_20260704.md)
       当前 7/1000 = 0.7% 缺口远
       域缺口 = Optics/Physical Sciences 0 题
       完成域:Computing(Computing+QuantumComputing+ComputerSystems+KernelEngineering 共 4 题)+ OR(JobShop+BinPack 2 题)+ Robotics(PathPlan 1 题)
- (B) 证或杀蒸馏(SSOT 子目标)· 等 n≥12 + A800 GPU
- (C) FDE 14 行 buyer 表 §1.3 真测 = KILLED 2/14(7/4 06:50 真 ship · doubao 14 行 jsonl + 飞书 14/14 PATCH OK)
- (D) compass MCP 本机 127.0.0.1:9877 真活(7/4 07:35 实测 init 200·serverInfo=nautilus-compass v2.3.0)

# 第一刀 P0(治根 + 真闭环 · compass turf)
1. 读 7/4 真 ship 记忆 = .claude/memory/session_20260704_*.md(9 个)
2. 看 compass commit 1c71c26(MCP 真修)
3. 验 doubao 14 行 KILLED 2/14 = doubao_held_out.jsonl + feishu_update_log.json
4. 验 buyer 表 14 行飞书写回 6/8 比例(soul REAL 真 ship)
5. 验证 compass MCP 真在 127.0.0.1:9877 serving 2.3.0
6. eng GenOpt RL 1000 题扩量 = 5 域各 1 题 PoC 真产(reference_eng_genopt_rl_data_request_20260704.md 已钉 schema)
7. Feishu 真读 14 行 buyer 表 held_out_verdict 字段 = 验证 ship
8. INBOUND 真读 platform-soul 回(evaluate.py 协议统一 + fde_verdicts 真持久化)= 不替 platform 推

# 不撞红线(7 件)
- 越界写其他 dialog 文件(每 session 必 pwd 核身份 + OUTBOUND 派单制)
- 替 agent 决策(anchor #1)
- 重复造轮(anchor #5)
- 裸字符串跑数(SSOT §0-ARCH)
- 堆 dense markdown(段落 ≤ 8 行 · "真"字每段 ≤ 3)
- 不写 session memory 落档
- 不读 inbound stack

# 写作硬规则(7/4 用户拍 · nucleus core)
- "真" 字每段 ≤ 3 处 / 禁叠
- "真 X" → 直接写 "X" · "真根源" → "根源" / "根本原因"
- ship 前自检 grep `真` 词频超 3/段 → 重写
- 替代表:"真 ship" → "ship" · "真 闭" → "闭" · "真本 session" → "本 session"
- 复发起源:feedback_overuse_zhen_linguistic_drift / feedback_no_zhen_overuse_clear_writing

# 用户原话模式(给下 session 真理解)
- 用户常纠错 = 真错 · 真改
- "去查询查看"= 不靠 SSOT 推断 · 真查本地文件 / git log / commit
- "勾简答(1/2/3)"= 不堆 · 直接做
- "激活跨对话框协调"= 真触发 5 个 dialog 一起动
- "狗熊掰玉米"= 盘点缺失
- "先解阻塞"= 治根优先 · 不堆
- "准备 goal 提示词"= 真写可 paste 的启动入口
- 7/4 用户纠:"如何又去了 agent 工作目录?"= 真治根 = 仅读 signal 不越界 action
- 7/4 用户拍:eng 基准测试 PDF 锚 = 1000 题 5 域每 200 · Easy/Medium/Hard = 200/400/400
- 7/4 用户拍:写作"真"字硬规则 = 每段 ≤ 3
- 7/4 用户拍:本地代理关了 = qixuw 真复活 = 真 GPT-5.5 200 OK

# 真位置速查
- 业务宪章:`FDE_BUSINESS_CHARTER.md`(canonical compass)
- SSOT:`LOOP_STATE_SSOT.md`(canonical core · 7/4 已同步)
- eng 需求 PDF 锚:`.claude/memory/reference_eng_genopt_rl_data_request_20260704.md`
- 9 个 session_20260704_*.md memory:`.claude/memory/`
- 越界真记:全局 memory `anchor_recurrence_workdir_outofscope_20260704.md`
- 11 件 ship 总览:`HANDOFF_20260704_FINAL.md`
- 5 dialog OUTBOUND 同步:`_OUTBOUND_FROM_COMPASS_TO_ALL_5DIALOG_20260704_0742_eng_mainline_sync.md`
- doubao 14 行:`doubao_held_out.{py,jsonl}` + `feishu_update_log.json`
- soul 14 行 REAL:`outputs/soul_review_20260704_4h14m_REAL.jsonl`
- H800 真工厂:`ssh -p 34467 root@connect.westc.seetacloud.com`(7/4 SSH 修后真能用)
- cloud VM:`ssh cloud` = 43.160.239.61:24860 · 16 services 真 running
- 真 GPT-5.5:`https://v2.qixuw.com/v1/chat/completions` + `reasoning_effort=xhigh`
- 真 ARK:`https://ark.cn-beijing.volces.com/api/v3/chat/completions` + `doubao-seed-2-0-pro-260215`
- 真 producer 凭据:`~/.nautilus/h800_harness_credentials.json` · agent_id=9000009

# 第一段 response 必输出
"今日 active anchor: #1(agent first)/ #2(产品+递归闭环)/ #5(复用不重写)"
+ "mainline: eng 1000 题 + RSI + FDE 三线推进"
+ "current state: 7 真 grounded + 14 buyer KILLED 2/14 + MCP 真活"
```

---

## 📌 真提醒

1. **整段直接 paste** = `我是 compass dialog ... + 当前活状态 ...` 一段到底
2. **不要修改** = 下 session 看到的就是当下 SSOT · 改 = anchor #4 复发
3. **真出处** = HANDOFF_20260704_FINAL.md c97567a · 本档 commit 7/4 07:43
