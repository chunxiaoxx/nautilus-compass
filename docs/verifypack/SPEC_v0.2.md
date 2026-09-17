# VerifyPack Spec v0.2(协议正本)

> trace: verifypack-v02-20260907 → 本文档为 2026-09-07-verifypack-v02.md 立项的协议正本。
> 一句话:**第三方数据效用验证的协议化**——把「信件人工验证流」升级为「可验签的自足协议」。
> 实现入口:`python -m tools.verifypack build|verify|receipt|check|keygen`(零第三方依赖,纯 stdlib)。

## 1. 动机(measured · batch001 复算教训)

v0 载体是 markdown 信件 + 自然语言复算指引,实测暴露三缺陷:

1. **活文件缺陷**:resource_log.csv 打包后仍被追写 25h——快照不可复现,无机制抓得住;
2. **复算不可规模化**:compass 侧复算器逐条硬编码(verify_batch001_recheck.py),每换一个包重写一遍;
3. **回执无签名**:"compass 验过 6/7 agree"只是自报,买方无法验明验证发生过且未被改。

## 2. 包结构(v0.2)

```
<pack>/
  pack.json        # 元数据 + claims[] + inputs 声明 + env_decl
  manifest.json    # seal:包内全部文件(含 pack.json)的 sha256 清单——build 最后写
  payload/…        # 数据文件(拷入,自足)
  repro/…          # 复算材料(仅 kind=script 的 claims 需要)
  receipts/        # verify 之后产生,不属于 seal 范围
```

### 2.1 inputs 声明(自足性的例外口)

pack.json `inputs` 数组声明**不拷入**的外部引用文件:

```json
{"name": "logs", "path": "../egostandard_sample/s2", "files": ["a.log", "b.log"]}
```

verify 时按声明路径找文件,**哈希与 seal 记录不符 = SEAL_FAIL(活文件抓现行)**。
这正是 batch001 resource_log.csv 教训的产品化:引用即留痕,改动即败露。

## 3. claim schema

```json
{
  "id": "D2_frame_integrity",
  "statement": "帧完整率 = sum(frames_written) / sum(frames_decoded)",
  "level": "L1",
  "value": 1.0,
  "checks": {"primary": {…}, "fallback": {…}}
}
```

- `level`: **L1** = 无需验证方环境即可复算;**L2** = 需环境(如 QC),缺环境时跑 `fallback`(通常是包内一致性核对),verdict 记 `degraded`。
- `checks.primary.fallback` 的结构 = check 对象(§4)。`level=L1` 可只写 `checks`(等价 primary)。

## 4. check 引擎(六种 kind)

| kind | 字段 | 语义 |
|---|---|---|
| `aggregate` | from, num, den, op, tol | 对数组行做受限表达式聚合(§5),op ∈ ratio_eq / value_eq |
| `file_hash` | file, algo, expect | 单文件重算哈希与 expect 比 |
| `file_hash_map` | from/dir_decl/names_from/key/path/algo | 名字→路径→哈希映射整体比对 |
| `group_count` | from, by, min_group, expect_groups | 按 by 分组,断言组内计数与组数 |
| `json_map_equal` | left(file,path,map_by,field), tol | 从文档求 {k:v} 与 claim.value 比 |
| `text_contains` | file, needles[] | 文本含各 needle(needle 可引其他 claim 的复算值) |
| `script` | repro, timeout_s | 子进程跑包内脚本,stdout JSON `{"value": …}`(信任边界:验证方自愿执行数据方复算代码,容器沙箱是推后项) |

`from` 语法:`<file>#<dot.path>`,file 相对 pack 根(payload.json → payload/payload.json 由 build 映射,见 pack.json files 段)。

## 5. 受限表达式(expr)

`aggregate` 的 num/den 只允许:数字、字段名(对行数组取列)、`sum/len/min/max/round/count` 调用、`+ - * /`、一元 `-`。
AST 白名单求值,其余节点(Attribute/Subscript/Name 越界等)一律拒绝——**不 eval 任意代码**。

## 6. seal 语义(manifest)

- build:写完全部内容后生成 `manifest.json` = {path: sha256}(覆盖 pack.json、payload/、repro/;不含 manifest.json 自身与 receipts/)。外部 inputs 记录 `{declared_path: sha256}` 于 `manifest.inputs`。
- verify 第一步:重算全部哈希。任何不符 → 所有 claims verdict= `seal_fail`,结果中指名被改文件,**不继续复算**。
- 语义:pack 是**不可变快照**。verify 通过 = 「build 时刻的这批字节,在这些判据下得出这些结论」。

## 7. receipt(schema v0.2)

```json
{
  "receipt_version": "0.2",
  "pack": "verify_batch001",
  "pack_manifest_hash": "<manifest.json 的 sha256>",
  "verifier": "compass",
  "verified_at": "2026-09-09T…",
  "environment": "win32 · python 3.13 …",
  "results": [{"id", "level", "verdict": "agree|disagree|degraded|seal_fail", "recomputed", "claimed"}],
  "summary": {"agree": 6, "disagree": 0, "degraded": 1},
  "boundary": "独立技术验证与回执,不作客户验收或结算决定"
}
```

- 签名:ed25519(RFC 8032,纯 stdlib 实现 `ed25519.py`),对 receipt.json 的 canonical bytes
  (`json.dumps(sort_keys=True, separators=(',',':'), ensure_ascii=False)`)签名,落 `receipt.sig`(64B hex)。
- 私钥路径从 `--key` 或环境变量 `VERIFYPACK_KEY` 读,**禁止硬编码**;公钥(`.pub`,32B hex)随回执分发/注册。

## 8. CLI

```
python -m tools.verifypack keygen   --out-dir DIR
python -m tools.verifypack build    --spec SPEC.json --out DIR      # 数据方:打包+seal
python -m tools.verifypack verify   PACK [--env CAP]… [--key K] [--out receipts/receipt.json]
python -m tools.verifypack receipt  PACK --receipt R --key K        # 对已有 receipt 签名
python -m tools.verifypack check    PACK --receipt R [--pubkey PK]  # 结算方:验签+摘要核对,不重算
```

`--env qc` 声明验证方具备某环境能力;未声明的 L2 claim 走 fallback。

## 9. 边界与红线(宪法,不可协离)

1. compass 只做验证方技术设施,**不作客户验收或结算决定**(写死,回执 boundary 字段强制);
2. verify 只读包内产物 + inputs 声明路径,不拉全量数据;
3. v0.2 全开源;计费/多验证方共识/链式审计均不在本版。

## 10. DoD(可裁决)

- [x] Spec v0.2(本文档)
- [ ] CLI 四命令 + keygen,测试绿
- [ ] **batch001 端到端**:build(v0 包升格)→ verify(7 条)→ receipt 签名 → check 验签通过
- [ ] flywheel 确认协议可用(回执形式投函,等对方回)
- 手几何第二包:产物缺失(见 #46),产物到位后补第二个样本。

## 11. export(verdict 语料导出 · 燃料层 · 2026-09-17 增)

`python -m tools.verifypack export <pack>... --out <corpus.jsonl> [--trace <id>] [--pubkey <hex>]`

- **一行 = 一条 claim-verdict**,来源只有 pack.json 声明 + receipts/receipt.json:
  `schema / trace / pack / claim_id / level / criteria_ref / payload_hash / verdict /
  recomputed / claimed / verifier / signed_at / pubkey_fp`。
- **criteria_ref 从 statement 正文提取**(`criteria:<id>@<catalog-vN>` 显式 +
  `<id>@catalog-vN` 裸锚引用)——声明文本是判据引用的唯一来源(锚引用纪律)。
- **payload_hash = pack_manifest_hash**(整包字节锚);pubkey_fp = 前8…后6,
  仅在 sig 存在且验签通过时非空(未验签语料仍可导,如实标 None)。
- **行内零时间戳**(signed_at 取回执)⇒ 同输入同输出;sidecar
  `<out>.manifest.json` 记 exported_at/rows_total/sha256/packs[]/orphan 计数。
- 语料 jsonl 不入仓(gitignore *.jsonl):可从 pack+回执逐字节再生,
  sha256 即防篡改锚(首份:c_family_b1_20260917.jsonl,6 行,
  sha256 b8b617156171e528…,trace=flywheel-c-family-b1-built-20260916)。
- 训练侧红线(T7 反自指)不变:语料只喂字节级复算类判分器,升级走
  AUC(hold-out)≥0.87 且 FPR 不升门,挂语料≥2000+M2。
