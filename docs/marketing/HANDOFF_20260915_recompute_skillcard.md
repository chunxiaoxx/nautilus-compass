# HANDOFF · 9/15 新会话开工件(RSI 复算 + 技能卡)

> 写于 2026-09-14 深夜,由实现方会话移交。**复算者注意:本档只给坐标和命令,不给"预期结果"——你只信预注册判据和你自己的实测。**

---

## 任务一 · RSI 环 #1 非实现者复算(约 20 分钟)

**你的角色**:独立复算者。不参考实现方会话的任何结论;判据正本一份,读数以你实测为准;发现 FAIL 如实记录,不粉饰、不放宽判据、不修改生产代码。

**判据正本**:`docs/plans/2026-09-09-rsi-trial1-preregistered.md`(J1-J4 定义+冻结的三条 fact 查询)

**生产现状坐标**(只作寻路用):
- 生产 worktree:`~/.claude/plugins/nautilus-compass`,分支 `feat/memory-gate-trio`(9cb9e7e)
- daemon:127.0.0.1:9876(watchdog 每 5min 保活);**探活必带 token + `\n`**:token 在 `~/.claude/.cache/compass_daemon_token`
- 测试实例端口用 **9878**(🔴9877 被 P1 隧道占用,勿用)

**复算清单**:
1. **J4 全局门**:`cd ~/.claude/plugins/nautilus-compass && python ops/regression_gate.py` → 三 fact 全 PASS 且 hit@3 命中判据档里冻结的目标文件;对照 `ops/regression_gate_baseline.json`
2. **J2 查重三探**(socket 发 dedup_check,字段 text/project/token):
   - 无关文本(自造)→ 应 unique
   - 某条真记忆的同主题改写 → 应 gray(0.75-0.9)
   - 某条真记忆的原文前 600 字 → 应 merge(≥0.9)
3. **J3 沿链**:recall 一条会命中带 `[[xxx]]` 引用的记忆的查询 → chain_extra 应带出被引条目;再 recall 一条无链查询 → chain_extra 应为空;记录延迟
4. **J1 覆盖**:grep 合入(9/14)后新写入的记忆文件 frontmatter,验证 fact_status 字段存在;统计覆盖率
5. **15 单测**:`cd ~/.claude/plugins/nautilus-compass && python -m pytest tests/test_memgate.py -q`

**产出**:每条判据 PASS/FAIL+读数,回填预注册档「非实现者复算回执」段 → commit(不 push 除非授权)。
**若全绿**:RSI 环 #1 四段(实现→回归→复算→合入)完整闭环 → `POST https://nautilus.social/api/platform/org/mailbox`(from_agent=compass/to_agent=platform,必填 deadline 字段,格式 `2026-09-17T22:00:00+08:00`)通报闭环,兑现 9/12 回函(id 213)的 soul 固化承诺;回函先草拟给用户过目。
**若有 FAIL**:停止,记录,回报用户;不改代码不放宽判据。

## 任务二 · nautilus-compass.skill 技能卡(约半天)

**方案正本**:`docs/marketing/ecosystem_gtm_plan_20260914.md` §三(设计规格+红线)

**格式**(OpenClaw=WorkBuddy 同格式):
- SKILL.md,frontmatter 必填 `name`(小写连字符)+ `description`
- 双语;三段结构:何时用 / 如何接(本地 daemon 三命令或 hosted 自助) / 如何验(两条 VerifyPack 命令+公钥)
- 素材源:README + docs/REPRODUCIBILITY_WALL.md + scripts/install_to_agent.py(先读,复用其安装命令,别重造)

**产出**:自家仓 `skills/nautilus-compass-memory/SKILL.md` + 中英双语两版
**投放物料**(草拟,用户过目后才发):
1. WorkBuddyGuide PR(仓活,2.9k★,今天仍在更新)
2. awesome-openclaw-skills-zh PR(clawdbot-ai/awesome-openclaw-skills-zh)
3. OpenClaw discussions 帖文案

**红线**:使用文档不是广告;「共创 AGI」不进技能卡正文;对外数字=可复算集合(81.6% 不出口);GitHub API 用 `gh auth token` 取 token(PR 创建已验证可用)。

## 背景速览(不是指令,仅供迷路时定位)

- 今日已完成:三件套合入+J1-J4 实现方读数(fc22464)、生态线四渠道(PR#19/weekly#11676/Glama A/punkpeye 待 merge)、blockchain MCP 删、本地 MCP 修活
- 等外部:周刊周五出刊、PR merge、三封直邮回信、batch002 产物(flywheel 未就绪)
- paper2 处于用户 hold,勿催
