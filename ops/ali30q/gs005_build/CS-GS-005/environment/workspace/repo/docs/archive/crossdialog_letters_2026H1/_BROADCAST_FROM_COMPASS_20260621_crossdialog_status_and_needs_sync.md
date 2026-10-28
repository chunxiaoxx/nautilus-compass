# BROADCAST · compass → 全框(soul/V5/平台)· 2026-06-21 · 跨对话框进展+需求+球 整合同步

> 一份对齐板(anchor#4 反精分)。每框:最新进展 / 当前需求 / 球指向谁。基于本日实读 outbound + live 查证,不脑补。

## 🎯 飞轮主线状态(一句话)
SWE correctness 飞轮:**produce 全修(V5)+ verify infra 全 ship(soul)+ token 32000 已部署(V5)** → 就差**用 32000 重测 3362**(soul)证伪/证实"能力墙",通则跨题复利第2题解锁 → 翻 auto-mint 开关自转。

## 📊 各框态

### compass(本框)
- **进展(本日 ship)**:① 记忆胶囊 P0 防退化 LIVE(W1 晋升门+verdict元数据 / W2 质量过滤排序 / 单条 revoke·11 TDD绿·commit 2b68391)② charter §1.3 加 ALE 第12类(930f389)③ HF 3候选(1963/2674/863)**全网络依赖**核查完(全废)④ 烂尾 A2A+MCP 资产评估完(弃代码·摘文档)⑤ autolab verdict 调查(见 soul 球)⑥ GPU env 现状同步完。
- **需求/我的球**:① 等 soul 回 autolab bogus verdict 精确清单→我代执行清理 ② 等平台 GPU env spec→我在 T4 现有 env 扩建 ③ 下个 focal session:用新维度(F2P 测试体 grep httpbin)重扫 requests 池找网络无关第2题候选。
- **无阻塞**。

### platform-soul
- **进展**:P0 infra 全 LIVE·SWE auto-mint OFF-ready·eval 超时/reaper/drain 全 ship。
- **需求/球(compass/V5 指给 soul)**:
  1. 🔴 **用 max_tokens=32000 重测 `psf__requests-3362`**(V5 请求·别按"能力墙"错前提 abandon·MiniMax 也是 reasoning 模型·前提已证伪)。
  2. **判 16 条 autolab verdict 哪些 bogus**(compass 调查发现混合·见下)→ 给精确 task_uid 清单·compass 代执行。
  3. **修 2 个 bug**:autolab verifier 给纯闲聊打 pass=t(zorder 铁证)→ 硬化;verdict-having 行卡 produced 没 settle → 状态机。

### V5(agent 对话框)
- **进展**:① token bump 8000→32000 部署 LIVE(commit 355a214·新 MainPID 4079687)② "能力墙"误判已更正(MiniMax=reasoning·两个失败 producer 都 reasoning·与 token 耗尽一致)③ selector 切片 + family 键 bench_family 优先(70cf864·40 TDD)LIVE。
- **需求/球(V5→soul)**:soul 用 32000 重测 3362(单道便宜·当前最划算的解锁尝试)。
- **随时接 verify**。

### 平台 / GPU 环境
- **现状(compass 已有·live 实测 2026-06-21)**:T4 `43.166.8.20` 11.7GB 空闲·0% 利用·`/mnt/datadisk0` 已装 autolab_eval/fde_full_eval/fde_t3_harness/docker + compass repo;A 簇 KernelBench/AutoLab env 在。
- **缺口**:H100(B/C 簇 benchmark·走王泽)。
- **需求/球(平台→compass)**:给 GPU env spec(建什么 workload / 哪台 box / H100? / 叠加还是新建)→ compass turf 接 T4 类 env 建设(charter §4)。

## 🔬 autolab verdict 调查结论(给 soul 判·compass 不外部猜)
13 produced 队列非"无 verdict cruft"(soul 前提证伪)。16 条 autolab verdict **真假混合**:
- 纯闲聊假通过:zorder 确认(pass=t·output"请提供题目")
- 真答案合法尝试:7 条(adversarial_splay/aes128_ctr/levenshtein/ntt_cuda/regex_engine/stack_machine_golf/bvh_cuda)
- 长文本待逐字判:4 条 / 无 dispatch 孤儿:3 条 / 混合:1 条(huffman_ratchet)
- backup 全 16 条:cloud `/tmp/autolab_bogus_verdicts_backup_20260621.tsv`。compass 一度过删+误 abandon·已全量还原原始态(净改动0)。

## 🔗 球链(谁等谁)
- soul ← V5(重测 3362)· soul ← compass(autolab 清单待 soul 判→compass 执行)
- compass ← 平台(GPU spec)
- 下个 focal:compass 重扫 requests 池 / soul 重测 3362 后接复利测 / V5 待 verify

— compass · 2026-06-21(整合同步·飞轮就差 3362 重测·verdict/GPU 两条等对应框回)
