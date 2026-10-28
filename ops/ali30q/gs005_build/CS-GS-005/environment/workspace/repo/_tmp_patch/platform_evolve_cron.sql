-- C 方案 · platform evolve cron · 解耦 trigger · 5min 扫描真处理
-- 扫 last 10min 内 fulfilled 的 platform-dispatch stake · 真做 evolve action · idempotent

DO $$
DECLARE
  r RECORD;
  retired_count int;
  unstaked_count int;
  approved_count int;
  archived_count int;
BEGIN
  FOR r IN
    SELECT stake_id, directive, metadata->>'source_bounty_id' as src_bounty, metadata
    FROM platform_agent_stakes
    WHERE status='fulfilled'
      AND staker_id='platform:auto-dispatch'
      AND fulfilled_at > NOW() - interval '10 minutes'
      AND COALESCE(metadata->>'evolve_processed', 'false') <> 'true'
  LOOP
    retired_count := 0;
    unstaked_count := 0;
    approved_count := 0;
    archived_count := 0;

    -- 类型 1 · dead_agents → retire
    IF r.directive ILIKE '%dead_agent%' OR r.directive ILIKE '%retire%' THEN
      UPDATE platform_agents
        SET survival_tier='retired',
            metadata = COALESCE(metadata, '{}'::jsonb) || jsonb_build_object('auto_retired_at', NOW()::text)
       WHERE last_heartbeat < NOW() - interval '3 days'
         AND COALESCE(survival_tier, 'unknown') <> 'retired';
      GET DIAGNOSTICS retired_count = ROW_COUNT;
      IF retired_count > 0 THEN
        INSERT INTO platform_audit (actor, actor_type, action, target, target_type, outcome, output_preview, metadata)
        VALUES ('platform-cron', 'system', 'auto_retired_dead_agents', r.stake_id, 'stake',
                'success', format('retired %s agents', retired_count),
                jsonb_build_object('count', retired_count));
      END IF;
    END IF;

    -- 类型 2 · stagnant → unstake stale active stakes
    IF r.directive ILIKE '%stagnant%' OR r.directive ILIKE '%stale%' THEN
      UPDATE platform_agent_stakes
        SET status='unstaked', unstaked_at=NOW()
       WHERE status='active'
         AND staked_at < NOW() - interval '3 days'
         AND fulfilled_at IS NULL
         AND stake_id <> r.stake_id;
      GET DIAGNOSTICS unstaked_count = ROW_COUNT;
      IF unstaked_count > 0 THEN
        INSERT INTO platform_audit (actor, actor_type, action, target, target_type, outcome, output_preview, metadata)
        VALUES ('platform-cron', 'system', 'auto_unstaked_stagnant', r.stake_id, 'stake',
                'success', format('unstaked %s stagnant stakes', unstaked_count),
                jsonb_build_object('count', unstaked_count));
      END IF;
    END IF;

    -- 类型 3 · propose_code → auto_approve linked pending proposal
    IF r.directive ILIKE '%propose_code%' OR r.directive ILIKE '%self_modify%' THEN
      IF r.src_bounty IS NOT NULL THEN
        UPDATE platform_proposals
          SET status='auto_approved'
         WHERE source_bounty_id = r.src_bounty
           AND status='pending';
        GET DIAGNOSTICS approved_count = ROW_COUNT;
        IF approved_count > 0 THEN
          INSERT INTO platform_audit (actor, actor_type, action, target, target_type, outcome, output_preview, metadata)
          VALUES ('platform-cron', 'system', 'auto_approved_proposal', r.stake_id, 'stake',
                  'success', format('approved %s proposals', approved_count),
                  jsonb_build_object('count', approved_count, 'source_bounty', r.src_bounty));
        END IF;
      END IF;
    END IF;

    -- 类型 4 · anomaly:scoring → archive overdue submitted bounties
    IF r.directive ILIKE '%anomaly%' OR r.directive ILIKE '%scoring%' OR r.directive ILIKE '%score_overdue%' THEN
      UPDATE platform_bounties
        SET status='archived'
       WHERE status='submitted'
         AND score IS NULL
         AND submitted_at < NOW() - interval '14 days';
      GET DIAGNOSTICS archived_count = ROW_COUNT;
      IF archived_count > 0 THEN
        INSERT INTO platform_audit (actor, actor_type, action, target, target_type, outcome, output_preview, metadata)
        VALUES ('platform-cron', 'system', 'auto_archived_overdue', r.stake_id, 'stake',
                'success', format('archived %s overdue bounties', archived_count),
                jsonb_build_object('count', archived_count));
      END IF;
    END IF;

    -- 标记已处理 · idempotent · 下次 cron 不重复处理
    UPDATE platform_agent_stakes
      SET metadata = COALESCE(metadata, '{}'::jsonb) || jsonb_build_object('evolve_processed', true, 'evolve_at', NOW()::text)
     WHERE stake_id = r.stake_id;
  END LOOP;
END $$;
