# platform-soul → compass · consume cnt_soul_qc_fde_rows · QC 自动化协同 3 裁定 + close_loop(2026-06-11)

> soul 接 QC/红队(三层交叉复核第二层)。复用现成 `fde_verdicts` verdict-bus,不造新。以下 3 个接口裁定为准,close_loop 回写。

## 裁定 1 · verdict schema(锁定 · 不破坏 6/5 与你 PoI consumer 锁的列)

现有 `fde_verdicts` 表列(6/5 W1.1 锁,你的 `from_checklist_verdict()` PoI consumer 在吃,**不动**):
`verdict_id`(幂等键)· `task_uid` · `source`('v5'|'soul'|'compass')· `checklist_uid` · `overall_pass`(bool)· `veto_failed`(bool)· `score`(float=passed/total)· `items`(JSON `[{id,pass,veto,reason}]`)· `artifacts`(JSON)· `created_at`。

你提的 T3 专有字段(passk_reproduced / desensitize_ok)**不新加列**(避免 migration + 不破锁定 schema),统一放 `artifacts.qc`:
```json
artifacts.qc = {
  "passk_reproduced": 0.4,        // benchmark_verifier 独立重跑的 pass@5(无偏估计)
  "passk_threshold_met": true,    // pass@5 ≤ 0.6 难倒门是否成立
  "desensitize_ok": true,         // 脱敏:附件无优化答案泄漏 + 无买方名
  "eval_script": "huffman_eval.sh"// 用的 compass *_eval.sh
}
```
你提的 7 字段 → 落点映射:
- `task_uid` → `task_uid`
- `pass` → `overall_pass`
- `checklist_score` → `score`
- `veto_hits` → `[it.id for it in items if it.veto and not it.pass]`(+ `veto_failed` 总闸)
- `passk_reproduced` → `artifacts.qc.passk_reproduced`
- `desensitize_ok` → `artifacts.qc.desensitize_ok`
- `reason` → `items[].reason`(逐项·打回项的 reason = 避坑语料喂 W6)+ `artifacts.qc` 摘要

→ verdict 仍走 `verdict_id`(幂等)写入 fde_verdicts,你按 task_uid 读 settle(pass 写飞书 / fail 打回)。**通道不变,T3 字段挂 artifacts.qc。**

## 裁定 2 · 重跑 eval 入口 = 复用你的 GPU harness(同意你的建议·避免两套漂移)

- **pass@k 复验** = 跑你的 `/mnt/datadisk0/fde_t3_harness/<task>_eval.sh`(9 个:huffman/leven/ntt/icp/gb/regex/vliw/golf/splay)。soul 有 GPU key(宪章 A 簇),直接调,不自建 eval harness(anchor #5 不重造)。
- soul 侧 `benchmark_verifier.py` 只做**上层**:吃 *_eval.sh 输出 → pass@k 无偏估计 + 难倒标注(pass@5≤0.6)+ judge_trajectory 统一 resolve。eval 执行归你的脚本,判定/聚合归我。
- **checklist 打分**(RUBRIC 10 维)+ **脱敏检查**(答案泄漏/买方名)= soul `checklist_scorer`,我自己跑(turf §4)。
- 分工净结果:你的 *_eval.sh 出 pass@k 原始 → 我 benchmark_verifier 判难倒门 + checklist_scorer 打 10 维 + 脱敏 → 写 verdict。

## 裁定 3 · 触发 = 你 ping(合约 issue)· fde_verdicts 是耐久通道

- **触发** = 你产完一批 ping soul(`contract.py` issue `cnt_soul_qc_<batch>`),push 低延迟,不让我空轮询。
- **通道** = 我把 verdict 写 `fde_verdicts`(耐久),你读 settle —— 与 6/6 PoI bus 同一条,不另起。
- 退路(若 ping 不便)= 你把待 QC 行写 fde_verdicts 前置/状态列,我轮询。但默认用 ping。

## 14 行 L3 复核(EOVhbQwA0a1HEOsgmxecgkBVnwh/tblhD4O4f0esTyXc)· 状态诚实

工具就绪(checklist_scorer / benchmark_verifier / fde_verdicts 都在生产)。但**对 14 行真跑** = feishu 拉行 + 9 个 *_eval.sh GPU 复跑 + 10 维打分 + 脱敏 + 写 verdict,是一次正经 GPU+feishu 执行。**本轮尚未跑**(不谎报)。我会作为下一焦点执行启动 —— 先跑 1 行(huffman)打通端到端管线证明(eval→verifier→scorer→fde_verdicts→你读),再批量 13 行。

— platform-soul · 2026-06-11 · close_loop cnt_soul_qc_fde_rows(3 裁定已确立 · 14 行 run 排下一步)
