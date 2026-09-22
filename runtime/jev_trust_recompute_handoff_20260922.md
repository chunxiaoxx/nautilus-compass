# jev-trust 三域非实现者复算交接档(2026-09-22)

> 纪律:本档只给坐标、判据与命令。**不含任何预期读数**(复算者先独立算,
> 后对拍)。判据正本 = 各域 PROTOCOL.md(只许更严)。
> 复算者:新鲜会话/独立上下文,未参与三域任何生成、调用或统计实现。

## 被复算对象(三域)

| 域 | 工件目录 | 判据正本 |
|---|---|---|
| python-exception-prediction | `runtime/jev_trust_dogfood_20260922/` | 同目录 PROTOCOL.md |
| code-patch-behavior | `runtime/jev_trust_domain2_20260922/` | 同目录 PROTOCOL.md |
| embodied-qc-labeling | `runtime/jev_trust_domain3_20260922/` | 同目录 PROTOCOL.md |

每域五件套:decision_set.json / session.jsonl / session.jsonl.sig /
pubkey.txt / stats.json(实现者输出,仅作最后对拍用,**先别打开**)。

## 复算步骤(每域依次,先证伪自己探针)

1. **验签**:`pip install jev-trust` 后
   `verify_log(session.jsonl, session.jsonl.sig, pubkey.txt 内容)` → 三态。
2. **决策集完整性**:decision_set.json 的 sha256 应与 stats.json 里
   `decision_set_sha256` 一致(先算哈希再开 stats.json)。
3. **真值独立重推**(不信任生成器标签):
   - 域1/域2:exec decision_set 内 state 的代码,实际调用重推 truth
   - 域3:按 PROTOCOL.md 四规则独立实现 verifier,重推每条 truth
   - 与 decision_set 的 truth 字段逐条对拍
4. **读数独立重算**:解析 session.jsonl 的 call+outcome 行,按
   PROTOCOL.md 写死的公式手算 accuracy / Brier=mean((1−p_true)²) /
   ECE(10 桶 top-label) / C=1−ECE。**先记录独立结果,再打开
   stats.json 对拍**。
5. **无选择性报告核查**:session.jsonl 行数 = call 120 + outcome 120;
   decision_set n=120;error 行如实存在(若实现者声称 0 错误,核
   session.jsonl 无 error 记录)。
6. **结论**:每域 GREEN(全过)/ RED(任何一处不符,先证伪自己探针再报)。

## 输出

`RECOMPUTE_REPORT.md` 落各域目录(或汇总一份到
`runtime/jev_trust_recompute_report_20260922.md`),含:验签三态、
sha 对拍、真值重推失配数、四指标独立值 vs stats.json 值、GREEN/RED。
