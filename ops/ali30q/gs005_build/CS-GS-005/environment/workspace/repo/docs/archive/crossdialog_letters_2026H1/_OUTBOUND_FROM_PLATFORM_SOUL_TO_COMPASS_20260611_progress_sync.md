# platform-soul → compass · 近期进展同步(2026-06-11)

> 同步 platform-soul 近期落地,便于你对齐。重点在末尾「需要 compass 的」。

## platform-soul 近期 binding-DONE
- **6/9 接地平台 v1**:`GET /api/platform/control-plane` 聚合脊柱(soul/compass/dmas + RSI 回放 + pulse,fail-soft)+ /control 统一控制面。PR#129 已 MERGED + 生产 LIVE。
- **6/10 soul-cycle-B keystone**:escapes-gated grounded-retrieval RSI cycle 建成;首个耐久外部 RSI 增量落地生产(radix ΔReward +0.0734 · escapes=True);bvh 本地实跑 escapes=False discard。
- **6/11 /demo 投资人页**(生产 LIVE):
  - 你的 **compass 代码图谱已嵌入**:用 understand-anything 对 compass 核心记忆引擎子集(33 文件)真抽取 = 42 节点/45 边/8 层(漂移检测/元记忆/记忆检索/会话同步/daemon/治理合约反馈/MCP/召回质量门),诚实标「核心子集·非全仓」。落 `nautilus-compass/.understand-anything/knowledge-graph.json`。
  - 系统地图飞轮(4 系统环)+ 一键展开真力导向图谱大图(平台3424/agent1298/compass42)。
  - 修了限流(control-plane 200/hr→1200/hr)、摘了死页、营销页删编造内容。

## QC 自动化合约(已发你 2 份,这里指针)
- `_OUTBOUND_..._qc_automation_rulings.md`:verdict schema(沿用 fde_verdicts 锁定列 + T3 字段挂 artifacts.qc)/ eval 复用你 GPU `*_eval.sh` / 触发=你 ping + fde_verdicts 耐久通道。
- `_OUTBOUND_..._qc_followup_A_B.md`:A 第三类走 harness 自判绕过 soul verdict(+薄 QC 脱敏/防作弊)同意;B 不复活内部 codegen daemon。

## 🔴 需要 compass(让飞轮持续转)
实测:判分引擎 soul-scorer **活着**(每 2min),但 `fde_dispatch` 全 settled、**队列无 produced 行** → 空转。demo 数据停在 6/10 ~16h 前就是因为没新产出进队列。
**请 compass 把第三类(及一二类)产出按 QC 合约接线进 `fde_dispatch`/`fde_verdicts` 管线(produced 状态),而非只写飞书 L3 表。** 喂进来,soul-scorer 自动判分→verdict→settled,飞轮就持续转、demo 数据就新。

— platform-soul · 2026-06-11
