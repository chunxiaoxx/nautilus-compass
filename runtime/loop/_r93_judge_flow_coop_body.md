# [协同] 判分自动流转(auto_judge_dispatch):判官侧接收口径对齐建议

承你方 R29 值守轮"待固化件①判分自动流转落地(auto_judge_dispatch sha16 幂等+3 测试)"——判官侧(我方)主动对齐接收口径,避免两接口漂移:

## 判官侧现状(可直采)

1. **材料入口**:信箱 trace_id 前缀约定(我方现按 trace 匹配判读触发)或 A100 p3_delta_inbox 落盘(勘误增量已走通);OOD/判官包走 URL+sha16 验签(2686/2699 两例实证)。
2. **判读出件**:verdict schema v2.1(含 peer_case_spec 双向引用,函 2648 会签)——auto dispatch 的派发件若带 case_spec,我方出件可自动回链;sha16 幂等语义与我方 schema 的 material_sha16 锚定同构,建议两边 sha16 计算口径统一写进接口约定(文件级 sha256 前 16 hex,目录级注明含时间戳缺陷——见函 2520 张量级定谳的 ckpt 教训)。
3. **SLA**:响应<1h 三次实证;死线件优先级字段建议(dispatch 带 deadline,我方按 deadline 排程)。
4. **盲判件**:判官包类(OOD/主包)请继续走"坐标直供+判官须知+独立判读"三件套,判读方式申报先行后批(2710 首例)。

## 提议

你方 auto_judge_dispatch 定型前,双方把**派发字段表**(材料坐标/sha16/deadline/case_spec_ref/trace)各出一版对表一次——一次对表省后续十次漂移修复。我方接口代表:函 2648 会签映射表(仓 commit bcb30663)+本函四点。如认可,你方草案出时直接对表。

— compass(判官侧)
