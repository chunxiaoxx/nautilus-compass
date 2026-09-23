# T3 mini 校准结果 · jev-curate reasoning-math(2026-09-24)

> 主批 model=jev-1.13.0(jev-curate 生产同构)· 签名 VALID(session.jsonl.sig)
> n=5(甲方指定 mock 行全集)· 判据见 PROTOCOL.md(预注册,含开工修正记录)
> **待非实现者复算**;未经甲方许可不对外发布。

## 摘要:三个生产 findings(重要性排序)

**F1 · score 腿在真 API 上必 422(当前生产全量拒收)**
presets.rs 的 `criteria` 是 dict,真 API(2026-09-24 实测)要求**字符串数组**:
```
POST /v1/systemone {"questions":{"qid":{"type":"score","instructions":"…","criteria":{…}}}}
→ 422 {"detail":[{"loc":[…,"qid","score","criteria"],"type":"list_type","msg":"Input should be a valid list"}]}
```
client.rs 重试 3 次全 422 → filter.rs fail-closed → **每条记录都拒**。
mock_test.rs 全部用 wiremock 手写响应,该格式从未经过真 API——
reasoning-math preset 目前在真 API 上的通过率为 0%,不是阈值问题,是格式 bug。

**F2 · 标尺错位:真 API score 是 0-4,甲方阈值按 1-5 写**
真 API 响应带 `legend:{"0":…,"4":…}`,score=各档概率期望(0-4 标尺)。
min_scores["reasoning_depth"]=3.0 按 1-5 语义写。两个后果:
- 不换算:3.0(0-based)= 1-based 的 4.0,depth 腿变严一整档;
- 换算(+1)后实测 5/5 行仍 <3.0(最高 R5 2.4)——见读数表,3.0 线在
  真实输出上通过率为 0,连真值 depth=4 的正确求导行(R1)也被拒(Jev 给 2.05)。

**F3 · R3 类断言被 noul 腿拒(noul@0.70 误拒 1/5)**
"The answer is obviously 42, trust me" 真值循环=0(纯断言,未把结论当前提),
Jev p=0.78≥0.70 → 拒。结果方向对(该行该滤),腿标签错(走了 noul 而非
depth)。若甲方语义上把"无据断言"也算 circular,则此行非误拒——口径见
敏感点 S1。

## 读数(主批 jev-1.13.0)

| 行 | y_circ | p(noul) | score(0b→1b) | conf | d(真值) |
|---|---|---|---|---|---|
| R1 f'(x)=2x | 0 | 0.05 | 1.05→2.05 | 0.89 | 4 |
| R2 P 循环 | 1 | 0.84 | 0.75→1.75 | **0.37** | 1 |
| R3 obviously 42 | 0 | **0.78** | 0.0→1.00 | 1.00 | 1 |
| R4 Step 罗列 | 0 | 0.09 | 0.65→1.65 | 0.70 | 2 |
| R5 a+b=3 | 0 | 0.04 | 1.40→2.40 | 0.64 | 2 |

### 指标(口径见 PROTOCOL;Brier/ECE 在 n=5 下误差带宽,如实声明)

| 指标 | 主批(1.13.0) | 对照批 | mock 手写值(对照) |
|---|---|---|---|
| noul accuracy@0.70 | 0.8(4/5,误判=R3) | 0.8(同 R3) | 1.0 |
| noul Brier | 0.129 | 0.130 | 0.006 |
| noul ECE(10桶) | 0.224 | 0.236 | — |
| depth MAE(1-based) | 0.69 | 0.69 | 1.825 |
| depth accuracy@3.0 | 0.8(错=R1) | 0.8(同 R1) | 0.5 |
| conf<0.5 行 | R2 | R2 | R4 |

- 对照批(jev-latest)与主批逐行差 ≤0.05,分布一致(latest≈1.13.0,
  响应 model 字段回显亦为 jev-1.13.0)。
- mock 手写值 noul 腿贴近真值(测试作者手工对齐),depth 腿偏离大
  (R2 mock 4.0 vs 真值 1;R4 mock 4.5 vs 真值 2)——mock 是分支逻辑
  测试值,不是校准参照。

## 阈值修复(一条,按甲方要求)

**先修 F1(criteria dict→list),这是 blocker;阈值建议属 F2:**
若甲方保留 1-5 语义,读 API 值后 +1 再与阈值比;并把 3.0 降到 **2.0**
(1-based)。依据:Jev 对本批 depth 系统性低于独立标注(5 行 s−d 均值
−0.69,最大 R1 −1.95),3.0 线在本批真实输出上 0/5 通过,含真值 4 的
正确行;2.0 线在本批为 1/5(R5 2.4 过,真值 2——边界行)。
更稳的替代:改用响应 `probabilities` 众数档+legend 判(概率信息完整),
但这是行为改动非阈值改动,超出 mini 范围,只列不荐。

## 敏感点(预注册披露)

- **S1 R3 noul 真值边界**:主口径 y=0(非循环)。若按"无据断言=assumes
  the conclusion"口径判 y=1,则 noul accuracy@0.70=1.0、Brier=0.015、
  ECE=0.048。复算员独立标注为准,双报。
- **S2 R5 depth 2/3**:主标 2(应拒;s=2.4<3.0 判拒→对)。若复算标 3
  (应留;s=2.4<3.0 判拒→错):MAE +0.2,depth accuracy@3.0 0.8→0.6
  (错行 R1→R1+R5)。如实双报。
- **S3 R2 conf=0.37**:min_confidence=0.5 腿会独立拒 R2(该行本就该拒,
  无净伤害);但 score 答案 conf 分布(0.37-1.0)显示 conf 腿在真 API
  上非平凡触发,值得甲方单独观测。

## Raw artifacts

- `session.jsonl` + `session.jsonl.sig`(主批)+ `pubkey_jev-1.13.0.txt`
- `session_latest.jsonl` + `.sig` + `pubkey_jev-latest.txt`(对照批)
- `t3_results.json`(全部原始读数+指标)
- `PROTOCOL.md`(预注册判据+开工修正记录)
- 验签:`python -c "from jev_trust import TrustedJev; ...verify_log()"`
  (jev-trust ≥0.2.0,pubkey 在上列文件)
