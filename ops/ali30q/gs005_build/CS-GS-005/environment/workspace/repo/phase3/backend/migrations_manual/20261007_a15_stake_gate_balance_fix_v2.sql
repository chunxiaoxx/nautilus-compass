-- A1.5 修复 v2(2026-10-07):余额真值字段=platform_agents.nau_balance(实测列分布确认;agents 整数表无余额字段)
-- 门禁读真值字段+两函数双写 platform_agents.nau_balance;platform_pool 无字段保持 SUM(ledger)
-- 注:整数表(agents)新注册体不在 platform_agents 名册→SELECT NULL→COALESCE 0→押金拒绝(保守防白嫖;其 500 survival 点为另一体系)

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

    SELECT COALESCE(nau_balance, 0) INTO claimer_balance
    FROM platform_agents WHERE agent_id = NEW.claimed_by;

    IF claimer_balance IS NULL THEN
        RAISE EXCEPTION 'STAKE_NO_ACCOUNT: agent % not in platform_agents roster', NEW.claimed_by
            USING ERRCODE = 'P0001';
    END IF;

    IF claimer_balance < stake_amount THEN
        RAISE EXCEPTION 'INSUFFICIENT_STAKE: agent % balance % < required stake % for bounty %',
            NEW.claimed_by, claimer_balance, stake_amount, NEW.bounty_id
            USING ERRCODE = 'P0001';
    END IF;

    new_balance := claimer_balance - stake_amount;

    INSERT INTO platform_nau_ledger (agent_id, delta, reason, balance_after, linked_bounty_id)
    VALUES (NEW.claimed_by, -stake_amount, 'stake_on_claim', new_balance, NEW.bounty_id);

    UPDATE platform_agents SET nau_balance = new_balance WHERE agent_id = NEW.claimed_by;

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
    pool_row RECORD;
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
    IF EXISTS (
        SELECT 1 FROM platform_nau_ledger
        WHERE linked_bounty_id = NEW.bounty_id
          AND (reason LIKE 'stake_release_on_%' OR reason LIKE 'stake_slash_on_%')
    ) THEN
        RETURN NEW;
    END IF;
    SELECT nau_balance INTO pool_row FROM platform_agents WHERE agent_id = pool_id;
    IF is_release THEN
        SELECT COALESCE(nau_balance, 0) INTO claimer_balance
        FROM platform_agents WHERE agent_id = stake_claimer;
        IF claimer_balance IS NULL THEN
            RETURN NEW;
        END IF;
        new_balance := claimer_balance + stake_amount;
        INSERT INTO platform_nau_ledger (agent_id, delta, reason, balance_after, linked_bounty_id)
        VALUES (stake_claimer, stake_amount, 'stake_release_on_' || NEW.status, new_balance, NEW.bounty_id);
        UPDATE platform_agents SET nau_balance = new_balance WHERE agent_id = stake_claimer;
        INSERT INTO platform_audit (actor, actor_type, action, target, target_type, outcome, metadata)
        VALUES (stake_claimer, 'trigger', 'stake_release_terminal', NEW.bounty_id, 'bounty', 'success',
                jsonb_build_object('stake_amount', stake_amount, 'terminal_status', NEW.status, 'new_balance', new_balance));
    ELSE
        IF pool_row IS NULL THEN
            RETURN NEW;
        END IF;
        SELECT COALESCE(nau_balance, 0) INTO pool_balance
        FROM platform_agents WHERE agent_id = pool_id;
        new_balance := pool_balance + stake_amount;
        INSERT INTO platform_nau_ledger (agent_id, delta, reason, balance_after, linked_bounty_id)
        VALUES (pool_id, stake_amount, 'stake_slash_on_' || NEW.status, new_balance, NEW.bounty_id);
        UPDATE platform_agents SET nau_balance = new_balance WHERE agent_id = pool_id;
    END IF;
    RETURN NEW;
END;
$function$;
