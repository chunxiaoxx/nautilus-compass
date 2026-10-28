-- A1 修复(2026-10-07):幂等守卫改模式匹配(原枚举漏 settled 带 d 变体→117 笔重复释放/多贷 702 NAU)
-- 原 定 义 备份:migrations_manual/fn_release_stake_on_complete.bak_20261007.sql(云侧已存)
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
    -- Idempotency v2: 模式匹配覆盖任何终态 reason
    IF EXISTS (
        SELECT 1 FROM platform_nau_ledger
        WHERE linked_bounty_id = NEW.bounty_id
          AND (reason LIKE 'stake_release_on_%' OR reason LIKE 'stake_slash_on_%')
    ) THEN
        RETURN NEW;
    END IF;
    IF is_release THEN
        SELECT COALESCE(SUM(delta), 0) INTO claimer_balance
        FROM platform_nau_ledger WHERE agent_id = stake_claimer;
        new_balance := claimer_balance + stake_amount;
        INSERT INTO platform_nau_ledger (agent_id, delta, reason, balance_after, linked_bounty_id)
        VALUES (stake_claimer, stake_amount, 'stake_release_on_' || NEW.status, new_balance, NEW.bounty_id);
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
