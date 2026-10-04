# L1 主流评测集登记 · 判据冻结注记 v1(SWE-bench Verified / GAIA / Terminal-Bench)

> 地位:PMF 主线 L1 件(platform benchmarks 端点回填正本,10/8 死线;用户拍"榜单开张先落判据"延伸)。
> 原则:判据主权在 compass;上游坐标=公开事实;口径冻结后只许更严,放宽须重预注册。榜判据总纲见 `LEADERBOARD_PREREG_CRITERIA_V1_20261005.md`(sinks 第 6 件),本档=三件的期判据。
> 上游坐标核验:2026-10-05 curl 实测(swe-bench/SWE-bench 原 princeton-nlp 重定向 301;HF gaia-benchmark/GAIA gating 防爬声明在卡;laude-institute/terminal-bench)。

## 一、SWE-bench Verified

- **上游正本**:HF `princeton-nlp/SWE-bench_Verified`(500 题,OpenAI 2024-08 人工验证 subset);判分引擎 swe-bench/SWE-bench(301 实测自 princeton-nlp 迁移);官方榜 swebench.com。
- **criteria_version v1 冻结口径**:主指标=**resolved %**(FAIL_TO_PASS+PASS_TO_PASS 单元测试全过);harness=官方 run_evaluation 栈(候选 agent harness=mini-swe-agent)钉 release tag;单 run 起步(k=1),k>1 时报 mean±spread;模型训练截止披露强制。
- **污染风险与对策**:①题目源自公开 GitHub issue——对策:报告模型 cutoff 与数据集发布(2024-08)关系,cutoff 晚于发布者标注"泄漏风险"进观察区;②harness 提示词差异——对策:harness 版本+agent 配置随成绩行公示;③容器架构——对策:linux x86_64 标准容器,环境哈希随行。
- **U 态条款**:官方评测栈大版本变更而未复跑=旧成绩转观察区。

## 二、GAIA

- **上游正本**:HF `gaia-benchmark/GAIA`(450+ 题,validation 165 题公开含答案/test 集答案不公开走官方 leaderboard;gating 防爬,不转载题面);官方 scorer 随数据集卡。
- **criteria_version v1 冻结口径**:主指标=**exact match**(官方 scorer 口径:数字/字符串规范化匹配);主轨=**validation 165 实测**(compass 自跑可复算);test 成绩只收官方 leaderboard 截图/URL,标 [不可验] 挂引用不入名次(UNVERIFIABLE 墙);level 1/2/3 分层申报;agent 工具栈(搜索/代码执行)配置随成绩行公示。
- **污染风险与对策**:①题面公开+2023 发布——对策:cutoff 晚于 2023 者标注"记忆风险",优先引用其在 test 官方榜成绩作交叉;②爬虫禁令——对策:compass 不转载题面,测评环境内用后即弃,成绩行只报数与配置;③工具差异——对策:是否联网/执行沙箱两项强制披露。
- **U 态条款**:scorer 口径变动未复跑=转观察区。

## 三、Terminal-Bench

- **上游正本**:GitHub laude-institute/terminal-bench(repo id 918420677 实测);任务集+官方 harness(terminal-bench CLI)+每任务官方 verifier;任务集持续扩张,版本敏感。
- **criteria_version v1 冻结口径**:主指标=**task resolve rate**(官方 verifier 判过);harness=官方 CLI 钉 release tag;**任务集钉 dataset 版本 tag**(成绩行必示 tag,防跨版本不可比);单 run 起步,agent 配置(模型/工具)全披露。
- **污染风险与对策**:①任务公开可被训练——对策:cutoff 晚于任务集 tag 发布者标"泄漏风险"进观察区;②verifier 版本漂移——对策:verifier 随 dataset tag 冻结,tag 升级=旧成绩转观察区;③环境侧信道——对策:容器镜像 digest 随行。
- **U 态条款**:任务集大版本迁移未复跑=转观察区。

## 四、登记元数据(端点回填用)

| 集 | 上游坐标 | criteria_version | preregistered_hash | 污染对策 | 状态 |
|---|---|---|---|---|---|
| swe-bench-verified | HF princeton-nlp/SWE-bench_Verified + swe-bench/SWE-bench | v1(本档§一) | 本档 sha16 | cutoff 披露+harness 版本公示 | planned→live(回填后) |
| gaia | HF gaia-benchmark/GAIA | v1(本档§二) | 本档 sha16 | validation 主轨+test 不可验墙+工具披露 | planned→live(回填后) |
| terminal-bench | laude-institute/terminal-bench | v1(本档§三) | 本档 sha16 | dataset tag 钉死+verifier 冻结 | planned→live(回填后) |

- pusht-frame-v2 preregistered_hash:deferred→**sha16 化承诺随本档一并回填**(冻结函 #2610/#2574 链,取其判据档现值算 sha16,10/6 端点操作时执行)。
- 版本:v1(2026-10-05);改版按活性机制回函+新 sha16。
