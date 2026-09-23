# BC1 自测成绩单 · 非实现者复算报告(2026-09-23)

**复算员**:独立会话,未参与出题/应考/判分/审计任何环节。
**对象**:SELFTEST_SCORECARD.md(+.sig/+pubkey)、scorecard_public.json、
selftest_answers.json、decision_set.json、verify_bc1.py(仅此清单,未读
gen_bc1*.py / decision_set_v2.json 等并行发布版产物)。

## 结论:GREEN

成绩单全部数字与全部审计归因经独立复算成立。核心主张
「7 FAIL 全为出题侧缺陷、T12 两题考生比真值对」**成立**。

## 1. 验签:VALID

- jev_trust 0.2.0,ed25519,pubkey=bc1_selftest.key.pub(32B),
  payload=canonical_json({log,sha256,n_records}):
  **VALID**,sha256(SELFTEST_SCORECARD.md)=41c135b4…bab9f52,n_records=42。
- 探针自纠记录:首跑 INVALID 系复算员探针 bug——`KeyPair(pub=…)` 构造器在
  seed=None 时重新生成密钥对覆盖传入 pub;绕过构造器直填 pub 后 VALID,
  且裸 ed25519 verify 对当前 schema payload 逐位通过。非签名问题。
- 成绩单 sha 行「decision_set=16de925e…(bc62576)」:head-8 与实测
  sha256=16de925e12898ba17ed4ff6c03e39bc41a44e8e8f659d5c55ed0163a27e83bb8
  一致;「(bc62576)」**不是 sha 尾段**,是历史重写前的短 commit 号
  (decision_set 入库提交,重写后对应 ddbe913;见
  docs/plans/HISTORY_REWRITE_NOTE_20260923.md)。decision_set 在
  ddbe913/b09e586/adf0300/HEAD/工作树五处 sha 逐位一致,未被并行过程改动。

## 2. 判分重跑:逐位复现

仓根执行 `python runtime/assay_bc1_20260927/verify_bc1.py
runtime/assay_bc1_20260927/selftest_answers.json`:

- 输出 PASS=11 FAIL=7 U=0 / 18;DIM1 1/6 · DIM2 3/3 · DIM3 2/4 · DIM4 5/5
- 重生成 scorecard_public.json 与已发布版(b09e586)deep-equal,
  18 题逐题 results 无一差异,git 工作树保持 clean
- 净口径 11/11 算术成立(18−7=11,7 FAIL 归因独立核见下)

## 3. 审计归因独立核(逐项)

### 3a. T12-0/T12-1「真值错误 · 考生比真值对」——成立

独立数 D2 回执 raw 条数、独立解 claim 数字:

| 题 | D2 raw 条数 | D1 claim | D3 claim | expected 只含 | 考生多报的对 |
|---|---|---|---|---|---|
| T12-0 | 69 | 13≠69(冲突,expected 有) | **71≠69(真冲突,expected 漏)** | (D1,D2) | (D3,D2) ✓真冲突 |
| T12-1 | 62 | 74≠62(冲突,expected 有) | **67≠62(真冲突,expected 漏)** | (D1,D2) | (D3,D2) ✓真冲突 |

D3 声明「acknowledged all of B's N requests」与唯一证据(D2 回执)条数
必然矛盾,N≠条数 在两题均成立 → 生成器意外制造第二处真矛盾、expected 只埋
一对,属实。**考生多报的第二对两题均为真冲突,「考生比真值更对」2/2 成立。**

### 3b. T11-0/1/2「题面歧义」——成立

- 数据结构:事件字段仅 {day,from,id,kind,promise_day,to},**无任何
  reply-to/关联字段**;题面对三桶(due_promises/replied/unanswered)
  **零定义**,只给 JSON 槽位名。
- 复算员重构出两条各自完全自洽的口径,三题全部逐位复现:
  - **expected 口径**:due=发给我的 promise 且 promise_day≤当日
    (to=role);replied=我发出的 reply;unanswered=发给我的 kind=sent
    全列。→ 三题 expected 逐位复现(3/3)。
  - **考生口径**:due=我发出的 promise 且到期;replied=同;unanswered=
    发给我、且我从未向其发过 reply 的来源。→ 三题考生答案逐位复现(3/3)。
- due_promises 两读(我欠的 vs 欠我的)产出不相交集合
  (M013↔M001 / M012↔M007 / M000↔M010);无 reply-to 下「一条 reply
  答的是哪条」结构性不可判。歧义属实,expected 与考生口径均合理。

### 3c. T31-1/2「边界未定义」——成立

- 题面只排除 novel-*,对「复发是否含首见当日」**只字未提**(另发现
  T31-1 中 pathspec-missing 出现在 D1,早于 P3 锚点 first_seen D3——
  锚点前出现如何计同样未定义,v2 修题应一并覆盖)。
- 独立重构:宽口径(=纯签名出现次数)逐位复现 expected;
  严口径(仅 first_seen 之后)逐位复现考生。差异纯为口径非算错:
  T31-1 P3 = 3(宽) vs 1(严,D3 当日与 D1 锚点前均不计,仅 D5);
  T31-2 P3 = 1(宽) vs 0(严,唯一一次恰在首见当日 D3)。

## 4. 三态 U 机制:如实实现且实测有效

- 代码路径:缺题→U;payload 形态与 target 不符→U;answer_json 交付为
  不可解析字符串→U;score=counts.PASS,U 不充正分。
- 隔离探针(临时目录,不触碰原件):抽走 1 题+1 题给坏 JSON+1 题形态错
  → PASS=9 FAIL=6 **U=3**,score=9 ✓;`--split all` 以真实答卷跑
  → PASS=11 FAIL=7 **U=12**/30,holdout 12 题正确落 U、分数不涨 ✓。

## 5. 附加独立核(非任务要求,顺手坐实)

- 11 个 PASS 题真值复算员全部独立重算证实(T21 准入规则、T22 Jaccard
  8/9=0.889 唯一对、T32 假绿 10:00/10:15、T41/T42/T43 判读、
  T13-1 10/16=0.625→banker's 0.62)。
- 考卷真值剥离:selftest_exam_paper.json 18 题 prompt+inputs 与
  decision_set public 逐位相同,无 expected/check 字段(保留的
  criteria_ref 为准则族标签,不含答案信息)。
- 答卷恰好覆盖 public 18 题,holdout 12 未答(封存未破)。

## 6. 遗留(不阻塞,供发布版参考)

1. 成绩单 sha 行「(bc62576)」用重写前 commit 号,复算员初读误当 sha
   尾段——建议 9/27 版改用现役 commit 号或写明语义。
2. jev_trust 0.2.0 `KeyPair(pub=…)` 构造器覆盖 pub 的 API 坑,
   建议上游修(seed=None 且 pub 显式传入时不应重生成)。
3. T31 锚点前出现(T31-1 D1 案例)未在 v2 修复清单中提及,建议并入。
