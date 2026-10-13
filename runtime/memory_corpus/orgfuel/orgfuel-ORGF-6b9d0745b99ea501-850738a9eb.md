---
name: orgfuel-ORGF-6b9d0745b99ea501-850738a9eb
description: "flywheel 档案 loop_night_R166_20261008.md # LOOP 值守轮 R166 留痕 2"
metadata:
  type: reference
  source: org_fuel:flywheel
  pf_id: ORGF-6b9d0745b99ea501
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

flywheel 档案 loop_night_R166_20261008.md
# LOOP 值守轮 R166 留痕 2026-10-08 19:3x(预标注流水线全链闭环轮)

> 用户令"继续推第③件"。当轮从"界面骨架"到"可上岗全链"。

## 本轮动作
1. **复核台 v1.1**:URL 加载框(远程标注员全程浏览器,免传文件);外网部署 **data.nautilus.social/review/**(200)。
2. **真产任务包#1 上线**:batch50 扩样 20 集(ep8/9/14/16/17/19/29/31/32/33/36/37/38/41/42/43/44/45/47/49,均未入 n30)——实例批量抽帧 160 帧(2.6M)→打包 2.9MB→**data.nautilus.social/review/pack_batch50_20.json**(200)。抽帧脚本 runtime/_review_frames_batch.py(帧源=droid_100 本地 snapshot,零下载)。
3. **回流验收闸** scripts/_review_intake.py:A1-A5 五道校验(理由防无脑过/枚举/去重/时长合法/objects 下限)+每第 5 集自动入双人盲核池;合成行红绿双测通过(1 收 3 拒,拒因逐条精确)。
4. **复核岗 SOP v0** 落 docs/SOP(四步工作流+三条纪律+计件建议口径 ¥8-12/集+质量意义)。
5. 打包器升级:--manifest 参数(task/时间戳从抽帧 manifest 补)。

## 流水线全链现状
AI 预标注(batch50/51-100,100 集,已在库) → 任务包(20 集/批,gen_review_pack.py) → 复核台(外网,标注员浏览器
