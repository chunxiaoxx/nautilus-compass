# g2b1 变体题生成设计(v1)

trace_id: variant-generation-design-20260828
frame: platform-dialog · GOAL_STACK 4b 破顶三路之三
maturity: design(待批1批实作)
前置考古: 矿机 `tools/g2_b1_bug_miner.py` / 双门 `fde_capsule/_g2b1_consistency_check.py`+`services/g2b1_double_gate.py` / 队列 `evidence/g2b1_mine_20260827/deep_batch.jsonl`

## 1. 背景与目标

- 矿藏实测上限 ≈100 题(四仓历史重叠+小仓到顶),日耗 ~2.3 → 续航 ≈26 天;executor 复活在即(钥匙包已投 V5),消费只会加速。
- **目标**:模板派生变体把供矿提到 ≥150,且不牺牲真实性/可验证性/分布多样性。
- 价值锚:①executor 的 verdict/income 产能燃料(群体自治翼发动机)②DPO/蒸馏多规格实验的题源(路线已收棺但 DPO 轮在用,资产保存)。

## 2. 现有资产(全复用,零重造)

| 件 | 位置 | 复用点 |
|---|---|---|
| 矿机(口径:fix 触 tests+源文件、<200 行、非 docs/chore) | `tools/g2_b1_bug_miner.py` | 模板筛选同口径 |
| 队列 schema `g2-b1-task-v1` | deep_batch.jsonl | 变体行同 schema+扩展字段 |
| 双门(worktree+pytest:门1 starter 必败/门2 fix 必过) | consistency_check 模式 | 变体验证同一把尺 |
| 生产验证链 | 云 auto-verify+g2b1_double_gate | 复活后自动生效,变体无特权 |

队列画像(100 题):core 37 / v5 36 / compass 17 / fde3 10;**79% 单源文件题**(变体注入面清晰,友好)。

## 3. 变体算子(三层,从真实 fix 对派生,非编造)

- **OP-1 受控回注**(批1):模板=fix diff(bug→fix)。在 fix 版代码上把原 bug **变换后回注**:
  - a 值变体:边界/常量/操作符方向(off-by-one 反向、`<=`→`<`、错误默认值)
  - b 条件变体:守卫条件取反/收紧一格/异常分支吞错改抛错
  - 每模板限产 ≤2 个变体,**单仓变体占队列 ≤30%**(防分布退化)
- **OP-2 测试变异联动**(批2):对测试做受控弱化+bug 对应变异,保持 starter/fix 仍可区分。复杂度高,批1 落地后评估。
- **OP-3 跨文件移植**(批3):同仓内 AST 相似结构文件间移植 bug 模式(需结构匹配器)。远期。

**排除**:跨仓移植(真实性存疑+工程量大,不做)。

## 4. 质量门(五门,前四机制化)

1. **双门**:门1 变体 starter 必败 + 门2 fix 版必过(worktree+pytest,与现队列同一把尺)。语法破坏/无区分度在这里死掉。
2. **幂等**:task_uid 命名 `g2b1:<fix_commit10>v<op><n>`(如 `g2b1:e49e8ade78v1a1`),唯一约束;evidence 文件名同规约(对账链不断)。
3. **novelty 门**(🔴 新增,防 v4 同质废料):变体 diff vs 模板 diff 的最小结构距离判据——bug diff 触及的行集/标识符集变化比例 ≥阈值(初值 0.3,预注册),纯常量改名的近克隆拒收。
4. **难倒抽样**(A 类口径):每批抽 ≥5 题跑 doubao pass@5 ≤0.6(抽样不是全量,控成本)。
5. **人工抽检**:每批 5 题人看 subject↔bug 语义一致性。

## 5. 分批与预注册判据

- **批1(P0)**:模板=100 题中 subject 语义清晰的 top 30(core/compass 优先,见风险#3),OP-1a/b,目标产 20-40 个过门变体 → 队列 120-140。
- 判据(预注册,三态):过门率(候选→双门过)≥30% 为形态成立;<15% 连续两批 → 杀 OP-1 路线;中间 → 调算子参数再来一批。
- 批1 验收含:变体题被 executor 实解 ≥5 题,verdict 链正常入账(external_verify 双门独立复现)。
- 成本:LLM 候选生成 ~100 次调用(GLM 臂,¥10 内);双门本地 pytest 零成本;难倒抽样 doubao ~5 题×5 次。

## 6. 实现与分工

- 生成器 `phase3/backend/tools/g2_b1_variant_gen.py`(平台仓):读模板队列 → LLM 出候选 diff(结构化约束,非自由生成)→ 本地双门 → 过门行写 `evidence/g2b1_variants/batch1.jsonl`(g2-b1-task-v1 + `variant_of`/`variant_op`/`template_task_uid` 三扩展字段)。
- **turf**:生成器+质量门+产物=平台;队列消费/executor 拾取=V5(**平台不代改 V5 队列**,产物路径函告 V5 自取——同 revival kit 规矩)。
- 与转移线⑥联动:生成器成熟(三条件:跑 ≥3 次+预注册判据+零人工一轮)后入固化度台账 L2;变体流水线是台阶二 goal-sourcing 候选(矿红→自动续矿→自动变体)。

## 7. 风险与边界

1. **同质化**(v4 教训):novelty 门+配额(§3)双保险;批1 后看 executor 实解分布再调。
2. **假难/假易**:难倒抽样+实解分布监控;变体若比模板显著更易解(采样臂 pass 率抬升)→ 算子无效信号。
3. **🔴 v5 归档仓依赖**:deep_batch 36 题 repo_path 指向 `nautilus-v5.archived-20260827`(V5 档观察一周后可能删)。**变体批1 模板避开 v5 题**;V5 复活版遇 v5 题需路径映射到新仓 ~/nautilus-v5(其 turf,revival kit 未含此条——需补一句)。
4. 燃料用途边界:SFT 蒸馏已收棺,变体题叙事=executor 产能+实验题源,不宣称"蒸馏将变强"(决策 C 边界)。
5. 变体题=内部燃料,**不进买方交付**(若未来对外,另过买方 QC+标 synthetic)。

## 8. 维护

- 批1 实作入 GOAL_STACK 新栈项;判据三态结果回写本文件 §5;重大拐点入 SSOT 增量。
