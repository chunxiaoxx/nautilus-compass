# JEV 判分证据包 · {题号}(judgement evidence v1)

> 生成方: compass 判读层 · 生成时间: {ts}
> 判分方式: UT judge(unit_test),全程不使用 LLM judge/rubric(甲方 §2.4)

## 1. 题目身份
- item: {题号}
- badpattern: {甲方机制ID+名称}
- 领域: {D编码·领域名}
- task_type: feature / bug-fix
- 来源: {真实踩坑出处·内部/开源/authored}

## 2. 五模型四轮判分矩阵
| 模型 | run0 | run1 | run2 | run3 | passrate | 均分(二值) |
|---|---|---|---|---|---|---|
| qwen3.8-max | | | | | | |
| glm5.3 | | | | | | |
| kimi-k3 | | | | | | |
| opus5.5 | | | | | | |
| gpt-6-astra | | | | | | |
- 环境指纹: {torch/transformers/pytest 版本}
- 判分器: ut_runner.py sha256 {hash}

## 3. G1-G7 七门判读
| 门 | 名称 | 结果 | 判读依据 |
|---|---|---|---|
| G1 | 区分度 | | |
| G2 | violations | | |
| G3 | gating 触发 | | |
| G4 | 等价变体 | | |
| G5 | 蒙对标 | | |
| G6 | 稳定性 | | |
| G7 | 蒙对率 | | |

## 4. verify 记录(assay 可复算)
- verify_manifest: {路径+sha256}
- replay 命令: {可直接执行的复算命令}

## 5. 证据分层标注(强制)
- 判分读数: **[实测]**(model_solve 自动判分)
- determinism: **[实测]**(ut_runner 三连)
- 区分度判读: **[实测]**(五模型矩阵数据)
- 异常裁决: **[推断]**(判读层分析,附依据)
- 不可验项: **[不可验]**(如实标注,不装确定)

## 6. 附件清单
□ 原始答卷(五模型×四轮)
□ UT 判分结果(junit xml)
□ 反例程序运行日志
□ verify_manifest.json
□ compass 签名(compass 判读岗·时间戳)
