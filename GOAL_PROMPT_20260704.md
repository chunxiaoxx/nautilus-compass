# Compass 新会话 · 针对性解决 + 规避提示词 · 2026-07-04

> 🔴 **8 件 dog熊掰玉米漏掉的事针对性解法** · compass dialog 7/4 真落档 · 给下 session 一开就规避 + 解决。

## 📍 第一动作(必须 · 永远)

```bash
pwd && cat CLAUDE.md && git log --oneline -5 && python ops/auto_surface_hook.py
```

期望:pwd = `C:\Users\chunx\Projects\nautilus-compass` · CLAUDE.md = nautilus-compass · 最近 commit 见 ce40d65 / d30d191 / d116e96 / f849b4f / 3d03909 · hook 0 待读已推完。

**核身份 4 件**(避免漏 2 越界复发):
1. `pwd` 必须是 compass 项目
2. `whoami` = compass(非 platform-soul / 非 core / 非 v5)
3. 唯一可改 = `C:\Users\chunx\Projects\nautilus-compass\` 项目内
4. 越界写其他 dialog 文件 = 立刻自纠并 revert

## 🎯 主线目标(用户原话 7/4 真钉死)

**推动 eng 基准训练 + RSI + FDE 三方一起推**(FSL 双轮引擎)· 真闭环判据:
- `agent_survival.total_income` 24h delta > 0(目前 0 · 真阻塞)
- ALE 真跑题 ahc005/009/018 出 reward 序列喂 RSI
- Producer 真注册(治 SSOT §0-ARCH 红线)

## 🚨 8 件漏掉的事 · 针对性解决(每件给真治法 + 不复发契约)

### 漏 1 · compass .claude/memory/ 6 周空

**真治法**:
- session-end 必写 `compass/.claude/memory/session_YYYYMMDD_*.md`
- 写 5 件真事件:commit hash + 真 ship record_id + 阻塞解路径 + 教训 + 下 session 入口
- 模板:`session_20260704_compass_genopt_main_loop_handoff_continuation.md`(7/4 01:30 真写的可参考)

**不复发契约**(每 session 必检):
```bash
ls .claude/memory/session_*.md | tail -3   # 至少 1 个本 session 写的
```

### 漏 2 · 4 个越界写 core 的 outbound 未挪回

**真治法**:
- 已挪回 1 个:`_OUTBOUND_FROM_COMPASS_TO_V5_CORE_20260704_0035_4ship.md`(7/4 01:02 挪)
- 还剩 3 个:`_OUTBOUND_FROM_PLATFORM_SOUL_TO_COMPASS_20260611_*.md` / `_20260614_*.md` / `_20260617_*.md` 实际不属我写(是 platform-soul 发的 inbound)
- **纠正**:这 3 个**不是我写的**,是 platform-soul 写给 compass 的 inbound = 真在 core 是 outbound=收件人 compass 在 core 路径发
- **真解**:`auto_surface_hook.py` 已配置扫多路径(含 core)· 真消费 = 不挪文件,只 watermark 标已读

**不复发契约**:
- 写任何文件前 `pwd && cat CLAUDE.md` 核身份
- 真要写跨 dialog 协调文件 = 先 outbound 到对方 dialog 真路径(对方 dialog 的 `_OUTBOUND_TO_*.md`)

### 漏 3 · HANDOFF 文档 2 版冗余

**真治法**:
- 删第一版 `HANDOFF_20260704.md`(0:50)
- 只留 `HANDOFF_20260704_FINAL.md`(01:15)
- 后续 handoff 一律 `_FINAL.md` 后缀 + 增量更新不另起新文件

**不复发契约**:
- session-end 不写 2 版 handoff
- 真要 update = `Edit` 第一版,不复写

### 漏 4 · SSOT 3 份漂移未真治

**真治法**:
- canonical SSOT = `nautilus-core/LOOP_STATE_SSOT.md`(不可改,只能 ingest)
- compass 副本 = `compass/LOOP_STATE_SSOT.md` 只**增量同步**(不全替换)
- v5 副本 = `v5/LOOP_STATE_SSOT.md` 同样只增量
- 三份同步协议:core canonical 改 → compass/v5 pull 同步,不直接写副本

**不复发契约**:
- 不再越权改 `compass/LOOP_STATE_SSOT.md`(我之前 7/3 17:25 改的是错)
- 真要 sync = 写 `_INBOUND_FROM_CORE_SYNC_*.md` 触发 inbound 同步

### 漏 5 · baseline 数字 4 题未修

**真治法**:
```bash
ssh cloud "FDE_API_SECRETS_ENV=/home/ubuntu/.claude/.cache/.fde_api_secrets.env python3 -c \"
import sys, urllib.request, json
sys.path.insert(0, '/home/ubuntu/fde-toolbox')
from feishu_client import tenant_token
APP='KY9ZbC2Qqa6ZZXsKrWyc5VGRnXe'; TABLE='tblQAW4aNM99nva6'
token=tenant_token()
# 4 题 record_id + 真 best_score 数字(从 v5 trajectory 读,不凭 SSOT)
fixes = [
    ('recvonYFKs6U4x', {'best_score': 100.0, 'baseline_score': 89.5}),   # TSP
    ('recvonYGbsVKc9', {'best_score': 66.67, 'baseline_score': 33.33}), # BinPack
    ('recvonYGBYYSMR', {'best_score': 23.06, 'baseline_score': 17.0}),  # Attention
    ('recvonYH6gNea7', {'best_score': 10.92, 'baseline_score': 9.0}),   # Cache
]
for rid, fields in fixes:
    url=f'https://open.feishu.cn/open-apis/bitable/v1/apps/{APP}/tables/{TABLE}/records/{rid}'
    req=urllib.request.Request(url, data=json.dumps({'fields':fields}).encode(), headers={'Content-Type':'application/json; charset=utf-8','Authorization':'Bearer '+token}, method='PUT')
    r=json.loads(urllib.request.urlopen(req, timeout=30).read().decode())
    print(f'{rid}: code={r.get(\"code\")}')
\""
```

**不复发契约**:
- 真 ship 前先读 v5 真 trajectory v7 字段,不凭 SSOT + commit 推断
- 数字以 v5 实际 record 字段为准,不是 core factory trajectory v7

### 漏 6 · ALE 真跑题未做

**真治法**:
```bash
# 跑 ahc005/009/018 出真 reward 序列
ssh cloud "python3 -c \"
import sys
sys.path.insert(0, '/home/ubuntu/fde-toolbox')
sys.path.insert(0, '/c/Users/chunx/Projects/nautilus-compass/ale_bench')
from ale_eval import eval_fn
# ahc005 真跑(rejected baseline reward=0, ref reward=已知)
print('ahc005:', eval_fn('# include guard', problem_id='ahc005'))
print('ahc009:', eval_fn('# include guard', problem_id='ahc009'))
\""
```

**不复发契约**:
- 真 reward 数据写 `.claude/memory/alc_real_rewards_*.md`(落档)
- 1 道题跑通后 = 用 V5 rsi_two_arm `eval_fn=ale_eval.eval_fn` 注入(已留接口)

### 漏 7 · H800 producer 未注册

**真治法**:
```bash
# H800 端跑 register(等 backend 通就执行 · SSOT §0-ARCH 红线)
ssh h800 "source /root/miniconda3/etc/profile.d/conda.sh && conda activate base && python /root/autodl-tmp/genopt/genopt_factory/tools/register_h800_producer.py"
```

**不复发契约**:
- 不裸字符串 "harness" 跑数(SSOT §0-ARCH 红线)
- 真 producer 必须整数 agent_id
- backend 未起 = 等,不替

### 漏 8 · 50 variant 无 trajectory

**真治法**:
```bash
# 50 variant GPT-5.5 真跑 trajectory(走 batch_runner 并发)
ssh h800 "source /root/miniconda3/etc/profile.d/conda.sh && conda activate base && python /root/autodl-tmp/genopt/jobs_orlib_trajectory_v3.py --tasks-dir /root/autodl-tmp/genopt/genopt_factory/tasks --variants 50 --n 3"
```

**不复发契约**:
- 50 题 generate 是 core 真 ship(锚 #5 复用 5 grounded)
- trajectory 跑 = compass ALE 真验 + 真 ship 飞书 = 真闭环

## 🚫 不撞红线(7 件)

| 红线 | 触发后果 | 规避法 |
|---|---|---|
| 越界写其他 dialog | 写错位置 · 用户纠错 | `pwd && cat CLAUDE.md` 核身份每 session |
| 替 agent 决策 | anchor #1 红线 | 跨 dialog 真走 outbound + 等对方回 |
| 重复造轮 | anchor #5 红线 | 复用 produce_task / gapclosed_batch / verifier_qc / fetch_*.py / ale_eval / liveness |
| 裸字符串跑数 | SSOT §0-ARCH | Producer 必须走 register_h800_producer.py |
| 堆 dense markdown | drift hook fire | 段落 ≤ 8 行 · "真"字 zero · 表格独立段 |
| 不写 session memory | 6 周 dog熊复发 | session-end 必写 `compass/.claude/memory/session_*.md` |
| 不读 inbound | 76 条 stack | session-start 跑 `python ops/auto_surface_hook.py` |

## 🎯 下 session 第一刀(推荐 3 件 P0)

**P0 · 治根 + 真闭环**:
1. **baseline 数字修剩余 4 题** = cloud `update_bitable_record` × 4(命令已给上面)
2. **ALE 真跑 ahc005** = 真 reward 序列 + 落档 + 喂 RSI
3. **session memory 落 compass** = session-end 必写(避免漏 1 复发)

**P1 · 推进**:
4. 76 条 inbound 看完(已推 watermark · 但要看真内容)
5. 50 variant GPT-5.5 跑 trajectory
6. H800 producer 注册(等 backend 通)

**P2 · 不阻塞**:
7. HANDOFF 早版删
8. SSOT 三份合一
9. 3 个 core outbound revert(实际是 inbound 不是 outbound)

## 📂 真位置速查

| 资源 | 路径 |
|---|---|
| compass 项目 | `C:\Users\chunx\Projects\nautilus-compass\` |
| 真 memory 落档 | `compass/.claude/memory/session_20260704_compass_genopt_main_loop_handoff_continuation.md` |
| 真 handoff | `compass/HANDOFF_20260704_FINAL.md` |
| Goal 提示词(本档) | `compass/GOAL_PROMPT_20260704.md` |
| auto_surface_hook | `compass/ops/auto_surface_hook.py` |
| ALE eval | `compass/ale_bench/ale_eval.py` |
| liveness | `compass/ops/liveness_audit.py` |
| 真基线 SSOT(canonical) | `nautilus-core/LOOP_STATE_SSOT.md` |
| v5 flywheel v3 | `nautilus-v5/docs/plans/2026-07-03-genopt-flywheel-v3-design.md` |
| 6/17 rootcause | memory `reference_crossdialog_sync_rootcause_autosurface_hook_20260617.md` |
| 6/8 dogfood | memory `dogfood-crossdialog-coordination-via-compass-20260608.md` |
| v5 NEW genopt base | `KY9ZbC2Qqa6ZZXsKrWyc5VGRnXe/tblQAW4aNM99nva6` |
| cloud VM | `ssh cloud`(43.160.239.61:24860) |
| H800 | `ssh -p 34467 root@connect.westc.seetacloud.com` |
| 真 GPT-5.5 推理配置 | `https://v2.qixuw.com/v1` · `gpt-5.5` · chat.completions + `extra_body={"reasoning_effort":"low"}` |

## 💡 用户原话模式(给下 session 真理解)

- 用户常纠错 = 真错(本会话工作目录 6 次跑错)
- 用户原话"去查询查看"= 不靠 SSOT 推断 · 真查本地文件 / git log / commit
- 用户勾简答(1/2/3)= 不堆内容 · 直接做
- 用户原话"激活跨对话框协调机制"= 真触发 5 个 dialog 一起动 · 不只 compass
- 用户原话"狗熊掰玉米"= dog熊掰棒子 · 漏掉关键事 = 真盘点缺失
- 用户原话"准备 goal 提示词"= 真写可 paste 的启动入口
- 用户原话"准备交接"= 真写 handoff 文档落档
- 用户原话"先解阻塞"= 治根优先 · 不堆

## 🎯 下次 drift fire 自检

drift hook 阈值:
- paragraph max_per_paragraph = 8 行(超就 fire)
- "真"字 ≥ 3 次 / 段(fire)
- 段落 total > 22(fire)
- score < -0.07(fire · R1)

**规避法**:每个表独立段 · 不堆 · "真"字 zero · 关键回复独立短段

## 🚨 3 档 alert 契约(必检 · 7/4 真 sync 后更新)

### 超红(🚨 立刻 stop)
- 越界写非 compass 项目文件(每 session 必 pwd 核身份)
- 不写 .claude/memory/session_*.md 就 Stop
- drift score < -0.07(R1 立停 · 不靠自律)
- 误以为在 platform-soul / core / v5 框工作(本 dialog 真在 compass)
- 5 dialog 全 6 周没 .claude/memory/(只有 compass 7/4 第一次真写 · 复发风险高)

### 红(🔴 本次响应必检)
- 段落超 8 行
- "真"字 ≥ 3 / 段
- 越权改 SSOT 副本(只改 canonical core)
- 堆 dense markdown 表格
- 不读 NEW_SESSION_START.md 就答"接住主线"
- 凭 SSOT 推断 + 不查 git log / commit message / 真文件(用户多次纠错"去查询查看")
- 把 v5/core commit 误当 compass 真 ship(60 commits/14d 分布:compass 20 + v5 20 + core 20)
- ship 前不读 v5 真 trajectory v7 字段(锚 #5 复用)

### 黄(🟡 本 turn 提醒)
- 不读 auto_surface_hook 推 watermark
- 不读 GOAL_PROMPT
- 不核身份
- 不写 session memory 落档
- 不验 v5 真 trajectory v7 字段就 ship
- 不跑 `python ops/cross_dialog_audit.py 14`(5 dialog 真 sync 工具)
- 不知道 5 dialog 14d 真实状态 = v5 7/4 推 5 版 handoff · core 7/4 50 题真生成 · compass 7/4 自己推 ABC 三件

---
*Goal 提示词定稿:2026-07-04 01:40 PDT · 8 件漏掉真治法 · 下 session 一开就 paste 第一动作段 + P0 3 件*