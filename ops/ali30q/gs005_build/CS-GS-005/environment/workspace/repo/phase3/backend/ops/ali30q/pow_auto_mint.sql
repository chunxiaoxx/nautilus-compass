-- PoW 自动铸造触发器(阿里30q)
-- 当 platform_bounties.status 变为 completed 时自动:
-- 1. 在 fuel_trajectories 插入 PoW 轨迹
-- 2. 在 platform_nau_ledger 入账 NAU
-- 前提: result 字段需含 golden_passrate 数据

-- 创建触发器函数
CREATE OR REPLACE FUNCTION pow_auto_mint()
RETURNS TRIGGER AS $$
DECLARE
    nau_amount INTEGER := 10;
    pow_id TEXT;
    bal INTEGER;
BEGIN
    -- 仅在 status 变为 completed 时触发
    IF NEW.status = 'completed' AND OLD.status != 'completed' 
       AND NEW.bounty_id LIKE 'ali30q%' THEN
        
        pow_id := 'pow-auto-' || NEW.bounty_id || '-' || extract(epoch from now())::bigint;
        
        -- IRT 难度加成
        IF NEW.difficulty = 'hard' THEN
            nau_amount := nau_amount + 10;
        ELSIF NEW.difficulty = 'medium' THEN
            nau_amount := nau_amount + 5;
        END IF;
        
        -- 余额查询
        SELECT COALESCE(balance_after, 0) INTO bal
        FROM platform_nau_ledger 
        WHERE agent_id = COALESCE(NEW.claimed_by, 'platform')
        ORDER BY id DESC LIMIT 1;
        bal := COALESCE(bal, 0);
        
        -- fuel 轨迹
        INSERT INTO fuel_trajectories 
            (traj_id, bounty_id, submitter, qid, context, trajectory, verdict, label_origin)
        VALUES 
            (pow_id, NEW.bounty_id, 
             COALESCE(NEW.claimed_by, 'platform'), NEW.qid,
             'PoW自动铸造 ' || NEW.bounty_id,
             json_build_object('bounty_id', NEW.bounty_id, 'status', NEW.status,
                 'difficulty', NEW.difficulty, 'nau', nau_amount,
                 'pow_hash', md5(NEW.bounty_id || now()::text)),
             'PASS', 'pow-auto-mint');
        
        -- NAU 入账
        INSERT INTO platform_nau_ledger
            (agent_id, delta, reason, balance_after, linked_bounty_id)
        VALUES
            (COALESCE(NEW.claimed_by, 'platform'), nau_amount,
             'PoW ' || NEW.bounty_id, bal + nau_amount, NEW.bounty_id);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 创建触发器
DROP TRIGGER IF EXISTS pow_auto_mint_trigger ON platform_bounties;
CREATE TRIGGER pow_auto_mint_trigger
    AFTER UPDATE ON platform_bounties
    FOR EACH ROW
    WHEN (NEW.status = 'completed' AND OLD.status != 'completed'
          AND NEW.bounty_id LIKE 'ali30q%')
    EXECUTE FUNCTION pow_auto_mint();
