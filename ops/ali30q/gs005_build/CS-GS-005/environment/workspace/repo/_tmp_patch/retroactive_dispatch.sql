-- retroactive 把现有 open platform_meta 全转 stake
INSERT INTO platform_agent_stakes (
  stake_id, staker_id, agent_id, amount_nau, share_bps,
  staked_at, status, directive, deadline, metadata
)
SELECT
  'auto-' || b.bounty_id,
  'platform:auto-dispatch',
  CASE
    WHEN b.assigned_to IS NOT NULL AND b.assigned_to != ''
      THEN b.assigned_to
    ELSE 'nautilus-prime-001'
  END,
  GREATEST(b.reward_nau, 50),
  0,
  NOW(),
  'active',
  format('PLATFORM AUTO-DISPATCH · %s · %s', b.title, COALESCE(b.description, '')),
  COALESCE(b.deadline, NOW() + interval '24h'),
  jsonb_build_object(
    'task_type', 'platform_auto_dispatch',
    'source_bounty_id', b.bounty_id,
    'requires_tools',
      CASE
        WHEN b.title ILIKE '%dead_agent%' OR b.title ILIKE '%retire%'
          THEN jsonb_build_array('pf_list_agents', 'propose_code_change')
        WHEN b.title ILIKE '%stake%' OR b.title ILIKE '%stagnant%'
          THEN jsonb_build_array('pf_list_bounties', 'propose_code_change')
        WHEN b.title ILIKE '%anomaly%' OR b.title ILIKE '%scoring%'
          THEN jsonb_build_array('pf_score_bounty', 'propose_code_change')
        ELSE jsonb_build_array('propose_code_change')
      END,
    'min_tool_count', 1
  )
FROM platform_bounties b
WHERE b.task_type = 'platform_meta'
  AND b.status = 'open'
ON CONFLICT (stake_id) DO NOTHING;

SELECT count(*) as auto_dispatched FROM platform_agent_stakes WHERE staker_id='platform:auto-dispatch' AND status='active';
SELECT count(*) as v5_active FROM platform_agent_stakes WHERE agent_id='nautilus-prime-001' AND status='active';
SELECT count(*) as v6_active FROM platform_agent_stakes WHERE agent_id='nautilus-v6' AND status='active';
