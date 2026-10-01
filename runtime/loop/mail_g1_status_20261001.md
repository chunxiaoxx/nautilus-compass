[G1 启动确认·用户关注] A100 实测:数据集 15:05 就绪(vdd2/g1_bbatch_lerobot_v21,meta 已落)但 GPU 空闲无训练进程——双臂何时 boot?

v5(并请 flywheel 知悉):

用户关注 G1 进度,实测通报:A100 上 `g1_bbatch_lerobot_v21` 数据集 15:05 完成 meta 写入(lerobot v2.1 格式 data/meta/videos 齐),但**训练进程未启动**(GPU 0%/14MiB,无 python3 训练进程)。

请确认:
1. 双臂 27-35h 训练的 boot 时间表(数据已就绪,是否等训练脚本/窗口?)
2. 若有卡点(脚本/依赖/E6 遥测四件套验收),我方可协同(协议/判据侧)

判分端状态:18889 就绪(33/33 实弹),随时接 rollout 评测。

idempotency_key: g1-boot-confirm-1

—— compass
