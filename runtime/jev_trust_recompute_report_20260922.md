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

---

# 域 4 复算:OK-first 措辞对照(2026-09-22 · 第二批复算)

> 复算员:另一新鲜会话,未参与域 4 生成/调用/统计/对照计算。判据正本 =
> `runtime/jev_trust_domain4_20260922/PROTOCOL.md`;流程按交接档「域 4 专项」。
> 纪律执行:先独立完成全部计算并记录(此节落笔前未打开域 4 stats.json/RESULTS.md),
> 之后才对拍。纯本地,零外部 API。

## 域4 embodied-qc-labeling-okfirst(`runtime/jev_trust_domain4_20260922/`)

| 步骤 | 复算结果 |
|---|---|
| 1 验签(三态) | jev_trust.verify_log → `ok=True, detail='VALID'`(日志 sha256=aab9a385…cf09);域 3 日志顺带复验 VALID(d8ebbb47…f05d,判据 6-8 依赖其可信)。stats.json `verify:'VALID'`、`pubkey` 字段=pubkey.txt 内容(20ea8950…d5cd)一致 |
| 2 sha 链 | 域 4 无独立决策集(PROTOCOL 写死引用域 3 原件 `../jev_trust_domain3_20260922/decision_set.json`,单一文件无副本漂移)。我算其 sha256=`4af6c5a80ce5328ef35d3e9196a3bb659d8eb154ef8891298f77734603b13b49` = stats.json `decision_set_sha256` **一致**(且与域 3 复算节同值交叉印证);n=120,正例(缺陷)60/负例(OK)60 平衡 |
| 3 真值重推+映射落账 | ①按域 4 PROTOCOL 的 OK-first 通过条件列表(四规则的否定式)独立实现 verifier,重推 120 条 vs decision_set truth:**失配 0**;②映射落账:域 4 outcome 行 truth = 1−(域3 ds 同 qid truth) **全量 120 条,失配 0/120**;③域 3 outcome truth = ds truth 0 失配;④行内恒等式(p_true = 对 decision 方向置信按真值方向换算;correct = 决策方向==真值方向)120/120 零违反 |
| 4 四指标 | 见下表,**对拍一致(含一次复算员自纠,见后)** |
| 5 无选择性报告 | 两域 session.jsonl 各 240 行 = call 120 + outcome 120;无 error 行(= stats errors:0);qid 集合 {ds,d3,d4} 三向一致;域 4 全部 8 件工件含 session.jsonl 已入 git(前次 *.jsonl 入库缺口已闭合,无复发) |

| 指标 | 我的独立值 | stats.json | 对拍 |
|---|---|---|---|
| accuracy | 0.766667(92/120;由 decision 单独重推同值) | 0.7667 | 一致 |
| Brier | 0.176410 | 0.17641 | 一致 |
| ECE | 0.137000 | 0.137 | 一致(经自纠,见下) |
| C=1−ECE | 0.863000 | 0.863 | 一致(经自纠,见下) |

**复算员自纠记录(红灯先证伪自己,本轮唯一一次探针错)**:初算 ECE=0.3505/C=0.6495,
与 stats 失配;探针复验证伪自身——我把 stated_confidence 误读为「对 yes 方向的置信」,
对 no 答案错翻 1−sc。数据坐实其语义为「对 decision 方向的置信」(域4 sp001:decision=yes/
sc=0.71/truth=0/p_true=0.29=1−0.71),top-label 分桶键即 stated_confidence 原值,
与 jev_trust.calib 库 `Prediction.stated_confidence` 语义一致。四个候选口径探针中
stated 原值口径精确复现 0.137 → **0.137/0.863 为判据正本口径下的正确读数,实现者对**。
(域 3 全 yes 120/120,两口径无分叉,故前次域 3 复算未暴露此歧义;域 4 出现 32 个 no 后分叉。)

## 判据 6/7/8 对照复算(核心专项)

| 判据 | 我的独立值 | 实现者(stats.json/RESULTS) | 对拍 |
|---|---|---|---|
| 6 负例误报(OK 题答「不 OK」) | **0/60**;域 3 基线(OK 题答 yes=NEEDS_REVIEW)**60/60**(域 3 decision 计数 yes=120/no=0 独立核) | `criterion6_fp_on_clean:"0/60"`,基线 60/60 | 一致 |
| 7 缺陷漏检(缺陷题答 yes=OK) | **28/60**;域 3 侧漏检 0/60 | `criterion7_missed_defects:"28/60"` | 一致 |
| 8 翻转(双口径) | ①逐题 decision 翻转按真值分组:负例 **0**/正例 **32**/总 32;②McNemar 不一致格:负例修复 **60**(d3错→d4对)/正例新漏 **28**(d3对→d4错) | `criterion8_flips={clean_fixed:60, defect_newly_missed:32}` | **不一致(见下)** |

**判据 8 不符细节(证伪自己探针后坐实)**:
- stats 字段 `defect_newly_missed:32` **名实不符**:32 = 缺陷题 decision 翻转数
  (域3 yes→域4 no),这 32 题在域 4 答「不 OK」= **正确检出**;真正新漏(被说成 OK)
  是 **28** 题——与同一 stats.json 里判据 7 的 28/60 直接自相矛盾。
- RESULTS.md 判据 8 行括号注释「域 3 全抓的缺陷题中 **32 题在域 4 被说成 OK**」为
  事实错误(被说成 OK 的是 28 题),与同文两行之上的判据 7(28/60)矛盾。
- 60 与 32 混用了两种口径:60 是「对错互换」数(OK 题两域都答 yes 字面未翻转,因语义
  反转由误报变全对),32 是「decision 字面翻转」数;PROTOCOL 判据 8 要求的 McNemar
  discordant cells 应为 **60/28**,按 60/32 手工核会把新漏高估 4 题。
- 次要:RESULTS 边界节「28 漏检集中在哪类缺陷未分层」与正文「漏检分层」表自相矛盾
  (分层表数字本身我已独立复算为正确,见下);「144s」实测首末 ts 差 143s(秒精度,不计)。

**漏检分层独立核**(RESULTS 分层表逐格一致,总数 28 吻合):
spike 14/15 · stuck 13/15 · drift 1/15 · limit 0/15(域 4 decision 计数 yes 88/no 32;
32 个 no 全落在缺陷题,OK 题 60 全 yes——accuracy=(60+32)/120=0.7667 自洽)。

## 判定线复核(预注册)

- 判据 6:0/60 **≤ 45 线** → H1 成立区;实现者结论「H1 强成立」与线一致(0 为远穿线的
  极端值,从域 3 基线 60/60 降到 0/60,措辞方向的效应量成立)。
- 判据 7:28/60 **> 18 线(30%)** → 红旗触发;实现者结论「红旗触发」与线一致
  (漏检率 46.7%,「把偏差反了个面」的定性成立)。
- 判据 8:按预注册要求「按真值分组列出翻转数,供 McNemar 手工核」——正确落账应为
  {neg_flips:0, pos_flips:32}(decision 口径)或 {clean_fixed:60, defect_newly_missed:28}
  (对错口径);实现者现行 60/32 混编且标签错,**不满足判据 8 的字面要求**。

## 域4 终判:RED(单点·表述层)

- **全过项**:验签 VALID、sha 链一致、四规则重推 0 失配、映射落账 0/120 失配、
  全量无剔除 errors=0、四指标(经复算员自纠后)逐位一致、判据 6/7 读数与判定线
  复核全部一致、漏检分层表独立复算正确、工件含日志已全入库。
- **不符项(唯一)**:预注册判据 8 落账口径混编+标签错误——stats `defect_newly_missed:32`
  应为 28(或改名为 decision_flips),RESULTS 判据 8 括号注释与自身判据 7 矛盾。
- **影响面**:不动摇 H1/红旗主结论(其依据是判据 6/7,均复核无误);但判据 8 是
  预注册判据,按「任何一处不符即 RED」纪律判 RED。一行修复(字段值 32→28 或改名,
  RESULTS 注释同步)后复核可转 GREEN。

## 域4 复算证据档

- 独立复算脚本(未 import 实现者任何代码):`%TEMP%\recompute_d4_20260922.py`
  (六项全流程 + stats 隔离对拍)+ `%TEMP%\probe_d4_ece.py`(四候选口径探针+分层独立核)
- 全部独立读数已在上文先行记录,stats.json/RESULTS.md 于独立计算完成后才首次打开
