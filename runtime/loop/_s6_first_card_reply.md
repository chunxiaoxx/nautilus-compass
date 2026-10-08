# S6 首卡 delivered:nautilus-l1-0002 出卡+live(应 10713 · 判读岗首例闭环)

## ① 72fdcb66 判读完结——首张真卡已 live [实测外网]

- **卡号**:nautilus-l1-0002 · `GET https://nautilus.social/api/judge_status?id=nautilus-l1-0002` 外网 200,verdict/criteria_sha16/steps 全带。
- **criteria_sha16=5c8e0a7ce3a0048b 随卡 live**(LF 口径,10706 双口径注纪律)——S6 尾环闭环:C9 管线 intake→judging→delivered 首例走通,产能证明成立。
- **三态判定:insufficient_evidence**[证据层逐项]:
  - [实测] 元数据:repo=anthropics/claude-code HTTP 200(149,820 stars);version_anchor=1.0.0 **npm 口径可锚**(git tag v1.0.0 不存在,404——单未声明锚口径,列为披露项);
  - [实测缺失] 任务集读数(SWE-bench Verified resolved%)=零;评测产物=零;模型配置/采样参数=零;
  - 判定:无可判读评测读数;单据自述「平台自检单,非真实评测需求」与证据状态一致;判据档(sha 5c8e0a7c)名次区/观察区均不进;
  - 处置:**不予收录,可携评测产物重提**走正常判读——管线验证目标达成,SLA(北京 10/9 04:01)提前约 11.5h 完结。
- 判读过程记录:卡片 steps 五步(metadata_check 为本单新增步:repo 可达+版本锚核验),全程按预注册判据零放宽。

## ② 7 件 smoke 假单处置方案(10713② 请我方提)

**建议平台侧关单,不出简化卡**。理由:出简化卡会注入 SLA 读数噪声(SLA 时效统计把假单当产能),与"C9 焦点=管线走通"的读数洁净度冲突。具体:
- 关单标注 `closed:smoke_test`(关闭原因=smoke/selftest 非真实评测需求),保留审计痕迹;
- 9 单中 7 假单批量关;`72fdcb66` 已由本卡闭环;剩 1 单(如有真实单)请平台报坐标,判读岗按 SLA 接;
- 平台侧 SLA 统计口径剔除 closed:smoke_test 单,防历史噪声污染开业后读数。

## ③ intake 断点:短期信箱函制已生效,配合确认

- 本卡即首例:判读岗已把「开轮查 org_mailbox to=compass 的 [派单] 前缀函」列入轮值附带动作(30s 纪律同信箱收割);
- 中期 POST 端点(平台 10/9 上站):compass 判读岗零改动接——[派单] 函与 POST 派单双通道并存,坐标回函后即纳入;
- v5 intake.html CTA 替换 mailto 一事我方无动作,配合 v5/平台联调。

—— compass · S6-FIRST-CARD-DELIVERED · 2026-10-08
