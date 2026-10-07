# PRECOR B/C 实验判定表 v1(2026-10-07 · 291 题实测收数)

> 判据正本:PRECOR_JUDGE_ROBUST_20261006.md(预注册,判门=对 bf16-greedy 一致率 ≥99%)。
> 被测物:NACRE 判读实例 v1(Qwen3-1.7B+best_lora,adapter sha16=dbcbab6fd1ff5821,merge 后统一权重)。
> 数据:split_test+split_dev 去重 291 题(qid 防泄漏口径同 corpus_pipeline);模板=训练族 PROMPT_TMPL+sample_text v2(剔 judge_output)。
> 证据层:全部读数=[实测](A100 run.log 终值+一致率矩阵);per-question 翻转清单=[不可验](CSV 增量写缺陷,数据随进程终止丢失;升级路径=补行级写入重跑,判门不受影响——终值读数完整)。

## 一、判定表(实验 B:量化漂移)

| 配置 | 三态 acc | vs bf16 一致率 | 判门(≥99%) | 部署裁定 |
|---|---|---|---|---|
| bf16-greedy(锚) | **0.8797** | — | — | 现役(生产评测 0.885 同域,模板自验证 PASS) |
| fp16-greedy | 0.8797 | **1.0000** | ✅ PASS | **可部署**(零漂移) |
| int8-bnb greedy | 0.8694 | **0.9828**(差 2 题) | ❌ FAIL | **禁上产**(按预注册);可走判据修订序 v2 或灰度披露 |
| int4-nf4 greedy | 0.8694 | **0.9416**(漂移 17 题) | ❌ FAIL | **禁用**(与 E1 4bit=0.8173 漂移信号同向互证) |
| bf16-T0.3 | — | 0.9931 | (披露不判门) | T 采样非零漂移,判读服务维持 greedy |

## 二、结论四条

1. **部署纪律 v1 定案**:判分器生产部署只允许 **bf16 或 fp16**;int8 差 2 题不过预注册门,照 FAIL 报;int4 禁用;
2. **模板复原正确性独立确认**:bf16 三态 acc 0.8797 与生产评测 0.885 同域(PRECOR 自验证门 0.80 过)——E1 复算所用管线与本次管线同模板族;
3. **精度-一致性阶梯实测成立**:fp16(1.0)≫int8(0.9828)>int4(0.9416)——漂移与量化强度单调,方向与 E1 3B 实验互证;
4. **E1 复算 U 态的归因补强**:判分器对量化敏感是系统性现象(两代模型实测),软维度门单列(PRECOR-C 产数)更必要。

## 三、实验 C(软维度双跑一致性)

- bf16-T0.3 vs bf16-greedy 一致率 0.9931=解码扰动实测基线;软维度(连续档)自一致率数据在 CSV 丢失范围,[不可验] 如实标注,升级路径同上。ER 门 v2 数值待 C 补跑。

## 四、复算口径

非实现者新鲜会话可按 PRECOR_JUDGE_ROBUST_20261006.md+本表复算;脚本 runtime/robust_exp/precor_replay_bnb.py(merge 后量化版,A100 /root/vdd4/robust_exp/ 同款);run.log 原件=A100 /root/vdd4/robust_exp/run.log(本地副本 runtime/robust_exp/run.log)。

—— compass · 2026-10-07 · PRECOR-BC-VERDICT-V1
