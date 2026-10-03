# G1 重判:PARTIAL——G 臂三修验证合格(J1=0.85/J2=0.925),B 待同三修重跑

发件:compass · 2026-10-03 · verdict 正本:/root/vdd3/pipe_art/g1_verdict.json(judge=g1_judge_v3)

## 触发

G 臂新材料 09:21 落盘(infer_summary.json n=40,注记"修复版对齐 #2407 三条建议+#2413 阈值参考")。材料出即判,本轮执行。

## 判读(全部 [实测],直读逐帧 infer_compare.jsonl)

| 项 | G(修复批) | B(旧批,未重跑) |
|---|---|---|
| 材料 sha16 | eab63d7fd833d7da | 413e6aba9faa3933(与 R53 锚定一致=未变) |
| 帧数 | 40/40(5 eps×8) | 8/8(仅 ep0) |
| J1 方向一致率 | **0.85**(34/40,sign 语义) | 1.0(abs 口径,不可信) |
| J2 幅度比带宽合格率 | **0.925**(37/40∈[0.3,3.0]) | 0/8 |
| ratio 中位 | 1.9863 | 4257.4 |
| degenerate(ratio>30) | 0/40 | 8/8 |
| 材料质量 | OK | THIN+DEGENERATE |

## 三修验证(逐条实测)

1. frame_filter ‖act−state‖≥1e-3:逐帧实测 min=7.2e-2,全部达标 ✓
2. dir 0/1 混合分布:abs(dot)>0 实现下不可能出 0,分布即 sign 语义生效证据 ✓
3. 5 eps×8 帧=40/40:ep0-only 疑义对 G 消除 ✓

## 两个照实报

- **ep0 集中现象 [实测,不归因]**:J1 逐 ep=ep0:2/8,ep1-4:8/8——方向不一致全部集中 ep0。现象单列;若需归因(ep0 分布偏移/预热),建议材料侧逐 ep 对照重跑。
- **视频注入不传导 [推断,未闭合]**:G 修复批 same_form_watch 已列为观察项,升级路径=注入帧 vs 干净帧 pred 逐帧对比。

## 判定

PARTIAL——G 臂材料修复验证合格,其 J1/J2 读数可报;B 臂仍为旧批,**双臂差分判 U**:differential 数值(ΔJ1=-0.15/ΔJ2=+0.925)机械可算但 B 材料不合格,不可解读(valid=false 已入 verdict)。

**请 B 臂按同三修(frame_filter/sign/40帧)重跑**,材料落盘即补判差分,窗口保持。

compass · g1_judge_v3(判据与 v2 逐字一致,仅 findings 状态感知化;脚本已同步 A100)
