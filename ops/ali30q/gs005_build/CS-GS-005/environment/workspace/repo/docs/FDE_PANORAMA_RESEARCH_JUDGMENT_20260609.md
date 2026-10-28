# FDE 全景研判 · 收敛梳理(供研判·不发散)· 2026-06-09

> 应用户:沉淀收敛、把散落各处的 FDE 产出+全维度思考梳理出来研判;直面"过程/记忆黑盒+旗舰视图反复烂尾"。
> 本 doc 只**收敛已有**(读三框真实工件),不设计新东西。

## 0. 一句话研判
**我们不缺设计,缺"建成并显性化"。** 全维度愿景(6/5 主设计)+ 旗舰视图(6/6 控制面 P1/P2)都设计完了,但散落 + 旗舰视图 build 烂尾 → 过程永远黑盒、全靠你脑子记。根治 = **把旗舰视图的一个薄切片真正建成并 binding-DONE**,让它成为唯一活体看板,之后所有过程/记忆/产出都从它显性化。

---

## 1. FDE 产出全清单(近几天·三框·我能读它们仓)

### 三类业务样例(交付物)
- **第三类(基准复现)= 今天落地**:飞书表「L3基准样例」5 行 —— radix(旗舰·完整链)/bvh(含诚实负)/daemon/capstone(我·soul QC 全 compliant·真附件齐)+ compass_data_007。形式贴甲方核准 14 列 + 任务类型 + 打分checklist + reward + 复现验证 + 附件。
- **第一类(行业专家)**:6 样例 data_001~006(题+真附件+checklist·教育/电商/安全/餐饮/法律/产品)。
- **第二类(知识教案)**:核准式=编程自动化四段式;真产出待真专家写(红线:查 AI)。

### 支撑能力(三框)
- **soul(我)**:RUBRIC/checklist_scorer/benchmark_verifier(pass@k+escapes)/难度指纹/grounding_probe/PoI substrate。
- **compass**:A 簇 env(AutoLab/KernelBench)+ 避坑语料检索 + read_buyer_tasks + feishu 读写 + 工具栈(fde-row-assembler/checklist-from-task/knowledge-tutorial-assembler/build-html-dashboard/parse-pdf/excel-formulas)。
- **agent(v5)**:出题主体 + 接地 Agent 内核(连贯 loop·6/9 设计+P0)+ RSI producer。
- **RSI 成果**:radix grounded-retrieval 首个真外部增量 escapes=True(单题·护城河雏形)。

## 2. 全维度现状(你要的"全方位"→ 既有 doc + 状态)
**源:6/5 `native-ai-org-fde-productization-master-design.md`(全维度愿景·已梳理)。问题=都 deferred 到 P2/P3 没动。**
| 维度 | 既有思考(在哪) | 状态 |
|---|---|---|
| 三线人/agent 分工 | 主设计 §1 | 🟢 清晰 |
| **招募/筛选** | §2:垂直社区+前同事+KOL·线3 需稀缺 ML/系统人才 | 🟡 设计·未动 |
| **培训/赋能** | §2:**QC 失败 reason=避坑=培训素材**(不单编教材)·录屏 data_001=操作样板 | 🟡 设计·未动 |
| **营销** | v5 `outreach-feedback-learning-loop`(6/2)散在 v5 仓 | 🟡 散落·未收敛 |
| **GUI/飞书赋能服务对象** | §3:A 飞书多维表格嵌 agent(专家零学习)/ B 桌面 app | 🟡 设计·未 spike |
| **三流(业务/数据/资金)** | §4:业务流🟢 / 资金流🔴未建(组织化关键缺口) | 🔴 资金流缺 |
| **agent 编队+维护自愈** | §4.5:现有 agent→FDE 角色映射+审计自愈 | 🟡 设计·未动 |

## 3. 旗舰视图/管理后台 = 烂尾的"形式"(黑盒解药)
- **设计齐全**:6/6 `control-plane-P1-P2-implementation.md` = 你贴的舰桥 spec(系统脉搏/拓扑/心跳流/闭环回放 + 5 子系统 drill + 指挥区 + 角色层 + 8001 聚合脊柱)。
- **建到一半**:仅 W-A 看板(`api/platform_rsi_fde.py`)落了;P1 数据脊柱 + P2 舰桥首页**设计完没 build = 烂尾**。
- **真数据现成**(6/6 只读核实):fde_verdicts 7 行 / platform_external_events 135 行 / agents 338 行 —— 数据有,缺的是"建成的活体看板把它显性化"。

## 4. 元问题根因 + 收敛提案
### 根因(诚实·复发)
1. **散落**:三框各自 design doc 几十个,无单一活体入口 → 全靠你脑子串。
2. **黑盒**:过程/记忆/产出没有显性化界面 → agent 做了但你看不见 → 你成唯一记忆体。
3. **烂尾**:工作流一直扩展/分歧、永不闭环(feedback_workflow_lock 已命名);一切 defer 到 P2/P3,而 P2/P3 被新东西挤掉永不到来。**旗舰视图就是被这样烂尾的。**

### 收敛提案(治本·不发散)
**把旗舰视图收敛成一个薄垂直切片,真正建成 binding-DONE,作为唯一活体看板:**
- 只做 P1 数据脊柱(8001 聚合 `GET /control-plane`,把已建的 W-A 并入)+ P2 舰桥首页的**一屏**(系统脉搏条 + 一次闭环回放 data_001)。
- 砍掉 5 子系统 drill / time-travel / 角色层等(全 parking-lot·建成第一屏再说)。
- **forcing function**:binding-DONE 判据 = 浏览器打开 `/bridge` 看到真数据的脉搏 + data_001 闭环回放。不到不算完。
- 之后所有 FDE 过程(verdict/RSI/编队/产出)都接进这一屏 → 黑盒消除、不再靠你记。
- 全维度其余(招募/营销/资金流/编队)= 接进这个看板后逐个显性化,不再散在 doc。

---

## 5. 待你研判的决策
1. **认不认这个根因**(散落/黑盒/烂尾)?
2. **形式**=旗舰视图薄切片(P1+一屏)当唯一活体看板,对吗?
3. **谁建**:控制面在平台(我 turf)·我建薄切片;compass/v5 接数据。
4. **如何防再烂尾**:冻结 scope(只第一屏)+ binding-DONE forcing function + 不在长 session 尾部建(分清醒 session)。

— platform-soul · 2026-06-09 · 收敛研判 · 不缺设计缺建成 · 旗舰视图薄切片治黑盒
