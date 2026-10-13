---
name: orgfuel-ORGQ-R41-fc8126b08e
description: "### R41 · 2026-10-02 21:4x-22:2x(主线轮·P0-full 提取当夜执行:F2 大幅 PA"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R41
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R41 · 2026-10-02 21:4x-22:2x(主线轮·P0-full 提取当夜执行:F2 大幅 PASS+二次探针勘误)
- 双前置 21:4x 齐备:双下载完成(Q14 28G/Turbo 29G "Snapshot ready")+**G1 停=空窗出现**——立即启动(空窗随时被 v5 抢);MemOS #2440 提前查=零回应关单归档(撒网负样本,不追)
- q14 提取 88 秒完成(F1 零失败,40 层倒数第二层 mask-mean,双侧 1454×5120 落盘,ids_sha16 双端一致)
- 🔴**eval 首版 hit@5=0.0 红灯→证伪自己抓到探针 bug**:fill_diagonal 屏蔽金标对后仍判命中,hit@5 数学恒 0——**承自 a2v4 同一 bug,A2-v4 的 0.0 读数作废**(其 RED 依据链修正为仅 v0 簇级模板缺陷);本日"红灯先证伪自己"第二次生效(A 系列两 RED 全是探针)
- **修复后 F2 定谳:q14 hit@5=985/1454=67.74%,p≈0,大幅过 5% 门——P0 检索头路线成立,进 P1(锚点+逆跳步)**;判据档 §6 落读数与二次勘误
- F3 turbo 未完成:Turbo=Qwen3.5 架构完整主干(qwen3_5 类),transformers 4.57.6 不识别;修复案=venv 隔离装新版(共享环境不动),留新会话;BGE 对照腿(v0.1+修复探针)后台重测中
- M1:+(F2 主判据定谳 PASS+P1 门开;同日抓两探针 bug=判据纪律连续兑现)
