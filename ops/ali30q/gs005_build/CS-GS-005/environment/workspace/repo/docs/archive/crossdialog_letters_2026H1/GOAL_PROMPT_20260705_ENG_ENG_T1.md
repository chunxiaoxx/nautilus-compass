# /goal ENG 收敛 · 7/5 接班

## active anchor
1 平台 agent first · 5 不重造 · 3 反 D 维护 · 6 禁真字

## 0. 第一动作(读 4 件顺序不变)
1. `nautilus-core/HANDOFF_20260704_TO_NEXT_SESSION.md`
2. `nautilus-core/FDE_BUSINESS_CHARTER.md`
3. `nautilus-core/LOOP_STATE_SSOT.md`
4. `nautilus-core/genopt_factory/PARKING_LOT.md`

---

## 1. 唯一目标

**产 1 道符合 buyer spec 的 ENG 题目,端到端闭合。**

- 1 道(不 10 不 100)
- 符合 spec = 14 文件 + 9 frontier_eval + verifier 三铁律 + N=3
- 端到端 = baseline 真 → verifier 真 → 大模型真 → trajectory 真入 fde_verdicts → 入飞书派活

失败定义:任一步骤没真活 = 0 闭合,不切换下一道。

---

## 2. 5 步顺序

1. **选模板**:用现有 5 题模板 1 道(JobShop orlib 真在)
2. **修模型接球**:doubao 真接 + 标 trajectory `model: doubao-seed-2-0-pro`(buyer spec §5 允许代理模型)
3. **跑**:写真复跑 H800 `/root/autodl-tmp/genopt/systemd/h800-genopt-runner.sh`
4. **入 fde_verdicts**:POST `/api/platform/fde/verdict` 绑 producer 9000009
5. **入飞书**:POST 派活表 1 row

闭合 = 5 步全 200 + trajectory 文件真写 + verdict 行真在 + 派活 row 真在。

---

## 3. 反掰玉米(6/14 真痛)

只 1 道 = 单一 forcing function。

不可:
- 多道并行 spawn
- 多组件并行 spawn
- 跳步(失败不绕)

只:
- 1 道真跑 + 5 步真顺序 + 每步真验后下一

---

## 4. 6 件硬守

1. n ≥ 12 不动(1 道 = 无 LOO 风险)
2. 易料复证(JobShop 已 ship 不动)
3. 每步真返 ✓ 才下一
4. 改 SSOT 必广播 4 框
5. ship 必 curl/SSH 真验
6. 禁真字(每段 ≤ 3,详 CLAUDE.md)

---

## 5. fallback(每步失败清单)

| Step | 失败改 | 不做的 |
|---|---|---|
| 1 模板 | 换 1 道 | 不写新模板 |
| 2 模型 | 换 doubao | 不 autopilot 编新凭据 |
| 3 .sh | 复用 | 不改 harness |
| 4 fde_verdicts | 真发 1 遍 | 不循环 |
| 5 飞书 | 真发 1 遍 | 不多道 |

任一 Step 真人手 N 次仍失败 → 问 user,不 autopilot 替拍。

---

## 6. 闭合后

1 道闭合 = SSOT 写 `GENOPT_RL_ENG_CLOSED` 锁
等 user 拍下一件,不 autopilot 启第 2 道。

---

## 7. 当前状态(7/4 23:55)

| 件 | 状态 |
|---|---|
| 5/5 verdict 行 | partial |
| 5/5 派活 row | partial |
| doubao 凭据 | ready |
| .sh H800 | ready |
| producer 9000009 | ready |

真阻塞:
- qixuw 拒接 → 换 doubao 路径
- 4 框 inbound 仅 V5 真回 1 次 → 等再回
- soul/fde 真接球 → 等 inbound

---

## 8. 真接球清单

任 1 拍即推:
- soul 框:verify 1 行 UPDATE 真标 external_verified=True
- FDE 框:真起 runner
- V5 框:第 2 轮真接
- compass 框:真接 cloud docs

---

## 9. 新会话第一件

```
1. cat GOAL_PROMPT_20260705_ENG_ENG_T1.md
2. cat /root/autodl-tmp/genopt/factory/operations_research_and_decision_science/JobShop/jobshop_orlib_v1_001/gpt55_trajectory_h800_v7.json | jq .
3. 顺序写真 5 步
4. 每步 curl/SSH 真返 ✓ 才下一
5. 闭合后写真 SSOT 锁
```

---

— 平台 · 7/5 接班 · 1 道真产 · 真合 buyer spec · 不掰玉米
