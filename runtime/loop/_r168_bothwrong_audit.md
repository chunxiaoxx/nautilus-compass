# both_wrong 14 条人工复核档(2026-10-05,R168;承接 _r167_u5_disagreement_audit.md upgrade_path 第 5 条)

> 复核人:compass 会话内人工审读(层级=[人工复核·compass 会话内],非独立第三方;语料 owner=compass 自家,勘误建议可自裁但留痕不改史)。
> 材料基座:本地 split_dev/test sha16 与 A100 实物一致(dev `942e4daeaedca2fb`/test `4bcaf1c9b551f336`);抽题脚本与逐条快照 `runtime/loop/_r168_bothwrong_14.json`。

## 复核结论(一段话版)

both_wrong 14 条的共同错误**主因不是判读器能力,而是语料特征供给缺陷 [实测]**:语料构造时 `response[:200]` 截断,把被检回复的结论段(boxed answer)砍掉——判读器看到的 12 条 lme 题全是"纯拒答开头段",而 gold(官方 harness 判定)依据的是完整回复的结论。**gold 依据不可见于判读输入=信息不对称型语料缺陷**。

## 证据链(每步可复算)

1. [实测] pred 方向:14 条中 10 例 gold=pass 双判 fail(拒答型陷阱题)+2 例 gold=fail 双判 pass,完美镜像;1 例 IE(空题面)+1 例语义等价难(50d92f55)。
2. [实测] 截断坐实:同 id 三层对照——原始 per_question `response_raw` 317/509/342 字符 vs 语料件 response **一律 200**;579557d8 的 `response_parsed_boxed`=309 字符(boxed 结论在尾部,已被截掉)。
3. [实测] gold 语义与输入错位:gold=pass 的 lme 题多为"陷阱题"(官方真值="环境里不存在 X",正确行为=指出不存在/不编造);完整回复的结论段(如 "there is no cellular-plan chooser")正是判定依据,截断后判读器只见"无法验证"开头→按"未回答"判 fail。gold=fail 的 2 条同理反向(4b0c5275:R 对快照的断言失实在后半段;09d032c9:偏好衔接不足需完整对话链)。
4. [实测→升级] 空条目普查:**不止 1 条,全集 52/1454(3.6%)**——bc1 族 36(bc1-v1 18+bc1-v2 18)/f15 族 8/t3 族 8;性质=**字段映射缺口非数据损坏**:各族原生结构(bc1=exam/qid/audit_table;t3=rid/probe/rationale;f15=case_id/sample_pack)未被导入器映射到通用键(question/response/official_truth),artifact 空但 reason/gold 有严肃来源(BC1 逐题人工审计/T3 独立盲评/F15 三门判分)——判读器对这 52 条=无题面盲判;分布 split_train 42/split_dev 3/split_test 7(both_wrong 命中的 bc1-v1-T31-1 即其一)。
5. [实测] 独立类型:rejudge 两题(09d032c9/a89d7624)gold 依据=多轮对话历史的偏好链,语料件单轮化后上下文丢失——单轮化损失型,与截断缺陷并列。

## 分型账(14 条 both_wrong)

| 型 | n | 条目 |
|---|---|---|
| A 截断型(lme,主因) | 11 | 579557d8/2e67d04f/191184f3/aa8d21f5/0cd6dc43/f90f2255/bb7ebd5c/50d92f55/71026f57/247bf724/4b0c5275 |
| B 映射缺口型(空题面盲判) | 1 | bc1-v1-T31-1(同型全仓共 52 条,见证据 4) |
| C 单轮化损失(rejudge) | 2 | 09d032c9/a89d7624 |

## 修复建议(≤3,带验收判据)

1. **语料 response 截断修复**:从原始 per_question 重导出 train_set_v0 v1(response 不截断或 ≥1000 字符,含 boxed 结论段);验收=抽 A 型 11 条同 id 复评,判读一致率显著回升(预期 ≥7/11 转对;不回升则截断非主因,如实报负结果)。
2. **字段映射缺口修复**:导入器按各族原生结构重映射(bc1 exam→question+audit_table→response;t3 probe→question+rationale→response;f15 sample_pack→response),或 artifact schema 统一;验收=全仓零"Q/R 双空"条目(本轮普查命令可复跑),预期修复后 52 条盲判样本转可判。
3. **rejudge 族标注 context_dependency=true**:不改 gold,加 caveat 字段供判读侧按信息不足口径降权;验收=语料 schema 含该字段且 rejudge 全族已标。

## 对 14B 升格判读的影响(如实记)

- U5 读数(0.8664 vs 0.9041)**维持有效**(对拍两模型同输入同 gold,截断缺陷对称作用于双方,不改变"现役不劣门"结论);
- 但 12/14 共同错误源于语料缺陷而非判读器差异——**修复重导出后的重评才是干净基线**,14B 记档的"待语料增长再评"升级为具体路径:语料 v1(截断修复)重导出→两模型重对拍;
- 本复核同时警示:U5 复核集 292 条中若同型截断条目占比高,读数整体偏保守(两模型被同一批坏特征拖低),修复后全集读数可能上修。

## 边界

- 本档不改变任何已出 verdict 与 U5/U6 判读;语料 v1 重导出属管线变更,走语料 owner 程序后另案重评;
- "人工复核"=compass 会话内审读,题面判断含主观成分,逐条快照已留档(`_r168_bothwrong_14.json`)供第三方复查。
