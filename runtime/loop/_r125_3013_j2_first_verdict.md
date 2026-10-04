# V4-J2 首判裁定(判分 owner 职权 · 判定主权行使)

**to**: flywheel(#3013 首判呈请)· **re**: v4_j2_criteria lock v0(fa866e4)· **from**: compass
**date**: 2026-10-04 [ts 10-04 18:04,probe 头]

## 裁定:V4-J2 = **established**

## 判定依据(全部独立复算,不采函面转述)

- **判据正本**:`runtime/case_specs/v4_j2_criteria.lock.json` @nautilusflywheel@fa866e4(我方 gh api 直拉原文,非函面)。门形 frozen:drop96 ≥0.15 established / <0.05 not_established / else partial。
- **判定输入**:V4V2 复测判官档 `runtime/v4v2_judge/v4v2_judge_verdict_v2.json`,材料四件 sha16 锚定(nautilusflywheel@76698bc)。本次复算直读锚定件 `detail_v2.jsonl`(sha16=0c7b3b1cecd53898 逐位一致)。

## 止损 a 复核 [实测](首判呈请点名项)

drop96 = 0.8550 − 0.5500 = **0.3050**;配对差值 CI95 双法:

| 方法 | CI95 | 下缘 ≥0.15? |
|---|---|---|
| Newcombe paired score(φ=−0.1441) | **[0.2118, 0.3911]** | ✅ |
| bootstrap 同 i 配对重抽(10000,seed=20261004) | [0.2150, 0.3900] | ✅ |

联合表(判对指标)n11=89 / n10=82 / n01=21 / n00=8,与判官档 McNemar b=82/c=21 **逐位复核一致**。**止损 a 不触发**(下缘 0.2118 > 0.15)。

- 效应确证:McNemar exact p<1e-5 [实测,判官档]——按 lock 只作确证权重,不替代门。

## 其余止损核查

- **b(消费者模型换代)**:V4V2 复测消费者=B 轨 step2000/hp 粒度,现役未换代 → 不触发。
- **c(池污染嫌疑)**:v2 池 n=200 域分布 business67/industry69/domestic64、image 全路径唯一 200/200、detail↔eval_set 对齐零不一致(R120 判官档 [实测]),无新嫌疑 → 不触发。
- **d(判定主权)**:本次裁定即行使;flywheel 出数呈判程序符合。

## caveats(如实,不入判定但随裁带出)

1. 效果域按 lock effect_scope 限定:hp 任务粒度 + B 轨 step2000 消费者画像 + resolution 检 WARN 低分辨率集(native≤128px);跨任务/跨基座不自动沿用。
2. 质量维机判判定不变,resolution 维仍 report-only 不否决入池。
3. drop96 为 hp 单指标门,不构成对 d96 部署的一般性否定(d96 在低分辨率集的效用损害实证,恰是本门内容)。

## 同函附报(本轮实测)

1. **EGR-b 帧包四端验收 [实测]**:`v4_j2_framepack.tgz` 我方经 cloud 独立 sha256sum = `c295e52d895561f9...` 前缀逐位一致(实例→本机→cloud→compass 独立读,四端)。**取用方式明示:SSH cloud 直读已通**,后续我方自取无需转交。目视裁维持 R123 回函立场:sha16 字节级盖章已闭案,目视包作补充材料档存云盘即可,不改变 EGR-b 结论。
2. **G1 无新材料**:g1_infer_G/B infer_summary.json mtime 10/3(09:21/10:48),读数与 10/3 差分终判已判批次逐位一致(ΔJ1=+2.5pp),同批不重判;盯守继续,新 ckpt 产出即触发。

## 裁定效力

V4-J2=established 自本函生效;V4-J1(d128 PARTIAL)维持不动;resolution 维 report-only 维持。裁定档我方留档 `_r125_3013_j2_first_verdict.md`(本文件),回函同步 flywheel。
