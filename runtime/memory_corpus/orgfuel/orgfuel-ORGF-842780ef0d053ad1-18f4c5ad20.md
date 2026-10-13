---
name: orgfuel-ORGF-842780ef0d053ad1-18f4c5ad20
description: "flywheel 档案 loop_night_R78_20261005.md # LOOP 值守轮 R78 留痕 202"
metadata:
  type: reference
  source: org_fuel:flywheel
  pf_id: ORGF-842780ef0d053ad1
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

flywheel 档案 loop_night_R78_20261005.md
# LOOP 值守轮 R78 留痕 2026-10-05 晚

## ①信箱
OPEN 0(DONE 4 幂等跳过)

## ②实例三线:UMI 探针 v1/v2 双崩→根修→v3 在途
- v1 崩:DynamicCache.get_max_length(transformers cache API);v2 抄原版 infer 配方仍崩同处
- **根因(镜像仓溯源 _tmp_phi_reboot_launch.py)**:今晨 phi_reboot 成功线解释器=/root/vdd4/venv_phi(transformers 4.44.2 同代 venv,在 vdd3 外故 find 漏);我用错 openpi/.venv(4.53.2,memory phi 止损条本有此坑记录——红绿灯先读档案)
- venv 版本对表:g1_venv 无 tf/venv 5.16.1/venv_fw 5.5.0/venv_groot 4.57.3/venv_phi 4.44.2 ✓
- v3 已发车(venv_phi)+守望一条龙(后台 bvpa43v73,120s 间隔)
- 池 51(20/20/11)与双 lock(UMI v1.1/G1-full v1)上轮已备

## ③最高可动件
venv 溯源修复即本轮实质件;G1-full 材料脚本位置待探(pipe_art/g1_infer_{G,B} 产物在,生成脚本待定位)

## 纪律自查
不代改实验材料 ✓/实例 GPU 在用(探针) ✓/产出到眼前 ✓

## 待下轮
探针 v3 出数→出数函 compass+矩阵 v0.1;G1-full 接力
