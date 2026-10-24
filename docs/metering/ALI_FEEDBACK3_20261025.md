# 甲方第三次反馈(2026-10-25)· 六点裁决+平台指南归档

## 六点反馈(用户转述+飞书指南[实测])
1. **0/1 分与比例分并存**(口径确认)
2. **难度精确目标:qwen passrate 25% 或 50%,同时 SOTA>qwen**(比"低 10-20 分"更可操作)
3. **批量生产在甲方"晓天荟聚平台"**(注册→组织→用户组→专家领题→沙箱五脚本流程)
4. **高于 20 分差可接受**(上限松绑)
5. **7 个 badpattern×2 题=14 题,下周五(10/31)前验收通过可收**
6. **先修改试标题,下周一(10/27)快速验收**——通过后走薏帆老师流程

## 晓天荟聚平台标注指南(飞书 CMPvddsJ 摘录)
- 注册:https://www.skyvendorise.com/skyvendor/organization-onboarding
- 流程:标准 harbor 包→code 沙箱→初始化→Terminal 顺序执行:
  1.task-pre-valid → 2.task-build → 3.**task-eval --env ap --providers kimi-k3,qwen3.8,opus5 --count 4** → 4.task-codesense-check → 5.task-submit
- ⚠️ **glm5.3 平台暂不支持**(TODO 参数待确认)——判分渠道带收窄为 k3/qwen/opus!
- 模板:钉钉《harbor-task-template-clean.tar.gz》

## 判读层裁决(产线即刻生效)
- R2 难度带更新:qwen passrate 锁定 25%-50% 区间,SOTA 严格>qwen
- R1 上限松绑:>20 分差可收(下限 10 分仍守)
- 新增 R8(平台合规):批量题必须在晓天荟聚平台跑通五脚本(本地判分为预检)
- 试标题修改列为最高优先(下周一快速验收)
- 7 pattern 待截图确认(已知 feature 六条+第 7 条?)
