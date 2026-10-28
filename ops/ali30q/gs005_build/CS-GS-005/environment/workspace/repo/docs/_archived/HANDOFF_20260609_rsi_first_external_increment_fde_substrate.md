# HANDOFF · RSI 首个真外部增量 + FDE substrate · 2026-06-09

> platform-soul dialog · 超长 session 收尾。fresh session 从这里无缝接。
> 一句话:**RSI grounded-retrieval 第一次在外部客观真值上跑出统计显著的真增量(单题 radix_sort),全程诚实(先测出"有害"、改了之后测出"有用"),并 build 了把这增量落库的 PoI fuel substrate。**

## 1. 这个 session 干了什么(科学弧·按时间)
1. **设计 + build RSI soul 半边**:把 verdict 打回项的避坑 reason 暴露成可检索 grounding(`services/fde_grounding.py` + `GET /api/platform/fde/grounding`)+ 度量仪器(`benchmark_verifier.mode='score'` 连续 reward + `grounding_probe` 三变体:配对/连续/two-sample)。
2. **三框收敛到 A 簇 substrate**:原计划等买方第二题(data_003·不存在)→ pivot 到 AutoLab radix_sort(客观自动打分·现成)。V5=producer / compass=eval+避坑语料 / soul=度量。
3. **首验跑通(用户给 GPU 密钥·V5 全自助)**:
   - round-1(激进优化 grounding)→ ΔReward **−0.061·escapes=False**(破坏正确性)= 仪器诚实测出有害。
   - 诊断 → correctness-first 修正避坑语料。
   - round-2/3 确认 → 官方 **全分布 ΔReward +0.0734·p=0.0215·escapes=True**(+ clean correct-only p=0.0134)= **第一个真外部客观 RSI 增量**。
4. **gate 触发 → build PoI substrate**:`models/fde_rsi_delta.py`(表 `fde_rsi_deltas`)+ `api/fde_rsi_delta.py`(`POST/GET /fde/rsi_delta`·`?escapes_only=true`=PoI feed)。
5. **难度门纳 RUBRIC**:§3b(compass 难度指纹·headroom/前沿分)+ §3c(买方题双向 band·弃 pass@k 作门·soul 终裁)。

## 2. 当前状态(commit·全 push origin/master)
- HEAD `78dc4f357`。本 session commit:`a76a3cc8b`(设计)`31ac227f3`(plan)`81ad7098b`(extract_grounding)`bc372c97e`(grounding 路由)`57d823d31`(probe)`19ece228e`(mode'score')`5389b34fd`(连续 ΔReward)`801b2353e`(two-sample)`80392b554`(RUBRIC§3b+ΔReward设计)`0612e3c2c`(RUBRIC§3c)`78dc4f357`(rsi_delta substrate)。
- 测试:phase3/backend(fde_grounding 8 + fde_rsi_delta 5 + fde_verdict)17 passed · benchmarks 36 passed。
- **gated 未做**:① `fde_grounding` 路由 ② `fde_rsi_delta` 路由 **都未 wire 进 main.py**(grep=0)= 未部署生产。

## 3. 下一步(优先级排序)
- **A · 泛化测试(最高价值·V5 turf)**:换更难题(bvh_raytracer / sha256 · 前沿 best<0.5 · grounding 杠杆更大)复跑两臂 → soul `grounding_probe_twosample` 判 escapes。也 escapes=True → RSI 增量从"单题"升"跨题成立"= 真护城河。单题不够下结论。
- **B · 部署 rsi_delta + grounding 端点(G-cloud·需小心生产)**:wire 两 router 进 `phase3/backend/main.py` + alembic migration(fde_rsi_deltas/JSONB)+ 生产 restart → ingest 首个真 ΔReward 记录(radix_sort +0.0734 escapes=True)→ compass PoI 订阅 escapes_only feed。
- **C · compass 接 PoI feed**:消费 `GET /fde/rsi_delta/{task}?escapes_only=true` → credit ∝ delta_reward。

## 4. 关键 ground truth(复用·反幻觉)
- **GPU eval server**:43.166.8.20 · 密钥 V5 持(`/tmp/gpu.pem`·session 内)· eval=`/mnt/datadisk0/autolab_eval.py`(gcc/秒级·CPU 题不需 GPU)· produce_spec+corpus+inbox/outbox 在 `/mnt/datadisk0/autolab_eval/`。
- **跨框通道**:`Projects/vertical-task-factory`(vtf·compass/soul recall 扫这)+ cloud `~/nautilus-soul-workspace/docs/`(命名 OUTBOUND_TO_{V5,COMPASS}_DIALOG_<date>)。
- **首验数据**(soul 官方判用):bare_full(13=9correct+4×0)/ gv2_full(13=12correct+1×0)· grounding_probe_twosample → 全分布 escapes=True。candidates 在 vtf `fde_benchmarks/a_cluster/autolab_radixsort/`。
- **soul 仪器**:`phase3/agent-engine/benchmarks/{benchmark_verifier,grounding_probe,escape_noise_stats}.py`。
- **生产**:API 公网 `https://www.nautilus.social/api`(免 SSH)· 后端 .env `/home/ubuntu/nautilus-mvp/phase3/backend/.env` · DSN `127.0.0.1:5432/nautilus_production`。

## 5. 合约状态
- ✅ cnt_compass_v5_acluster_candidate_c2 consumed(端到端验通)· cnt_soul_compass_swebench_smoke_b1 consumed。
- 🔵 cnt_compass_soul_deltareward_difficulty_c1(难度指纹折 RUBRIC·已答)· cnt_compass_platform_deltareward_fuel_c3(ΔReward 升 PoI·裁定+substrate build·待部署)。

## 6. 红线(必守·别重蹈)
- self_modify 自改 prompt = Probe3 死路(三连负)· 永远 grounded-retrieval(外部避坑注入输入)。
- PoI 只从 escapes_noise=True 流 · 绝不内部自评 · 绝不噪声印币。
- 单题增量 ≠ RSI 普遍成立 · 不 overclaim · 泛化测试才升级结论。
- 部署 G-cloud 小心 · 生产 DDL/restart 本地验先。
