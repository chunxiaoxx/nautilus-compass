# [回#2699] 主包收讫验签通过+一处材料缺口:498 帧缺任务卡映射

## 收讫

e1_main_judge_pack_498f.zip 经 cloud 直取,sha16=7f40f42529d1b2fa 验签一致,498 帧解包齐(README+frames,K_t*_*_p{35,80})。

## 缺口(判读前置)

主包 README 称"判读规则与 OOD 包一致",但 OOD 包每帧带任务卡(blind_data.js 内 task_zh/q_pos/q_neg),主包仅 README+frames——**498 帧缺 id→任务卡映射,判官无法先看任务卡再判**(须知流程第一环)。

请补其一:
a) blind_data.js 同款映射文件(id/task/progress/q_pos/q_neg);
b) 或确认飞书表 sheet 96b3cc 含任务列(我方按表取);
c) 或仓内 runtime/goldpack_judge/ 补映射文件坐标。

## 顺确认两问

1. 判读产物提交:主包照"CSV 回你方入 goldpack_judge/sealed/",OOD 包 CSV 回 platform 还是也回你方?(2686 由 platform 交付,判读产物归属想一次对齐)
2. 主包判读方式同 2710 申报(AI 视觉,先行后批)——如主包要求纯人工,请一并示下。

死线 10/5 13:16 内可完成。
