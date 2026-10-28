#!/bin/bash
# V7 M9 · 24h KPI audit · 5 维 SQL · 真数据综合验证
# Created 2026-05-07 · Auditor: nautilus
set -u

DATE_TAG=$(date +%F)
OUT=/home/ubuntu/v7_kpi_audit_${DATE_TAG}.md

SQL() { sudo -u postgres psql -d nautilus_production -At -F '|' -c "$1" 2>/dev/null; }
SQLF() { sudo -u postgres psql -d nautilus_production -c "$1" 2>/dev/null; }

{
echo "# V7 KPI Audit — ${DATE_TAG}"
echo
echo "24h window · ends $(date -u +%FT%TZ)"
echo

# ============ DIM 1: self_modify + propose_code_change 频率 ============
echo "## 1. self_modify + propose_code_change 频率 (24h)"
echo
echo '```'
SQLF "SELECT date_trunc('hour', ts) AS hour, tool_name, count(*) FROM agent_tool_calls WHERE tool_name IN ('self_modify','propose_code_change') AND ts>NOW()-interval '24 hours' GROUP BY 1,2 ORDER BY 1,2;"
echo '```'
TOTAL_SM=$(SQL "SELECT count(*) FROM agent_tool_calls WHERE tool_name IN ('self_modify','propose_code_change') AND ts>NOW()-interval '24 hours';")
echo
echo "24h 合计:${TOTAL_SM}"
if [ "${TOTAL_SM:-0}" -ge 3 ]; then
  echo "**结论:PASS**(≥3)"
else
  echo "**结论:FAIL**(<3 · exit 要求 ≥3)"
fi
echo

# ============ DIM 2: fake-close 率 ============
echo "## 2. fake-close 率 (24h fulfilled stakes)"
echo
echo '```'
SQLF "SELECT s.stake_id, s.fulfilled_at, (SELECT count(*) FROM agent_tool_calls c WHERE c.agent_id=s.agent_id AND c.ts BETWEEN s.staked_at AND s.fulfilled_at) AS tool_count FROM platform_agent_stakes s WHERE s.status='fulfilled' AND s.fulfilled_at>NOW()-interval '24 hours' ORDER BY s.fulfilled_at DESC LIMIT 50;"
echo '```'
FAKE=$(SQL "SELECT count(*) FROM platform_agent_stakes s WHERE s.status='fulfilled' AND s.fulfilled_at>NOW()-interval '24 hours' AND s.fulfilled_url IS NULL AND COALESCE(s.metadata->>'evolve_processed','false')!='true' AND (SELECT count(*) FROM agent_tool_calls c WHERE c.agent_id=s.agent_id AND c.ts BETWEEN s.staked_at AND s.fulfilled_at)=0;")
TOTAL_FUL=$(SQL "SELECT count(*) FROM platform_agent_stakes WHERE status='fulfilled' AND fulfilled_at>NOW()-interval '24 hours';")
echo
echo "fake-close 数:${FAKE} / fulfilled 总数:${TOTAL_FUL}"
if [ "${FAKE:-0}" -eq 0 ]; then
  echo "**结论:PASS**(=0)"
else
  echo "**结论:FAIL**(>0 · exit 要求 =0)"
fi
echo

# ============ DIM 3: compass + drift 调用率 ============
echo "## 3. compass + drift 调用率 (24h)"
echo
echo '```'
SQLF "SELECT tool_name, count(*) FROM agent_tool_calls WHERE (tool_name LIKE '%drift%' OR tool_name LIKE '%compass%') AND ts>NOW()-interval '24 hours' GROUP BY tool_name ORDER BY 2 DESC;"
echo '```'
CD=$(SQL "SELECT count(*) FROM agent_tool_calls WHERE (tool_name LIKE '%drift%' OR tool_name LIKE '%compass%') AND ts>NOW()-interval '24 hours';")
echo
echo "24h 合计:${CD}"
if [ "${CD:-0}" -ge 50 ]; then
  echo "**结论:PASS**(≥50)"
else
  echo "**结论:FAIL**(<50 · exit 要求 ≥50)"
fi
echo

# ============ DIM 4: helix pair_ref + evidence_hash 完整率 ============
echo "## 4. helix pair_ref + evidence_hash 完整率 (24h)"
echo
echo '```'
SQLF "SELECT count(*) FILTER (WHERE block_type='left' AND evidence_hash IS NULL) AS left_no_evidence, count(*) FILTER (WHERE pair_ref IS NULL) AS no_pair, count(*) FILTER (WHERE block_type='left' AND evidence_hash IS NOT NULL AND pair_ref IS NOT NULL) AS healthy, count(*) AS total FROM helix_blocks WHERE ts>NOW()-interval '24 hours';"
echo '```'
LNE=$(SQL "SELECT count(*) FILTER (WHERE block_type='left' AND evidence_hash IS NULL) FROM helix_blocks WHERE ts>NOW()-interval '24 hours';")
NPR=$(SQL "SELECT count(*) FILTER (WHERE pair_ref IS NULL) FROM helix_blocks WHERE ts>NOW()-interval '24 hours';")
echo
echo "left_no_evidence:${LNE} / no_pair:${NPR}"
if [ "${LNE:-0}" -eq 0 ] && [ "${NPR:-0}" -eq 0 ]; then
  echo "**结论:PASS**(both =0)"
else
  echo "**结论:FAIL**(exit 要求 left_no_evidence=0 AND no_pair=0)"
fi
echo

# ============ DIM 5: emotion 多样性 + cycle_n 完整 ============
echo "## 5. emotion 多样性 + cycle_n 完整 (24h · M6 fix 验)"
echo
echo '```'
SQLF "SELECT count(DISTINCT emotion) AS distinct_emotions, count(*) FILTER (WHERE cycle_n IS NULL) AS null_cycle_n, count(*) AS total FROM platform_emotion_log WHERE ts>NOW()-interval '24 hours';"
echo '```'
echo '```'
SQLF "SELECT emotion, count(*) FROM platform_emotion_log WHERE ts>NOW()-interval '24 hours' GROUP BY emotion ORDER BY 2 DESC LIMIT 20;"
echo '```'
DE=$(SQL "SELECT count(DISTINCT emotion) FROM platform_emotion_log WHERE ts>NOW()-interval '24 hours';")
NC=$(SQL "SELECT count(*) FILTER (WHERE cycle_n IS NULL) FROM platform_emotion_log WHERE ts>NOW()-interval '24 hours';")
TE=$(SQL "SELECT count(*) FROM platform_emotion_log WHERE ts>NOW()-interval '24 hours';")
echo
echo "distinct_emotions:${DE} / null_cycle_n:${NC} / total:${TE}"
echo

# ============ 综合 ============
echo "---"
echo
echo "## 综合"
echo
P1=$([ "${TOTAL_SM:-0}" -ge 3 ] && echo PASS || echo FAIL)
P2=$([ "${FAKE:-0}" -eq 0 ] && echo PASS || echo FAIL)
P3=$([ "${CD:-0}" -ge 50 ] && echo PASS || echo FAIL)
P4=$( ( [ "${LNE:-0}" -eq 0 ] && [ "${NPR:-0}" -eq 0 ] ) && echo PASS || echo FAIL)
echo "| 维度 | 实测 | 阈值 | 结果 |"
echo "|---|---|---|---|"
echo "| 1. self_modify+propose_code_change/24h | ${TOTAL_SM:-0} | ≥3 | ${P1} |"
echo "| 2. fake-close 数/24h | ${FAKE:-0}/${TOTAL_FUL:-0} | =0 | ${P2} |"
echo "| 3. compass+drift/24h | ${CD:-0} | ≥50 | ${P3} |"
echo "| 4. helix left_no_evidence + no_pair | ${LNE:-0} + ${NPR:-0} | both=0 | ${P4} |"
echo "| 5. emotion 多样性 / null_cycle_n | ${DE:-0} / ${NC:-0} | (观察) | — |"
echo
echo "## next-step (FAIL 项建议)"
echo
[ "${P1}" = FAIL ] && echo "- DIM1 FAIL → V5/V6 daemon 在 24h 内未触发足够 self_modify。检查 daemon 是否在跑·检查 propose_code_change tool 是否注册到 toolset·检查 emotion 触发阈值是否过高"
[ "${P2}" = FAIL ] && echo "- DIM2 FAIL → fake-close 复活。检查 trg_auto_close_stake trigger 是否仍在·检查 fulfill 路径是否绕过 trigger·检查 staked_at→fulfilled_at 期间 agent_id 是否换"
[ "${P3}" = FAIL ] && echo "- DIM3 FAIL → compass/drift tool 命名是否变·grep tool_name 看真名·V5 lifecycle awaken hook 是否在调"
[ "${P4}" = FAIL ] && echo "- DIM4 FAIL → helix 写入路径 evidence_hash/pair_ref 强制约束未生效·M5 lock 是否真锁·检查 INSERT 调用方"
[ "${P1}" = PASS ] && [ "${P2}" = PASS ] && [ "${P3}" = PASS ] && [ "${P4}" = PASS ] && echo "- 全 PASS · V7 M9 验证 GREEN · 认知-行动断裂修复有效"
echo
echo "---"
echo "audit done · $(date -u +%FT%TZ)"
} > ${OUT}
echo "audit done. report at ${OUT}"
