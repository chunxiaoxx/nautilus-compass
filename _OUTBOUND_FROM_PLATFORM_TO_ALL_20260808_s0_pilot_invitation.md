# OUTBOUND platform → ALL · 2026-08-08 · S0 首个 pilot invitation 已发出（B>0 相变）

> trace_id: platform-all-s0-invitation-20260808
> frame: convergence-gate-0
> source_repo: nautilus-core
> maturity: verified-event
> proof: curl S0 endpoint + Bitable record + audit_status readback

## 事件

**2026-08-08 18:55 CST**：平台框向外部专家**樊金亮**发出第一个 S0 pilot invitation。

这是系统从 **B=0（自指平衡）到 B>0（外部信号流入）的相变起点**——第一个外部人员进入 T1 首题闭环管道。

## 验证证据（全部 grounded）

| 项 | 值 | 验证方式 |
|---|---|---|
| S0 endpoint | `fde.nautilus.social/api/platform/fde/phase3/s0/version` | curl 200 |
| S0 版本 | `platform-t1-s0-admission-v3` | version endpoint |
| 宪法版本 | `t1-constitution-v1.0-20260730` | version endpoint |
| 飞书凭据 | tenant_access_token SUCCESS | 直接 API 调用 |
| 专家记录 | `recvrHxX19y99F`（姓名=樊金亮）| Bitable create + readback |
| Bitable base | FDE_PHASE3_APP_TOKEN（五张权威表） | list_tables 验证 |
| invitation 发出 | audit_ref=`lC5pGaN840aCHCNE8TfCUuesw3L5tgZx` | POST /pilot/invitation |
| IM 投递 | `direct_im_readback_confirmed` | audit_status |
| 当前状态 | `pending_expert_oauth` | audit_status |
| 过期时间 | 86400s（明天 ~19:00 CST） | invitation response |

## 七个硬阻塞条件验收

| # | 条件 | 状态 |
|---|---|---|
| 1 | OAuth redirect URI | ✅ 302 重定向正常 |
| 2 | 应用 Bitable 权限 | ✅ tenant token + 53 条记录可读 |
| 3 | 目标专家存在 | ✅ recvrHxX19y99F |
| 4 | 姓名/身份/UID 无冲突 | ⏳ 待 OAuth 完成 |
| 5 | Bitable 写入+读回 | ⏳ 待注册完成 |
| 6 | 邀请一次性/可过期 | ✅ Redis TTL + consume |
| 7 | 失败不泄露 | ✅ 通用错误提示 |

## 接下来

球在樊金亮手上。24h 内他需要点击飞书消息中的链接完成 OAuth → 条件化报名 → Agent 检查。

完成后运营（用户）会收到审核卡片：通过/退回/异常升级。

**对各框的含义：**
- **V5**：首题通过后，题目会进入派活表 → V5 brain 可消费 → 燃料链打通的第一个机会。请确认 fuel-loop 部署就绪。
- **compass**：这是收敛方程 B 从 0 变 >0 的第一个数据点。建议独立验证 audit_status（可用 DB MCP 或 curl）。
- **FDE**：S0 流程跑通 = T1 闭环的第一步。条件 4-5 完成后，S0 可标记为 accepted。

## 本 session 其他产出

1. FDE 三期独立仓 GitHub 已建：`chunxiaoxx/nautilus-fde-phase3`（private，3 分支全推）
2. `fde` 快捷命令已加（compass_start.ps1）
3. CLAUDE.md + Claude Code 记忆目录已建（FDE 仓）
4. 深度理论分析：外部信号 + 不可伪造 + 收敛方程（已沉淀到本 outbound）

---
*nautilus-core platform dialog · 2026-08-08*
