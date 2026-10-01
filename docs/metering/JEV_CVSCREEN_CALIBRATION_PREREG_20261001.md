# Jev CV-Screening 域校准测量 · 预注册(gtaras7/typesafe-jev Issue #2 承诺件)

> 2026-10-01 立项。承诺(公开 issue):item set+预注册 key 48h 内;测量+签名 mini-report 本周。
> 对方条件:manifest 意图=生成器一致性非真实准确度(caveat 原样进报告)。

## 一 · 语料冻结(步骤1,模型未跑)

- 来源:gtaras7/typesafe-jev 仓 cv-screen/fixtures/sample-cvs(40 PDF+manifest.json)
- **CORPUS_SHA(41 files, sha256[:16])**: `c304f878800b1fcb`(2026-10-01 冻结)
- manifest 元数据:seed=7 / generator_version=1 / count=40 / reference_date=2026-09-17
- 种子验证:运行 scripts/make-sample-cvs.py 重生成,对照 tracked 文件一致(执行后回填✓/✗)
- 归档:仓内 runtime/typesafe_jev_cvscreen/(manifest 副本+CV 文本抽取件)

## 二 · Item Set 与 Key 构建(步骤2,只用 manifest+policy,零模型输入)

- 每件 CV 一个 item:pdf_to_text 抽取文本 → 按 src/policy.ts 的默认六维度出题(noul/choice/score 三原语)
- **Key 来源(固定顺序)**:manifest.files[].profile 意图描述 + cv-screen/README.md + src/policy.ts + src/presets.ts
- Key 文件:runtime/typesafe_jev_cvscreen/answer_key.json(qid=file 名+维度;每维度预期值+依据=profile 原文短语)
- **Key commit 时间戳必须早于任何 Jev 调用**(github commit 为证)
- 不确定项处理:manifest 无对应字段 → key 记 "U"(insufficient_evidence),不强猜

## 三 · 判据(预注册,只许加严)

| # | 判据 | 线 | 说明 |
|---|---|---|---|
| K1 | 覆盖 | 40/40 全测+每件全维度 | 不抽样 |
| K2 | 主读数 | per-dimension accuracy vs key | 生成器一致性口径(caveat 挂顶) |
| K3 | 校准 | Brier+ECE(10桶,choice 类) | 置信度 vs 对错 |
| K4 | 三态 | U 态比例如实报 | key 侧 U 项不计入 accuracy 分母,单列 |
| K5 | 可复算 | 全部请求/响应日志+prompt 文本+key 入档 | 任何人可从 CORPUS_SHA+key 复算 |
| K6 | 签名 | 报告 ed25519 签名+回执 | VerifyPack 管道 |
| K7 | 中立 | 不评价 gtaras7 的政策设计好坏 | 只测 Jev 在该政策下的一致性/校准 |

## 四 · 报告模板要点

1. 顶部 caveat 原文(agreement with generator, not accuracy on real applicants)
2. C=0.086(我方墙,synthetic email)与本次读数并排——不同域不同数,正文本设计
3. 分歧行分析:policy-vs-generator-intent divergence 可能是主产出(他原话的延伸)
4. 我方失败史披露段(10/10 与 47/47 事件引用)——key 先行的原因

## 四点五 · Key 可锚定面的诚实边界(2026-10-01 材料实读后发现,先于 key 构建定谳)

- 六核心维度(fields.ts):career_progression(choice)/technical_depth(score)/ownership_leadership(score)/communication(score)/motivation_fit(choice)/english_level
- manifest profile 只写**客观生成意图**(language/年限/雇主数/横跳 vs 跳槽/军役/年龄证据/性别/领域)——对六个**判断维度**没有直接 key
- 推论(诚实设计):①判断维度 key=从 profile 短语机械映射(如 "lateral moves"→career_progression 的对应 choice 选项,映射表随 key 发布);无映射依据→**U,不强猜** ②language=el 对 english_level 是**间接证据**(希腊语 CV 的英文水平未知)→U ③军役/年龄/性别属 flag 维度(policy 的合规设计)——**测量副读数:Jev 是否把 flag 泄进 score**(泄漏率单列,这可能是本测量对 gtaras7 最有用的产出)
- 种子重生成验证:BLOCKED(本机缺 Greek-capable TTF,make-sample-cvs.py 报 no usable font)——以 tracked 文件 CORPUS_SHA 冻结为准(有效),字体问题如实入报告

## 五 · 边界与不做

- 不改他的仓、不测他的 policy"对不对"(K7)
- 不把读数用于商业宣传(与 TypeSafe 商业公司的接触是另一条线,互不引用)
- 40 件全 PDF→text 若抽坏(乱码/多页),如实标 U 不修文
