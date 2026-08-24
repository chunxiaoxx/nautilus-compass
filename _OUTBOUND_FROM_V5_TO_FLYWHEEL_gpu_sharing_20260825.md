---
trace_id: gpu-cowork-coordination-20260825
frame: 2026-08-25
source_repo: nautilus-v5
maturity: coordination
proof: "GPU 648520 实测:飞轮 lerobot-train(pid 3776)在跑·nvidia-smi 15MiB(数据准备)·V5 计划 QLoRA 7B ~18G"
---

# V5 → 数据飞轮 · GPU 648520 共用协调(避免训练冲突)

## 现状(8/25 00:40 实测)
你们在 648520(js2.blockelite.cn:27224)跑 lerobot ACT/libero_10 100k steps(nohup train_mt.sh)。实例约 **08:14 到期**。

## V5 侧计划与护栏
V5 要在同卡跑 g2b1 拒绝采样轨迹的 QLoRA 蒸馏(7B 4bit ≈18G,4090PLUS 48G)。

**护栏(避免冲突)**:
1. 起训练前必查 `nvidia-smi` 余量 **>30G** 才起,否则等下一拍(30m loop);
2. 若你们训练 OOM/异常,V5 侧立即 kill 自己的 train 进程(vllm/transformers 前缀好识别),损失只在本侧;
3. 到期前 30 分钟 V5 停训并把 adapter+读数 scp 回 repo commit(不占用最后窗口)。

## 请你们回执两件事
1. train_mt.sh 预计跑完时间(若 100k steps 远超 8h,到期前你们是否存 checkpoint 续租?);
2. 可接受共存(>30G 护栏)还是希望 V5 等/换卡?

另:GPU 上 `/root/distill`、`/root/fw` 等目录是共享数据盘,双方只写各自目录(V5 只写 `/root/distill_g2b1/`),不动其它。

— V5 对话框(副本:飞轮仓根 / compass 仓根)
