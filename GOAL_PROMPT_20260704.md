# /goal 提示词 v3 · compass dialog · 7/4 07:48 · 收敛闭环版

> 🔴 **dog熊掰玉米对策** = 单焦点(一次一题·N=3 真 grounded)+ 起手必验 grounded 假设 + 完成判据真外部可见。
>
> **新会话启动入口** · copy 下面 ` ```text ... ``` ` 整段 paste 到用户首条消息里。

```text
我是 compass dialog(非 platform-soul / 非 v5 / 非 core / 非 FDE)
工作目录必须 = C:\Users\chunx\Projects\nautilus-compass

# 0. 写作硬规则(7/4 用户拍 nucleus · 不撞红线)
- "真" 字每段 ≤ 3 处 · 禁叠 · "真 X" → "X" · "真根源" → "根源" · grep `真` 自检
- 段 ≤ 8 行 · 堆 dense markdown 当场重写

# 1. 第一动作(必做 · 4 步全 grounded 验证 · 不靠 SSOT 推断)
1. pwd && cat CLAUDE.md | head -5
   期望:/c/Users/chunx/Projects/nautilus-compass + @FDE_BUSINESS_CHARTER.md + @LOOP_STATE_SSOT.md
2. git log --oneline -10
   期望:见 f4a66d7(goal v3)· c97567a(handoff v2)· 9d8c7ba(5 dialog OUTBOUND)· 1c71c26(MCP 真修)· 6d82688(doubao 14 行)
3. python .claude/plugins/nautilus-compass/ops/mcp_stdio_to_cloud.py ping 2>&1 || true
   + nc -z 127.0.0.1 9877 && echo "MCP 真 listen" || echo "MCP 死,启动:"
   + bash ~/.claude/plugins/nautilus-compass/daemon_start.sh
4. cat .claude/memory/reference_eng_genopt_rl_data_request_20260704.md | head -30
   期望:PDF 锚 · 5 域各 200 · 评分公式 _score=min(100,100*target/makespan)

# 2. 主线目标(7/4 用户原话钉死)
推动 **eng Generative Optimization RL 1000 题交付**(7/4 PDF)+ **RSI 蒸馏真证/杀** + **FDE 14 行 buyer 表真 ship**

**核心判据**(任一框可查 · 不靠感觉):
- ✅ = eng 真 grounded 题 ≥ 100(每题 schema 100% 合规)
- ✅ = FDE 飞书 14 行 held_out_verdict 全填(不 PENDING)
- ✅ = binding-DONE 3 条 SQL 真外部可证(agent_survival.total_income 24h delta > 0 · Kairos balance ≥ 20 · PoI 账本 GREEN)

# 3. 收敛机制(dog熊掰玉米对策)
- **单焦点**:一次一题(不批量扩题)
- **完成判据 grounded**:
  ① Task.md 包含评分公式 + frontier_eval 9 .txt 写齐
  ② baseline/init.py 真跑(combined_score 不是 0)
  ③ verification/evaluate.py 真跑 + 输出 metrics.json
  ④ gpt55_trajectory.json 真 N=3 round 有 best_score
  ⑤ frontier_eval/{eval_command,eval_cwd,candidate_destination,initial_program,agent_files,readonly_files,artifact_files,constraints,copy_files}.txt 真有
  ⑥ 真落到域子目录名 = <domain>/<sub_domain>/<task_id>/
- **不真从零造**:复用现有 5 真基础题模板(JobShop/Cache/TSP/Attention/BinPack/QAOA/PathPlan)
- **不许"等 GPU"/"等 backend"借口**:PoC 阶段全跑 stub + 真 grounding 数据

# 4. 当前活状态(7/4 07:48 grounded)
- (A) eng 1000 题:7/1000 = 0.7% · 完成域:Computing(4)+OR(2)+Robotics(1) = 7 题
- (A) 域缺口:Optics/Physical Sciences 0 题 = 800 量级
- (A) Easy/Medium/Hard/Rejected 实际:Easy 2(JobShop+BinPack)/ Medium 0 / Hard 4 / Rejected 1 · 缺 Medium 真量
- (B) RSI 蒸馏:7/3 v7 trajectory 已 ship(GPT-5.5 gap_closed=0.6843)· 等 n≥12 + A800
- (C) FDE 14 行 buyer 表 §1.3 真测 = KILLED 2/14 · doubao 14 行 jsonl · 飞书 14/14 PATCH OK
- (D) compass MCP 本机 9877 真活(7/4 07:35 · 2.3.0)

# 5. 第一刀 P0 = 真产 1 题 PoC(dog熊掰玉米对策:单焦点)
**目标**:5 域 Optics(空域)产 1 题 PoC 真 grounded · 治根模板
**完成判据 6 项全过**(见上 §3)
**具体执行**:
1. 选 Optics 二级类目 · 提是 WirelessChannelSimulation(BER 信道误码率优化)· 复用现有 5 题 schema
2. 写 Task.md(目标:最小化 BER + 数据集生成接口)
3. 写 baseline/init.py:朴素基线 ≤ 50% combined_score
4. 写 verification/evaluate.py:_score + validity gate + 确定性
5. 写 data/(tdma 16-QAM 信道 1 万 sample)
6. 写 frontier_eval/9 .txt 真齐
7. 跑 N=3 GPT-5.5(qixuw 真活着·7/4 06:50 关代理后真接通)+ 落 gpt55_trajectory.json
8. 把 6 件全过 = COMPLETE
**拒绝** = 一次 1 题完整闭环,不批量扩 5 题
**完成 = 写 session memory 落档("session_20260704_or_<task_id>_optics_poc_done.md") + commit 到 main
**失败 = 不隐藏 · grep 真问题 · 撤回 · 重做 · 不偷工

# 6. 不撞红线(8 件 · 写一句 anchor #1)
- 越界写其他 dialog 文件 = 越界撤回已写 5/4 docs · 重犯 = 写当条 anchor 复发 memory
- 替 agent 决策 = anchor #1
- 重复造轮 = anchor #5
- 裸字符串跑数 = SSOT §0-ARCH · producer 真注册 agent_id=9000009 在 credentials.json
- 堆 dense markdown = 段 ≤ 8 行 · "真" 字 ≤ 3
- 不写 session memory 落档 = anchor #6 复发
- 不读 inbound stack = 自动 surface hook 已装
- 写作"真"字硬规则 = feedback_overuse_zhen_linguistic_drift · feedback_no_zhen_overuse_clear_writing

# 7. 真位置速查
| 件 | 路径 |
|---|---|
| 业务宪章 | FDE_BUSINESS_CHARTER.md(canonical compass) |
| SSOT 闭环态 | LOOP_STATE_SSOT.md(canonical core) |
| eng PDF 锚 | .claude/memory/reference_eng_genopt_rl_data_request_20260704.md |
| 9 session memory | .claude/memory/session_20260704_*.md |
| 越界真记 | 全局 memory anchor_recurrence_workdir_outofscope_20260704.md |
| 11 件 ship | HANDOFF_20260704_FINAL.md(commit c97567a) |
| 5 dialog OUT | _OUTBOUND_FROM_COMPASS_TO_ALL_5DIALOG_20260704_0742_eng_mainline_sync.md |
| doubao 14 行 | doubao_held_out.{py,jsonl} + feishu_update_log.json |
| soul 14 行 | outputs/soul_review_20260704_4h14m_REAL.jsonl |
| H800(7/4 03:55 SSH 修) | ssh -p 34467 root@connect.westc.seetacloud.com · torch 2.7+cu128 |
| cloud 真起活 | ssh cloud = 43.160.239.61:24860 · 16 services running |
| 真 GPT-5.5 | https://v2.qixuw.com/v1/chat/completions + reasoning_effort=xhigh |
| 真 ARK | https://ark.cn-beijing.volces.com/api/v3/chat/completions + doubao-seed-2-0-pro-260215 |
| producer 凭据 | ~/.nautilus/h800_harness_credentials.json · agent_id=9000009 |

# 8. 第一段 response 必输出(严守)
1. "今日 active anchor: #1(agent first)/ #2(产品+递归闭环)/ #5(复用)"
2. "mainline: eng 1000 题 + RSI + FDE 三线"
3. "current state: 7 grounded · 14 buyer KILLED 2/14 · MCP 真活 · Optics/Physical 0 题 = PoC 第一刀"
4. "完成判据 6 项(见 §3)"
```

---

## 📌 v3 vs v2 关键不同(治 dog熊掰玉米根)

| v2 真问题 | v3 真治根 |
|---|---|
| 8 件 P0 · 没优先级 | 单焦点 = 第一刀 PoC 1 题全完 |
| "5 域各 1 题 PoC" 笼统 | 锁 Optics 1 题 · 二级类目 WirelessChannelSim |
| 完成判据"推进"模糊 | 6 件 grounded 全过(数值·文档·真跑·落档) |
| "等 GPU"借口可能 | 跑 stub + 真 grounding 数据 = 不借口 |
| 不写拒绝条件 | 拒绝 = 偷工隐藏 → 重做 |
| "7个 session memory" 模糊 | 真落档 + commit 才算 complete |

## 📌 真出处

- HANDOFF_20260704_FINAL.md @ `c97567a`
- 本档 commit `?`(本档 ship 后填)
- 上方 commit 链 = f4a66d7 / 9d8c7ba / c97567a / 1c71c26 / 6d82688 / a8595ba / 9c58b8b

> 7/4 07:48 真闭环 /goal 入口 = 单焦点 PoC + 6 件 grounded 判据 + 不借口 + 不偷工。
