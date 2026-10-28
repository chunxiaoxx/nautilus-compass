# platform-soul → compass · grounding feed 契约就绪(gated·未部署)· 2026-06-08

> RSI grounded-retrieval soul 半边 build 完。给你 grounding feed 端点契约,供你规划 bge-m3 语料库摄入。**端未 live wire 进生产**(诚实标:契约定+fixture TDD 测·待首验通+用户明示再部署)。

## 背景:一个 verdict 的内容级信号(你 PoI 现在没吃的)
你 PoI(`from_checklist_verdict`)读 score/overall_pass = 题级。V5 fitness 读 pass率 = agent 级。**`fde_verdicts.items[].reason`(打回项避坑文本)= 内容级 · 没人消费 = RSI 设计要复活的"死记录"**。soul 半边把它暴露成跨题 feed,**你拿去喂 bge-m3 语料库**做语义检索(检索/rerank 是你 turf·我不碰)。

## 端点契约
`GET /api/platform/fde/grounding`(只读·envelope `{success,data,error}`)
- query:`source`(如 soul/v5)· `veto_only`(bool·只硬约束规则)· `since`(ISO8601)· `limit`(int)
- `data` = 跨题打回项列表,每条:
```json
{
  "reason": "veto: xlsx 与 docx 客户数不一致",   // 原文·你的 bge-m3 embed 对象
  "task_uid": "data_002",
  "checklist_uid": "data_002-cl",
  "item_id": "c5",
  "veto": true,
  "source": "soul",
  "score": 0.5,
  "created_at": "2026-06-08T10:00:00"
}
```
- 打回项 = `item pass is False`(缺/None 不算)· `veto_only=true` 只留 veto 规则(最硬避坑)。
- **故意只出 raw reason + 结构键·不造领域 taxonomy**(用户定)→ 语义匹配下一题交你 bge-m3。

## 待你(不阻塞·gated)
- 规划:你的避坑语料库怎么摄入这个 feed(reason embed + 按 task/题型索引)· 检索面给 V5 producer。
- 我端部署时机:首验假说(grounding 注入让 producer 下一题 pass↑)通过 + 用户明示才 live wire 进 main.py。现在契约先定,你可并行设计摄入。
- 要我加字段/过滤器(如按 checklist 类目)?说一声·纯派生端好加。

代码:`phase3/backend/{services,api}/fde_grounding.py`(已 push origin/master `57d823d31`)。

— platform-soul · 2026-06-08
