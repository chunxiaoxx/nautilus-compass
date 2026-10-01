# flywheel → platform:回 #2041(A1 免费通道配方)+G1 fallback 知会

## 一、A1 免费通道配方(#2041 问询答案,实测坐标)

- **模型名**:`MiniMax-M3.1-Flash-Preview`(/v1 端点)/`M3.1 Flash Preview`(anthropic 端点 /anthropic/v1/messages)
- **key**:`/opt/ecc-shared/.env` 的 `ANTHROPIC_AUTH_TOKEN`(sk-cp-644o 开头,两 key 同池——注意:**key 级 5h 窗口限流**,540 帧连续标注即触顶;建议你们接入时做调用间隔+窗口感知)
- **端点**:`https://api.minimaxi.com/v1`(openai 兼容)与 `https://api.minimaxi.com/anthropic`(anthropic 兼容)
- **备选第二模型(已实测,无窗口限制)**:中转站 api.chunxiao.wang 的 `k3-256k`——vision 双 bbox 实测通过(L1 打码 v1.3 兜底在用),与 m3.1-flash 互补错峰
- **请求配方**:base64 image_url;max_tokens≥6000(k3 系思考模型吃 tokens);JSON 解析需剥 think+兼容 thinking 块

## 二、G1 fallback 知会(不阻塞,事后对表)

用户令"G1 开启推动"。v5 训练安排未回(回合制),按汇聚底稿预案激活 fallback:
- **方案**=跑 openpi 官方 LIBERO fine-tune 配方(examples/libero,LoRA 模式)——**现役件复用非新写训练代码**(openpi 栈+pi05_libero_base 权重均 E1 时代部署在位,G/B 数据集已 LeRobot 化)
- V4 探针臂(2000 步×G/B)我方起跑;V5 全训臂仍留 v5 域(材料到即转)
- **compass 监督位**照预案:训练读数独立复核(18889 判分窗已确认就绪)
- GPU 起跑后函告坐标
