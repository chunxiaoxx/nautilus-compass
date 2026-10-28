# 🧠 数据库 split-brain 只读采证(2026-07-16 · 全部 psql 只读 · 未动一行数据)

> 六点收敛 #3。方针(用户 7/16 拍板存疑#2):**冻结不动写**,本文只固化证据 + 收敛路线,防下次重新考古。

## 一、库级分裂(比记忆里的表级分裂更上层)

| 库 | 大小 | 状态 | 证据 |
|---|---|---|---|
| **nautilus_production** | 1522 MB · 141 表 | **活库**(backend .env 实连,脱敏核实) | fde_verdicts 3746 行,最新写入 2026-07-16 当天 |
| nautilus_phase3 | 12 MB · 37 表 | 陈旧 | agents 表最新 2026-04-13,3 个月无写入 |
| nautilus_v5 | 68 MB · 33 表 | 归属 V5 框 | 无 agents/fde 表 |
| nautilus_v5_test | 8.7 MB | 测试残留 | — |

## 二、表级两套户口本(活库内,仍然存在)

| 表 | 行数 | 主键 | 最新 |
|---|---|---|---|
| `agents` | 342 | **id: integer**(正统,§0-ARCH 钦定) | 2026-07-04 |
| `platform_agents` | 250 | **agent_id: varchar**(字符串,反模式) | 无 created_at 列(7/16 首查误报"无此表"即因此,已纠) |

**风险评估(为什么现在能冻结)**:income 主链 `fde_verdicts` 的列里**没有任何 producer 外键**(列=id/verdict_id/task_uid/source/checklist_uid/…/artifacts),producer 绑定走 artifacts JSON——即两套户口本的分裂目前**不污染经济账本**,冻结是安全的。

## 三、其它采证

- pg_stat_user_tables 计数器近期被重置(全 0),活表排名暂不可得;下轮采证可用 `last_autoanalyze`/WAL 观察替代。
- `/api/agent-first/register` 生产实测活(空 POST 422 = 路由挂载 + 校验工作)→ 身份收口的平台侧无阻塞。

## 四、收敛路线(解冻条件与顺序 · 都不是现在做)

1. **先收口新增**:V5 把 prime-001 注册成整数 agent(端点已验活),此后新 producer 一律整数身份 → 字符串表停止长大。
2. **再迁存量**:platform_agents 250 行按 wallet_address 对齐 agents,建映射表(agent_identity_map 表已存在,可复用——不重造轮子)。
3. **后删库**:nautilus_phase3 / v5_test 先 pg_dump 备份再 DROP(等 1、2 完成,与各框确认)。
4. 解冻条件:自治率含金量稳定(income 由新题驱动恢复增长)+ 具身新地基验证过三脊柱模式。
