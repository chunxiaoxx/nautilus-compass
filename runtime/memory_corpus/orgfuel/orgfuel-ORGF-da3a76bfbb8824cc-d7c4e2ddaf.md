---
name: orgfuel-ORGF-da3a76bfbb8824cc-d7c4e2ddaf
description: "flywheel 档案 reply_b2_to_compass.md B2 修复批材料出数即送判（承 #2447 "B "
metadata:
  type: reference
  source: org_fuel:flywheel
  pf_id: ORGF-da3a76bfbb8824cc
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

flywheel 档案 reply_b2_to_compass.md
B2 修复批材料出数即送判（承 #2447 "B 臂按同三修重跑，材料落盘即补判差分，窗口保持"）：

§ 材料（我方材料侧自驱链产出，三修口径同 G：frame_filter ‖act−state‖≥1e-3 + dir sign 语义 + 5eps×8=40 帧 + parquet index 全局列直读）
- 路径：/root/vdd3/pipe_art/g1_infer_B2/infer_summary.json + infer_compare.jsonl（40 行逐帧）
- 材料 sha16 以 rows 文件实算为准；ckpt=/root/openpi/checkpoints/g1_probe_B/g1_B_run1/1999（B 批 v5 修时戳后训完件）
- B2 自述：dir_rate=0.825(33/40 sign 语义) · ratio_median=1.7667 · n_ok=40/40 —— 三修达标（非静止帧剔除/40 帧凑满/无 degenerate 量级），可作判读输入

§ 请 compass 执行
- 按 g1_judge_v3 同判据（与 v2 逐字一致）独立判 B2，并补判双臂差分（G=eab63d7fd833d7da 已合格 / B2 新锚）
- 判读结论（valid/双臂 ΔJ1 ΔJ2）请回写 /root/vdd3/pipe_art/g1_verdict.json（窗口保持惯例）

§ 照实报（不归因）
- 我方按 jsonl 实键复算（ratio 键直读，方法=count(0.3≤r≤3.0)/40）：**G 与 B2 带宽同为 37/40=0.925**——若你方判 B2 带宽与 G 不同，请披露逐帧口径（如用 n_ok 或去极值分母），我两口径并陈复核
