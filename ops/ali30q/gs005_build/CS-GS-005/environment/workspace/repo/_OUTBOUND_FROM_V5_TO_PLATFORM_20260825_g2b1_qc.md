---
trace_id: g2b1-qc-v5-20260825
frame: 2026-08-25
source_repo: nautilus-v5
maturity: verified
proof: "g2b1_fuel_nautilus-v5.jsonl 32 题全量双门自检(worktree@buggy_commit+fix版测试→门1必败;git diff buggy..fix 全量应用→门2必过):31 OK / 1 坏。工具 fde_capsule/_g2b1_consistency_check.py(会话提交)"
---

# OUTBOUND · V5 → platform · g2b1 燃料 v5 仓 32 题正解一致性自检结果

## 读数
- **31/32 OK**(96.9%):starter 必败 ✕ 正解必过 双门全过
- **1 坏**:`g2b1:7eed69f1f35f`(genopt re-baseline 提交:改 baseline json+evaluate+test)——正解应用后仍 1 failed。该类"re-baseline"提交本身非干净 bug fix,**建议从燃料池剔除或换干净 fix commit**

## 两个流程发现(供矿机出厂门)
1. **多文件 fix**:初期 2 题"假坏"是只替换 starter 单文件导致——已修为应用 fix 完整 diff。**矿机挖题时应记录 fix 是否多文件;多文件题的 verifier 需要 repo 全上下文**(这也是 pytest 适配器要处理的形态)
2. **第三方依赖**:2 题收集失败是本地缺 python-pptx/matplotlib——**建议矿机导出时附 requirements 清单**(测试文件的 import 依赖),否则跨环境复现会假失败

## 下一步
- v5 仓 31 题可用;core(27)/compass(17)/fde(10) 54 题同法待检(工具已就绪,一条命令)
- 剔除 7eed69f1 后即可进入拒绝采样(题×80 轨迹)
