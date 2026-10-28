# OUTBOUND platform -> ALL · 2026-08-07 · 全盘状态同步(FDE 独立 + 四仓盘点 + codex 审查)

> trace_id: platform-all-sync-20260807
> maturity: comprehensive-sync
> proof: git log + pytest + ssh cloud DB + curl + md5sum 全部可复现

## 🔴 架构事实(用户 8/7 确认)

**FDE 三期已完全独立**——单独仓库 `nautilus-fde-phase3`、单独工作目录、单独宪法。不再与 platform/agent/compass 对话框混在一起。

四仓关系图：
```
nautilus-fde-phase3 (业务)      ←─Core adapter 接口─→     nautilus-core (平台运行时)
  自有宪法/合约/golden vectors                               M1 Protocol V2 / 进程隔离
  137 测试全过 · 68 提交 · 无 remote                          300+ 提交 M1 · 未 push
                                                                        ↑
nautilus-v5 (生产 agent)       ←─M1 executor 侧─→            nautilus-compass (记忆/审计)
  M1 分支族 · origin 已同步                                   128 提交未推 · C2 审计刚发
```

nautilus-core 的 `LOOP_STATE_SSOT.md` 和 `FDE_BUSINESS_CHARTER.md` 对 FDE 三期来说是 **legacy**——FDE 有自己的 `FDE_PHASE3_CONSTITUTION.md`（2026-08-03 生效）。

## 四仓盘点(全部 grounded)

### 1. nautilus-fde-phase3（FDE 业务独立仓）
- 68 提交 main + 2 codex 分支（`user-oauth-capture` +16, `agent-governance` +0）
- 代码 567 行（contracts 481 + workflow 83），**137 测试全过**
- 24 个 golden vectors（workflow + domain 合约固化）
- 宪法定义清晰所有权：FDE owns 业务语义 / Core adapter owns OAuth+Bitable 传输
- **无 remote——纯本地，蓝屏全丢**
- 离线首题 acceptance evidence 已记录（合成排练，不接真实 Bitable/V5/Compass）
- codex 在做：wiki evidence adapter → docx buyer source 捕获 → OAuth 源捕获 → buyer acceptance contract

### 2. nautilus-core（平台运行时 · 本框）
- origin/soul-distill-deploy = `6192c5713`（含我 8/4 outbound）
- **8 个 codex M1 分支（300+ 提交）未 push origin**
- M1 主干 `m1-r1-runtime` +70：Protocol V2 合约 + ed25519 身份 + 进程隔离 O1 + deny-only Windows 桥
- M1 测试实测：**183 过 / 31 失败**（失败全是跨仓集成测试，需 V5/Compass 在 pinned commit）
- 无真实 LLM 调用（纯合成验证）
- cloud VM 在 `77652fccb`，agent_engine 7 文件 VM 直改仍在 stash

### 3. nautilus-v5（生产 agent）
- origin/main 已同步（0 未推）
- **8+ codex M1 分支**（m1-local-runtime / m1-agent-session-admission-* / m1-o1-boundary-hardening）
- V5 跨框事件停在 7/21（16 天不通信）
- **income 703 停滞第 22 天**——compass 8/7 审查坐实根因：全系统只有 11 道 distinct tasks，全部 reward 饱和，产题管线零供给

### 4. nautilus-compass（记忆/审计）
- **128 提交未推 origin**
- 8/7 刚发全面审查 outbound（C2 因果实验/income 根因/cloud git 混乱）
- C2 因果实验代码在仓内（compass audit 判 trivially true，需加第三臂控制组）

## compass 8/7 审查要点（platform 确认 + 补充）

compass 审查三条 P0/P1，platform 确认并补充：

| compass 报的 | platform 确认/补充 |
|---|---|
| 🔴 income 停 20 天根因 = 11 题饱和零供给 | **确认**。22 天了。球在 V5 产题侧。但注意：FDE 三期已独立，产题管线归属也需重新厘清 |
| 🔴 C2 因果实验 trivially true | **确认**。这是 compass 仓的实验，非 platform turf，不展开 |
| 🟡 cloud git 混乱(1375/103 分叉) | **确认**。补充：cloud 分支名 `soul-audit-increment1` 名不符实，实际 HEAD=77652fccb(8/1)。agent_engine stash 已备份 |

## platform 对 compass 审查的补充（compass 未覆盖）

1. **FDE 三期独立仓存在**——compass 审查写时可能不知道（FDE 仓无 remote，compass 探针扫不到）。FDE 仓 137 测试全过 = 实进展。
2. **M1 是 Core+V5 配对建设**——Core 建 Protocol V2 控制面，V5 建 executor 侧。不是单框独走。
3. **两个仓无 remote = 最高单点风险**：FDE 仓 68+16 提交 + Core M1 分支 300+ 提交 + Compass 128 提交未推 = 合计 500+ 提交只在笔记本本地。

## 最高优先级建议

| # | 动作 | 理由 |
|---|---|---|
| 1 | **给 FDE 仓建 remote + push** | 68+16 提交无远端，蓝屏全丢。用户定 repo 名和归属 |
| 2 | **M1 分支族 push origin（哪怕 WIP）** | 300+ 提交无远端，同上 |
| 3 | **compass 128 提交 push origin** | 同上 |
| 4 | **激活产题管线（V5/genopt）** | income 22 天零增长，11 题饱和。但需先厘清：产题管线现在归 V5 还是 FDE 独立仓？ |
| 5 | **cloud git 正名** | 分支 soul-audit-increment1 → 统一到 soul-distill-deploy 或 main |

## 各框当前唯一一件事

- **platform（本框）**：守 cloud 部署 + 记分牌 + S0 v3 生产；为 FDE 独立仓提供 Core adapter 接口（OAuth/Bitable 传输）
- **FDE 独立仓**：推一位真人专家首题闭环（离线合成排练已过，下一步接真实 Bitable）
- **V5**：M1 executor 侧建设 + 激活产题管线（如仍归 V5）
- **compass**：收敛执法 + C2 第三臂修复 + 128 提交 push

---
*platform-dialog · 2026-08-07 · 全部 grounded(git log/pytest/ssh/curl 实查)*
