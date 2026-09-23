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

---

# v2 成绩单复算(2026-09-23 · 独立会话)

**复算员**:独立会话,未参与 v2 出题/应考/判分。**对象**:SELFTEST_SCORECARD_V2.md
(+.sig/+pubkey)、scorecard_public.json、selftest_answers_v2.json、decision_set.json、
verify_bc1.py。

## 终判:RED(验签一腿;判分与口径两腿全绿,成绩单数字本身成立)

成绩单自设门为「待非实现者复算后上墙」+commit 自称「v2 成绩单签名 VALID
待复算上墙」——验签被复算证伪,不得上墙,修复重签后再走本节复验。

## V2-1. 验签:INVALID(红灯,探针先尽证伪)

- **探针自纠**:交接提示「新版已修复 pub 保留 bug」在本机不成立——site-packages
  装的 0.2.0 构造器仍 `if seed is None: seed,pub=keypair()`,实测传入
  8cf767a6… 被覆盖为 76c35782…;修复只落在仓内 sdks/jev-trust(75900f1),
  未发布未安装。两种方式均验:装版绕过构造器直填 pub + 仓内修复版
  KeyPair(pub=)(pub preserved=True)——结论一致。
- **探针链路自证(关键对照)**:v1 成绩单重写前字节(sha=41c135b4…bab9f52,
  n=42,取自 75900f1^)+ 原 v1 sig(自 b09e586 未变)→ **VALID**,与首轮
  复算记录逐位一致 → 验签方法与 pubkey 均可靠,红灯不是探针病。
- **V2 原地验签(文件名正确)→ INVALID**,证伪穷尽:schema payload
  {log,sha256,n_records} / 裸文件字节 / sha-hex / sha-digest / 去尾换行×2 /
  n_records=0..59 全扫 / 无 n_records / 9 个错文件 payload(v1 md、
  decision_set、answers、考卷等)/ CRLF / BOM——全部不通过。
- **结论**:SELFTEST_SCORECARD_V2.md.sig 不是由 bc1_selftest.key.pub
  对应私钥对当前 md 字节产生。时间线(md mtime 09:47 < sig 09:48)排除
  「签后改文」,指向**签字侧密钥不对**;最可能成因(假说,无私钥不可终证):
  签字时撞装版 0.2.0 同款构造器 bug(重新生成密钥对后签字)——即仓内修了
  bug、签字却仍用 bug 版。
- **连带发现**:v1 三元组现亦断链——SELFTEST_SCORECARD.md 于 09:41
  (75900f1)改 sha 行未重签,v1 sig 只覆盖改前字节 41c135b4…;当前挂着的
  v1 md+sig 对不上。目录内两件签名物双双名不副实。

## V2-2. 判分重跑:逐位复现(GREEN)

仓内执行 `cd runtime/assay_bc1_20260927 && python verify_bc1.py
selftest_answers_v2.json`:

- 输出 **PASS=18 FAIL=0 U=0 / 18**;DIM1 6/6 · DIM2 3/3 · DIM3 4/4 ·
  DIM4 5/5——与成绩单 18/18 主张及 scorecard_public.json 逐位一致
- 重生成的 scorecard_public.json 与已提交版 byte-identical,git 工作树
  该文件保持 clean(判分器确定性复现)
- 答卷恰好覆盖 public 18 题,holdout 12 题零泄漏(封存未破)

## V2-3. 口径核对:GREEN

- decision_set.json meta.version = "v2 (post-selftest fixes)" ✓
- public=18 / total=30 / holdout=12 ✓
- sha256(decision_set.json)=3b9def7d…(=decision_set_v2.json)与成绩单
  考卷 sha 行一致 ✓

## V2-4. 抽查:T12 真值修复成立

独立数回执行数+独立解 claim:T12-0 raw=68,D1 claim 73(冲突,expected
含 ✓),D3 claim 68=68(不再冲突);T12-1 raw=66,D1 claim 71(冲突 ✓),
D3 claim 66=66。两题 expected=[(D1,D2)] 独立重推逐位一致——v1「第二处
真矛盾漏埋」缺陷确认已修(修法=D3 claim 对齐回执行数)。

## V2-5. 处置建议(数字不阻塞,上墙阻塞)

1. 用正确私钥重签 SELFTEST_SCORECARD_V2.md(仓内修复版 sdk 或
   KeyPair.from_hex(seed)),按 V2-1 方法复验 VALID 后再上墙。
2. v1 md 09:41 的 sha 行改动补重签或回滚,恢复 v1 三元组自洽。
3. 装版 jev-trust 仍为 bug 版——仓内修复未发布,后续验签者会继续踩
   同一坑,建议发 0.2.1 并重装。

**数字汇总:验签 INVALID / 判分 18-0-0 逐位复现 / version=v2·public=18·
sha=3b9def7d 一致 / T12 抽查 2/2 修复成立。终判 RED(仅验签)。
(此为 10:1x 阶段判;修复后复核见 V2-6,终判以 V2-6 为准。)**

## V2-6. 修复复核(同日 10:30 工件 = bdff7f90 提交字节,独立复核)

**复核终判:GREEN(验签腿——双三元组外部直验 VALID + 根因法证闭环);
另记 v1 披露段一处事实错误(必修小修,不阻塞 V2 上墙)。**

### 1. 新三元组外部视角直验:2/2 VALID

不走 from_hex、不碰 seed,直填 pub bytes → ed25519 verify
(pub=be070105…ed102):

- SELFTEST_SCORECARD_V2.md:**VALID**,sha=03e42491…eb6feb21,n_records=38
- SELFTEST_SCORECARD.md:**VALID**,sha=22a70b20…4fd60d13,n_records=44
- 交叉:新签在旧 pub(8cf767…)下均不通过 → 密钥确已轮换,非换标签
- 私钥卫生:seed 在 ~/.claude/.cache/bc1_scorecard_seed.hex(32B,
  pub_from_seed(seed)==published pub 实测);git grep 证 be070105 仅出现于
  .pub 文件,seed 未入仓
- 所验字节 = bdff7f90 HEAD 字节(worktree clean),签名链已冻结在提交

### 2. 根因法证确认(独立重现,不采信自报)

- **V2 根因实锤**:旧 V2 签名(f65feb9d…)在 pub_from_seed(旧pub
  8cf767…)下对旧 md(75900f1 字节)payload **验过**,在旧 pub 下不验
  →「from_hex(pub 文件误作 seed)」成立;签字自验走同一错 KeyPair
  (其 pub 由错 seed 派生)→ 假 VALID 机制成立。V2-1 假说「签字侧密钥
  不对」方向正确,机制修正为 from_hex(pub-as-seed),非 ctor 重生成路径。
- **v1 初版签名密钥无误(法证)**:旧 v1 签名(125903e5…)在旧 pub 下
  对改前字节(41c135b4…)验过、在 pub_from_seed(旧pub) 下不验 →
  v1 断链根因确为 09:41 改 sha 行未重签(V2-1 连带发现记录无误)。

### 3. 披露段核对:V2 一致;v1 一处事实错误(RED 点)

- V2 末「签名记录」段与事实逐点一致:根因(已法证)/复算抓出属实/
  专用密钥重签+外部直验 VALID 属实/「留档不删」实践到位。
- **v1 披露段照抄 V2 根因**:「初版签名密钥使用错误(pub 文件误作
  seed,自签自验同错路未暴露)」对 v1 与法证相反(v1 初版密钥正确),
  且 v1 真实根因(09:41 改 sha 行未重签)只字未提——与 bdff7f90
  commit message 自身表述("v1 系改 sha 行未重签")矛盾。建议:改
  v1 披露段一行 → 第三次重签 v1(改文必破现签)→ 本节快验一次收口。

### 4. 装版确认

jev-trust 0.2.1 已装,`KeyPair(pub=…)` pub 保留实测通过——V2-1
探针自纠所踩的装版坑已消除。

### 5. 不受影响项

修复仅触 5 个签名相关文件;decision_set.json/答卷/判分器未动,
V2-2(18/18 逐位复现)/V2-3(version=v2·public=18·sha=3b9def7d)/
V2-4(T12 抽查 2/2)全部维持。

**复核数字汇总:双三元组外部直验 2/2 VALID(03e42491…/22a70b20…)/
根因法证 2/2 闭环(V2=pub-as-seed 实锤;v1=初版密钥无误)/ 披露段
V2 一致·v1 一处事实错误 / 装版 0.2.1 pub 保留实测通过。
终判:GREEN(带 1 处 v1 披露修正待办:改行+末次重签)。**
