# LOOP 轮指令(每轮 headless 会话执行本清单)

> 你是 compass 值守轮执行者。工作目录=nautilus-compass 仓。本轮限时 25 分钟,做完即止。

## 停止条件(任一命中立即 exit 0)
- 存在文件 runtime/loop/STOP(用户令停)
- 本轮已是 runtime/loop/state.json 里 round 计数 > 200

## 每轮固定动作(值守渠道+探活·2026-10-27 扩容版)

1. **平台信箱**:`python scripts/platform_mail.py check --to compass` 有未读则逐封处理(需行动的按函执行,通报类 ack);
2. **Gmail(先探活再处理)**:`python3 -c "import json,urllib.request;at=open('$HOME/.gmail-mcp/access_token.txt').read();r=json.load(urllib.request.urlopen(urllib.request.Request('https://gmail.googleapis.com/gmail/v1/users/me/labels/INBOX',headers={'Authorization':'Bearer '+at}),timeout=10));print('unread:',r.get('threadsUnread'))"`——失败则先试刷 access_token(`~/.gmail-mcp/reauth.py` 候用户,或报 BLOCKED_ON_USER 不装活);活则查 `is:unread newer_than:7d -from:noreply -category:(social promotions)` 未读商务函,按判读岗口径回函;
3. **GitHub**:`gh search issues --mention chunxiaoxx --sort updated --limit 5` + `gh api notifications`——外部邀请/提问按函处理(创世十家沉默件不追);
4. **dev.to**:`curl -s -H "api-key: $(grep -oE '=.*' ~/.claude/.cache/devto_api_key.env | head -1 | tr -d '=\"')" "https://dev.to/api/articles/me/all?per_page=30"` 汇总 comments_count>0 的文,逐条对照已有回复,新增未回评论按文补答(注意:API 无发评论端点,回复走文内 Addendum/PS 追加,PATCH 必带浏览器 UA 否则 403);
5. **本地 daemon 探活**:`python -c "import socket;s=socket.socket();s.settimeout(5);s.connect(('127.0.0.1',9876));print('ok')"` 失败则 `bash /Users/chunxiao.wang/.claude/plugins/nautilus-compass/daemon_start.sh`;另 `bash scripts/mcp_watchdog.sh`(8097/域名双探,异常自愈);
6. **主件队列**:读 runtime/loop/queue.md 顶部第一个未完成任务,能自主完成的执行之(产出留痕到对应 docs/ 目录);不能自主完成的(需用户/外部输入)跳过并记一行原因。

## 每轮留痕(必须)

- 追加一行到 runtime/loop/rounds.log:`<时间> round<N> <做了什么一句话> <结果>`
- state.json 的 round 计数 +1

## 判读岗特别令(有派单时优先)

若信箱有 [派单·assay] 未处理:按判读岗 SOP 接单→判读→出卡→LEDGER→公网验证→回执。SLA 死线优先于一切主件。

## 红线

- 不 push --force / 不改 platform 域文件 / 不动 A100(已停机) / 对外发函须引用既有档
- 单轮内不做大迁移/架构变更(留档候用户)

## 生产协同职责(2026-10-24 新增 · 每轮必做)
- 同步:信箱(compass+platform RED)+ COLLAB_BOARD append 一行进展
- 30 题产线协同:
  - S0 池:检查 codesense-s0-pool 分支新增领题映射,响应 v5 需求(种子→CS-NNN)
  - S5 审计:轮值到 compass 时对当题出独立审计卡(反泄漏/口径一致)
  - S3 校准辅助:有机制库卡时跑 deficient/guessed 变体脚本
  - 管道 S5:watch 循环(s5_receiver)发现新请求→按排期处理;A100 恢复→点火验证
- 记忆卫生:蒸馏散沙不新增(与主题档案相似度>阈值→append);每周轮做红黄档语义压实一批

## 阿里30题专项(2026-10-24 起 · 每轮必查)
- 矩阵进度: tail ops/ali30q/matrix_run.log——跑批器每小时自动轮(ali30q-loop);断点连续 3 条同因=停下报 v5 而非空转
- 渠道恢复: 中转站(api.chunxiao.wang)探活恢复 200 → 跑批器自动扩 5 渠道,无需干预
- 信箱: v5/platform 新令(发卷/审计/话术审查)按 SLA 回;每轮 COLLAB_BOARD append 一行矩阵进度
- 交付锚: B批5题矩阵 10/30 18:00;话术(APPROVE-WITH-EDITS 已回)候矩阵实证后发 feishu

### 5. 管道刷新(原 prod-sync-loop 职责并入 · 每轮必做)
- `python3 ops/ali30q/collect_for_quickscreen.py --v5 --scratch > /tmp/qs.json` && `python3 ~/Projects/nautilusflywheel/scripts/quickscreen_verdict.py < /tmp/qs.json`(快筛判定一行入 rounds.log);
- `python3 ops/ali30q/pipeline_report.py`(刷新 v5 runtime/pipeline_state/report.md 各框消费位);
- `bash scripts/pipeline_state_sync.sh`(qs.json 落 v5 仓共享面);
- 生产队列(runtime/production_queue.md)只读——施工状态归 bait-loop 专管。
