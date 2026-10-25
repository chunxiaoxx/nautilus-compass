**[SFT 排程更新] 微调步环境问题连环,深夜暂停转明早干净会话**

如实通报:四步验证第二步(S4 微调)在 A100 上遭遇连环环境问题:
1. transformers 版本(4.47 不认 qwen2_5_vl/4.49 已解)
2. vdd 本地 Qwen 权重 visual bias 损坏(已 ModelScope/hf-mirror 重拉完整版,DL-OK 确认)
3. sentencepiece 新版与词表不兼容(已降 0.2.0)
4. torchvision CUDA 错配(已卸载,PIL 替代)
5. **当前未决:训练脚本起跑后仍 HFValidationError(models_dl 路径)**——多处路径残留未清干净

处置:深夜疲劳端不再硬撑(防疲劳误操作),明早干净会话集中清路径残留后一击起跑。SLA 10/27 01:00 仍有富余(预计 10/26 午前完成四步全链)。
第一步基线读数(真官方权重 8292M 复核)有效在案不受影响。

—— compass 判读层(疲劳端自律:不在疲劳端做不可逆操作)
