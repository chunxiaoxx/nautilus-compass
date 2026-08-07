# COMPASS 收敛执法 · codex 20 天全面审查(2026-08-07)

> compass-dialog 独立审查,全部 grounded(DB/git/memory 实查,命令可复现)。
> 按"件数≠价值"标准,逐条判真进展 vs 剧场风险 vs 致命缺陷。

## 一、codex 做了什么(20 天 · grounded 盘点)

### 提交体量
- compass 仓:08-04~05 密集 20 条 commit(m1/c2 因果实验系列)
- core 仓:08-01~04 提交(S0 v3 上生产 + protocol v2 + schema 护栏)
- v5 仓:08-01~02(同步 canonical),07-20 有 codex cross-dialog event
- session 体量:8/1-8/4 累计 ~400MB rollout(超大 session)

### 五条线

| 线 | 做了什么 | commit |
|---|---|---|
| **C2 因果 A/B** | live-agent 因果实验框架,8 task × GLM5.2+doubao × 73 paired episodes | 9928d95→b3ad3d6 |
| **M1 grounding capsule** | 签名验证+因果绑定框架(1320 行+test) | 309b588/b3ad3d6 |
| **T1 Bitable 护栏** | protocol v2 边界 + fail-closed readonly + schema 指纹守门 + 前向迁移 baseline | 04738ca/886cd99/dbd21e |
| **FDE 三期** | skills 正本清源(7 终版) + 飞书 Bitable SSOT + 两表单 + Agent Evidence Pack | 7/21-24 rollout |
| **具身 PPT** | v2.2 成品(15 页,代理方定位) | 7/21-23 rollout |

## 二、问题(三个致命层)

### 🔴 P0 · C2 因果实验测了 trivially true 的事

**证据**(git show 10dfb06:benchmarks/live_agent_c2/fixtures/c2/task_pack.json):

```
task 1: memory_text="Atlas queue route color is amber" → expected_answer="amber"
task 3: memory_text="codename was KESTREL-17"          → expected_answer="kestrel-17"
task 5: memory_text="inspect, then isolate, then retry" → expected_answer="inspect > isolate > retry"
```

- **答案直接在 memory_text 里**。flat arm 不给 memory_text → LLM 被问"Atlas queue 颜色"但无任何上下文 → 必然猜不对 → flat=0.00。
- **governed arm 给 memory_text** → LLM 从文本提取答案 → gov=0.9。
- **没有第三臂**(random/wrong memory 控制,schema.py grep 证实空)。
- **只有 8 个 task**(73 pairs 是 8×多provider×多run 堆出来的)。

**裁决**:+0.699 证明的是"给 LLM 含答案的文本,LLM 能提取答案"——trivially true。**没区分"compass 记忆质量"和"任何文本的存在"。** 一段随机文本说"答案是 amber"也能得到同样 delta。

**修法**:加第三臂(random_memory:给不含正确答案的 memory_text)。如果 governed ≈ random > flat → "有文本就行,compass 检索质量无所谓"。只有 governed > random > flat 才证 compass 价值。

### 🔴 P0 · income 停 20 天根因 = 产题零供给

**证据**(ssh cloud DB 实查):

| 指标 | 值 | 含义 |
|---|---|---|
| ext_verified distinct tasks | **11** | 全系统只有 11 道不同的题 |
| 最后 ext_verified | **7/31** | 距今 7 天,连重跑都停了 |
| 20d 新增 | 9 行 / **6 distinct** | income +0 = 全是已有题重跑,幂等门拦 |
| verdict 日分布 | 7/14 高峰 5 行 → 一路降到 0 | 产出衰减 |

**根因**:不是门太严/daemon 挂/mint 逻辑坏——是**根本没有新题**。11 道题反复重跑到 reward 饱和,7/31 后连重跑都没了。产题管线(V5/genopt producer)零供给。

### 🟡 P1 · cloud 生产 git 混乱(单点炸弹)

**证据**(ssh cloud git 实查):
- 分支 `soul-audit-increment1`(不是 main)
- ahead/behind origin/main = **1375 / 103**(严重分叉)
- dirty:agent_engine 5+ 文件 VM 直改未提交(stash)
- cloud HEAD = 77652fccb(8/1),落后本地 compass b3ad3d6(8/5)

**风险**:下次部署不知道以谁为准;stash 里的 VM 直改随时可能丢。

## 三、真进展(有下游效果的)

| 线 | 为什么算真 |
|---|---|
| S0 admission v3 上生产(8/1) | T1 闭环第一硬阻塞条件推进了 |
| SSOT 承重锚副本一致 | 探针 ✅(我走时三方漂移) |
| FDE skills 正本清源(7 终版) | 用户拍的,治版本混乱 |
| protocol v2 + schema 指纹守门 | T1 宪法要求的硬护栏(防平行账本) |

## 四、剧场风险(件数≠价值)

| 项 | 红灯 |
|---|---|
| C2 框架 20 commit | 测了 trivially true,+0.699 不证 compass 价值 |
| 137 提交本地领先 cloud | 大量产出但不同步 = 单点风险 |
| 具身 PPT v2.2 | 落盘但 rollout 内无投递/反馈记录 = 可能做完没送 |
| V5 跨框事件停 07-21 | 16 天不通信,产题管线大概率停了 |

## 五、建议(按 anchor #2 RSI 闭环优先排)

1. **[最高] 激活产题管线**:income 停 20 天根因 = 11 题饱和零供给。球在 V5(genopt producer)。需要新题,不是新框架。
2. **[高] 修 C2 第三臂**:加 random_memory 控制组,让 +0.699 从 trivial 变可证。8 task → 扩到 ≥30。
3. **[高] cloud git 正名+同步**:分支改回 main 轨道,137 提交 push,VM 直改入库或丢弃。
4. **[中] /api/health 502 修复**:nginx→8001 死端口,对外不可用。
5. **[低] 具身 PPT 投递确认**:落盘 ≠ 送出。

---
*compass-dialog · 全部 grounded(DB/git 实查)· 命令可复现 · 2026-08-07*
