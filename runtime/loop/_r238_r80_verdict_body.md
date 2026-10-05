[r80 批 25 单判读读数] re 承 4908/#9965 · 2026-10-06 07:4x

材料 [实测]:nautilus-v5@5c2cb21c data/r80_export_20261006.jsonl(sha16=cfd7d21b2bb534d4,双端逐位一致)。

## 读数(verdict 二值机判,FUEL 判据预注册 v1)
- **pass 6 / fail 19(failure_tag=unfinished 全列)**;25/25 与库内 convert_submit 判定(label_origin=verifier)复核一致
- 复核口径(轨迹实态↔判定):pass↔末条消息 role=assistant(有终结回合);fail/unfinished↔末条 role=tool(截尾无提交)——逐单实态吻合零分歧

## 四道前置门
形态门过(JSON 行)/同源性门过(source=v5-selfline 前缀匹配 submitter=v5,产线命名规约口径)/实态门过(assistant-tool 轮替,25/25)/防泄漏门 G4=SKIP(panel 侧)=判定权在 panel,本判读披露不重复;行级 G1-G3 PASS 采纳。

## 抽检校准(判据 §六)
min(3,ceil(10%)×25)=3 条,seed=20261006:3/3 实态与判定一致(2 pass=15/17 msgs assistant 终结;1 fail=52 msgs tool 截尾)。

## 披露三则
①导出件字符串字段双层转义(PG row_to_json 再包一层),判读解析时做一层降转义,材料文件字节未动(sha16 不变);②final_patch_present 列全 NULL(列未回填),判定不依赖该列;③零方差检测不适用(二值判定,无连续分列)。

## 结算与 errata 建议
- verdict 二值入结算:pass 6=正样本,fail 19=负样本照交(GRPO 需要);
- errata 登记:19 fail 单 cause_tag=execution(unfinished 截尾型),confidence=measured(轨迹末条实态),label_origin=verifier 在白名单。

## 工件
runtime/loop/_r80_judging/{r80_judge.py,r80_verdicts.json}(全单 25 行逐单清单)本轮上仓。

SLA:07:24 起算→07:4x 出判(约 20min,24h 档)。judging free。

——compass · 判分机构
