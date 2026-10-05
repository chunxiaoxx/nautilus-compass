# 预注册 · 14B 判读器升格判据(2026-10-05 立;smoke PASS 后续件)

> 依据:报数纪律(判据只许更严)+PREFOR_JUDGE14B_SMOKE_20261004(smoke 判据不含升格决策,升格另立——本档即另立件)。
> 前提事实 [实测]:smoke 五门全绿(200 步 86.3s/峰值 22.44G/loss 收敛/格式 20/20/n20=0.80);14B 管线可行性已证。
> 本档回答:14B QLoRA 判读器**是否值得从 1.7B 现役手里接棒**。开跑前冻结,开跑后只许更严。

## 升格判据(全 [实测] 层)

| # | 判据 | 门 | 说明 |
|---|---|---|---|
| U1 | 训练完成 | 全量 judge 语料(qid 分组防泄漏版,条数以语料实物为准,执行时回填)零 OOM 正常退出落 adapter | 复用 smoke 配方(train_judge14b_smoke.py,MAX_STEPS 按全量重定,预注册改为 ≤2000 步或 3 epoch 取先到) |
| U2 | 显存峰值 | <36G | 同 smoke S2 |
| U3 | 收敛 | loss 末 20 < 首 20 | 同 smoke S3 |
| U4 | 格式合规 | 抽 n=100 题推理,JSON 判读输出合规 ≥98/100 | 比 smoke S4(20/20)加大样本 |
| U5 | **判别力不劣门** | 现役判读器判绩账复核集(n≥200,同题同集同 gold):14B gold 一致率 ≥ 现役 1.7B 同集读数 | 不劣=可换;核心门。复核集=判例勘误+人工抽检沉淀(非训练集,qid 不相交) |
| U6 | **判别力显著门** | 同 U5 集:14B ≥ 现役读数 +3pp | 达此档=**推荐**切换;仅达 U5 未达 U6=保留 1.7B 现役、14B 记档待语料增长再评 |
| U7 | 成本申报 | 推理时延 P50/P95+吞吐+VRAM 如实入档,不设门槛 | 装订定价与热路径评估用;14B 慢是预期,只申报 |

## 反自指与纪律(冻结)

- 判官自产标签不入训练(smoke 纪律延续);
- U5/U6 复核集与训练集 qid 零相交,执行时出交集核查命令与结果;
- 收工走非实现者复算(新鲜会话,交接只给坐标与命令,不给预期读数);
- 升格与否的决策由 U5/U6 读数+用户拍板产生,本档不预授权切换。

## 执行坐标(交接用;2026-10-05 开跑时回填)

- 机器/基座/配方:A100 223.109.239.30:23236(paramiko;限流退避 115s);/root/vdd2/models/Qwen3-14B;环境=/root/venv_fw(torch 2.11.0+cu126/peft 0.21.0/transformers 5.5.0,smoke 同环境实测);
- 脚本:`tools/train_judge14b_upgrade.py`(smoke 同构迁移;GPU 守门>2G 退出不抢 B 臂);
- **U1 语料回填 [实测]**:全量 judge 语料=qid 分组防泄漏切分三件,A100 实物 sha256 前 16 位三件全对上 P2v2 档——split_train 1162 条(`35683198dd3c4992`)/split_dev 143 条(`942e4daeaedca2fb`)/split_test 149 条(`4bcaf1c9b551f336`),合计 1454;训练用 split_train 全量,3 epoch(≈873 步,MAX_STEPS_CAP=2000 取先到);
- **U5/U6 复核集回填(核对结果如实记)**:预注册原设想构成="判例勘误+人工抽检沉淀"——执行时核对判分语料仓(runtime/verdict_corpus/),**该构成无现成实物,不臆造**;回填=split_dev+split_test 全量 **292 条**(held-out,qid 分组切分保证与 train 零相交,n≥200 满足);构成差异如实申报:dev+test 与训练同语料同分布,比"勘误沉淀新题"口径偏易,对冲=同集两模型对拍(同题同 gold)+逐条读数落盘(eval292_14b/17b.jsonl)供复算与分歧对账;qid 零相交核查命令与结果随 report 落档(qid_of 派生键,与 corpus_split.py 同构);
- 现役 1.7B champion:adapter `dbcbab6fd1ff5821`(runtime/judge_lora_p2v2/best_lora,已传 A100 副本);基座 Qwen3-1.7B(A100 无库存,modelscope `Qwen/Qwen3-1.7B` 现下);
- 产物:/root/vdd2/judge14b_upgrade/(judge14b_lora+upgrade_report.json+eval292 两件+训练 log)。

## 状态

- [x] 2026-10-05 判据档预注册(用户批"有所作为推动"当日立,先于任何开跑动作)
- [x] 2026-10-05 开跑时窗到达:GPU 空窗 [实测](14MiB/40960MiB,零计算进程)+用户明示拍板"现在开跑";U1 语料与 U5 复核集坐标已回填(见上)
- [x] 2026-10-05 执行完毕:**UPGRADE_EVIDENCE_PASS(核心门 U1-U4 全绿)+U5/U6 判别力门双红(负结果照报)**——
  - [实测] U1 873/873 步零 OOM(train 445.7s)/U2 峰值 22.42G<36G/U3 loss 0.319→0.1138/U4 100/100 合规/qid 零相交=0;
  - [实测] **U5 未过**:292 条 held-out 同集对拍 acc_14b=0.8664 < acc_17b=0.9041(14B 劣 3.77pp);U6 未达(需 +3pp);
  - [实测] 分歧对账:only_17b 对 25 vs only_14b 对 14(现役净胜 11 题),both_wrong 14;
  - [实测] U7 申报:14B-4bit 推理 P50 49.9ms/吞吐 20.05/s vs 1.7B-bf16 13.5ms/74.3/s;
  - **判读(按预注册语义,不预授权切换)**:保留 1.7B 现役(P2v2 `dbcbab6fd1ff5821`);14B 记档待语料增长再评。更大基座在同分布判读任务上未带来判别力增益(4bit 量化+配方未调优为候选归因,upgrade_path=bf16 推理对拍/超参 sweep/语料扩容后重评);
  - [实测] U5 分歧对账(R167 追补,`runtime/loop/_r167_u5_disagreement_audit.md`):**错误方向不对称**——14B 分歧错误集中错杀侧(pass→fail 23 例),1.7B 集中错放侧(fail→pass 10 例,危险侧);分歧与共同盲区(both_wrong 14 条双双错成 fail)均聚集 lme 族;判读不变(U5=一致率口径 1.7B 胜),错误代价不对称重定义属判据演进走程序;upgrade_path 新增:①错放加权判据(如采纳)②both_wrong 盲区人工复核(gold 勘误活水优先);
  - 产物:/root/vdd2/judge14b_upgrade/(adapter `07a168b377e91ea9`+report `8fcea6bbe3d46b5a`+eval292 两件);执行插曲如实记:首起用错环境(venv_fw 缺 bitsandbytes)即败退出,改系统 python3(torch2.6/peft0.13/tf4.57/bnb0.50,与 smoke 实配一致)成功;双开被 GPU 守门正确拦截(第二进程 busy abort),train.log 因同写出空洞(观察件损坏,report/eval 落盘件不受影响)。
- [ ] 非实现者复算(新鲜会话按坐标复跑;交接只给坐标命令不给预期读数)
