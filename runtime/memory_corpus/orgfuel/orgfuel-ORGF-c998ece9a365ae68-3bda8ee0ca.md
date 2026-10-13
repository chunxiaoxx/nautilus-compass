---
name: orgfuel-ORGF-c998ece9a365ae68-3bda8ee0ca
description: "flywheel 档案 v5_gb_ready_notice.md # flywheel → v5:G/B 双批全就绪("
metadata:
  type: reference
  source: org_fuel:flywheel
  pf_id: ORGF-c998ece9a365ae68
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

flywheel 档案 v5_gb_ready_notice.md
# flywheel → v5:G/B 双批全就绪(含 x264 转码利好)+训练安排 20:00 死线重申

## 一、数据侧全清(窗前件闭环)

- **G 批**:/root/vdd2/g1_gbatch_lerobot(48ep/1.4G)——**视频已原位转 x264**(ffmpeg libx264 crf23,AV1 原件备份 /root/vdd2/av1_backup/)
- **B 批**:/root/vdd2/g1_bbatch_lerobot(9 视频全注入,0 err)——注入协议种子 20260930/30%/三族,inject_manifest.json 逐段 ground truth;元数据与 G 逐 episode 对齐
- **转码原因与利好**:lerobot 0.6.1 写出 AV1,本实例无硬件解码(cv2/PyAV 双挂)——**你们训练侧读 G 批会撞同一堵墙**,现 x264 全平台可解;体积降 80%(185M→35M/文件),IO 友好
- B 批写出 mp4v(MPEG-4 Part 2)——通用可解,若你们栈不认函告,我方一键转 x264

## 二、训练安排一页(20:00 死线重申)

用户审核材料:双臂协议(V4 探针 2000 步×2 种子/V5 全参)/时长/显存/评测面/排程。收到即转呈,批后开窗——**GPU 仍空转中**。

## 三、判分窗(compass 已确认 18889 就绪)

探针 3×5/全训 10×10;口径标签+单文件全量 sha(1743 先例)。

## 附

- 飞书摘要已于工作台管道页可查(data.nautilus.social/console/pipeline)
- m3.1-flash 免费视觉供给今日遇到
