# jev-trust v0.2 双极性实测 · 非实现者复算(2026-09-23)

> 复算员未参与实测的生成、调用或统计。只信工件与判据,不信自报。
> 对象:本目录 PROTOCOL.md / session.jsonl(.sig) / pubkey.txt / field_results.json /
> sample.json / RESULTS.md / domain1_sym.jsonl(.sig) / pubkey_d1.txt /
> domain1_sym_results.json / domain1_sym_check.py / field_run.py;
> 上游原件:../jev_trust_domain3_20260922/ · ../jev_trust_domain4_20260922/ ·
> ../jev_trust_dogfood_20260922/。

## 终判:GREEN(复算通过)

六步全部独立复现,RESULTS.md 全部头条读数逐项对拍一致。发现两处文档级
小瑕(不影响任何读数,见「瑕疵记录」)。

---

## 第 1 步 · 验签两份日志(双实现)

先 jev_trust 0.2.1 `verify_log(log, sig, pub)`,再用 cryptography 库
Ed25519 独立第二实现交叉验签(负载=回执 canonical_json
`{log, sha256, n_records}`,从源码 receipt.py 坐实,非猜测)。

| 日志 | sha256 | jev_trust | cryptography 独立实现 |
|---|---|---|---|
| session.jsonl | b8be0c4fc3e0b626c46754b1b300cb4f139aeb71ea12b4d75378571fa967bcf2 | VALID | VALID |
| domain1_sym.jsonl | d8293cf9f71166fe36c12c6368ff3dc00c3682b7f244c27f4f5c38339cf89f6a | VALID | VALID |

n_records:50 / 20,与行数一致。两份日志未被事后改动。

复算员探针自纠记录(红灯先证伪自己):第二实现初跑对 raw 文件字节与
sha256 摘要两种猜法均 invalid → 查源码证伪探针(签名负载是回执 JSON 非
文件原文)→ 按正确负载重跑即 VALID。另两次探针自身 bug(Ed25519 构造
API 用错、f-string 括号笔误)均先修探针再下结论,未误判被测物。

上游三份参照日志(domain3 / domain4 / dogfood 的 session.jsonl)同法验签
均 VALID;d4 stats.json 内记的 decision_set_sha256 与域 3 decision_set.json
实际 sha256(4af6c5a80ce5328e…)一致——分组所依赖的域 4 行为与域 3 真值
原件可信。

## 第 2 步 · 抽样核:sample.json 50 题与域 3/域 4 按声明规则对应

独立重放 pick_sample 逻辑(域 3 decision_set 全 120 题 + 域 4 call 行;
域 4 语义 yes=OK,domain4_run.py 源码坐实):

- spike 缺陷 15 = 域 4 漏 14 + 检出 1(sp011)——与 PROTOCOL「漏 14+检 1」一致
- stuck 缺陷 15 = 域 4 漏 13 + 检出 2(st002, st005)——与「漏 13+检 2」一致
- clean = smooth/noise 前 20 = sm000–sm019(全 smooth),域 4 对这 20 题
  全部判 OK(「域 4 全对」对照组声明成立)
- 重放得到的 50 个 (qid, group) 与 sample.json **逐项全等**,无缺无重;
  truth 字段与域 3 decision_set 全等
- 问法措辞:field_run.py 的 SPEC_REVIEW 与域 3 SPEC、SPEC_OK 与域 4
  SPEC_OK **逐字节相同**(ast 提取常量比对)——「不自创新措辞」声明成立

随机抽 5 题交叉(sp012/sp007/sp009/sm011/sm007,seed=20260923):
missed 组 3 题域 4 均 yes(OK)、clean 组 2 题域 4 均 yes(OK)——分组与
域 4 会话行为全部 MATCH。

## 第 3 步 · 冲突率独立重算(session.jsonl 50 call 行,对拍 field_results.json)

- 50 行全为 kind=call,qid 覆盖 sample.json 无缺无重;tokens 非零
  (input≈720–744 / output=44 每行,非"tokens=0"假调用);ts 单调
  (16:52:47→16:53:41),与 run_log「55s」相容;field_results.json 无
  error 行(「0 错误」成立)
- 仪器内部字段自洽 50/50:opposite_mapped == 翻转(opposite_decision_raw),
  polarity_consistent == (decision == opposite_mapped);定义已对照 0.2.1
  源码 decide_symmetric 坐实(mapped=翻转(反向答案),consistent=(正向==mapped))
- 逐题对拍 field_results.json:polarity_consistent / conflict /
  sym_decision_says_defect / group / truth 五字段 50/50 全等

分组重算(独立数出,再对 RESULTS.md):

| 组 | n | 复算冲突 | 复算率 | RESULTS.md | 对拍 |
|---|---|---|---|---|---|
| 全部 | 50 | 49 | 98.0% | 98% | 一致 |
| 难组(spike+stuck 缺陷) | 30 | 29 | 96.7% | 97% | 一致 |
| —域 4 漏检 | 27 | 27 | 100% | 100% | 一致 |
| —域 4 检出 | 3 | 2 | 66.7% | 67% | 一致 |
| clean 对照 | 20 | 20 | 100% | 100% | 一致 |

一致时判定正确率:唯一 consistent 题 sp011(decision=yes=缺陷,truth=1)
= 1/1,与 RESULTS「1/1(样本无意义)」一致。

## 第 4 步 · 对照域 domain1_sym.jsonl(20 题)

- 20 行 kind=call,qid e1-zd000…e1-zd019 与 dogfood decision_set 的
  zerodiv 20 题一一对应,truth_raises 与原件真值全等
- 内部字段自洽 20/20;逐题对拍 domain1_sym_results.json 全等
- **冲突 0/20(0%),一致时准确率 20/20**(19 题 truth=0 判不抛,
  zd017 truth=1 判抛)——与 RESULTS.md「0% 冲突 / 20/20」一致

## 第 5 步 · 三源交叉抽验(今天 normal≈域 3,flip≈域 4)

逐题(今天的 normal 侧 vs 两天前域 3 会话 | 今天的 flip 原文 vs 两天前域 4 会话):

| 题 | 组 | normal vs 域3 | flip vs 域4 |
|---|---|---|---|
| sp000 | spike-missed | yes = yes 一致 | yes = yes 一致 |
| sp011 | spike-caught | yes = yes 一致 | no = no 一致 |
| sm000 | clean | yes = yes 一致(review 误报复现) | yes = yes 一致 |
| st002 | stuck-caught | yes = yes 一致 | yes ≠ no **不同** |
| st005 | stuck-caught | yes = yes 一致 | yes ≠ no **不同** |

全量 50 题扫描(超出 3 题要求):normal 侧与域 3 一致 **50/50**;
flip 侧与域 4 一致 **48/50**,不同者恰为 caught 组的 st002、st005 两题
(今天 flip 侧说 OK、两天前域 4 说缺陷)。RESULTS「单次调用内复现两域
完整分离、大方向不变」的结论在全集上成立。

## 第 6 步 · GREEN/RED

**GREEN。**判据逐条:

1. 两份日志双实现验签 VALID;
2. 50 题抽样与域 3/域 4 原件按声明规则逐项对应(含 5 题交叉);
3. 冲突率五档(98/97/100/67/100)独立重算与 RESULTS.md 全部一致;
4. 对照域 0% 冲突 + 20/20 准确复现;
5. 三源交叉:极性分离可复现(normal 50/50、flip 48/50);
6. 工件链完整:域 4 分组依赖的上游日志亦验签 VALID,decision_set sha 对账一致。

## 瑕疵记录(不改变终判,建议原作者顺手修)

1. **PROTOCOL.md L17 笔误**:「A+B=难组(29 漏/3 检)」按其自身 A/B
   定义应为 **27 漏/3 检**(14+13 漏);RESULTS.md 正文用的是正确的 27。
2. **RESULTS.md 三源注记覆盖不全**:「st005 一题 flip 侧与域 4 不同」
   系其 4 题抽样的口径;全量为 **st002+st005 两题**(均在 caught 组)。
3. 版本口径:RESULTS 自报仪器 0.2.0,工件未内嵌版本号,无法从工件独立
   坐实(复算用 0.2.1 验签路径,格式兼容)。后续 run 建议把版本写进日志行。

## 复算环境

- Python 3.13 · jev-trust 0.2.1(PyPI,`verify_log` + 源码对照)
- cryptography 库 Ed25519(独立第二实现,负载构造从 receipt.py 坐实)
- 命令式重放:解析 jsonl/decision_set 全部独立脚本,未复用 field_run.py
  的统计代码
