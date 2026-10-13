---
name: orgfuel-ORGG-410dcc69cdefbead-87535cb498
description: "判读档判例 PREFOR_JUDGE14B_SMOKE_20261004 · smoke 判据(预注册,只许更严;全部 "
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-410dcc69cdefbead
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 PREFOR_JUDGE14B_SMOKE_20261004 · smoke 判据(预注册,只许更严;全部 [实测] 层)
## smoke 判据(预注册,只许更严;全部 [实测] 层)

| # | 判据 | 门 |
|---|---|---|
| S1 | 训练完成:200 步 QLoRA 零 OOM、零崩溃、正常退出并落 adapter | 必须 |
| S2 | 显存峰值:torch.cuda.max_memory_allocated < 36G(40G 卡留 10% 余量) | 必须 |
| S3 | 收敛信号:train loss 末 20 步均值 < 首 20 步均值(非发散) | 必须 |
| S4 | 判读格式:训毕 adapter 加载,对 judge 语料抽 20 题推理,JSON 判读输出合规 20/20(复用现役 verdict-judge 输出 schema) | 必须 |
| S5 | 读数申报:同 20 题对 gold 一致率**如实入档**;smoke 级不设准确率门槛(small-n 不做升格依据),读数仅供参考 | 申报 |

- **升格决策不在本 smoke 判据内**——smoke 只回答"管线可跑否";若 S1-S4 全绿且拟升格,另立预注册(全量语料+判别力判据)再跑。
- 训练数据:judge 语料(qid 分组防泄漏版)抽 ≤500 条;标签=已固化人工/外部标签;**反自指护栏:判官自产标签不入训练**。
- 时窗:**GPU 空窗即跑(2026-10-05 用户拍)**——脚本自带启动守门(nvidia-smi 显存占用>2G 即退出不训练),B 臂/flywheel 优先不抢卡;撞车风险由守门兜底。执行读数时间戳从服务器头抄。
- 复算:收工走非实现者复算(新鲜会话,只信判据与自测);交接只给坐标与命令,
