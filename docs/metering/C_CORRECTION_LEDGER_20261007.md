-- 裁定C冲正清单 · 生成器(compass,2026-10-07 深夜;应 10417/10432 口径)
-- 口径:#10432 用户批——分组键(linked_bounty_id, agent_id)、delta>0、reason 非 stake%、
--       保留(created_at,id)首条、余条生成 delta=-原delta 对冲行(linked=原id||'.dedup', reason 标源 ledger id);
--       hr-agent-web 排除;跨 agent 同单按分组键=合法不冲。
-- 只读生成,不改库;输出=correction_c.csv(逐行)+统计。

\copy (
  WITH grp AS (
    SELECT id, agent_id, linked_bounty_id, delta, reason, created_at,
      row_number() OVER (PARTITION BY linked_bounty_id, agent_id
                         ORDER BY created_at, id) AS rn,
      count(*) OVER (PARTITION BY linked_bounty_id, agent_id) AS cnt
    FROM platform_nau_ledger
    WHERE linked_bounty_id IS NOT NULL
      AND delta > 0
      AND reason NOT LIKE 'stake%'
      AND agent_id <> 'hr-agent-web'
  )
  SELECT
    'CORR' || g.id                 AS corr_id,
    g.id                            AS source_ledger_id,
    g.agent_id,
    g.linked_bounty_id,
    -g.delta                        AS corr_delta,
    g.linked_bounty_id || '.dedup' AS corr_linked,
    'dedup:' || g.id                AS corr_reason,
    g.created_at
  FROM grp g
  WHERE g.rn > 1
  ORDER BY g.agent_id, g.linked_bounty_id, g.created_at, g.id
) TO '/tmp/correction_c.csv' CSV HEADER;

-- 统计(供验收)
SELECT count(*) AS corr_rows, sum(corr_delta) AS corr_total FROM (
  WITH grp AS (
    SELECT id, agent_id, linked_bounty_id, delta, reason, created_at,
      row_number() OVER (PARTITION BY linked_bounty_id, agent_id
                         ORDER BY created_at, id) AS rn
    FROM platform_nau_ledger
    WHERE linked_bounty_id IS NOT NULL AND delta > 0
      AND reason NOT LIKE 'stake%' AND agent_id <> 'hr-agent-web'
  )
  SELECT -delta AS corr_delta FROM grp WHERE rn > 1
) t;
