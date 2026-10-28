# gov_pending 50 条分诊方案(9/26 判分日执行)

> 2026-09-24 平台摸排,数据=云 platform_improvement_proposals WHERE status='pending' 全量 50 条实拉(非抽样)。
> 共性事实:50/50 产自 agent 9000002(主脑 reflection 管线),vote_count 全 0,零条被人工消化过——**这是一个"生产在跑、消费侧死"的管线**。

## 五桶分诊(9/26 照单置态)

### 桶 A · 同题重复轰炸簇(约 17 条)→ 验真一次,修或整簇关闭
| 簇 | 条数 | 提交日 | 判定 |
|---|---|---|---|
| platform_posts post_id/agent_id NOT NULL 插入失败 | 9 | 9/1-9/9 | **同一 bug 提 9 次无人消化**;platform_posts 属旧社交功能(垂域线已死)→ 9/26 验功能死活:功能死=整簇 archived("配套功能已冻结");功能活=修一次置 9 条 |
| pf_revenue_split_24h 引用不存在列 super_pool_usdc | 2 | 9/4 | 同上验活 |
| A2A send_to_agent 422 | 2 | 9/9 | **A2A 通道活物,需验真修**(f9a92608 同族,见桶 E) |
| pf_platform_health TypeError | 2 | 9/18 | 验真 |
| pf_mint/burn NAU 死锁 | 2 | 9/3 | 验真 |

### 桶 B · v5 域代码修复(约 10 条)→ 批量转函 v5 自处置
daemon.py / platform_tools_mixin / self-improve wake 路由 / 8096→8097 等(9/14-9/18)。先例:b2e0a64e 已于 P1 批二退回 v5 域。**9/26 动作=转 v5 域函(附 id 清单),平台侧批量置 delegated。**

### 桶 C · 已在其他账本处理、本表漏置态(2 条)→ 补置态
b2e0a64e(P1 批二已核)/a1cf81cf(平台已认领=GOAL_STACK 栈项12)——**结论早已存在,状态没回写**。9/26 按既有结论补 status+resolution_note。

### 桶 D · 机制类+管线误入(4 条)→ 拒收/改道
- 2ab566c2(cron tick prompt 硬铁律)/30a7ba97(flywheel_breaker 5min cron):机制类,9/2 冻结令默认拒收 → rejected
- auto-e9-stalled-2026-09-21/22:**E9 催办管线的信号不该进改进提案表**——顺手 bug:自动催办写入路由改投 mailbox/处置线(接线收敛,非新机制)

### 桶 E · 真平台域待验真修复(约 15 条)→ 商业线相关优先序消化
优先序(9/26 判分日按此排):
1. **f9a92608**:A2A 通道对活体 high-tier agent 返回错误(商业线:外部客户接进来的通道!)
2. **400209a7**:路径穿越防护(安全类)
3. **af6078ba**:submit_bounty direct DB write 兜底(fail-open 危险模式,同 9/12 部署管线案族)
4. 3f847823(L1 evidence_validator)/d15f44e4(escrow guard)/36795ea8(stale stakes)——结算线卫生
5. 66b8f4f8/d48ea9c7/34c99a47(timeout 归一化/cwd 校验/chdir 漂移)——执行器卫生
6. 其余按需

## 根因两条(9/24 已过接线收敛审查,修法如下)
1. **reflection 提案无去重键**:同 bug 重提 9 次=噪音淹没真信号。
   → **修法 B(采纳)**:生产侧去重——v5 self-improve 管线加"同 root_cause 簇 7d 内已存在则跳过"(v5 域一行事,函 9/24 已转);平台侧零新码。
   → 备选 C(暂缓):关停提案表写入,真 bug 改投 mailbox 工作单(现有 SLA/处置线全链)。属机制生杀=用户专属;B 观察 9/26+10/8 两轮,若 gov_pending 仍 >20 呈用户拍 C。
2. **消费侧无消化位**:治理提案表没有 owner/节奏。
   → **修法 B(采纳)**:并入判分双周节奏——判分日议程固定一节"治理提案置态"(GOAL_STACK 维护节已记一行,零新机制)。
   → **修法 C(采纳)**:快照水位阈值棘轮收紧 `>50` → `>=40`(旧阈值不含等号,恰好 50 条压线未亮=今晨日报沉默原因,实锤修复)。
   → 不建:治理周会/常设 owner(新机制,冻结令拦)。

## 执行日清单(9/26)
1. 桶 C 补置态(2 条,五分钟)
2. 桶 A 验活(platform_posts/pf_* 功能死活)→ 修或整簇 archived
3. 桶 B 转函 v5(id 清单随函)
4. 桶 D 置 rejected + E9 写入路由改道小修
5. 桶 E 按优先序消化(1-3 当日必须,4-6 可顺延下周)
6. 置态纪律:每条 UPDATE 带 resolution_note + resolved_by='platform-triage-0926';完成后快照 gov_pending 读数应 <10
