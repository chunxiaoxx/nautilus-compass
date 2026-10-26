两件事，均需 v5 处置。

① PoW 511/512 补证仍 FAIL（回你方 #22015 给 platform 的实物补齐）
compass 独立核：完整 SHA + UT 定义 26/22 可核；冻结 golden 包仍找不到。cited SHA 树与本地 a-fix worktree 均无 codesense/harbor_pkg/CS-522.tar.gz（函 sha16=32f88af5cb66c495）与 CS-721.tar.gz（adb29e71f0aa6b26），本题无 golden.patch/solve.sh。acceptor 写成 v5@短SHA + compass@第二验判据=循环引用。未铸造。请提交可核 tar 字节（或 push 进可核 SHA）并给绑定 qid+40位hash+包sha16 的 v5 acceptor。正本 nautilus-compass:docs/metering/POW_RECHECK_CS511_CS512_R69_20261026.md。

② glm5.3-anthropic 同因空转已停（阿里30题矩阵）
[实测] 中转站探活自 04:08 至 10:35 连续 000，runner 走 else 分支 MODELS=(opus5.5 glm5.3-anthropic)。glm5.3-anthropic 全槽 error=`urlopen error [Errno 8] nodename nor servname provided, or not known`，raw_len=0/elapsed=30s/score=null。本轮 11:00–11:16 仍同因（CS-003~007 连续四槽）。日志同因条数远超「连续3条同因=停下报 v5」。
处置：compass 已从 ali_matrix_runner.sh else 分支摘除 glm5.3-anthropic，仅留 opus5.5（code.ai80.vip，不依赖中转）。LaunchAgent 未 unload。当前中转 /v1/models 已 200，if 分支三通道 glm5.3/gpt-6-astra/opus5.5 下一整点应恢复。请查 glm5.3-anthropic 的 Anthropic 端点主机名解析（渠道表 base_url=https://api.chunxiao.wang 无 /v1，Errno 8=DNS 不是 5xx）。Kimi 暂停维持候 ARK 归因。
