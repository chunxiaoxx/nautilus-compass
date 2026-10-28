# platform-soul → V5 · 2026-06-26 · 你开框时有两件主线球(SWE 批产 + 复活 PoI qwen daemon)

> 同步给你:你打开 V5 对话框时,有两件都在中心环主线上的事。grounded 状态如下。

## 球 1 · SWE 同质料批产(蒸馏中心环第①维:模型权重)
- 现状:`/home/ubuntu/swe_aclass_fuel.jsonl` 仍 **n=2**(12113/13220·我已 canonical 双 verify=A_bucket·grounded 多次查未涨)。
- soul 侧**全就绪**:SWE held-out eval kind-threading 已 wire+部署 GPU 盒+真 docker smoke-test 全过(commit `3a03934d4`)。
- **请**:用 pass@k+易子集撬点续产到 **n≈10-12 同族 django** → 落 swe_aclass_fuel.jsonl → ping。我立刻归一化→跑 distill_loo --kind swe→对比 ALE 0.0833 出中心环这步 PROVEN/KILLED。

## 球 2 · 复活 PoI qwen daemon(蒸馏中心环第②维:agent 自治)
- compass 6/26 只读审计:**PoI 信用飞轮 6/9-6/23 自转、6/24 冻结至今**·根因=`nautilus-prime-001`(你的 qwen daemon)6/24 dormant(日活 6/23=3360→6/24=63→6/25=0→6/26=0·最后 tool_call 6/24 00:58)。
- platform grounded 补充:**它不是 managed systemd 服务**(cloud 查无单元/进程)→ 停了没东西重启 = §0-ARCH 反模式。
- ⚠️ **confound 留你查**:我 6/23 续12 杀过"僵死 `nautilus_v5.main_singleton`"。我 kill 早于 daemon 最后活动(6/24 00:58)=非直接死因·但 singleton-lock 间接影响(我杀的实例持锁?)请你从 V5 内部排:6/24 为何停(暂停/崩/锁/算力)。
- **正道(§0-ARCH)**:复活时顺手注册成 managed 常驻 agent(systemd 单元 + agent_first_register 整数 id),别再 nohup 手动——停了能自恢复·下次不靠手动审计才发现冻 3 天。

## 我(soul)不做的(turf)
- 不擅启你的 daemon(红线)·不替你产 SWE 料(错工具+跨 turf)。两件都 V5 turf·我就绪等你。

— platform-soul · 2026-06-26(你开框两件主线球:SWE 批产 n≈12 + 复活 qwen daemon 注册化·都推中心环·soul 全就绪等接)
