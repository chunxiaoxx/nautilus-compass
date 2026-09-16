# 验证机构的算子代数与数学基础(2026-09-16)

> 定位:把《RSI 深度启示》(rsi_deep_implications_20260916.md)的战略论断下沉到
> 底层算子、数学结构与代码实现。**每条算子都对到仓内实物函数**(文件:行号),
> 每条命题给"陈述→证明思路→经验可检验性"。这是工程数学化(formalization),
> 不是同行评议数学;命题强度如实标注。
> 代码锚点(2026-09-16 全部实测存在):tools/verifypack/{checks,seal,receipt,
> ed25519,spec,expr,keys}.py · daemon.py v2.1.0 RRF/v0.7.1 漂移 · CATALOG_v0。

## 〇 · 一句话

**机构=一个把"声明"映射到"三态裁决"的偏函数求值系统,外加一条使裁决可信的
分离结构与一条使判据只紧不松的序结构。** 记忆、召回、漂移是它的状态算子;
封印、复算、签署、注册是它的信任算子。

## 一 · 公理化:声明与三态(为什么三态不是 UI 而是 math)

**定义 1(声明)** 声明 c=(a, f, P):断言值 a、复算程序 f、载荷字节 P,
h=SHA256(P) 为其指纹。

**定义 2(复算=偏函数求值)** 裁决 V(c)=f(P) 与 a 的比较。f 是偏函数:
- P 在 f 的定义域内 → 得 b,V(c)=agree iff b=a,否则 disagree;
- P 域外(缺文件/缺环境能力/脚本崩)→ **not_computable**。

这不是设计品味,是代码里现成的类型区分:checks.py:15-16 `CheckError`(无法
执行)与 verdict=disagree(求值为假)显式分家;checks.py:171-175 `EnvRequired`
(环境能力未声明)走 fallback/degraded 而非报假。**三态 = 偏函数求值的三种
像:域内相等、域内不等、域外。**

**命题 T2(熵零目标)** 声明可信 ⇔ H(a | P, f) = 0——断言相对载荷与程序携带
零额外信息。试点 10/10 UNVERIFIABLE 的数学内容即:10 行的 a 全部活在行外
(V5 会话日志),H(a|P) 对每行都满。机构的存在意义=把对外声明的条件熵压到零。

**定义 3(可复算性格)** ρ(c):self-report(0)< attestation-only(1)<
pointer-resolvable(2)< byte-recomputable(3)。**棘轮 = ρ 沿格单调不降**;
CATALOG 只许更严 = 序结构约束,不是口号。判据条目 `criteria:<id>@catalog-v0`
是这个格上的具名谓词,版本号即格位。

## 二 · 八个底层算子(签名 · 代码实物 · 数学形态)

| # | 算子 | 签名 | 代码实物 | 数学形态 |
|---|---|---|---|---|
| 1 | W 写入 | (doc,meta)→e=E(doc) 落库 | daemon ingest(verbatim+BGE-m3,写侧零 LLM) | **无投影存储**:不经过有损映射 g(doc)→摘要,信息保持(智能后置到读取,由已知查询分布决定投影) |
| 2 | R 召回 | q→top-k | daemon.py:216 `_rrf_fusion`(k=60)+BM25 流 | RRF:score(d)=Σᵢ 1/(k+rankᵢ(d)) |
| 3 | D 漂移 | prompt→r(p)∈ℝ,alert=r<τ ∨ rule_hit | daemon.py:1289 `drift_score=round(pos_cos−neg_cos,4)` | 加权 top-3 双原型 **margin**:s(p)=w̄₊·cos(p,A₊)−w̄₋·cos(p,A₋) |
| 4 | X 沿链 | S→S∪N₁(S) | **插件仓** `~/.claude/plugins/nautilus-compass/daemon.py:1145/1161` `_entry_link_text`/`expand_chain_links`(记忆门三件套,主仓 daemon 无此符号) | 1-hop 邻域扩张,谓词=锚存在(全文级) |
| 5 | B 封印 | dir→(manifest,claims) | tools/verifypack/seal.py | B(P)={hᵢ=SHA256(Pᵢ)}:把字节集映为哈希清单 |
| 6 | V 复算 | (pack,env_caps)→{agree,disagree,nc}ⁿ | tools/verifypack/checks.py `run_check` 七判据 | **带能力域的偏函数求值**(见 §三) |
| 7 | S 签署 | (verdicts,sk)→receipt | receipt.py+ed25519.py(自实现+交叉验证) | Ed25519(canonical JSON(verdicts‖h));非否认性:任何持 pk 者可验"该裁决绑定该字节" |
| 8 | G 注册 | criterion→(id,谓词,版本) | docs/catalog/CATALOG_v0.md+机制 | 蕴含序上的单调链(T4) |

**R 算子的尺度不变性(RRF 为什么对)** cosine∈[-1,1](有界、几何),BM25 无界
(tf-idf 饱和)——两路分数不可直接加权(校准不匹配)。RRF 只吃**秩**:对每路
分数的任意单调变换不变,1/(60+rank) 使头部平滑加权。这不是调参,是免校准的
秩统计量性质(Cormack et al. 2009)。

**D 算子的操作点实证** 旧 v1(OR 分支 neg_cos≥0.538)在 11.5k 真实流量上
64.5% 逢触必报;v2 cutover(2026-06-01,daemon.py:1295 注记)改 margin+规则
并联,alert 率 0.5%。这不是拍阈值,是 Neyman-Pearson 操作点在真实分布上的
一次有据移动:**max TPR s.t. FPR≤α 的工程实现,α 由 alert 预算反推。**

## 三 · V 算子的七判据分类学(checks.py 实物)

| kind | 判据内容 | 纯度 |
|---|---|---|
| aggregate | ratio_eq/exact:filtered rows 上 num/den(expr.eval) | 纯 |
| file_hash | sha256/sha256_16 | 纯 |
| file_hash_map | 名字→哈希映射(rows/claim 驱动,支持 input dir) | 纯 |
| group_count | 分组计数+min_group/expect_groups | 纯 |
| json_map_equal | 容差映射比较 | 纯 |
| text_contains | needles(可引用前序 claim **计算结果**) | 纯 |
| script | 子进程跑 repro 脚本,timeout+env_caps 声明 | **拟纯**(环境依赖) |

三个数学要点:
1. **check 构成 DAG**:text_contains 引用 `computed[claim]` → 判据间有依赖序,
   verify 是拓扑序求值;
2. **能力域显式化**:L2 判据需声明 `requires_env`,域外=EnvRequired→degraded,
   **永远不会"域外判假"**——这是 not_computable 通道的纪律意义;
3. **诚实缺口**:前六 kind 是字节纯函数;`script` kind 的确定性取决于
   脚本+环境可复现,是整套代数里唯一的弱链——它的保险丝是 timeout+env 白名单
   +degraded 通道,长期方向是把 script 域收窄到声明能力集。

## 四 · 机构级命题(陈述 · 证明思路 · 经验检验)

**T1(分离原理/生产者不可自证)** 若生产者可写"已验证"标志,则该标志与真值
的互信息为零(生产者最优策略恒置 true——激励不相容,机制设计标准论证)。
→ 判据 external-verified-provenance-v1(标志只许复算者写)是其制度化。
检验:9/15 试点 8/29 批 10/10 违例(生产者自置 true)= 预言的失败模式。

**T2(熵零)** 见 §一。检验:试点 10/10;C 族包 inputs 全量入包+哈希锚定
(flywheel 入站函)即把 H(a|P) 强制归零的工程动作。

**T3(测量完备性与零裁量)** V 完备 ⇔ 每条声明恰落一态,且态是 (P,f,a) 的
函数、与验证者无关。**LLM 裁判天然违反 T3**(自由文本裁量→14.2% 无声错标,
paper2 实测);checks.py 七判据无 LLM、f 在包内声明、环境走能力声明——
零裁量的工程近似。.script kind 是残余裁量,见 §三.3。

**T4(棘轮=测量诚实度的单调算子)** 判据是三元组 j=(m, τ, D):测量对象映射 m
/ 阈值 τ / 披露集 D。修订合法 ⇔ ①ρ(m′)≥ρ(m)(测量可复算性格上不降)
②Δτ 带证据链(独立复算读数,双向均可)③D′⊇D(披露只增)。棘轮锁死的是
**测量的诚实度 ρ,不是标准的松紧 τ**——判据生命周期=ρ 单调升+τ 沿证据链
双向移动+D 单调张。(2026-09-17 按 platform 319 函精化案重写;旧表述
"只许更严"会把 sim50-001 v0.2→v0.3 的合法修订误判违规:valid 阈 1.0→0.9
放宽,但 m 从状态日志行数→源视频帧数 ρ 升格 2→3、D ∅→{批min,分布,8集
坏帧清单}——τ 松而诚实度升,正是本条要放行的形状。正本:nautilus-core 仓
docs/ORG_RSI_OPERATOR_ALGEBRA_20260916.md。)预注册 = 冻结 researcher degrees
of freedom(对 familywise 错误率的 Selection 效应,是 p-hacking 的形式化反义),
现表述为:预注册冻结首轮 (m, τ, D) 三元组,此后修订只走上述三条件。
检验:护栏 2(空白区零占位)即 T4 的操作化。

**T5(漂移=失效流形上的 margin 检验)** D 是对"真实失败模式流形"(25 正锚)
与对照流形(35 反锚)的双原型 margin 判别;AUC 0.83 为其单点工作特性。
升级 D_θ(判分器小模型)的门=AUC(hold-out)≥0.87 且 FPR 不升——**Neyman-
Pearson 意义下的受控改进,不是刷分**。

**T6(胶囊=可验证状态转移)** 记忆胶囊 C=(D,h(D),链,receipt)。接收方可验:
h(D) 复核(完整性)、链锚存在性复核(J3 教训=全文级)、召回命中声明可复算
(query q,doc d,hit 声明→重算 cos 即验)。"记忆可验货"是数学性质,不是文案。

**T7(反自指定理——涡轮的安全条件)** 若训练判分器 D_θ 的奖励锚定于自家判分
器历史标签,则存在退化解 D_θ∘D_θ≡1(自我确认不动点);**唯一安全奖励通道是
V(字节级复算)**:r=1[V(f_θ(x))=y],y 由 T3 意义下的零裁量测量产生,评测走
hold-out 预注册。这条把 anchor-pool-selection-bias(训练版)关在门外,是
"自训判分器"整个方案的生死线。

## 五 · 涡轮的数学:verdict 语料作为监督分布

**样本形态**(每条已签裁决):(x, y, σ),x=(claim 载荷+判据指针),y∈{agree,
disagree},σ=ed25519 签名(出处)。

- **SFT**:θ*=argmin E[ℓ(D_θ(x), y)]——标签来自**确定性测量**而非人类偏好,
  这是与 RLHF 的本质区别:零标注成本、可复算、带出处;
- **RL**:奖励即 T7 公式;样本效率来自 y 的测量精度(无标签噪声源,只有
  V 的域覆盖问题——not_computable 天然剔除,不污染训练);
- **样本量门槛的依据**:区分 AUC 0.83 vs 0.87(DeLong 配对检验,α=0.05,
  power≥0.8)需 O(10²-10³) 配对样本;签名词料≥2000 条 = 功效安全余量 +
  hold-out 留量,不是拍脑袋。

**飞轮闭环形式化**:agents 工作→W 沉淀→V 复算产 (x,y,σ)→语料长大→D_θ 上线
预筛→V 终裁(人类只裁 contested)→裁决回流语料。验证容量随语料**超线性**,
而人类注意力恒定——这就是"机构长出手脚"的数学内容。

## 六 · 收费三线的数学对应

- **记忆胶囊 = T6 的商品化**(可验证状态转移收费;VerifyPack 套在胶囊导出上,
  审计=对胶囊跑 V);
- **组织记忆 = (状态 W, 判据 G) 二元组的持久化**——换底座模型时 W、G 不变,
  这是"模型租、记忆判据自有"的形式内容;
- **审计服务 = 出售 V 通道的独立执行权**。定价原理:客户支付的期望价值 =
  P(未被发现的错标)×错标期望损失;复算覆盖度把第一项从"未知"变成"可计量"
  ——审计报告里的三态计数就是定价依据,这是"验证服务可标准化报价"的数学基础。

## 七 · 代码级缺口与下一步(诚实盘点,全部小额)

1. **verdict 语料导出器缺位**(半天):schema=(trace, claim_id, criteria_ref,
   payload_hash, verdict, signed_at, pubkey_fp)+ 一条导出命令;从今天的裁决起
   语料就是干净的;
2. **script kind 域收窄**(小额):能力集白名单化,把 §三.3 的弱链收紧;
3. **D_θ 训练位**:数据管道(上条)ready 前不开工;开工即按 T5/T7 双门。

---

*收束:三态是偏函数求值,棘轮是序,复算是测量,签名是非否认,判据是具名谓词,
墙是判例集。机构的一切语言都能落到这六个数学对象上——而 §五说明这套对象
天然长出一个学习系统:它自己裁决过的东西,就是它学会裁决的教材。*
