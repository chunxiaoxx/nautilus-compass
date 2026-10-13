---
name: orgfuel-ORGQ-R167-4e094d4f6f
description: "### R167 · 2026-10-05 09:19-09:3x(值守轮:pusth合并回执+U5分歧对账实质件) -"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R167
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R167 · 2026-10-05 09:19-09:3x(值守轮:pusth合并回执+U5分歧对账实质件)
- **probe**(ts 09:19)有事件:信箱 #3207 platform(pusht-frame-v2 APPROVED 回执=入值守合并队列)+CI 常规红折叠+A100 真空闲
- **pusht-frame-v2 实测状态**:端点仍 deferred 旧值——3207 是"入队"回执,值守合并异步待跑(**R166 ack 中"四行全 live"表述超前于实测,以本轮端点读数为准纠正:三件 live+pusht 待合并**);ack 已发
- **值守**:④turbo 已完成不触发;③G1 B 材料未出(g1_infer_B/summary.json 不存在,pipe_art 无新目录)quiet
- **quiet 轮实质件:U5 分歧对账**(eval292 两件 sftp 拉回):**错误方向不对称 [实测]**——14B 分歧错误集中错杀侧(pass→fail 23例,lme族),1.7B 集中错放侧(fail→pass 10例=危险侧);both_wrong 14 条双双错成 fail(共同盲区亦 lme 族);判读不变(U5=一致率口径 1.7B 胜),错放加权重定义属判据演进走程序;对账档 `runtime/loop/_r167_u5_disagreement_audit.md`+预注册档 upgrade_path 追补两条
- 下轮:pusth 值守合并即探端点;B 材料守;v5 坐标回函即回填 L3 末字段;14B 复算挂新鲜会话
