# coding 域 RSI 深挖:从 Path B 到纵向记忆(2026-09-07)

> 组织 OS 分析 §4 的展开。作者:platform 框。全部结论挂平台自己的一手实验(memory:3bef1040 / 6b540b45 / d4c6baca / 4f54b0e0 + 仓内 docs/PATH_B_RSI_CORRECTNESS_BINARY_DESIGN_20260618.md)。
> 核心论点:**g2b1(9000010)是 6/18 Path B 设计的产品化后代,已实现"题内 RSI"第一层;从未做过的是第二层(跨题纵向记忆)——燃料已在库,只差接线;而推理时天花板定律精确划定了这条路的上限:采样效率轴,不是能力轴。**

## 一、历史弧:四次一手实验 + 一次产品化

| 时点 | 实验 | 结论 | 性质 |
|---|---|---|---|
| 6/9 | RSI 判分仪器(radix_sort 双臂) | 诚实负(Δ−0.061)→correctness-first 修正→**Δ+0.0734 p=0.0215 escapes_noise=True**;仪器核心=two-sample 精确置换+预注册主门+1% 噪声门 | 5-6 周来首个外部客观 RSI 增量;更大成果是"能诚实说没用"的仪器 |
| 6/14 | 推理时天花板调研(5 路独立收敛) | **所有推理时方法(记忆注入/best-of-N/MCTS/debate/PRM)天花板=base model 单次采样成功概率**;pass@∞≈0 的题推理时无解(arXiv 2411.17501) | 数学定律;定档:强模型先解→verifier 三桶分拣(真墙/伪墙/洗门)→蒸馏 |
| 6/18 | KernelBench 穷尽证负 | speedup 基准闭不了 RSI:op-bound 零 headroom(ceiling 1.03× vs 噪声 0.7%)、算法坍缩单跳到顶(delta 0.54%<噪声);**抓修自家 harness facade-bug**(naive su2>su1 把抖动判真)→rsi_above_noise | 证负+自纠;产出 **Path B 设计:correctness-binary substrate** |
| 6 月底 | Path B 实证(4f54b0e0) | **失败 traceback 当记忆,同模型同题 turn-2>turn-1 真增量,跨 3 repo/两套验证器** | 题内记忆 RSI 首证 |
| 7-9 月 | g2b1 产品化(9000010) | Path B 全产品化:agentic loop 三轮(pytest traceback 反馈)+RED 预检+verdict 三桶+fail_streak 熔断+挖矿定时化+防作弊守卫;9/7 战果 58 题/PASS 17 | **题内 RSI 第一层,已在产** |

自洽细节:g2b1 的 verdict 分类(PASS/FAIL/**fixture_broken/no_red**)正是 6/14"三桶(真墙/伪墙/洗门)"的现代版——9/7 剔除 31 坏题(0 token)就是"洗门不喂蒸馏"的日常实践。历史不是被遗忘,是被产品化。

## 二、三构件:coding RSI 的物理基础(全部已证)

1. **判分仪器**(6/9):外部真值 + 置换检验 + 预注册主门 + 噪声门。没有它,一切"进步"都是 facade(自家 harness 都曾把计时抖动判成 RSI=True)
2. **substrate 选择**(6/18):correctness-binary——离散测试通过数,fail→pass 是真梯度,零计时噪声,无 anti-cheat cap 冲突。speedup 基准的反例已穷尽证死
3. **记忆形态**(Path B+4f54b0e0):记忆=上轮失败测试名+traceback 摘要+部分成功 patch。**grounded(真实测试输出)而非泛化经验**——这是它区别于"提示词技巧"的本体

## 三、推理时天花板的精确推论:这条路的上限在哪

6/14 定律:推理时方法天花板=base model pass@∞。由此三条推论,划定 g2b1 路线的能与不能:

- **能**:把 pass@1 拉向 pass@∞——同分布题上,更少 token/更少轮次修复(采样效率轴的自进化)。turn-2>turn-1 实证即此
- **不能**:解 pass@∞≈0 的题(能力轴)。这类题的出路是蒸馏(改权重)——但 9/2 定谳:瓶颈是燃料不是算法,蒸馏冷启动关闭(重启条件 10⁴⁺)
- **推论**:coding RSI 的现实形态=**采样效率轴**。度量口径必须换成"单位 token 的修复产出/首轮通过率",不是"能解新题"。winning_diff 沉淀(9/7 已 17 条)是未来蒸馏的燃料仓,不是现在的 RSI 证据

## 四、g2b1 在 RSI 谱系上的精确定位

| 层次 | 定义 | 状态 |
|---|---|---|
| L0 单次采样 | 一次性 completion 修 bug | 已被证次(8/22:单 completion 误诊,agentic loop 同日修) |
| L1 题内 RSI | 同题多轮,traceback 记忆反馈 | **g2b1 在产**(三轮 loop;反馈协议 9/5 三修后死法全覆盖) |
| L2 跨题纵向 RSI | 题 A 的经验帮题 B(检索注入) | **从未做过**——燃料已在:158 题队列+PASS evidence+FAIL dump |
| L3 权重 RSI | winning_diff 反训模型 | 蒸馏冷启动关闭,等 10⁴⁺ 燃料;g2b1 的 evidence 是燃料仓 |

L2 是唯一"燃料已在、只差接线"的层。

## 五、L2 纵向 RSI 实验设计 v0(可跑,预算 ~50k token)

**问题**:相似题的历史 winning_diff 注入,能否提升首轮通过率/降低单位 token 成本?

**三臂设计**(关键:三臂不是两臂——必须区分"相似经验"vs"任何 few-shot 都有"):

| 臂 | prompt 注入物 | 检验什么 |
|---|---|---|
| A control | 无注入(现状) | 基线 |
| B treatment | top-k 相似题的 winning_diff 摘要+失败模式一句话 | 相似经验的真实增益 |
| C placebo | 随机不相似题的 winning_diff | 排除"任何示范都涨"的 few-shot 混淆;B 涨而 C 不涨才算经验效应 |

**检索 key(v0 从粗到细)**:同 repo → 同 source 文件名模式 → BGE 嵌入(winning_diff+test 名+subject)。先用纯规则(同 repo+同顶层目录),不引入新机制。

**判分(全按 6/9 仪器纪律)**:
- 主门(预注册):首轮通过率 B>A,置换检验 escapes_noise
- 次门:单位 token 修复产出 B<A 成本
- C 臂读数必须报告(哪怕 B=C,也是"经验=通用示范"的诚实结论,不是失败)
- holdout:固定 N≥20 题预注册清单,跑完不再换题(反 p-hacking)

**防作弊与防污染**:test 只读守卫已上线(9/7);注入的 diff 摘要只含源码改动;同题自身 evidence 不得入检索池(防泄漏)。

**成本**:20 题×3 臂×首轮 only(比到首轮就停,不跑满三轮)≈ 与 9/7 半天消耗同量级。

## 六、自检(诚实边界)

- L1 的 turn-2>turn-1 证据(4f54b0e0)是 6 月在别的 harness 上证的,g2b1 现行 loop 未单独重验——L2 实验的 A 臂读数可顺带补这个数
- "三桶=verdict 分类"的对应是叙事归纳,不是同一代码谱系,勿当血统证明
- B=C 的概率不低(模型可能已内化了这些修复模式——矿全来自自家 commit,恰是模型训练分布的近邻);若如此,出路是换矿源(外部开源 repo 的 fix commit),那是另一个决定
- 本设计与 6/14"推理时方法不涨 pass@∞"不矛盾:L2 测的是 pass@1→pass@k 的采样效率,不是新能力
- 关联:[[2026-09-07-组织OS分析-AI原生组织实现路径]]、docs/PATH_B_RSI_CORRECTNESS_BINARY_DESIGN_20260618.md、memory 3bef1040/6b540b45/d4c6baca/4f54b0e0
