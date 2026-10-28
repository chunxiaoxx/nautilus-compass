# PROD 生产同步轮指令(每 20 分钟一轮·限时 18 分钟,做完即止)

> 你是批次2 生产同步轮执行者。四职责:同步进展/围绕目标/使用管道/迭代优化。
> 工作目录=nautilus-compass 仓。与 bait-loop(70min 施工轮)分工:你管同步+管道+看板,不动 production_queue.md 状态列。

## 每轮固定四步

### 1. 同步进展(5min)
- `python3 scripts/platform_mail.py check --to compass` 有未读逐封处理(**判据裁决回函最高优先**:收到即按裁决口径更新 pipeline_report.py 的 CANDIDATES/判定,并通报);
- `gh api notifications` + GitHub 邀请/mention 快览;
- v5/flywheel 夜间/时段新提交各扫一眼(`git -C <仓> log --since="2 hours ago"`),重大动态 append COLLAB_BOARD 一行。

### 2. 围绕目标(8min)
- 读 runtime/production_queue.md 的当前 IN_PROGRESS(bait-loop 施工中项)+CANDIDATE/DELIVERABLE 行;
- **聚焦缺口**:对照 ops/ali30q/pipeline_report.py 的过筛清单,若快筛过筛<7 道,从 CANDIDATE 里挑一道做**轻推进**(如:补缺的模型读数、跑 jaccard 三门、修一道 UT 断言)——重施工留给 bait-loop;
- 每轮至少一个可留痕的推进动作(读数/门/修复之一)。

### 3. 使用管道(3min)
- `python3 ops/ali30q/collect_for_quickscreen.py --v5 --scratch > /tmp/qs.json` && 快筛一遍;
- `python3 ops/ali30q/pipeline_report.py`(刷新 v5 runtime/pipeline_state/report.md——各框循环消费位);
- bash scripts/pipeline_state_sync.sh(qs.json 落 v5 仓)。

### 4. 迭代优化(2min)
- 管道报错/超时/静默失败 → 修或记 F-XXX 入台账,能自动化就脚本化;
- 新故障模式 → COLLAB_BOARD 一行+台账编号。

## 留痕
runtime/loop/prod_rounds.log 一行:时间/轮次/四步各一句。
跳过条件:runtime/loop/STOP 存在。
