CREATE OR REPLACE FUNCTION auto_dispatch_bounty_to_v5_stake()
RETURNS TRIGGER AS $$
DECLARE
  required_tools_json jsonb;
  default_agent text := 'nautilus-prime-001';
BEGIN
  IF NEW.task_type != 'platform_meta' THEN RETURN NEW; END IF;
  IF NEW.status != 'open' THEN RETURN NEW; END IF;
  IF NEW.assigned_to IS NOT NULL AND NEW.assigned_to != '' THEN
    default_agent := NEW.assigned_to;
  END IF;

  IF NEW.title ILIKE '%dead_agent%' OR NEW.title ILIKE '%retire%' THEN
    required_tools_json := jsonb_build_array('pf_list_agents', 'propose_code_change');
  ELSIF NEW.title ILIKE '%stake%' OR NEW.title ILIKE '%stagnant%' THEN
    required_tools_json := jsonb_build_array('pf_list_bounties', 'propose_code_change');
  ELSIF NEW.title ILIKE '%anomaly%' OR NEW.title ILIKE '%scoring%' THEN
    required_tools_json := jsonb_build_array('pf_score_bounty', 'propose_code_change');
  ELSE
    required_tools_json := jsonb_build_array('propose_code_change');
  END IF;

  INSERT INTO platform_agent_stakes (
    stake_id, staker_id, agent_id, amount_nau, share_bps,
    staked_at, status, directive, deadline, metadata
  ) VALUES (
    'auto-' || NEW.bounty_id,
    'platform:auto-dispatch',
    default_agent,
    GREATEST(NEW.reward_nau, 50),
    0,
    NOW(),
    'active',
    format('PLATFORM AUTO-DISPATCH · %s · %s', NEW.title, COALESCE(NEW.description, '')),
    COALESCE(NEW.deadline, NOW() + interval '24h'),
    jsonb_build_object(
      'task_type', 'platform_auto_dispatch',
      'source_bounty_id', NEW.bounty_id,
      'requires_tools', required_tools_json,
      'min_tool_count', 1
    )
  )
  ON CONFLICT (stake_id) DO NOTHING;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

SELECT 'trigger fn updated · jsonb_build_array' as status;
