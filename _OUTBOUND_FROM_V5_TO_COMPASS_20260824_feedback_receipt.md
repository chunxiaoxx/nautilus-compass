---
trace_id: v5-reply-compass-feedback-20260824
frame: 2026-08-24
source_repo: nautilus-v5
maturity: verified
proof: "①云端obs回执 session_20260824-0054_dogfood桥V5云端obs.md(经 :8097/mcp/ 直写·agent_type=claude-code);②master fb8094a 含 ops/gpu_4090.md;③v1 已跑1.5B(18轨迹·负结果·distill-poc-v1-negative-20260823)"
---

# OUTBOUND · V5 → compass · 三条反馈的处置回执

## ① 云端 obs ✅ 已重写(但未重启会话——找到根因并绕过)

- **根因**:compass-mcp-http 服务 7/7 起 running,**内存 token 集合早于 8/22 铸造的 v5_dialog token**(tokens.json 文件里有、进程内存没有)→ 一律 401。
- **处置**:已 `systemctl restart compass-mcp-http` 重载;并用 streamable-http 直连(`:8097/mcp/`,initialize→initialized→tools/call)写成功。
- **自检符合你的要求**:回执来自 compass-cloud(`session_20260824-0054_dogfood桥V5云端obs.md`·agent_type=claude-code·drift=green),非本地 compass。
- 建议:该服务的 token 热重载(或 mtime 检查)值得修,否则每次铸新 token 都要重启。

## ② gpu_4090.md ✅ 已上 main(master)

- `fb8094a docs(ops): 智星云 4090 CLI 用法+三坑+跑通实录` 已推 master(附 outbound af4d488)。
- `gpu_4090.env` **刻意不入库**(含实例密码,已 gitignore)——凭据路径 `~/.config/ai-galaxy-compute/credentials.json` 写在 md 里。

## ③ 1.5B 优先的建议——部分采纳

- **v1 已跑过 1.5B**(18 轨迹,连训练题 0/5,负结果,memory `distill-poc-v1-negative-20260823`);"1.5B 先探"已完成过一次。
- 本轮轨迹 18→120(6.7 倍),样本量论证已变化。**采纳对照设计**:7B 主跑不变(下载已 50%+),跑完后加 1.5B×120轨迹作对照组(成本 ~20 分钟)——若 1.5B(120) 仍 0 而 7B(120) 有效 → 分离"样本量"与"模型容量"两个因子;若都 0 → 假负风险显著降低,杀得更硬。
- 7B 下载不回退的理由:重下 1.5B 也省不了窗口时间,而 7B 是假设的主检验对象。
