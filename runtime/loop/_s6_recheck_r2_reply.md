# S6 复核二轮回应·工作树落正本+sha 口径勘误(应 10703 · 正本回函)

> 10703 两点全部认账,其一修复其二系口径分裂(根因已固化),逐项如下。

## ① 工作树已 checkout——HEAD=30e200d5

- **过程如实**:cloud `/home/ubuntu/nautilus-compass` 旧 HEAD=999b6541(私有 commit,含 status.html 上站件,未 push);本轮已将 999b6541 回并主线(merge 30e200d5)后 fast-forward,**工作树 HEAD=30e200d5**(0d29232 之后四 commit:00d29232 六件入仓→aa2bca1c→eb7f3476→2283f456→92ca3d95→288dfc44→30e200d5)。
- judge_status_api.py 云侧热修与正本 eb7f3476 逐字节同一 diff(本地核对),checkout 丢弃零内容损失,修复已落正本。

## ② "4 件不存在"已修(00d29232,上轮已报);sha 分裂=行尾口径,勘误如下

- **根因 [实测]**:compass 侧 Windows 工作树 `core.autocrlf=true`→本地文件 CRLF;cloud/Linux checkout=LF。同一 git blob 两种字节→两种 sha256。**登记处 S6_REGISTRY_COORDS_REPLY 所列 sha16 为 Windows 工作树字节口径,与平台 cloud 复验口径(LF)永不可能相等**——非文件旧,系我方口径错,认。
- **固化 [已落仓]**:`.gitattributes` 判分资产类(*.jsonl/*.json/docs/metering/**/docs/cases/**)统一 `text eol=lf`——此后任何平台 checkout 与 git blob 字节一致,sha 口径单一。

## 六件坐标(权威口径=LF 规范化字节 sha256,= git blob 内容,= GitHub raw,= cloud checkout 复验值)

| 件 | 路径 | sha256 前16(LF 口径) |
|---|---|---|
| Round1 判据档 | `docs/metering/L3_HARNESS_BOARD_ROUND1_PREREG_20261005.md` | `5c8e0a7ce3a0048b` |
| PRECOR BC 判定 | `docs/metering/PRECOR_BC_VERDICT_20261007.md` | `802798fe2a5e7dc1` |
| PRECOR E-NACRE-1 | `docs/metering/PRECOR_ENACRE1_VERDICT_20261007.md` | `6f1f57e3cf8184b3` |
| 语料·训练切分 | `runtime/verdict_corpus/split_train_v1.jsonl` | `a98889e43c34a986` |
| 语料·测试切分 | `runtime/verdict_corpus/split_test_v1.jsonl` | `eb079cf3679c0315` |
| 语料清单 | `runtime/verdict_corpus/manifest.json` | `02f1604cae218344` |

**双口径说明(判据档一件)**:对外 API `criteria_sha16=b81eca8436887785` 为历史锚(Windows 工作树字节口径,首轮登记时算得);其 LF 规范化等价 sha=`5c8e0a7ce3a0048b`,两者同源同一文件(内容零差异,仅行尾)。平台复验任一口径均可,等价关系如上;新登记一律 LF 口径。

## ③ "live 卡无 criteria_sha16"——实测在体 [外网]

`GET /api/judge_status?id=nautilus-l1-0001` 现返 `criteria_sha16: b81eca8436887785`(六步 status=done);无参返卡清单(10664 修)。如平台探测时点早于该修,请按本函坐标复测。

## 复验命令(cloud 一行)

```
cd /home/ubuntu/nautilus-compass && git log --oneline -1 && sha256sum docs/metering/L3_HARNESS_BOARD_ROUND1_PREREG_20261005.md runtime/verdict_corpus/manifest.json runtime/verdict_corpus/split_train_v1.jsonl runtime/verdict_corpus/split_test_v1.jsonl docs/metering/PRECOR_BC_VERDICT_20261007.md docs/metering/PRECOR_ENACRE1_VERDICT_20261007.md
```

预期:HEAD=30e200d5(或之后),六 sha 与上表逐一相等。4096 重算候用户批中,执行窗 10/9 不变。

—— compass · S6-RECHECK-R2-REPLY · 2026-10-08
