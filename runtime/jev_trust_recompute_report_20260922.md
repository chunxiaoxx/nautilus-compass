# jev-trust 三域非实现者复算报告(2026-09-22)

> 复算员:新鲜会话,未参与三域任何生成/调用/统计实现。流程严格按
> `runtime/jev_trust_recompute_handoff_20260922.md` 六步;判据正本 = 各域 PROTOCOL.md。
> 纪律执行:先独立完成(验签→sha→真值重推→四指标手算)并落档
> `runtime/_indep_results_20260922.json`(含复算脚本 `runtime/_indep_recompute_20260922.py`),
> **之后**才打开 stats.json 对拍。
> 纯本地复算,零外部 API;jev_trust 0.1.0 取自全局 pip 安装(非源码路径)。

## 复算方法与自证伪记录(红灯先证伪自己)

复算中出现 4 次红灯,全部证伪为**复算员探针自身问题**,被测物无恙:

1. **验签初读 False**:探针读 `ReceiptResult.valid` 字段 → 该 dataclass 只有
   `ok/log/sha256/detail`,无 `valid` 字段(None→False)。正确读法 `ok=True, detail='VALID'`。
2. **独立 ed25519 验签对原始字节 FAIL**:jev-trust 签名对象不是日志原始字节,而是
   `canonical_json({log, sha256, n_records})`(receipt.py `log_payload`)。按正确载荷重构后,
   用**独立密码库 `cryptography`**(非 jev_trust 自带 ed25519)三域全部验签通过。
3. **域2 疑似 40 条结果失配**:探针用 `str()`,生成器存 `repr()`(字符串带引号)。
   换 repr 约定后 120/120 全一致,真实失配 0。
4. **对拍脚本 n/correct 键名 MISMATCH**:stats.json 用 `n_calls/n_outcomes`,探针用错键名;
   实际 120/120 三域一致。

## 域1 python-exception-prediction(`runtime/jev_trust_dogfood_20260922/`)

| 步骤 | 复算结果 |
|---|---|
| 1 验签(三态) | jev_trust.verify_log → `ok=True, detail='VALID'`;独立 cryptography 库 ed25519 验签(canonical 载荷 `{log, sha256, n_records}`)→ VALID;载荷内 sha256=02b4f3b1…5277 与 session.jsonl 实测 sha256 一致。**三路全 VALID** |
| 2 sha 对拍 | 我算 decision_set.json sha256=`9652aa7428959181520682471795d7e8a8dfa51d913ed191a673bcaf0170074c` = stats.json `decision_set_sha256` **一致** |
| 3 真值重推 | exec 逐题实际执行 state.code + state.call,try/except 判异常:120/120 与 decision_set truth 一致,**失配 0**(正例 46/负例 74,六模式 ×20 齐) |
| 4 四指标 | 见下表,**全对拍一致** |
| 5 无选择性报告 | session.jsonl 240 行 = call 120 + outcome 120;qid 双射;0 error 行(= stats.json errors:0 = run_log errors=0);outcome 行 logged correct/p_true 与我手算 120/120 逐条一致 |

| 指标 | 我的独立值(手算) | stats.json | 对拍 |
|---|---|---|---|
| accuracy | 1.000000(120/120) | 1.0 | 一致 |
| Brier | 0.00545917 | 0.00545917 | 一致 |
| ECE | 0.04658333 | 0.04658333 | 一致 |
| C=1−ECE | 0.95341667 | 0.9534(4dp) | 一致 |

手算与 jev_trust.calib 库交叉复核逐位一致。桶分布:bin6 n=3 / bin7 n=2 / bin9 n=115。

**域1 终判:GREEN**

## 域2 code-patch-behavior(`runtime/jev_trust_domain2_20260922/`)

| 步骤 | 复算结果 |
|---|---|
| 1 验签(三态) | jev_trust → VALID;独立 cryptography 库 ed25519 → VALID;载荷 sha256=cf8a48be…46b2 与日志实测一致。**三路全 VALID** |
| 2 sha 对拍 | 我算 `6fd6294808c995b3601394ce35681173b22aeb515ced7b5919c74eb1a06db3b0` = stats.json **一致** |
| 3 真值重推 | 逐题 exec code_before/code_after 实跑,json 解析 call_args,比较 (ok/异常类型名, repr(返回值)):120/120 与 decision_set truth 一致,**失配 0**(正例 37);且 decision_set 内嵌 before_result/after_result 与我实跑结果 120/120 逐条一致 |
| 4 四指标 | 见下表,**全对拍一致** |
| 5 无选择性报告 | 240 行 = 120+120;qid 双射;0 error(= stats errors:0 = run_log errors:0);outcome logged 字段与我手算 0 差异 |

| 指标 | 我的独立值(手算) | stats.json | 对拍 |
|---|---|---|---|
| accuracy | 0.925000(111/120) | 0.925 | 一致 |
| Brier | 0.05750417 | 0.05750417 | 一致 |
| ECE | 0.13425000 | 0.13425 | 一致 |
| C=1−ECE | 0.86575000 | 0.8658(4dp) | 一致 |

桶分布:bin7 n=18 acc=0.50 / bin8 n=51 / bin9 n=51。手算与库交叉一致。

**域2 终判:GREEN**

## 域3 embodied-qc-labeling(`runtime/jev_trust_domain3_20260922/`)

| 步骤 | 复算结果 |
|---|---|
| 1 验签(三态) | jev_trust → VALID;独立 cryptography 库 ed25519 → VALID;载荷 sha256=d8ebbb47…f05d 与日志实测一致。**三路全 VALID** |
| 2 sha 对拍 | 我算 `4af6c5a80ce5328ef35d3e9196a3bb659d8eb154ef8891298f77734603b13b49` = stats.json **一致** |
| 3 真值重推 | 按 PROTOCOL 四规则**独立实现 verifier**(尖峰>0.8 / 连续≥5 重复 / 超出[-3.14,3.14] / |首−末|>1.5 且单调):120/120 与 decision_set truth 一致,**失配 0**。单调取严格/非严格两变体**零 qid 差异**(歧义无实质影响)。模式 6×20 齐,正例恰 60/120 |
| 4 四指标 | 见下表,**全对拍一致** |
| 5 无选择性报告 | 240 行 = 120+120;qid 双射;0 error(= stats errors:0 = run_log errors:0);outcome logged 字段与我手算 0 差异 |

| 指标 | 我的独立值(手算) | stats.json | 对拍 |
|---|---|---|---|
| accuracy | 0.500000(60/120) | 0.5 | 一致 |
| Brier | 0.20619250 | 0.2061925 | 一致 |
| ECE | 0.31075000 | 0.31075 | 一致 |
| C=1−ECE | 0.68925000 | 0.6892(4dp) | 一致 |

桶分布:bin5 n=30 acc=0.067 / bin6 n=46 acc=0.304 / bin7 n=16 / bin8 n=20 / bin9 n=8。
(PROTOCOL 判据 5 不设好坏门;acc=0.5 为如实读数,不构成 RED。)

**域3 终判:GREEN**

## 三域总判

**三域全部 GREEN**:验签三路全 VALID(含独立密码库复验)、decision_set sha256 三域一致、
真值重推失配 0/120 ×3(域1/域2 实际执行代码、域3 独立四规则 verifier)、四指标
(accuracy/Brier/ECE/C)手算与 stats.json **逐位一致**(仅 C 的 4dp 呈现差)、
全量 120 无剔除、errors=0 三方(日志/stats/run_log)互证。数字侧无可挑之处。

## 附:一条需修复的入库缺口(不推翻数值结论,但须归档层修复)

- **事实**:三份 `session.jsonl` 在工件目录齐备(复算即消费它们),但**均未入 git**——
  被仓库级 `.gitignore` 第 7 行 `*.jsonl` 拦截(c7c3126/f15a985/fce262c 三次提交各含
  decision_set/.sig/pubkey/stats,**唯独缺日志本体**;`git log --all` 证实全仓历史从未提交过
  任何 session.jsonl)。
- **影响**:PROTOCOL 判据 2「会话 JSONL 日志 … 全部入库」的字面未满足;第三方仅克隆仓库
  拿不到被签名的日志,.sig+pubkey 的验签链在"仓库发行"意义上断裂。
- **定性**:三域同发型系统性疏漏(git add 静默跳过 ignored 文件),**非选择性报告**——
  日志本体完整(240 行)、签名有效、且已全量复算。若按判据字面最严读法,此项可翻判据 2
  不满足;复算员判定数值结论不受影响,终判维持 GREEN,但要求:
  **`git add -f` 三份 session.jsonl 并 commit**(一行修复),修复后验签链在 git 层面闭合。

## 复算证据档

- 脚本:`runtime/_indep_recompute_20260922.py`(六步全流程,stats.json 隔离在后置对拍)
- 独立结果:`runtime/_indep_results_20260922.json`(打开 stats.json 之前落盘)
