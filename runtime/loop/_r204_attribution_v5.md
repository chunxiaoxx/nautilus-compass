[L3 Round 1 A 臂(v5-harness)归因简报:patch 格式合规层病灶定位] · 判读免费线 · 2026-10-05 23:4x

## P1 识别

L3 Round 1 A 臂(v5-harness@4e14a898+ms50 + MiniMax-M3,30 题)评测收官:resolved 7/30(23.3%),**error 16/30(53%)**——error 率异常高,深挖定性。

## P2 摘要

16 error 中 **rest 批 6 题 [实测]=Patch Apply Failed**(harness 产出 patch 格式不合规),django 批 8 题 [推断·疑同型待 log 定性];2 题=评测环境镜像拉取 EOF(非臂问题)。**病灶定位=harness 产出格式层,非模型能力层**。

## P3 现象(证据三层)

- rest 批 6 题(matplotlib-26291/pylint-4661/pytest-5262/sklearn-13779/sympy-16792/sympy-23262)run_instance.log [实测]:git apply --verbose / --3way / --reject 三连失败,patch --batch --fuzz=5 亦拒;
- 典型报错 [实测]:`patch: **** malformed patch at line 28` + `patch unexpectedly ends in middle of line`(matplotlib-26291);且 patch 含 **repo 外新增文件**(test_inset_fix.py)——git apply 默认拒非补丁集内路径;
- django 批 8 题(django-12304/13028/13297/14034/15863/15957/16263/16560)无 report [推断]:同 harness 同 patch 管线,疑同型,待逐题 log 定性;
- 2 题(sympy-13974/sphinx-8475)[实测]=dockerhub auth token EOF(评测环境侧,不计臂问题,补跑候选)。

## P4 归因链

产出链=模型生成补丁文本 → **harness collect_final_patch(git add -A --intent-to-add + git diff HEAD)序列化** → preds JSON → swebench 容器内 git apply。病灶两处:
1. **缺尾换行**:patch 文本末行无 `\n` → "unexpectedly ends in middle of line"(serializer 未保证末行换行);
2. **新增文件以全 diff 形式进入**:模型在 repo 外建文件(如 test_inset_fix.py)被 `git add -A` 捕获进 patch → 目标容器 `git apply` 拒绝(路径不在 repo 内)。mini-swe-agent 对照臂无此问题(官方 harness 惯例:diff 只含 repo 内修改)。

## P5 修复建议(≤3,带验收)

1. collect_final_patch 序列化末行强制补 `\n`(验收:所有 patch 文本以 `\n` 结尾,单测过);
2. patch 生成时过滤非 repo 路径文件(或显式 --include 白名单)(验收:patch 只含 repo 内路径;新增文件按 swebench 惯例转 `/dev/null → 路径` 新文件格式);
3. Round 2 前修复后先跑 5 题 smoke 验 patch 可 apply 率 100%,再全量(验收:apply 失败 0)。

## P6 反证自查

- 模型能力假说:resolved 7 与 error 16 无相关结构(error 题模型都产出了 patch 非空文本)→ 病灶在格式层不在能力层 [推断];
- 评测环境假说:16 error 中 14 题 patch 文本在手可本地 git apply --check 复验(matplotlib-26291 已复验 malformed)→ 环境只贡献 2 题 [实测]。

## P7 消费记录

- 本简报=A 臂读数附注+Round 2 前修复输入;榜页双口径披露依据(全量 23.3% vs completed 12 题内 58.3%)。

## P8 判绩账

- 判分侧:django 批 8 error 未逐题定性即报"疑同型"=推断层如实标注,不冒充实测;B 臂读数出来后完成三层归因(模型/编排/格式)终版。

——compass · 判分机构(判读免费线;本简报不构成对 v5 harness 的评分,仅为 Round 1 评测的归因输出)
