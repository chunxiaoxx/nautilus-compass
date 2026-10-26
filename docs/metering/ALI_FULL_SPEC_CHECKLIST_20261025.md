# 阿里 CodeSense 30 题 · 甲方完整验收规格 Checklist V1(2026-10-25 判读层从 1012 全文逐条提取)

> 来源: docs/metering/ali_docs/ali_1012_txt_full.txt(661 行全文)
> 用途: 每题出包前逐条过——全部 PASS 才发运

## §A 五件套结构(Harbor 1.4)
- [ ] A1 schema_version = "1.4"(非 1.3!)
- [ ] A2 task.toml 元数据全字段(badpattern/focus_points/trap_type/code_origin/code_license/source_note)
- [ ] A3 instruction.md(模型可见)+ tests/(模型不可见)
- [ ] A4 标杆校准四件套(满分/缺陷/蒙对/等价变体,各附逐条打分单)
- [ ] A5 包外证据包 + 批次清单

## §B UT 规格
- [ ] B1 ≥21 独立 test_* 方法
- [ ] B2 UT 覆盖 badpattern 每处下游/相关改动点
- [ ] B3 主分=UT 通过率(不用 LLM judge/rubric)
- [ ] B4 gating UT 一票否决标记
- [ ] B5 等价变体≥2 个,各自过全部非 gating UT
- [ ] B6 陷阱反例程序可执行+真实运行日志
- [ ] B7 蒙对率检验:模板化答案不能拿及格分

## §C 内容规格
- [ ] C1 ≥40%(12/30)题内嵌错误前提或半错断言
- [ ] C2 ≥3 题内嵌明确错误前提(正确行为=拒绝)
- [ ] C3 挑战不得泄题(不点出正确答案或陷阱名)
- [ ] C4 expert_design_notes 含区分意图说明
- [ ] C5 expert_design_notes.boundary 语义边界声明
- [ ] C6 陷阱可证性:反例程序+运行日志(stdout/stderr+版本+平台)
- [ ] C7 badpattern≥3 条,tests/assets/ 有真实答卷片段
- [ ] C8 focus_points 显式声明(固定③⑤+选1~3)
- [ ] C9 来源许可证:SPDX/宽松许可/GPL 不收
- [ ] C10 脱敏(去除真实凭证/主机名/员工信息)
- [ ] C11 真实仓库>300 文件(建议,非硬门)

## §D 五模型矩阵
- [ ] D1 五模型×4轮全跑(qwen/glm/kimi/opus/gpt)
- [ ] D2 qwen passrate=25% 或 50%
- [ ] D3 SOTA>qwen(passrate 与均分双口径)
- [ ] D4 均分差 10-20 分(>20 可收)
- [ ] D5 跨模型失败集合 Jaccard 距离÷同模型平均 ≥1.25
- [ ] D6 失败 UT 集合数/非全过运行数 ≥50%
- [ ] D7 最大单一失败签名占比 ≤50%
- [ ] D8 pass_rate 平均 <70%
- [ ] D9 至少 2 次非全 1;不可全 1 或全 0
- [ ] D10 opus 至少一次全 1

## §E 红线(直接退回,8 条)
- [ ] E1 纯功能实现题(无语义陷阱)
- [ ] E2 传统 SWE 任务(全测试变绿)
- [ ] E3 纯运维/环境/终端操作
- [ ] E4 纯 API 记忆/版本背诵
- [ ] E5 纯算法竞赛难度(无隐蔽语义陷阱)
- [ ] E6 无唯一/共识答案的开放题
- [ ] E7 陷阱编造无法反例复现
- [ ] E8 UT 断言依赖自然语言判定
- [ ] E9 公开 benchmark 复制(CRUXEval/LiveCodeBench/SWE-bench 等)

## §F 出厂门(我方自检,非甲方要求但为质量兜底)
- [ ] F1 金标自检(solution swap→UT 全过=1.0)
- [ ] F2 坑版部分挂(非全过非全过)
- [ ] F3 conftest.py sys.path 显式
- [ ] F4 知识树四级(knowledge_path/L0-L3)
- [ ] F5 三对号(机制ID×领域×场景)
- [ ] F6 泄题扫描(题面无机制名/golden/exploit 词)
