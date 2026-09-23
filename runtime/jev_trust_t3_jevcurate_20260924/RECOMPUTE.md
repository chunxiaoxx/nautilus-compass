# T3 mini 校准 · 非实现者复算交接(2026-09-24 · 新鲜会话执行)

> 复算员纪律:你是非实现者,只信判据与工件。执行顺序写死,顺序不可换:
> 先盲标落档,再读判据全文与实现者报告。本档不含任何预期读数。

## 坐标(全部在 nautilus-compass 仓)

目录:`runtime/jev_trust_t3_jevcurate_20260924/`

| 文件 | 用途 |
|---|---|
| `blind_pack.json` | 5 行文本+Jev 原始读数,**无真值字段**——步骤 1 唯一允许输入 |
| `PROTOCOL.md` | 判据正本(预注册标注/指标公式/调用规格/开工修正记录)——步骤 3 才许读 |
| `RESULTS.md` | 实现者报告——步骤 4 才许读 |
| `session.jsonl` + `session.jsonl.sig` + `pubkey_jev-1.13.0.txt` | 主批工件 |
| `session_latest.jsonl` + `.sig` + `pubkey_jev-latest.txt` | 对照批工件 |
| `t3_results.json` | 原始读数全集(含实现者预注册标注,步骤 3 后可读) |

## 步骤(顺序固定)

1. **盲标**:读 `blind_pack.json`,对 5 行独立标注:
   - `y_circ`:该行是否含循环推理/同义反复/在前提中预设结论(0/1)
   - `d_depth`:数学严谨度 1-5(1=肤浅/错算,2=缺中间步骤,3=推导可靠
     有标准细节,4=清晰完整分步,5=形式化完美)
   每行一句理由;写 `blind_labels.json`。**落档前禁读 PROTOCOL/RESULTS/
   t3_results.json。**
2. **验签**:用 jev-trust ≥0.2(pip 包)对主批验签,大致:
   `python -c "from jev_trust.receipt import ..."`(用 `pubkey_jev-1.13.0.txt`
   + `session.jsonl` + `session.jsonl.sig`;receipt 模块 KeyPair 按包内源码
   实际接口调用)。结论记 VALID/INVALID。
3. **重算**:此时读 PROTOCOL.md 指标口径,用**你自己的盲标注**+blind_pack
   的 Jev 读数独立计算:noul accuracy@0.70 / Brier / ECE(10桶);depth
   MAE(1-based=0based+1)/ accuracy@3.0 / conf<0.5 行。ECE 桶内 conf
   用 noul 行读数:noul 答案无 conf 字段时以 p 代(与 PROTOCOL 口径同)。
4. **比对**:此时才读 RESULTS.md 与 PROTOCOL 预注册标注,逐行对比;
   分歧行写分歧与双方理由(预注册已列敏感点,以你的独立标注为准判敏感
   口径归属)。
5. **结论**:GREEN=指标与实现者一致或全部分歧可归因于已披露敏感点;
   RED=存在无法归因的数值不一致。写 `RECOMPUTE_REPORT.md`(读数+
   比对+结论+签名建议)。

## 红灯处理

数值不一致时先证伪自己:检查标注口径/公式实现/读数抄录/换算(0-4→1-5
的 +1)是否按 PROTOCOL;确认无误才算实现者 RED。

## 边界

- 不重跑 API(工件已签名,复算读数以 session.jsonl/t3_results 为准)
- 对外交付(issue 回帖)由实现者会话执行,复算员不回帖
- ETA:9/26 12:00 前(向甲方承诺 48h)
