# S6 预检实测补充(2026-10-08 深夜 · 排期回执 10647 的先行执行)

- swebench 5.0.2 已装 cloud:/home/ubuntu/s6_rerun/venv [实测 import OK];
- preds_arm_a.json 已上传 /home/ubuntu/s6_rerun/ [实测];
- 镜像覆盖 [实测]:30/30 全缺(cloud 现存 3 个 swe.eval django 镜像=11299/12143/14672,与 board30 无交集,旧评测残留);
- 镜像获取走 swebench 内置按需 pull(run_evaluation 自动),无手工名猜测;
- 🔴 磁盘硬缺口:30 镜像全量解压后预计 90-120G,现余 62G——明日(10/9)预拉前需清盘或扩容。清理候选清单(列单待批,未删):docker Exit 容器 swe_b50_x 系/nautilus-v5 仓 5.7G(归档可移)/nanojev_ckpt 2.3G;或向平台申临时扩容(用户令背景优先)。
- 明日开跑条件:磁盘到位 → 预拉+30 题复跑 → 10/10 出全量读数 → 10/11 对表出档。

—— compass · S6-PRECHECK
