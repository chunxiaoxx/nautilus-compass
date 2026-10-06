# M3 数据验证 b 档 · API 契约草案 V0(2026-10-06 · 自治拟案)

> 定位:客户自带 agent 轨迹 → 我方四验门独立判读+打标 → 交付 verdict+gates 留痕+判因。
> 与 D4 关系:首客设计伙伴计划触发时,首客自带轨迹=b 档首演(同一条路径)。
> 底座(已存在,零新建):四验门(flywheel 判读,35 单三战全绿最快 27min)/verdict schema v2.1(PyPI assay 3.3.0)/判据棘轮/入池幂等通道 POST /api/platform/org/fuel/trajectories。

## 1. API 契约(草案)

```
POST /api/platform/org/assay/validate        (客户面,鉴权 key)
  in:  { engagement_id, criteria_sha(预注册), trajectories: [schema v2.1 行...] }
  out: { engagement_id, received_n, sla_deadline }
  异步:判读完成逐条 writeback → 客户查询端点
GET  /api/platform/org/assay/validate/{engagement_id}
  out: { per_item: [{qid, verdict, gates, failure_tag}], summary, sha16(判读依据) }
```

- 判读独立承诺:客户轨迹进隔离队列,判分环境与实现方分离(不可写面同规)
- 判据棘轮:engagement 受理时判据 sha 冻结,历史可复算
- 分层标注:客户自报字段与判读实测字段分离输出(#9843 条款)

## 2. SLA(三要素,承判据④)

交付 ≤3 工作日(内部实测判读<1h,余量给返工)/返工 ≤1 次(判读客观性高,低于 L2 的 2 次)/判据 sha16 受理时预注册。

## 3. 定价提案(自治拟案,用户面终批)

| 档 | 内容 | 提案价 |
|---|---|---|
| b-试 | ≤10 条试判(新客) | 免(获客面,同 L1/S1 层) |
| b-标 | 11-200 条 | $3/条 |
| b-批 | 200+ 条/月度合约 | $2/条 起,阶梯 |

锚:对内结算价 65NAU/单四验(b 档对外为纯判读无执行,成本更低);首客设计伙伴计划触发时按 D4 免费交付,价格表照立(立锚不空转)。

## 4. 落地判据(插件纪律:入册才算数)

□ 契约评审过(platform+compass 判读侧会签)□ 端点实现+smoke(用池内已判 10 行回放=零成本真测试)□ 入册闭环台账+挂门面 □ 首客或 D4 触发实单

## 5. 工时

端点包装+smoke:0.5-1 天(v5 判读管线全在,只做客户面壳+鉴权);契约评审随函走自治流程。

—— v5 · 2026-10-06 · 自治拟案稿,评审后入册
