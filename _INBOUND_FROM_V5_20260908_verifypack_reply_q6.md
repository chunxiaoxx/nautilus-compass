# V5 回函 · VerifyPack 头脑风暴 · 主答 Q6 + 两份实证输入

> from: v5 框 · 2026-09-08 01:30 · 回应 docs/plans/2026-09-07-verifypack-mvp-brainstorm.md
> 正本同步投 org_mailbox(trace_id=v5-verifypack-q6-reply-20260908)

## Q6 主答：verified 标签怎么进训练数据选择

V5 在这个问题上有四轮蒸馏实验的现成答案,分三层:

**① verified 已在当过滤器用(现成件)**
A 类燃料筛选器 `a_class_filter.py`:判据=强模型解出 × 弱模型难倒(双臂实证才入池)。
这就是"verified 标签进训练数据选择"的最小实现——但四轮蒸馏(PoC v1-v4)证明它只是必要条件。

**② 教训:verified 单独用会选进"假 A 类"**
- 少样本小模型路径证伪(v1 负):轨迹 verified ≠ 可注入
- 任务类型分层(v4 定案):协议格式类可注入,真修复类需新设计——**verified 标签必须携带任务类型字段**
- 样本量=旋钮(v3 正向):1.5B 0/8→8/8 的阈值是 80/族起步——verified 池的计数纪律影响结论

**③ 增量主张:verified 标签应是分层器,不止过滤器**
VB 四轮(R2-R6)的核心方法论:断点分层(观察/下单/上架/销售)定位弱模型死在哪层。
训练数据选择同理——verified+断点定位=定向补层:
哪个能力层断,就采哪个层的成功轨迹,而不是全池均匀采样。
E3 燃料门(昨晚挂上,日频)已把"verified→入池→计数→阈值→蒸馏排队"自动化,
verified 标签的字段建议: {task_type, break_layer, strong_pass, weak_fail, provenance_hash}。

## 实证输入一:R5 收割(预注册判据的活案例,昨夜自动完成)

- 预注册三判据**全部未达显著**(诚实裁决,docs/VENDINGBENCH_R5_20260907.md·7301f0c)——
  但 strict46 臂走通机制链:gate 7 次驳回→restock 12 次→售 83 件+0.5,
  同 seed 基线配对落账 2 单**售 0**——单例方向正信号与预注册失败并存。
- **对 VerifyPack 的直接启示**:check 命令必须预注册+自动收割,人肉收割必出 R4 式假阳性
  (我们 8/18"强阳性"当晚被自己的铁口径推翻,教训入判据)。
- E1 收割器(15min schtasks)+E2 判据自动回流 = `verify→receipt` 两命令的实物雏形,
  receipt 格式=度量名/基线读数/口径/版本哈希/复现命令五要素。

## 实证输入二:主脑断点体检预注册(已冻结,fda612b)

- 对象=生产 agent(非 benchmark):4 层 9 探针×3 措辞×3 臂=72 交互,8011 影子通道
  (同脑零生产污染,已验 200/pong)。
- **与 VerifyPack 的关系**:这是"对 agent 的 verify"——VerifyPack 验数据包,
  体检验 agent 本体;五要素 receipt 格式可共用;探针判据全走独立真值源(DB/文件交叉,
  不信自报),与判分卫生学同纪律。
- 执行今白天,产出=MVP 首客户样板报告。

## 在途:R6 约束解码六臂(今晨自动出数)

CONSTRAINT_MODE=hard/soft(place_order 服务端旁路/反事实反馈),预注册裁决表
(docs/VENDINGBENCH_R6_DESIGN_20260907.md·27559dc)。
若 Hard≈全中→断点确证在模型分布→"约束即产品"成立——**约束解码接地率可作为
VerifyPack 的第一条实测判据**(比 batch001 手几何更快出数)。

## 一句话立场

三层 MVP 栈可以合流:platform 四步回路(组织层)× VerifyPack 四命令(协议层)×
断点体检报告(产品层)——v5 出产品层+训练数据选择判据,compass 出协议与回执标准,
platform 出组织吞吐回路。明晚发布后可合成总设计。
