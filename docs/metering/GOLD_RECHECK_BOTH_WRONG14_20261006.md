# gold 复核报告:14B/1.7B 双盲区 14 条(2026-10-06,J4-C 零成本件)

> 复核人:compass 判读(逐条读 artifact 原文;14/14 全过,无抽样式省略)。
> 起因:U5 对拍 both_wrong=14 条(R167 对账指其聚 lme 族);J4-C 拍定逐条核 gold。

## 一、逐条分类(全 [实测],材料原文直读)

| 类 | n | 条目 | 复核结论 |
|---|---|---|---|
| **① abstention 族·gold=pass** | 10 | lme-d12/d14 web+ente 10 条(2e67d04f/191184f3/aa8d21f5/0cd6dc43/f90f2255/579557d8/71026f57/247bf724 等) | 回答均为纯弃权型("I lack access to the live environment…"),gold=pass——口径=环境不可达时诚实弃权算对 |
| **② abstention 族·gold=fail** | 1 | lme-d14-web-4b0c5275 | **同族同构**:同为 is_abstention_problem=True、同为纯弃权回答(未给 gold 内容)、同 question_type(dynamic-environment-abs)——官方却判 **fail**(gold="There is no Search button…"即快照可确认答案) |
| ③ 实质回答判读分歧 | 1 | lme-d12-ente-50d92f55 | 非弃权(gold=pass,双模型 fail);材料实质分歧,单条待细读,不入族 |
| ④ 偏好/memory 型·gold 合理 | 1 | rejudge-a89d7624 | 回答非空(推荐 Red Rocks 音乐场),gold=pass 依据用户 live-music 偏好**合理**;双模型判 fail=漏用 memory 上下文——**模型共同盲区,非 gold 问题** |
| ⑤ 引用型 artifact | 1 | bc1-v1-T31-1 | artifact=审计表引用(无可判实体材料),gold=insufficient_evidence(人工审计)——**语料构成问题**:引用型件不应作判分输入 |

## 二、主发现:abstention 族 gold 口径自相矛盾(①vs② 实锤)

10 条弃权回答 gold=pass,1 条同构弃权回答 gold=fail——同 type(dynamic-environment-abs/procedure-abs 混布)、同 is_unknown=False、同"未给答案内容"回答形态。**eval_function 对弃权题的 pass 语义在族内不一致**(或:pass 依赖"快照是否真无答案"的隐式判定,但 is_unknown 字段全 False 无法区分,且 4b0c5275 的 gold 文本型与 579557d8 的 gold 文本型同构——均为"明确答案内容"型)。

**对 U5 对比结论的修正幅度** [推断]:both_wrong 14 条中 11 条处 gold 张力区(①+②),即 −3.77pp 差距的相当部分在 gold 噪声上;"1.7B 仍优"判读不变(non-common 题 only_17b=25 vs only_14b=14 仍指向现役),但**差距幅度存疑,待语料方澄清口径后重评**。

## 三、errata 登记(判绩账第 7 例入口)

1. **gold 张力条**:lme-d14 abstention 族口径矛盾(①②对)——申请语料方(v5/上游 LME)澄清 eval_function 弃权语义;澄清前该族题标 [不可验] 不作判分器差异依据;
2. **语料构成项**:引用型 artifact(bc1-T31-1)不应作判分输入——语料方筛选规则补条;
3. **燃料候选**:memory/偏好上下文利用(a89d7624/09d032c9)——双模型共同盲区=14B 重评(实验 C)与 P3 语料的定向扩容方向。

## 四、对 14B 翻案阶梯的回填

阶梯终局(实验 B 后归因=语料量-参数匹配)再获一证:**U5 差距的噪声成分比首判更大**——重评(实验 C)不仅等语料扩容,更等**本族口径澄清**(errata 条 1)。两条前置都接 P3 燃料线。


## 五、勘误(2026-10-06,函 10058;判绩账第 7 例闭合)

v5 四象限澄清(可答性×行为,函 #10028)收讫成立:10 条 gold=pass=不可答而正确弃权(象限①),4b0c5275 gold=fail=可答而弃(象限④)——**标注一致无矛盾**。本报告第二节"abstention 族 gold 口径自相矛盾"判定**撤回**;矛盾感实为 is_abstention_problem 旗标粒度过粗(题族级),我方复核仅凭旗标+回答形态未取证每题快照可答性=复核深度不足,如实记。该族 [不可验] 标注维持,旗标修题级(语料侧下版)。
