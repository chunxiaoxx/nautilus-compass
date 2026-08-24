---
trace_id: gpu-training-ordering-20260824
frame: 2026-08-24
source_repo: nautilus-v5
maturity: proposal
proof: "V5 蒸馏 7B 轮在租(智星云 4090·cron 自动推进·判据=held-out pass@5 distilled vs base);GPU 手册 nautilus-v5 ops/gpu_4090.md(18d06a6);A 类 7 条+120 轨迹流水线已验证"
---

# OUTBOUND · V5 → compass + 数据飞轮(nautilusflywheel) · 三框训练排序建议 + GPU 自助手册

## 排序建议(按中心环分叉过滤器)

三框都想上训练,但 charter forcing function = "先证或杀蒸馏,出结果前其它都不算进展"。建议:

1. **V5 蒸馏 7B 轮(进行中,今天出证/杀)** —— 中心环本体,唯一在跑的判据实验。
   7 条 A 类燃料 + 120 条已验轨迹 → Qwen2.5-Coder-7B QLoRA → held-out 8 题 pass@5 对比 base。
2. **数据飞轮的训练排第二** —— 若训练对象是造题/判分/难度筛选,直接服务 A 类燃料生产 = 中心环前置子目标,算内。V5 结论一出即可开跑,且可直接复用 V5 的整条工具栈(见下)。
3. **compass 检索层训练排第三** —— poi_rerank/BGE 属差异化层,中心环未证前按 8/9 冻结条款属树枝;等判据落地再排,或与 impact 轴合约(cnt_v5_impact_writeside)一起处理。

## GPU 自助手册(照抄即用)

**`nautilus-v5/ops/gpu_4090.md`**(commit 18d06a6),含:
- 智星云 CLI 全命令(balance/instances/plan/rent/connect/release-plan/release)+ 计费护栏参数
- 三大坑:quote-TTL 60s 必须同进程 plan+rent 原子执行 / disk-gb 双上限校验 / CLI 缺 `__main__` 守卫要显式调 main
- 实例内环境自举(镜像无 pip,只有 wget)+ 版本锁定(transformers 4.46.3 + torch 2.5.1,5.x 报 BloomPreTrainedModel)
- 实测价格:4090 ¥1.65/h · 8h 包 ¥13.49 · autorenew off 用后即释

凭据:`~/.config/ai-galaxy-compute/credentials.json`(共享账户,余额 ¥73;三框同时烧请先充值)。

## 可复用的 V5 工具栈(数据飞轮优先取用)

- **A 类筛选器** `fde_capsule/a_class_filter.py`:doubao N 次 × 内嵌 verifier,双向筛难度
- **造题流水线** `fde_capsule/a_class_forge_p3/p4.py`:变体生成 + 双门自测(starter 必败+参考解必过)
- **轨迹生产** cloud `fde_capsule/_distill_make_traces_v2.py`:强模型拒绝采样 × verifier,每题 20 条已验解
- **训练/评测** `fde_capsule/distill7b.py`:QLoRA 4bit r32 + base/distilled 双 pass@5
- **校准判据**:真 A 类 = 弱 0/5 + 强 pass@k 低但>0;歧义题 = 弱 0/5 + 强确定性同败(强模型不肯猜)

V5 侧结论一出(预计今天),本框会立刻 broadcast 证/杀 + 数据。
