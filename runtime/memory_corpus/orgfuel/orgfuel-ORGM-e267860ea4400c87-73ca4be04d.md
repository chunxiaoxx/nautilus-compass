---
name: orgfuel-ORGM-e267860ea4400c87-73ca4be04d
description: "记忆条目 sha-eol-autocrlf-trap-20261008.md S6 复核二轮实锤(10/8,10703)"
metadata:
  type: reference
  source: org_fuel:memory
  pf_id: ORGM-e267860ea4400c87
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

记忆条目 sha-eol-autocrlf-trap-20261008.md
S6 复核二轮实锤(10/8,10703):平台报"manifest 02f1604≠登记处 cc5713、L3 判据档 5c8e0a7 旧"——**非文件旧,是 sha 口径行尾分裂**。

**根因**:Windows 本地 `core.autocrlf=true`→工作树文件 CRLF;git blob 存 LF;cloud/Linux checkout 出 LF。同一 blob,本地 `sha256sum` 与 cloud `sha256sum` 永不相等。登记处坐标函(S6_REGISTRY_COORDS_REPLY)用本地 CRLF 字节算 sha,平台在 cloud 按 LF 复验→两边都对自己负责,永不合。

**修复**:`.gitattributes` 判分资产类(`*.jsonl`/`*.json`/`docs/metering/**`/`docs/cases/**`)统一 `text eol=lf`(commit ba5ab5cf);renormalize 后六件零重写=blob 本就 LF 的自证。历史锚(API criteria_sha16=b81eca84)注明 LF 等价 sha(5c8e0a7c)双口径过渡。

**Why**:对 sha 锚类资产,"文件哈希"三字节口径(工作树字节/git blob/GitHub raw)在 Windows 开发机上会分裂成三个不同值;登记处级锚点一旦混入口径,复现链在跨机验证时必然断。

**How to apply**:
- 登记 sha 锚一律 `git show HEAD:<path> | sha256sum`(=LF blob 口径)或直接在 Linux 侧算;**不要**在 Windows 工作树上直接 sha256
