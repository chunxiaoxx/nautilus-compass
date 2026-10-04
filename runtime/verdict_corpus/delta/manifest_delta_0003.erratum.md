# 勘误注 · manifest_delta_0003 账实差(2026-10-04 R138 记)

**差异**:manifest_delta_0003.json 记 n_new=4,但 delta_0003.jsonl 现存 **3** 条(E3/E4/S6)。

**事实**:
- A 案交付件(absorbed/p3_delta_v5_20261003.samples.jsonl)10 条中 eligible=True 共 4 条:E3/E4/S2/S6。
- 现存 3 条缺 **errata_S2_m1-milestone-attribution**(domain=state_narrative,truth=fail,内容=compass M1 归因叙事勘误)。
- S2 不在指纹账(accepted_hashes.json)——移出时指纹同步清除,manifest 未同步。
- 留存件 S6 的 domain 同为 state_narrative——移出 S2 留 S6 的规则依据无法从现存证据确定(delta_0003 未进 git,无考古链)。
- S2 原件在 absorbed 完整保留,无丢件。

**处置**:不改 manifest(追补不改史);本注 accompany。upgrade_path=前会话 transcript 溯源(jsonl c62a754e… 前段)可定死因;或按 10/4 拍板在 p3_delta 白名单门新增 domain 门槛(有 domain 且非判读域→拒,向后兼容不追溯),此后同类差异不再产生。

**影响评估**:delta 计数口径=以 jsonl 文件行数为准(3 条),manifest n_new=4 作历史账留痕;对 200 门进度无实质影响(33/200)。
