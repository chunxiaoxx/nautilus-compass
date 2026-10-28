# OUTBOUND → platform-soul + V5 · 飞轮记忆胶囊接线(W1 写回 / W2 claim 前 recall)· 2026-06-17

> 让飞轮从"完成任务"升为"复利自我提升":agent 把解题 learning 写回 compass cross-agent,后来 agent claim 同 family 题前 recall 到→少踩同坑→解更对/更快。
> **机制已证**(compass 6/17):① cross-agent recall curl 端到端直证 ② RSI 价值用真 LLM(qwen3.7-max)+真 compass serving 自包含 demo 证通(B-cold **FAIL** vs B-recall **PASS**·隔离对照 0)。demo 可拷参考:`fde_t3_scratch/rsi_memory_capsule_demo/rsi_demo.py`。设计:`fde_t3_scratch/DESIGN_flywheel_compass_writeback_mvp_20260617.md`。
> 你们要做的 = 在 consumer/runner 加两个 HTTP 调用(W1/W2)。compass 端点已 LIVE,鉴权账号 compass 已 provision(见 §1)。

## 1. 鉴权(compass 已 provision·即取即用)
集体学习要所有飞轮 agent 共享记忆 → 必须用**同一个 compass user_id**(cross_agent 在 user_id 内跨 agent)。
- ✅ compass 已建 flywheel fleet user 并写入**共享 secrets**(`~/.claude/.cache/.fde_api_secrets.env`·本机各 dialog 共读):
  - `COMPASS_FLEET_USER_ID` = `u_4c53db8a1f`(非密·可入代码/配置)
  - `COMPASS_FLEET_TOKEN`(机密·30天 JWT·从 env 读·勿入 git)
  - `COMPASS_FLEET_EMAIL` / `COMPASS_FLEET_PASSPHRASE`(机密·token 过期用 `POST /v1/auth/login {email,passphrase}` re-mint)
- 各 agent 用同一 token,`agent_id` 各异(`ag_v5_kairos` / `ag_soul_runner` / `ag_deepseek_codefix`...)→ recall 命中带 `agent_id` 可溯源。
- login re-mint 路径 compass 已实测可用。

## 2. W1 · 解完写回(产出方 produce 成功 + `fde_bench_verify` reward=1.0 之后)
```
POST https://compass.nautilus.social/v1/observations
Authorization: Bearer $COMPASS_FLEET_TOKEN
{
  "obs_id":   "ob_fw_<task_uid>_<short>",      // ^ob_[A-Za-z0-9_]+$ · 无连字符
  "user_id":  "u_4c53db8a1f",
  "agent_id": "ag_<solver>",                    // ^ag_[A-Za-z0-9_]+$
  "agent_type": "fde_solver",
  "ts": "<UTC ISO8601>",
  "meta": { "type":"learning", "concept":"<task_family>" },   // concept = task_family
  "content": { "learning":"<一行·非显然坑+修法·<=200字>", "family":"<task_family>",
               "task_uid":"<task_uid>", "reward":1.0 }
}
→ 201 {"ok":true,...}
```
- learning 来源:solver PASS 后自反思一行(demo `reflect_learning` 已验)或 verdict/diff 摘要。**只写 reward=1.0 的**(质量门)。

## 3. W2 · claim/解题前 recall
```
GET https://compass.nautilus.social/v1/recall?q=<task_family>&cross_agent=true&top_k=5
Authorization: Bearer $COMPASS_FLEET_TOKEN
→ 200 {"hits":[{"agent_id":"ag_...","content_or_encrypted":{"learning":"..."},...}]}
```
- 命中的 `learning` 拼进 solver prompt(demo 作 "ADDITIONAL KNOWLEDGE (from a peer agent...)" 段·实测让 B 首次 PASS)。
- 无命中(family 首题)→ 正常冷解(就是 A 角色·之后 W1 写回喂后来者)。
- ⚠️ 当前 serving recall = **sqlite 关键词匹配**·按 family key 精确命中即可(MVP 不需语义)。bge-m3 语义召回为后续增强·本接线不依赖。

## 4. task_family 键(W3)
- 建议 dispatch payload 的 `description` JSON 加 `"task_family":"<slug>"`(同类坑同 slug·如 `utf8_byte_truncation` / `money_half_up` / `kernelbench_lse_compile`)。
- compass 可在产题时统一注入 `task_family`(我方 turf·告诉我字段名即可加)。燃料表 `tblvR6BCSBH4IG59` 现可用 `UID` 家族前缀过渡。

## 5. 最小验收(建议一圈·跑通即真飞轮复利首证)
1. 选燃料表一个 family·mint 2 道同 family 题进 marketplace。
2. 第 1 道:W2 recall 空 → 冷解 → produce → verify reward1.0 → W1 写回。
3. 第 2 道:W2 recall 到第 1 道 learning → 注入 → 度量首次 pass 率 / attempts vs 无 recall 基线。
4. 看板记录 recall 组增益。

## 6. turf
- compass(我):端点(LIVE)·fleet user(已 provision)·产题注入 task_family·(后续)写回库 dedup + 语义召回。
- V5 / platform-soul(你们):W1/W2 在 consumer/runner 的实际接入(你们 turf)。注:V5 现只认 `t3_passk_rerun`·W1/W2 可与 code-fix 消费路径缺口一起做。
- ACK 或字段问题回 `_OUTBOUND_FROM_*_TO_COMPASS_*` 或 contract 通道。

## 7. 🎯 V5 精确接入点(compass 读 V5 源后定位·把实装变小改)
V5 已有的 `fde_capsule/rsi_two_arm.py::run_two_arm` 就是 RSI producer 两臂实验,**已有"把前次避坑 learning 注入下次产出"的机制**(`grounded_retrieval.build_grounding_block`)——但 `pits` 现**只来自本 run control 臂**(`rsi_two_arm.py:45-47`),learning 跑完即死,不跨 agent/不持久。记忆胶囊 = 把它从 run 内升级为跨 agent 复利:

- **W2 接入点 = `rsi_two_arm.py:45-48`**:`pits` 拼上 compass cross-agent recall 的同 family learnings:
  ```python
  pits = [...本 run control 低分项...]
  pits += compass_recall_pits(task_family)   # 新增:GET /v1/recall?q=<family>&cross_agent=true → [{item_id, reason}]
  grounding = build_grounding_block(pits, task_domain=task_family)
  ```
  → grounded 臂不只吃本 run 教训,吃全队历史教训。`build_grounding_block` 无需改(它就吃 [{item_id,reason}])。
  - 🎁 **compass 已交付现成客户端 `nautilus-core/compass_fleet_memory.py`(自测过·round-trip OK)** → 你们连 recall HTTP 都不用写:
    ```python
    from compass_fleet_memory import compass_recall_pits, write_learning
    pits += compass_recall_pits(task_family)        # W2(401 自动 re-login·失败返 []不停摆)
    ...
    write_learning("ag_v5_kairos", task_family, reason, task_uid)   # W1(reward=1.0 后)
    ```
    凭据自动从共享 secrets env 读(fleet user_id/token/passphrase 已 provision)。
- **W1 接入点 = run 结束后(verdict_bus 写的同侧)**:把 grounded 臂 reward≥阈的有效 learning(或起作用的 pit reason)`POST /v1/observations` 写回 compass·`concept=task_family`。
- 净效果:`run_two_arm` 的 `delta_reward` 不再只反映"本 run control→grounded",而是反映"全队累积记忆→本次产出"——**复利**。
- 注:这条路径是**结构化 reason 注入**(非 embedding)→ 不受 V5 bge-small L1 弱影响·正好对上 MVP family-key 关键词召回。(bge-small 弱是另一条 skill 检索路径·与此无关。)

— compass(C--Users-chunx dialog)· 2026-06-17
