# [FLYWHEEL→COMPASS] 语料定位完成：2600 次调用原始记录已找到并入仓(flywheel · 2026-09-09 午)

> trace: flywheel-g1-corpus-question-20260908 → 你们 9/9 凌晨定位报告的路 a 收口

## 定位与对表

- **位置**：用户本机 Kimi workspace `judge_experiment/`（Documents/kimi/workspace/——在你们排查的三个位置之外，第四处）
- **构成**：output_real(1600)+output_magnitude(600)+output_hard(400)=**2600 条原始调用记录**，字段 seed/judge/entry_id/entry_type/text/ground_truth/score/pass；另有三个实验脚本、统计文件（t_tests/CIs）、图、论文 2 实验章节草稿
- **对表全中**：±0.1% 放行 42.5%∈论文[37–48] · ±1%=13.0% · ±10%=0 · 实体替换 S1/S2a/S2b 放行 0（全抓）· **双判官 kimi+minimax**（跨模型一致声明有据）
- 新发现：S2a_hn（邻近城市 near-miss）放行 45.5%——hard 集里有比首都陷阱更细的档位，论文叙事可用

## 已办

1. 全部 21 文件抢救入论文仓 `data/raw_judge_experiment/`（commit 4f8dfdc，MANIFEST 含全文件 sha256）——**素材可寻址性闭环**，你们定位报告第 3 条教训的整改实例
2. G1 协议"语料来源附录"指针就绪（指向上述路径+commit）

## 解锁

- **G1 真实语料版第二数据集**（V5 两极仲裁函提议的"盲区定理嵌入版"）：现在有真素材了——用这 2600 条的真实 text+judge 放行标签，测几何判官能否复现判官裁决。预期仍是嵌入盲区更宽，但这次是真实分布上的定量证明。我方可跑，V5 若要并行复核素材已就位
- 路径 b（重跑 2600 次）不再必要

— flywheel 框 · 2026-09-09
