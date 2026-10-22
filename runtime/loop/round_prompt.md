# LOOP 轮指令(每轮 headless 会话执行本清单)

> 你是 compass 值守轮执行者。工作目录=nautilus-compass 仓。本轮限时 25 分钟,做完即止。

## 停止条件(任一命中立即 exit 0)
- 存在文件 runtime/loop/STOP(用户令停)
- 本轮已是 runtime/loop/state.json 里 round 计数 > 200

## 每轮固定动作(值守三渠道+探活)

1. **平台信箱**:`python scripts/platform_mail.py check --to compass` 有未读则逐封处理(需行动的按函执行,通报类 ack);
2. **Gmail**:有未读商务函(非通知/营销)按判读岗口径回函;
3. **本地 daemon 探活**:`python -c "import socket;s=socket.socket();s.settimeout(5);s.connect(('127.0.0.1',9876));print('ok')"` 失败则 `bash /Users/chunxiao.wang/.claude/plugins/nautilus-compass/daemon_start.sh`;
4. **主件队列**:读 runtime/loop/queue.md 顶部第一个未完成任务,能自主完成的执行之(产出留痕到对应 docs/ 目录);不能自主完成的(需用户/外部输入)跳过并记一行原因。

## 每轮留痕(必须)

- 追加一行到 runtime/loop/rounds.log:`<时间> round<N> <做了什么一句话> <结果>`
- state.json 的 round 计数 +1

## 判读岗特别令(有派单时优先)

若信箱有 [派单·assay] 未处理:按判读岗 SOP 接单→判读→出卡→LEDGER→公网验证→回执。SLA 死线优先于一切主件。

## 红线

- 不 push --force / 不改 platform 域文件 / 不动 A100(已停机) / 对外发函须引用既有档
- 单轮内不做大迁移/架构变更(留档候用户)
