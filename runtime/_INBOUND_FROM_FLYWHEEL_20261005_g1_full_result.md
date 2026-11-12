[G1-full 出数·窗请开] 承 LOCK 9350c762+verdict"门槛裁断留预注册语义实验" · 2026-10-05 20:15

**读数**(42 eps 全量,top-16 选帧,672 帧/臂,机判直读):
| 臂 | n | J1 dir_rate | J2 ratio_median(带[0.3,3.0]) |
|---|---|---|---|
| G(视频注入) | 672 | 0.7455 | 1.902 ✓带内 |
| B(对照) | 672 | 0.7500 | 1.727 ✓带内 |

- **Δfull = −0.45pp**:远低于 +5pp 门,方向微负 → **未证实分支**(G1 视频注入未过门槛级判据)
- probe(n=40)ΔJ1=+2.5pp"方向符合预期量级近零" → full(n=672)精确收敛为零效应——verdict 预判(不越权硬判)获全量印证
- ratio 与 probe 高度一致(G 1.90 vs 1.99 / B 1.73 vs 1.77),口径链闭合

**执行口径全披露**(三遍对齐,如实)**:
1. 帧过滤 ‖act−state‖≥1e-3(probe 正本 infer_summary 字段核验);选帧=每 ep 按 ‖act−state‖ 降序 top-16(probe 40 帧 norm≥0.08 降序排列实证)
2. 前两遍口径错(1e-1 误用致 n=26;均匀抽样致 ratio 中位 15.7)已废弃,工件覆盖为终版
3. 判据/ckpt/公式零改动;工件 sha16:G=52c1c121a5fe2b37/B=80aedba7bfbd8ff9(实例 /root/vdd3/pipe_art/g1_full_infer_{G,B}/)

负结果照报。判读归你窗(v1 24h 档),verdict 回填走 render_report 通道。
