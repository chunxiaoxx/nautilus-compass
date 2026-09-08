# VerifyPack v0.2 Spec 草案(2026-09-08 夜 · D2)

> 输入:9/7 立项(2026-09-07-verifypack-v02.md)+ V5 两函(182 回函/183 两极仲裁)+ 9/8 三洞立场。
> 分工(V5 182 拍):**compass 出协议与回执标准**;V5 出产品层(断点体检)+训练数据选择判据;共用本协议。
> 诚实分级:MVP 期只说「可复核」(tamper-evident 版本哈希);ed25519 签名落地后才有资格说「不可伪造」。

## 1. 四命令(CLI)

| 命令 | 干什么 | 产出 |
|---|---|---|
| `vp build <dataset>` | 打包数据集+口径+环境指纹 | verifypack 归档(data+manifest) |
| `vp verify <pack> [--l0-only]` | 两级验证(§2) | PASS/FAIL/PARTIAL + 分层定位(断在哪层) |
| `vp receipt <pack>` | 出回执(§3) | receipt JSON |
| `vp check <receipt>` | 验回执 | 哈希链校验 + 复现命令重跑 + 降采样抽查 |

## 2. verify 两级化(183 采纳)

- **L0 嵌入分诊(几何仲裁)**:BGE 在 daemon 现成(零新增)。判据向量化索引;高置信区直接引用缓存 receipt(边界带收敛后目标 90%+ 免终审);lossy-tolerant 用途=路由/去重/预筛。
- **L1 grounding 终审**:真值度量(判官/规则),回填 L0 校准。Δ 信号当预测器不当裁决者(paper2 立场即此架构原型)。
- **安全域红线**:L0 只能放行到「引用缓存」,不能单独产生 PASS——嵌入盲区定理(bevco.com vs bevco.example.com:嵌入距离≈0、真值相反;嵌入比判官压缩更狠、盲区更宽)。「维度换算力」的座位在分诊台,不在审判席。

## 3. receipt schema(JSON)

```json
{
  "metric": "...",
  "baseline": "...",
  "protocol": {"judge_model": "...", "scoring_protocol_version": "..."},
  "version_hash": "...",
  "repro_cmd": "...",
  "embedding_vector": null,
  "judgment_ref": null
}
```

- 五要素(度量/基线/口径/哈希/复现命令,与 E1/E2 收割器雏形同格式,一次对表三方共用)
- `embedding_vector`:L0 索引用(183)
- `judgment_ref`:判据库条目指针——**回执=指针非快照**,引用可解析到活条目
- 口径必含判官型号+判分协议版本(判分卫生学立场:判官侧静默失效=本领域最大混淆源)

## 4. verified 五字段(训练数据选择层,182)

`{task_type, break_layer, strong_pass, weak_fail, provenance_hash}`

- verified=**分层器不止过滤器**:断点哪层补哪层
- 四轮蒸馏教训内化:verified≠可注入——标签携带 task_type+计数纪律(80/族旋钮)
- 现成件:a_class_filter 双臂判据(强模型解出×弱模型难倒);E3 燃料门(日频已挂)自动化该链

## 5. 判据库条目 frontmatter(9/8 回函 180 已定)

`judgment_family / 口径 / result_sign(必填)/ 版本哈希 / 复现命令`;负结果同等入库;**禁止原地手改,改=新版本条目**(否则回执可伪造)。与 #47 判据库同源,一次对齐不建两套。

## 6. 里程碑与依赖

- 9/9-10:#46 batch001 效用报告复算——手工回执先行,格式对齐 §3(首个真用例)
- 9 月内:CLI 四命令 v0.2;DoD=batch001 端到端新协议跑通(build→verify→receipt→check)
- R6 约束解码判据(V5 今晨出数)=第一条实测输入;主脑体检(4 层 9 探针)=验 agent 的姊妹用例,receipt 共用
- compass 现成件盘点:BGE(daemon)=L0;审计「合并无触发器」→嵌入聚类候选对+LLM 只裁合并;drift 锚点匹配可加 L0 预筛
- paper2 续作(盲区定理嵌入版,183 提议):2600 调用语料测几何分类器,一次嵌入+一个分类器,可与 CL1/X1 并批——**待用户批**

## 7. 开放问题(合成总设计时与 V5 对表)

1. L0 边界带宽度定标(主脑体检 72 交互的 claim-verify gap 几何分布=第二组标定数据,V5 白天出)
2. check 降采样率与漂移阈值(健康流形假设的验证方式)
3. ed25519 签名密钥治理(谁持钥=组织问题)
