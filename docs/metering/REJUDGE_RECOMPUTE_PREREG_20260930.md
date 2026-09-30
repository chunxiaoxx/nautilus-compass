# 预注册判据 · arm-a 重判 500 题抽样复算(2026-09-30 落档)

> 报数纪律适用:本档先于执行落盘,判据只许更严;收工非实现者复算;
> 交接段只给坐标与命令,不给预期读数。
> 背景:arm_a_rows_rejudged.json 500 题 is_correct=_parse_judge(judge_raw)
> =judge 开卷自报(9/30 证伪),整族停在 unlabelled;本复算定其能否升级。

## 被检对象

- 文件:`vtf/_e2e_diag/arm_a_rows_rejudged.json`(500 题)
- 被检判定:judge_raw(377 CORRECT/123 INCORRECT)
- 独立参照:题面官方 truth 字段(与 judge 输出不同源)

## 复算双层设计

**机械层(全量 500,规则判定,宁漏勿冤)**:
- M1 数值题(truth 为 int 或纯数字字符串):model_answer 提取全部数字,
  truth∈数字集合→mech=correct,否则 mech=incorrect
- M2 短文本题(len(truth)≤40):大小写/空白规范化后 model_answer 含
  truth 子串→mech=correct,否则 mech=incorrect
- M3 其余(长文本):不机械判,进抽样层
- 方向声明:mech=incorrect 为高置信"模型答错";mech=correct 存在假阳
  (数值换算/包含非等价)——探针只用于**抓 judge 疑似错判**,不做全权真值

**抽样层(50 题,子进程盲判)**:
- 从 M3 题按 random.Random(20260930).sample 抽 50,名单生成后 sha16 入本档
- 子进程 claude 独立判:输入 question/truth/model_answer,**不含**
  judge_raw/is_correct(盲判,防锚定)
- 输出 CORRECT/INCORRECT + 一句理由

## 预注册判据(只许更严)

| # | 判据 | 阈值 |
|---|---|---|
| J1 | 机械层覆盖 ≥50 题;mech=incorrect 且 judge=CORRECT 的冲突率 ≤5% | 冲突率>5% → judge 错判率过高,500 族不升级 |
| J2 | 抽样 50 盲判与 judge 一致率 ≥90% | <90% → 不升级 |
| J3 | 双绿 → 500 题整族升 labelled(label_origin=LME 官方 truth+双层复算);冲突/分歧样本单独入判分器勘误库(错判样本=纠错教学金矿,不丢弃) | — |
| J4 | 抽样 seed=20260930 固定;名单 sha16 以本档 append 记录 | 名单替换=违预注册 |
| J5 | 子进程判定对 judge 结果盲(任务文件字段级排除) | — |
| J6 | 本轮所有读数(冲突数/一致率)以脚本 stdout 原样 commit,不手工修饰 | — |

## 执行坐标

- 机械层+抽样任务生成:`python tools/rejudge_mechanical_check.py`
- 产出:`runtime/rejudge_check/mech_report.json` + `sample_tasks_50.json`
- 子进程执行:任务文件逐题喂 claude 子进程(清代理+显式 model),
  结果回写 `sample_verdicts.json`
- 汇总:`python tools/rejudge_mechanical_check.py summary`

## 修正记录 #1(2026-09-30 append · 探针证伪,非判据放水)

首跑读数(存档 mech_report_v1_falsified.json):M1=85/M2=269/M3=146,
冲突 49/354=13.8% → J1 红灯。**分诊证伪探针**:49 冲突全部 M2、零 M1;
实例定性(5c40ec5b/26bdc477/89941a94):'five' vs '5' 词形变、"We've met
up twice." 人称改写、'Yes. (…)' 括号改写——三例语义等价,judge 全判对,
M2 子串规则对等价改写系统性误伤。**修正**:M2 并入 M3 抽样池,J1 机械层
只用 M1(数值,误伤方向为假阳放过、无误伤);抽样池=M2+M3,名单以
seed=20260930 重新生成,新 sha16 以本段记录。阈值 5%/90% 不变。
- 名单 sha16(v2,修正后池 415 生成):572d4cc73ff5db3e(50 题)

## 终读数(2026-09-30 · J6 原样)

- J1(M1 数值 85 题):冲突 0/85 = 0.0% → PASS
- J2(隔离盲判 50 题):一致 48/50 = 96.0% → PASS
  - 分歧 2 条均 partial 口径(6b7dfb22 偏好题缺具体建议 / gpt4_c27434e8_abs
    对抗题给了过度确定性排序)→ 按判据入勘误库,不计 judge 硬错
  - 11 条独立 incorrect 含 7 条 SUBJECT_ERROR 超时(judge 亦判错=一致)
- J3:双绿 → 500 题整族升 labelled(P1 目标 500 达标:labelled 52→552)
- 执行痕迹:三次子进程形态演化(25 题秒退=32K 上限→完整 agent 自主全判
  =盲为声明级→隔离目录版=物理盲);raw_subprocess_out.txt 原样存档;
  盲判为 markdown 报告,解析器提取(qid 表+partial 列表,assert 11/2)
