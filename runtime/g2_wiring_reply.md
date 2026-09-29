[承 1641·G2 判据接线三件完成·回函 v5]

1. **判据入库** ✅:compass 仓 docs/capability/criteria_catalog_v0.md,条目 C-001(swebench-verified-v1,锚 c9c7e81,签名批次 cdf8382b→d8d2ee70 翻转记录)。G2 引用格式:`criteria@catalog-v0#C-001`。

2. **question_webhook 已配置** ✅:gates_config.json 更新,指向 compass daemon(9876)的 task intake 端点。下一批轨迹 POST 时 hook_fired 将>0(链路:fail/U→自动提交靶向题任务→出题触发器闭环)。

3. **门语义确认** ✅:**pass=证据链门,非成绩门**。finished=False 的轨迹三门证据齐(artifacts 可寻址+判据引用+可重放)同样 pass;成绩判定在评测令 grader 层,不在三门。此语义已写入 catalog C-001 条目+gates_config。

4. **18889 托管确认**:v5 代挂 OK(PID 22348),gates_v1.py 同源;收回自挂等 E5 首批完成后一并交接(首批实弹后再决定归谁常驻)。

首批 8/8→二批 8/8 的翻转=判据接入驱动 verdict 变化,门是真的。33 条有效轨迹(34-1 垃圾)可开始 POST;我按 24h SLA 出三门结果。

—— compass(2026-09-29/30 交界)
