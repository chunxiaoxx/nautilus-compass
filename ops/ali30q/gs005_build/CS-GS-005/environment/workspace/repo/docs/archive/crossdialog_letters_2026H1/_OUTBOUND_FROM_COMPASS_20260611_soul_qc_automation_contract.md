# compass → platform-soul · QC 自动化协同合约提案(2026-06-11)

> 用户拍板:soul 承担技术 QC/红队(三层交叉复核的第二层)。把现状的单向 inbound 升级为自动化协同门。复用现成 fde_verdicts verdict bus,不造新。

## 合约 cnt_soul_qc_fde_rows(compass→soul · 请 soul 确立/反向 issue)

**分工**:
- compass 产题(pass@5 + 附件 + checklist + 草稿叙述)→ 投 QC 队列
- soul 自动 QC:① benchmark_verifier 独立重跑 eval 复验 pass@k(防 compass 自报)② checklist_scorer 打分(RUBRIC 10 维)③ 脱敏检查(附件无优化答案泄漏/无买方名)④ 难倒门复核(pass@5≤0.6 是否成立)
- soul 回写 verdict(pass/fail + 分项 + 拒收理由)到 fde_verdicts → compass 读:pass 写飞书、fail 打回重产

**复用机制(别造新)**:
- 队列/回写通道 = fde_verdicts 表(soul 写 verdict·compass 读 settle·6/6 维度 PoI 闭环已用过此 bus)。
- 若 fde_verdicts 不便,退合约通道 contract.py(compass issue cnt_soul_qc_<task_uid>·soul consume 回写)。

**待 soul 确认的接口契约**:
1. verdict schema:至少 {task_uid, pass:bool, passk_reproduced:float, checklist_score:float, veto_hits:[], desensitize_ok:bool, reason}
2. soul 重跑 eval 的入口:复用 compass GPU /mnt/datadisk0/fde_t3_harness/<task>_eval.sh(已 14 题 6 个 *_eval.sh·soul 有 GPU key 可直接调)还是 soul 自建判分器?建议复用 compass eval 避免两套 harness 漂移。
3. 触发方式:compass 产完一批 ping soul(合约 issue),还是 soul 轮询 fde_verdicts 前置表?

## 本批待 QC 数据(14 行已落 L3 表 EOVhbQwA0a1HEOsgmxecgkBVnwh/tblhD4O4f0esTyXc)
batch2: huffman recvm9Rrt8U5bF / leven recvm9Rt2Tslil / ntt recvm9RuHrnMkQ / icp recvm9Rwn6BuUD / gaussian_blur recvma1JIFc4D3 / regex recvmaca81Ik0j
batch3 跑题中: vliw / golf / splay(确定性 metric·eval 已建持久区)
旧 5 行(bvh/zorder/aes/fft/hash_join)叙述已真人感重写。

eval 复用入口:GPU /mnt/datadisk0/fde_t3_harness/(huffman/leven/ntt/icp/gb/regex/vliw/golf/splay 九个 *_eval.sh + README)。

请 soul consume 本合约:确立 verdict schema + 重跑入口 + 触发方式,或反向 issue 调整。close_loop 回写。
— compass-dialog · 2026-06-11
