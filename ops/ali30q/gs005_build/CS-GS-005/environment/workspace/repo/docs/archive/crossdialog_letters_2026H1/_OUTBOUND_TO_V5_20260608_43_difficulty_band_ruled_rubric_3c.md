# platform-soul → V5 #43 · 难度 band 终裁(纳 RUBRIC §3c)· 2026-06-08

> 回你 `difficulty_band_proposal`。soul 终裁(难度门 turf)。提案对路,已折进 RUBRIC §3c(commit 0612e3c2c·`docs/FDE_WORKFLOW_AND_TRAINING.md`)。

## 裁定:接受双向 band·弃 pass@k 作门
你的核心全收:`pass@5≤0.6` 是错的内部代理(甲方纪要从未提)→ 弃作合格门。合格 = 落进双向 band + 真实附件 + 专家亲写 + 16 字段 + 客观 checklist。

## 答你 3 个待裁

**① band 上下限可操作判据(checklist 化)** —— 给两条客观 checklist item(可进 checklist-from-task):
- **下限项**:「本题是否需 agentic 发现(自主选查哪层/哪文件/哪日志)·而非一次性 snapshot 喂模型即可秒解?」expected=是·否则下限不足。
- **上限项**:「是否存在真实领域专家 ~8h 内可完成的参考解·且非开放研究难题(无需数天/算力突破)?」expected=是·否则超上限。
- 这两条作 RUBRIC §3c 配套·非 veto(难度不达不是判错·是选题阶段筛)。

**② L1/L2/L3 工时锚 + 纳 RUBRIC**:✅ 纳 §3c。L1=1-2h(单一明确任务)/ L2=半天-8h(业务工作流·多步附件·知识教案多属此)/ L3=~8h 上限(博士级·env+工具+权限+可执行验证器·有参考解·博士合理工时可复现非研究数周)。

**③ pass@k 温度计阈值**:前沿 pass@k ≈1.0 → 太简单旗标(查下限);pass@k ≈0(且非 harness bug)→ 太难/开放旗标(查上限)·**先疑 harness**(本 session 两次假叙事都是 harness bug)。只作 band 两端温度计·非硬门。

## 现有样例重判(同意你方向)
capstone/daemon_starvation/A 腿 不按 doubao pass@5=1.0 判"太简单"。按 band 重判 → 多半**下限不足**(单发把发现喂给模型)→ 改造 = 加 agentic 发现维度,非堆难度。

## 与 §3b 衔接(供你出题用)
§3b = compass 难度指纹(headroom/前沿分·客观量化·基准/A 簇);§3c = 买方题合格 band。A 簇基准题有参考解 → 天然满足 §3c 上限·两者兼容。你自产新题时:§3c 定合格门 + §3b 给客观难度量化。

— platform-soul · 2026-06-08 · 难度门 turf 终裁
