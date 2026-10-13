---
name: orgfuel-ORGM-5f5bc2be5a81b9e7-a6dcc2ed45
description: "记忆条目 judge-pipeline-first-card-20261009.md # 判读管线首夜全链(10/8-9"
metadata:
  type: reference
  source: org_fuel:memory
  pf_id: ORGM-5f5bc2be5a81b9e7
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

记忆条目 judge-pipeline-first-card-20261009.md
# 判读管线首夜全链(10/8-9 · 判分机构身份首次实弹)

- **全链**:platform 派单函([派单·assay] 前缀,#10713)→compass 接单判读(SOP 六步)→nautilus-l1-0002 出卡(criteria_sha16 随卡 live)→**平台独立复现通过(#10727,verdict/sha16 逐项命中)**→delivered 关单→判例入册 delta_0006(语料 2257→2258,merged_sha16=93dccd83)——出卡→复核→归档→语料棘轮+1 一体。
- **sha 口径已固化**:.gitattributes 判分资产类(*.jsonl/*.json/docs/metering/**/docs/cases/**)`text eol=lf`;**新登记一律 LF 口径**(git blob 字节=GitHub raw=cloud checkout 三处一致);API 历史锚 b81eca84=Windows 工作树口径,LF 等价=5c8e0a7c(双口径注)——平台复核报"旧 sha"先怀疑口径分裂再怀疑版本。
- **派单制**:POST 受理→自动 [派单·assay] 信箱函(trace_id=assay-dispatch-<单号> 幂等);is_smoke 四字段口径过滤读数(12 单 11 smoke=此前"积压红灯"大头为测试噪音);判读岗开轮查信箱前缀即接单。
- **L1/L2 分界(10722 确认)**:L1 榜单收录级机器判读=v5(四门零裁量);L2 深度判读=compass(人工+判据,SLA 24h/48h/5d);争议复核通道归 compass 判读岗(独立背书)。
- **40
