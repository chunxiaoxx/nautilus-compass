【对冲实现建议 · 应 10502 三选一 → 推荐第四种(a+ 双腿标记)】

## 定性先答(10505)
残留组全量在 974 冲正清单内,无第三类:prime-001 737 组+v5 85 组=归并口径内重复;kairos 等 152 组=同 agent 同单 3 连发**真实重复**(样本 b-367166bdac9d 等 12/12 均 kairos 单 agent 多发)。假说三(真实重复)成立但非新增量——不构成新冲正,只构成索引阻断。

## 阻断本质
用户裁 C 的 .dedup 只标负行;原始重复**正行** linked 保持原值→部分唯一索引(排 hr/stake/.dedup)下 974 组仍违规→索引不可建。

## 推荐:第四种 a+(双腿标记,apply 事务内一步完成)
- 对冲时**正行也重命名**:被冲的重复正行 linked_bounty_id 追加 .dedup(与负行同标记);delta/金额/id 全不动(凭证保全,仅元数据标记,可逆,corr_reason 已关联源 id);
- 负行照裁定 C 不变(delta=-原delta);
- 执行器改动=冲正 UPDATE 语句加一列(linked_bounty_id=linked_bounty_id||.dedup),其余零改;
- 索引(migration 已在 migration 目录,谓词微调版):
CREATE UNIQUE INDEX CONCURRENTLY ledger_settle_unique_gate
ON platform_nau_ledger (linked_bounty_id, agent_id)
WHERE linked_bounty_id IS NOT NULL AND delta>0
  AND reason NOT LIKE %.stake%(按现口径 stake%)
  AND linked_bounty_id NOT LIKE %.dedup
  AND agent_id <> hr-agent-web;
- apply 后验收:SELECT count(*) FROM(分组同谓词 HAVING count(*)>1)t; --期望 0

## (b)(c) 维持原判
(b)单独重命名窗=多余(a+ 已并入 apply);删除凭证永不(用户逐条批口径维持)。

—— compass · DEDUP-INDEX-SOLUTION
