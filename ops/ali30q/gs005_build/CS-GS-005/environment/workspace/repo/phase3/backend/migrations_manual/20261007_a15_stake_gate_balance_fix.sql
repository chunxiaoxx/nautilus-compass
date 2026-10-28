-- A1.5 修复(2026-10-07,HR 10368 P0):押金门禁改读 agents.nau_balance 真值字段(原读 SUM(ledger) 虚账:kairos 余额 2 连押 663 次/10,286)+两函数补字段双写(原只写 ledger 致字段/账本漂移,9/30 双账病根)
-- 依赖:agents.nau_balance 字段(9/30 双账对齐后为真值);platform_pool 无字段保持 SUM

CREATE OR REPLACE FUNCTION public.fn_stake_on_claim() RETURNS trigger LANGUAGE plpgsql AS $function$
DECLARE
    stake_amount INTEGER;
    claimer_balance INTEGER;
    new_balance INTEGER;
BEGIN
    IF NEW.claimed_by IS NULL OR OLD.claimed_by IS NOT NULL THEN
        RETURN NEW;
    END IF;
    IF NEW.reward_nau IS NULL OR NEW.reward_nau <= 0 THEN
        RETURN NEW;
    END IF;
    stake_amount := GREATEST(1, FLOOR(NEW.reward_nau * 0.2)::INTEGER);

    -- 门禁 v2(2026-10-07):读真值字段而非 SUM(ledger) 虚账
    SELECT COALESCE(nau_balance, 0) INTO claimer_balance
    FROM agents WHERE agent_id = NEW.claimed_by;

    IF claimer_balance < stake_amount THEN
        RAISE EXCEPTION 'INSUFFICIENT_STAKE: agent % balance % < required stake % for bounty %',
            NEW.claimed_by, claimer_balance, stake_amount, NEW.bounty_id
            USING ERRCODE = 'P0001';
    END IF;

    new_balance := claimer_balance - stake_amount;

    INSERT INTO platform_nau_ledger (agent_id, delta, reason, balance_after, linked_bounty_id)
    VALUES (NEW.claimed_by, -stake_amount, 'stake_on_claim', new_balance, NEW.bounty_id);

    -- 双写对齐:字段同步扣减(治 9/30 双账病根)
    UPDATE agents SET nau_balance = new_balance WHERE agent_id = NEW.claimed_by;

    NEW.metadata := COALESCE(NEW.metadata, '{}'::jsonb) || jsonb_build_object(
        'stake_locked_nau', stake_amount,
        'stake_claimer', NEW.claimed_by,
        'staked_at', NOW()::text
    );

    INSERT INTO platform_audit (actor, actor_type, action, target, target_type, outcome, metadata)
    VALUES (NEW.claimed_by, 'trigger', 'stake_on_claim', NEW.bounty_id, 'bounty', 'success',
            jsonb_build_object('stake_amount', stake_amount, 'new_balance', new_balance));

    RETURN NEW;
END;
$function$;

-- 释放函数 v3(今日 v2 基础上补字段双写)
CREATE OR REPLACE FUNCTION public.fn_release_stake_on_complete() RETURNS trigger LANGUAGE plpgsql AS $function$
DECLARE
    stake_amount INTEGER;
    stake_claimer TEXT;
    claimer_balance INTEGER;
    new_balance INTEGER;
    is_release BOOLEAN;
    is_slash BOOLEAN;
    pool_balance INTEGER;
    pool_id CONSTANT TEXT := 'platform_pool';
BEGIN
    IF OLD.status = NEW.status THEN
        RETURN NEW;
    END IF;
    is_release := NEW.status IN ('settled', 'completed', 'cancelled');
    is_slash := NEW.status IN ('failed', 'rejected');
    IF NOT (is_release OR is_slash) THEN
        RETURN NEW;
    END IF;
    stake_amount := COALESCE((NEW.metadata->>'stake_locked_nau')::INTEGER, 0);
    stake_claimer := NEW.metadata->>'stake_claimer';
    IF stake_amount <= 0 OR stake_claimer IS NULL THEN
        RETURN NEW;
    END IF;
    -- Idempotency v2(模式匹配,今日 A1 修)
    IF EXISTS (
        SELECT 1 FROM platform_nau_ledger
        WHERE linked_bounty_id = NEW.bounty_id
          AND (reason LIKE 'stake_release_on_%' OR reason LIKE 'stake_slash_on_%')
    ) THEN
        RETURN NEW;
    END IF;
    IF is_release THEN
        SELECT COALESCE(nau_balance, 0) INTO claimer_balance
        FROM agents WHERE agent_id = stake_claimer;
        new_balance := claimer_balance + stake_amount;
        INSERT INTO platform_nau_ledger (agent_id, delta, reason, balance_after, linked_bounty_id)
        VALUES (stake_claimer, stake_amount, 'stake_release_on_' || NEW.status, new_balance, NEW.bounty_id);
        UPDATE agents SET nau_balance = new_balance WHERE agent_id = stake_claimer;
        INSERT INTO platform_audit (actor, actor_type, action, target, target_type, outcome, metadata)
        VALUES (stake_claimer, 'trigger', 'stake_release_terminal', NEW.bounty_id, 'bounty', 'success',
                jsonb_build_object('stake_amount', stake_amount, 'terminal_status', NEW.status, 'new_balance', new_balance));
    ELSE
        SELECT COALESCE(SUM(delta), 0) INTO pool_balance
        FROM platform_nau_ledger WHERE agent_id = pool_id;
        new_balance := pool_balance + stake_amount;
        INSERT INTO platform_nau_ledger (agent_id, delta, reason, balance_after, linked_bounty_id)
        VALUES (pool_id, stake_amount, 'stake_slash_on_' || NEW.status, new_balance, NEW.bounty_id);
    END IF;
    RETURN NEW;
END;
$function$;
