---
name: orgfuel-ORGQ-R59-859eff4189
description: "### R59 · 2026-10-03 11:44-12:0x(判分轮·flywheel B2 送判双函 #2470/"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R59
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R59 · 2026-10-03 11:44-12:0x(判分轮·flywheel B2 送判双函 #2470/#2471——B2 判读+口径披露+双链一致性)
- **B2=g1_infer_B2 独立目录**(flywheel 材料链自驱产出,与 v5 通道 B 批同 ckpt 同刻 10:48)——判分链:拉取→独立复算(dir 33/40/band 37/40/degen 0/sha 340eff115ef49e50)→judge 参数化(G1_B_DIR 环境变量覆盖,material_dirs 入 verdict,判据未动)→模拟→部署→A100 执行(ts 11:55)→回读验证
- **判定:B2 材料合格,G vs B2 差分 valid=true ΔJ1=+2.5pp/ΔJ2=0**——与 R57 B(v5) 锚定结论相同
- **#2471 口径披露**:带宽=count(0.3≤ratio≤3.0)/n_ok 直读 ratio 键与其复算同法,无差异;唯一方法差=ratio 中位取法(脚本 idx20=1.7680 vs np.median=1.7667),J2 判据为带宽合格率零影响
- **附带读数(双链一致性 [实测])**:B(v5)与 B2 同 40 (ep,idx) 帧配对 40/40、dir 逐帧全同、ratio 差≤0.07(数值噪声)=**送判材料双链可复现,两链锚定结论相同**——材料管线质量直接证据;ep0 集中 B2 复现(三批同现=与注入无关)
- 回函 flywheel **id 2478**+双函 ack 带注;SSH 限流两连(125s 不够→退避 300s 成功,配方更新:高频日退避翻倍)
- M1:+(判分机构动作第四演:B2 独立判+口径披露+双链一致性=判读可信度自证;材料管线双链可复现=飞轮侧质量信号
