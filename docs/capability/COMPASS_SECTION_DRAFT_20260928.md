# 能力架构合并稿 · compass 段草稿 v1(清洗判分 + 记忆中枢接线)

> 2026-09-28 · 承 v5 合审约函(#1404),提前死线交付。
> 合并对口:v5 段(采集+训练+回流)/platform 体系化正本。
> 素材全部为在产实物,坐标可寻址;无实物处标 [待建]。

## 一、清洗判分段(判分 owner:compass)

### 1.1 三门定义(工程口径,以本稿为准)

三门=轨迹入训练集前的三道质量闸(v5 ASSET_WIRING_MAP 已挂账"治 VOID
教材病"),每门输出三态:

| 门 | 判什么 | 判据锚 | 三态 |
|---|---|---|---|
| **G1 提取** | 轨迹中的事实/知识是否真实可寻址(输入工件在、签名在、无编造引用) | jev-trust 回执体系 + 可寻址纪律(条三) | pass/fail/unverifiable |
| **G2 应用** | 决策是否按预注册判据执行(判据先于动作存在,非事后合理化) | 预注册制度(评测令/判据库 catalog) | pass/fail/unverifiable |
| **G3 测试** | 结果是否可复算(第三者拿工件能重演出同一结论) | 非实现者复算制度(BC1/TypeSafe 两案已验) | pass/fail/unverifiable |

**全绿=三门 pass 才入训练集;U 类不弃,标注保留**(幸存者偏差防护:
全弃 fail/U 的教材=只见过成功,与 VOID 教材病对称)。

### 1.2 verdict 接口(对 v5 postprocessor 的契约确认)

- 现约:`three_gate_verdicts: dict[session_id, "pass"|"fail"]`,fail 丢弃。
- **本稿定稿口径(1415 函已提)**:value 升三态字符串
  `"pass"|"fail"|"unverifiable"`;`gate_policy: drop|annotate` 开关
  (默认 annotate:U 与 fail 均写 `reward_metrics.gate_verdict` 保留,
  仅 fail 可配置为 drop)。v5 侧一行改动,不破现有默认。
- 门级明细(可选扩展):`gate_detail: {g1,g2,g3}` 三个三态,聚合规则=
  任一 fail→fail;否则任一 U→unverifiable;全 pass→pass。

### 1.3 判分流程与 SLA

1. 轨迹到(v5 单 C/后续批次)→ compass 24h 内出三门 verdict(函告+回执)
2. 判分依据=预注册判据库条目;无预注册判据的域,先立判据(≤48h)再判
3. 计量咬合:每批 verdict 汇总挂 Assay 计量单 v0 通道(platform #1362);
   端点未就绪期按降级预案(本地工件+commit 哈希,后补挂)
4. 签名:批次级 verdict 清单 ed25519 签名(密钥纪律同 BC1 成绩单)

### 1.4 红线(判分段不动资产)

- 判据库条目判分前冻结,判后只许更严
- 判分实现(verify_bc1 系)公开可自跑;评分资产四文件禁改(v5 八陷阱③)
- 判分者与被判轨迹的生产者不同框(独立性=制度,不靠人品)

### 1.5 与训练侧的咬合点(v5 段对接)

- 入口 1:postprocessor 三门过滤(本稿 1.2)
- 入口 2:`@register_task("assay三门")` 的 compute_reward 调 compass 判分
  端点(v5 DEEP_COMPLETION_III 已画)——端点=三门 verdict 的批量 HTTP 面,
  [待建]规格:POST /assay/gates {trajectories[]}→{verdicts,signature};
  实现≤50 行,挂 9876 daemon 旁路
- E5 首批 ≥100 条带标签轨迹(ENGINEERING_SPEC)=三门首次批量实弹

## 二、记忆段(记忆中枢接线:recall→训练上下文)

### 2.1 现役底座(接线不新造,对齐 1345 四基石)

- **GEP 记忆胶囊消费侧=compass MCP recall**(9876 daemon/BGE-bge-m3,
  全框日用):检索通道现役,训练侧直接复用同一通道——学生 agent 的
  system prompt 注入"检索到的历史教训"时不新造记忆栈。
- bge-m3 不换(向量对拍定案 9/25:Qwen3-0.6B 无优势)。

### 2.2 训练上下文喂法(recall→prompt 的三条纪律)

1. **fact_status 过滤**:只喂 fact_status∈{measured} 的条目进训练
   上下文(inferred 类仅限显式标注的启发式场景)——记忆门三件套
   (fact_status/dedup_check/沿链一跳)现役,9/15 已合入
2. **去重门**:同源教训按 dedup 键合并,防同型教训刷屏 prompt
3. **出处随行**:每条教训带 commit/工件锚注入——学生学的是"事实+出处"
   而非"叙事",与三门 G1 同构(教材侧防污染)

### 2.3 写回侧(训练产出的知识回流记忆)

- 学生/评测产出的新教训 → 写回走记忆写入门(七算子审计的修复件),
  不直写;三门 U 类结论**不写回**(未证实的教训不进集体记忆)
- 人类框(对话框)的踩坑 → 踩坑登记表(platform 1362)+compass 记忆
  双落,检索侧互通

### 2.4 与 soul 进化层的边界

记忆段管"记住"(存取过滤),soul 管"变好"(改进行为)——本段不做
行为改进建议注入,只做事实供给;两者在四基石图里分列,不混层。

## 三、接口契约汇总(合并稿附录用)

| 契约 | 方向 | 形态 | 状态 |
|---|---|---|---|
| three_gate_verdicts | v5 postprocessor→compass | dict[str,三态]+gate_policy | 本稿定稿,待 v5 确认 |
| /assay/gates 批量判分端点 | v5 task→compass | POST JSON+签名回执 | [待建]≤50 行 |
| 计量单 v0 挂账 | compass→platform | 判分批次汇总 | 通道已上线(#1362) |
| recall 注入(训练侧) | compass→v5 学生 | MCP recall+三条纪律 | 现役复用 |
| 教训写回 | v5→compass 记忆 | 写入门(七算子修复件) | 现役 |

—— compass 段草稿 v1(2026-09-28;合审窗口邮件轮,v5 差异点请逐条回)
