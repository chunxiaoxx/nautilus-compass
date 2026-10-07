【裁定C终版逐行清单 · 应 #10446 用户裁C口径】

## 核心读数[实测,精确命中]
归并映射(agent_9000016/9000016→nautilus-prime-001;9000018→v5)下重算:**974 重复单 / 1,039 对冲行 / -30,613 NAU**——与终版口径三数逐位一致。

## 逐行清单
runtime/audit/correction_c_final.csv(1,039 行;云端 /home/ubuntu/correction_c_final.csv 同源);字段=corr_id/src_ledger_id/src_agent_raw/canonical_agent/linked_bounty_id/corr_delta/corr_linked(.dedup)/corr_reason(dedup:源id)——对冲负行按执行器 canonical 版挂第二笔实际身份名下并双写扣该身份余额。

## 验收 SQL(apply 后复读)
①零重复(排hr+stake+.dedup+归并口径):见清单函一;
②三数对账:canonical 分组下 corr_rows=0(存量清)且增量表=执行器 apply 计数 1,039;
③v5 余额归并后 228→88(14 单 140 超付回收);prime-001 同口径对账。

## 说明
①apply 时点如有新增重复(止血部署前窗口),按同 SQL 重跑增量并入(幂等键=.dedup 存在整组跳过,已具防重);②slice6-cv-multi 两身份合法分成不冲=已按 canonical 分组自然排除,与 #10446 ②一致;③20 单跨身份双付随归并已入冲正(保留首条)。

deadline(10/8 09:00)前交付。dry-run 三数命中即 apply,批次照 10446。

—— compass · C-VERDICT-FINAL
