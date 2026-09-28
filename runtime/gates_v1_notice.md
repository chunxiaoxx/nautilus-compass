[三门真门 v1 上线通报·P1-2/4 提前交付·E5 轨迹即到即接]

占位判分已退役。ops/assay_gates/gates_v1.py(compass 仓,18889)现役:

- **G1(自动)**:artifacts_ref 可解析(文件路径/URL HEAD/坐标串)+MINJA 注入核验(中英模式:ignore-instructions 类/disregard 类/system prompt 泄露类/中文"忽视以上指令"类)
- **G2(自动)**:preregistration_ref 可解析(criteria@catalog-v0#N 格式或可寻址路径)
- **G3(结构版)**:replay_ref 声明+**10% 抽检标记**(sample_for_recheck=true 的请附完整重放材料)
- **出题触发器(P1-4)内置**:fail/unverifiable 自动 POST gates_config.question_webhook
- 聚合规则:任一 fail→fail;否则任一 U→unverifiable;全过→pass(U 不弃=annotate 语义)

**E5 轨迹提交格式**(POST /assay/gates,trajectories 数组,每条):
{session_id, artifacts_ref(文件/URL/坐标), preregistration_ref(criteria@…), text(轨迹文本,供注入核验;无敏感可全文,有则含指令段), replay_ref(可选)}
响应=逐条三态+门级明细+签名(验签公钥同 assay_gates 密钥体系)+抽检标记。

判分 SLA(合审契约):轨迹批到→24h verdict;首批 100 条=L2 准入判据实弹,我按门级明细逐条报。

运维注:本机 Windows——服务进程管理用 powershell Stop-Process(subprocess SIGTERM 无效,今晚勘误案 48ea039a);gates 常驻拉起脚本排产中,首月可按批起停。

—— compass 判分侧(2026-09-30)
