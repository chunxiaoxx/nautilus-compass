# 全框生产快照 2026-09-04 19:39

## 四框 git(24h)
- **flywheel**: 17 commits · goals=GOALS.md · FRAME=✗未落
  - 16:12 docs(s9): 原力灵机微信开场话术——三段节奏(Dexbotic开源由头/数据网络+IMU+lerobot3.0+十万小时级探底/样例试吃+数据采购或以数据换训练);备注转引
  - 15:42 docs(s9): 近期工作报告存档(9/2-9/4说人话版)——主线10万小时订单三天盘点:卖的材料/生产的家当/验证的路径三类齐备;瓶颈全在仓外(设备快递/甲方伙伴回复/发送动
  - 13:20 fix(s9): 报价单v0.2对外版终审三修——①定价依据段(供给端¥40-80成本底牌)转内部引用块剥离+A层说明改中性,防亮压价空间;②总价改分段精确值:共享920→905万
- **v5**: 15 commits · goals=GOAL_ACTIVE.md · FRAME=✗未落
  - 16:46 fix(eval): run500_gpu 护栏修正——dockerd 嵌套 overlay 致数据落根盘而非 /eval 数据盘,df 检查目标 /eval→/ ·清理阈值 8G
  - 16:34 feat(eval): GPU 5路并行500题脚本入仓(slice 50:550·判分flock互斥·镜像清理护栏)+playbook补pull_timeout=120根因与修法
  - 16:21 docs(eval): GPU 第二评测机通——烟测死因谱系(镜像预热120s/计费ignore/filter锚点转义)+500题5路并行配方(run500_gpu.sh·slic
- **compass**: 54 commits · goals=(无专属,看仓内 docs) · FRAME=✓
  - 16:08 docs(runbook): 全量跑分启动命令模板固化——harness 判官两默认值皆坑(401 变量名·4096+medium 空响应风暴),启动必带 16384+low;附 
  - 14:28 docs(paper2#41): 评审清单补修复状态——P0 4/4+P1 15/15+P2 6/12,剩余为待拍板/待考证/提交时项
  - 14:25 fix(paper2#41): 补 PDF 重编译(P0#2 第4处 edit 后漏编译,真编译 0 错 0 undefined·248KB)
- **platform**: 13 commits · goals=docs\GOAL_STACK.md · FRAME=✓
  - 16:02 docs(org-os): 孤儿表扫描 v1 定稿——清理建议撤回降级挂账+org_snapshot_daily 修复终验坐实
  - 15:57 feat(org-os): 拍板雷达 LLM 判读器——平台第二个中转站消费场景落地
  - 13:45 feat(org-os): 接入自有中转站 api.chunxiao.wang——用户授权直用;manus服务器newapi容器(sqlite备份后插platform-ops专属t

## 云关键表(经 backend API 只读)
- mailbox_24h=2 last=2026-09-04
- capability_recent=[('nautilus-prime-001', datetime.date(2026, 9, 3)), ('nautilus-prime-001', datetime.date(2026, 9, 3)), ('nautilus-prime-001', datetime.date(2026, 9, 3))]
- cards_undecided_sent=3
- ledger_latest=['decision-paper2-judge-taxonomy-20260904', 'decision-frame-compass-20260904', 'decision-gangqu-gov-perspective-20260903', 'decision-dispatch-commercial-terms-20260903', 'decision-quote-v02-reprice-20260903']
- agents_heartbeat_1h=1

## 判读口诀
- 判断组织状态以本快照+各框 GOALS 为准,勿拿单框度量外推全景;
- 决策卡/发函前:先查 ledger_latest 有无同主题更新拍板(>48h 未决卡默认过时);
- 快照缺失某框=该框 24h 零 commit(正常休眠,不是死亡)。