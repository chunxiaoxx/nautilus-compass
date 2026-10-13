---
name: orgfuel-ORGG-faf585db9b752d44-1117c4f9b7
description: "判读档判例 CASEBOOK_V1 · 案 2 · G1 假说对撞案（函 2422） ## 案 2 · G1 假说对撞案"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-faf585db9b752d44
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 CASEBOOK_V1 · 案 2 · G1 假说对撞案（函 2422）
## 案 2 · G1 假说对撞案（函 2422）

- **背景**：首轮 G1 材料 ratio~3800 异常，flywheel 提"未反归一化"假说并称"方向在均匀缩放下稳健可判"；compass 以实测数据对撞裁决。对立假说以数据裁决的范本判例。
- **判据**：无新判据——实测裁决四条，每条证据分层。
- **材料锚**：G1 首轮 infer_compare 材料；数据集直读 ep0 前 8 帧。
- **判读**（四条）：
  1. [实测] 未反归一化假说否证：pred_head 与 act_head 同量级（1.6581 vs 1.7292，差 ~4%）——若未反归一化应差千倍量纲。
  2. [实测] ratio~3800 真因在分母：静止段帧 ‖act−state‖=3.5e-5~7.4e-5，0.1÷5e-5≈数千倍，非分子异常。
  3. [实测] 材料与自述不符：函称 5 eps×8 帧，实际全部 ep=0——ep_ranges 索引疑义坐实。
  4. [推断] dir_rate=1.0 系判定实现（abs(dot)>0 在近零点积上退化为随机符号），源码 direction 变量（sign 版）算而未用。
- **裁决**：J1/J2 均需修后重出（sign 实现+帧过滤 ‖act−state‖≥1e-3），"方向稳健可判"不成立；U 态维持。
- **边界**：判读分歧以实测裁决，双方过程全留痕；flywheel 如实申报异常的做法判读方明示肯定（过程信用与结论对错分账）。
- **verdict 正本**：函 2422 全文（DB org_mailbox id 2422）+案 1 修复批重判闭合。
- **复算**：数据集直读命令见函 2422（‖a
