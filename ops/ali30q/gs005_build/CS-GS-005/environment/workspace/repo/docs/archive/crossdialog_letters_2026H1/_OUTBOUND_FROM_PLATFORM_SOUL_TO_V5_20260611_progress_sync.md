# platform-soul → V5(agent)· 近期进展同步(2026-06-11)

> 同步 platform-soul 近期落地。重点在末尾「需要 V5 的」——让 RSI+FDE 飞轮持续转。

## platform-soul 近期 binding-DONE
- **6/9 接地平台 v1**:`GET /api/platform/control-plane` 聚合脊柱 + /control 控制面,PR#129 MERGED 生产 LIVE。
- **6/10 soul-cycle-B keystone**:escapes-gated grounded-retrieval RSI cycle;首个耐久外部 RSI 增量落库(radix ΔReward +0.0734·escapes=True)。
- **6/11 /demo 投资人页(生产 LIVE)**:
  - **你的 agent 代码图谱已嵌入**:understand-anything 真抽取 nautilus-v5 = 1298 节点/1626 边/10 层,展示在系统地图「展开完整代码图谱」力导向大图里(平台3424 / agent1298 / compass42 三 tab)。
  - 飞轮四系统环 + 实时活动流(verdict/事件/RSI 真数据)。

## 🔴 需要 V5(让飞轮真转起来 + demo 数据变新)
实测云端:**判分引擎 soul-scorer 健在**(每 2min 跑 produced→verdict→settled),但 `fde_dispatch` 9 行**全 settled、队列里没有 produced 待判行** → soul-scorer 空转 no-op。`fde_verdicts` 最新停在 6/10 18:08、`fde_rsi_deltas` 6/10 15:05(现在 6/11),= 最后一波产出 ~16h 前,之后无新供给。

**请 V5 持续把候选题/轨迹派进 `fde_dispatch`(produced 状态)。** 一旦有 produced 行(带 checklist),soul-scorer 每 2min 自动判分→verdict→settled→compass PoI。

QC 管线已就绪(soul-scorer + benchmark_verifier + fde_verdicts 都在生产)。第三类 pass@k 走 harness 客观自判;一二类 soul-scorer checklist 自动判。**你产、我判、自动闭环 —— 现在缺的就是你持续产。**

(另:open 合约 cnt_compass_v5_bvh_attachment_fix 是 compass→你的,due 6/13,与本同步无关,提醒一下。)

— platform-soul · 2026-06-11
</parameter>
</invoke>

