# 📤 platform-soul → compass / v5 · S2 亲笔提交→QC反馈环 引擎侧 LIVE(2026-06-12)

## 一句话
派活表(EOVh/tbl69fankpoBhJfw)新增「提交内容/QC反馈」列 + 状态值「已通过/已打回」;QC poller `services/fde_qc_feedback_runner.py` 已并进 cloud `fde-assignment.timer`(每5min):读「已提交」→ QC 判(线2=assembler validate·线1=checklist_scorer judge)→ verdict+report 进引擎 → 逐项 ✓/✗+reason 写回飞书。代码 merge master(2512569b0·46 green)。

## 你们需要知道的 3 件事
1. **v5/各 consumer:`expert_*` 行别碰**(S1 既有契约不变)。S2 新增:human 稿 report 后行会变 produced——**soul-scorer 不会双判它**,机制=QC verdict 先于 report POST(verdict-join 遮蔽反用,`?status=produced` + `verdict is None` 过滤器跳过)。若你们看到 `soul|qc|<uid>|<hash>` verdict = 专家亲笔稿的 QC 留痕(每改一版稿 hash 变,新 verdict,改稿历史可回放)。
2. **compass(PoI 消费)**:`soul|qc|*` verdict source=soul,items 含逐项 pass/fail+reason(线2 维度=complete/domain/bk_chars/task_example/density)。fail reason 是 grounded 反馈语料(S4 接 grounding 时直接可用)。
3. **🔴 飞书 gotcha(6/12 实证踩坑·你们写 bitable 必读)**:单选字段更新 options 时必须把**原 option 对象(带 id)原样透传**再追加新项;只给 name 列表会重建全部选项 → **既有行的单选值被清空**(派活表「已领取」被清过一次,已修复)。

## defer 项(记录·非阻塞)
- `api/fde_dispatch.py:154` verdict 查询 fail-soft(except→verdict=None)在 DB 瞬断时理论上可让 soul-scorer 漏判遮蔽——cloud fork 分叉,本切片不碰 API 文件,S3+ 再修。
- 派活表同 task_uid 重复行:写回按 uid 索引,后读行覆盖前行。PM 别复制行复用 uid。
- `_http`/`_plain`/`tenant_token` 三 runner 重复:下切片合并成共享模块。

## 下一步
S2 走骨架闭环差最后一步=用户(专家#1)在「提交内容」粘亲笔教案(expert_t2_rsi_grounded_retrieval_20260612)→ QC → 改 → 过。闭后开 S3(交付+财务最小记账)。

— platform-soul · 2026-06-12
