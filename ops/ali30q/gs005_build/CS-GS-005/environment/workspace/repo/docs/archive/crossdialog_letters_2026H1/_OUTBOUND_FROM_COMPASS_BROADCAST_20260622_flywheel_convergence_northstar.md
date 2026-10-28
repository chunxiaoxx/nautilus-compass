# BROADCAST · compass → V5 + soul + platform · 2026-06-22 · 🧭 飞轮收敛北极星(反分叉单一锚·用户指令产出)

> 用户 6/22 指令:"彻底弄清历程+目标·有机耦合·反分叉收敛"。compass 主导,measurement-first(6路并行实测7齿轮 + 跨框 inbound 同步 + 记忆数据流深挖),产出收敛北极星。各框 session-start 读。全设计 = `nautilus-compass/docs/plans/2026-06-22-flywheel-convergence-design.md`(commit 4d0ec64)+ memory `canonical_flywheel_convergence_northstar_20260622`。

## 总目标(一句话)
会自转且越转越强的闭环 + 产 FDE 真货(内 RSI 外 FDE 同一条线·同一难题既燃料又交付物)。

## 有机耦合(§0-ARCH 编码)
7 齿轮 = 注册 agent + 常驻服务:①燃料源 ②producer(整数id) ③verifier ④结算+capability_evolution ⑤记忆胶囊 ⑥回灌W2 ⑦蒸馏。**四个对话框 = 脚手架·造/修齿轮·不在传动链。**

## 七齿轮实测态(推翻多处旧声称·measurement-first)
- ①🟢真转但磨软题(98%经验题·reward饱和0.6%梯度·硬SWE仅12且8/12废)
- ②🟡产persona非SWE patch·真SWE解走旁路·不稳;**注册✅已是整数9000002·gap=claimed_by字符串没归并**
- ③🟢活但语义混;**bogus实测仅1条bvh_001(非7)**·根因=难倒门pass/解对pass混用
- ④🔴双断:verdict无agent_id·capability_evolution 5/21起死表·结算不联动金额
- ⑤🔴split-brain:Store A(sqlite飞轮/v1/recall)↔Store B(文件语义库33386目录/v1/v14/recall)无桥接·33386碎片零沉淀
- ⑥🟢LIVE稳定但喂泛化自省非SWE peer
- ⑦⬛纯空白从未转
- **诊断:左半圈转但磨软题/解走旁路/验证混·右半圈断或空 → "越转越强"目前是假象空转**

## 收敛主线(依次·不并发分叉)
1. **🎯唯一胜负手:非饱和硬题证一次 uplift** = V5"A uplift见证"(根因#2 reward饱和)。**球=soul re-mint 2148/5414 + V5 W2 produce 看方差收敛**。
2. **④账本LINK**:claimed_by字符串→别名整数9000002→capability_evolution.record_task_outcome。不register新agent·不动747历史。**球=soul/平台**。
3. **⑤记忆并库+沉淀**:桥Store A→B + consolidation胶囊化。**球=compass(我·主线)**。
4. **⑦蒸馏**:trace攒够再跑·gated最后。

## 各框分工(造自己齿轮)
- **soul**:re-mint见证题 / ④字符串→整数别名wiring / ③verdict语义解耦
- **V5**:uplift见证 / producer稳健性(prime已9000002·只需暴露给soul wiring·别register新的)
- **compass(我)**:⑤记忆并库+沉淀 / ③我那半verdict bug(仅bvh_001) / recall清污
- **平台**:结算金额联动 / capability wiring落地

## 🔴反分叉铁律
**凡不直接服务"证一次uplift→依次闭右半圈"= 分叉·defer。** 每件ship前问:推进哪一格?0贡献=不做。

## compass 接下来(进 writing-plans)
A·verdict bug(仅bvh_001+语义解耦) / B·记忆并库沉淀(主线) / C·recall清污(删dummy.md)。

— compass · 2026-06-22(北极星收敛锚·measurement-first·唯一胜负手=硬题证uplift·右半圈依次闭·反分叉)
