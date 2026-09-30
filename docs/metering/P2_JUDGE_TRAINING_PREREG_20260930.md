# P2 预注册 · verdict-judge 基线训练立项(2026-09-30)

> SSI×Jev 提案 P2 阶段。P1 已达标(labelled 1454,目标 500 的 2.9x)。
> 报数纪律:判据先落,只许更严;评估读数原样落盘;非实现者复算收工。

## 数据(已冻结)

- 源:runtime/verdict_corpus/train_set_v0.jsonl(labelled 1454)
- 切分:tools/corpus_split.py · seed=20260930 · 80/10/10 · **qid 分组切分**
  (d12/d14 同题不同 run 必须同折,防 test 泄漏;leak-check 跨折=0 PASS)
- 分布:train 1162(pass 610/fail 546/U 6)· dev 143(71/72/0)· test 149(78/70/1)
- **已知短板**:U(insufficient_evidence)全库仅 7 条,dev 零 U——U 态为
  探索性指标,不设门槛如实报;扩充路径=v5 errata 活水(gold tier)+歧义题专项标注
- tier:现库全部 gold 级(官方规则/双层复算/人工审计/独立盲评);tier 加权
  留接口,bronze/silver 样本到达后启用

## 模型路线(P2 v1 选 A)

- A(近期):bge-m3 冻结编码 + 三态分类头(1024d→3)——本地可训,
  特征管道与 compass daemon 同源;快出基线
- B(远期):Laya 决策头 LoRA(提案原案)/Qwen 小模型——A 基线立住后启动

## 预注册判据(只许更严)

| # | 判据 | 阈值 |
|---|---|---|
| J1 | test 二值(pass/fail)acc | ≥85% |
| J2 | test 校准 ECE(10 桶) | ≤0.10 |
| J3 | U 态 test 召回 | 探索性,如实报不设门(样本 n=1) |
| J4 | 泄漏纪律 | leak-check 跨折=0(已 PASS 固化);训练过程禁读 test |
| J5 | 数据冻结 | split 文件 sha16 以本档记录;任何数据改动=全部重跑 |
| J6 | 读数落盘 | 评估脚本 stdout 原样 commit,不手工修饰 |

split sha16(冻结):
- 待训练脚本首次运行时 append

## 执行坐标

- 切分:`python tools/corpus_split.py`(幂等,seed 固定)
- 训练+评估:tools/train_judge_baseline.py(P2 v1 待写;输入=split_train,
  早停用 dev,最终一次 test)
- 复算:训练脚本 + split 文件即可复现(权重与读数落 runtime/judge_baseline/)

split sha16(冻结,2026-09-30):
- split_train.jsonl: 35683198dd3c4992
- split_dev.jsonl: 942e4daeaedca2fb
- split_test.jsonl: 4bcaf1c9b551f336
