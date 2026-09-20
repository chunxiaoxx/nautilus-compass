# VerifyPack Spec v0.3(协议正本 · 增量)

> v0.2 全文见 SPEC_v0.2.md,**全部语义不变**;本文只写 v0.3 新增。
> trace: verifypack-v03-20260920 · 两个来源:Jev 吸收线 B(轨迹验证格式,568 函
> flywheel 具身验收 Day0 等用)+ Let's Encrypt 剧本收敛(90 天续期 ↔ 持续适航订阅
> 是同一结构,docs/strategy/letsencrypt_playbook_20260920.md §四)。
> 兼容性:protocol_version 新增 `verifypack-0.3`(0.2 包继续可验);不带新字段的
> 回执仍标 0.2,字节流与 v0.2 完全一致(c_family 回执可再生性不破)。

## E · episode check kind(轨迹验证 · J2)

验证单位从「产物」变「轨迹」:声明帧数组 + **逐转移不变量**,引擎独立重放判有效性。

```json
{"kind": "episode", "from": "payload/frames.json#frames",
 "episode_by": "episode_id",
 "invariants": [
   {"name": "dt",     "field": "t",     "op": "incr_eq",      "rhs": 1},
   {"name": "jump",   "field": "x",     "op": "abs_delta_le", "rhs": 0.15},
   {"name": "ep",     "field": "episode_id", "op": "same"},
   {"name": "tnonneg","field": "t",     "op": "ge_const",     "rhs": 0}]}
```

- `episode_by`(可选):按该字段分组,**转移只在组内相邻帧间判定**(跨组不比);
  省略=全数组一条链。
- pair 类算子(相邻帧 prev→cur):`same / incr_eq / incr_ge / incr_le /
  abs_delta_le / abs_delta_ge / delta_le / delta_ge`;frame 类算子(每帧):
  `ge_const / le_const / eq_const`。`same` 外 rhs 必填数值。
- recomputed = `{"transitions": N, "violations": {名: 违规数}}`;
  **ok ⇔ 与 claim.value 相等 ∧ 全部违规数为零**——不变量是有效性谓词,不是
  可预测值:「声称吻合的违规」不构成 agree(gaming 关口)。
- 终局计数器(collisions/成功数)不进 episode,仍用 aggregate(如
  `count(coll == 1)`)——validity 与 counters 分工,判据各归各。
- 帧缺字段 → CheckError(不可执行,非 disagree)。首个实弹目标:NanoJev 式
  轨迹回放(帧数=steps+1·collisions 帧级·运动学零跳跃)+ flywheel episode cohort。

## R · receipt subject(T8 指纹)+ TTL(LE 续期)+ 续验链

```json
{"receipt_version": "0.3",
 "subject":     {"pubkey_fp": "…", "code_hash": "…", "config_hash": "…"},
 "subject_fp":  "<subject canonical bytes 的 sha256 前 16>",
 "valid_until": "2026-12-19",
 "chain":       {"replaces": "<前驱 receipt.json 文件的 sha256>"}}
```

- **subject**(T8 身份三元组,pack.json 可声明,verify 原样入回执):改脑即新
  主体——回执绑的是三元组,不绑「名字」。check 时回执 subject ≠ 包 subject →
  `SUBJECT_MISMATCH`(签名有效但元数据错配,按 drift 拒)。
- **valid_until**(verify `--ttl-days N`,推荐 90):**信任是连续量**。到期 =
  `EXPIRED`,reason「UNVERIFIABLE until re-verified」——签名仍可验,但声明
  不再被背书;续验出新回执。未到期 → `status: VALID`。不带 TTL = v0.2 语义。
- **chain.replaces**(receipt 命令 `--replaces <旧回执路径>`):续验链前驱锚,
  LE 的 renew 与我们的再验在结构上是同一动作;链可回溯审计主体历史。

## CLI 增量

```
verify … --ttl-days 90          # pack 带 subject 时建议 90(LE 默认)
receipt --receipt R --key K --replaces OLD_R    # 续验签发
check …                          # 输出增 status/chain_replaces 字段
```

## DoD

- [x] episode 引擎 + spec 校验(8 测试:分组/跳跃/跨组/帧级/缺字段/单帧/校验×2)
- [x] subject/TTL/chain + 向后兼容(8 测试:v0.2 字节不变·过期·错配·链·spec)
- [x] verifypack 全量 77 passed(旧 61 零回归)
- [x] CLI 端到端冒烟:build→verify --ttl-days→check VALID;重签过期回执→EXPIRED
- [ ] 首个实弹 episode pack(NanoJev Tier-2 重放或 flywheel Day0 验收)
