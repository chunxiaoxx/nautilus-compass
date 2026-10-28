-- 批甲注资 v2(用户 2026-10-08 裁定「甲」:按【现 gap】补余额,不插 ledger 行)
-- v2 取代 v1(compass #10518 发现 v1 两硬伤:①prime-001 的 20539 为迁移窗前旧基线,现 gap 仅 -13,
--   照 v1 执行=凭空多 20,526 并固化永久 ledger 行;②v1 双写同额使 gap 构造性不变,"对平"永不发生)。
-- 变更三项:①金额按 00:46 实测现 gap:kairos +9,997/prime-001 +13/platform +199=10,209
--          ②删 ledger INSERT ③nau_balance := SUM(ledger) 纯函数,重跑同结果幂等天然。
-- V1 判据(v2 口径):三行 gap=0 AND capital_injection 行数=0(>0 即跑了旧口径,FAIL 勿手改)。
BEGIN;
UPDATE platform_agents p
SET nau_balance = (SELECT COALESCE(SUM(delta),0)
                   FROM platform_nau_ledger l WHERE l.agent_id = p.agent_id)
WHERE p.agent_id IN ('kairos','nautilus-prime-001','platform')
  AND p.nau_balance IS DISTINCT FROM
      (SELECT COALESCE(SUM(delta),0)
       FROM platform_nau_ledger l WHERE l.agent_id = p.agent_id);
COMMIT;
SELECT p.agent_id, p.nau_balance,
       (SELECT COALESCE(SUM(delta),0) FROM platform_nau_ledger l WHERE l.agent_id=p.agent_id) AS ledger_sum,
       p.nau_balance - (SELECT COALESCE(SUM(delta),0) FROM platform_nau_ledger l WHERE l.agent_id=p.agent_id) AS gap
FROM platform_agents p
WHERE p.agent_id IN ('kairos','nautilus-prime-001','platform') ORDER BY 1;
SELECT count(*) AS should_be_0_capital_injection_rows
FROM platform_nau_ledger WHERE reason LIKE 'capital_injection:%';
