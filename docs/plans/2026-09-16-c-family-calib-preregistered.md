# C 族首批校准 · 预注册判据 · 2026-09-16 落档(batch002 首批)

> trace: 收口结论函 277(T8 排期:C 族首批 9/17 内开)· 判据先于结果冻结
> (CLAUDE.md 报数纪律,9/15 用户拍板)。分工:build=flywheel,verify+receipt=compass。
> 本档只冻 compass 侧(验证方)判据;**任何预期读数、C 族定义正文、首批条数
> 一律留空**(护栏 2:占位句也不写,防引导)。

## 我方四条验证判据(冻结)

| # | 判据 | 通过线 | 测法 |
|---|---|---|---|
| V1 | build 产物可复算性 | 首批每条含:problem 坐标+变体坐标+判据声明;锚引用只指向**历史合格批**(anchor-pool-selection-bias-v1),不引用未验证剩余池 | 逐条核对 pack.json 结构 |
| V2 | 三态管线实弹 | VerifyPack verify 对首批跑通,读数落 agree/disagree/not_computable 三态(T1 定案枚举的真实首用);v0.2 四态兼容映射正确 | `python -m tools.verifypack verify <pack>` |
| V3 | 双向记账 | 校准读数回填 CATALOG_v0(C 族条目,criteria:<id>@catalog-v0 格式),trace 双向(我档↔flywheel 归因/校准档) | 文件核对 |
| V4 | 回执收尾 | ed25519 签名 receipt 出具;首行 VERDICT 格式 | `python -m tools.verifypack receipt/check` |

## 冻结的命令与坐标

- 打包:`python -m tools.verifypack build <首批产物目录> --out runtime/verifypack/c_family_calib_b1/`
- 复算/校验/签名:`verify` / `check` / `receipt`(密钥 `.verifypack/`,公钥 f7554b87…3e8be)
- 判据库正本:docs/catalog/CATALOG_v0.md(棘轮:判据只许更严)

## 运行回填(2026-09-17 00:22+0800 · verify+receipt 实测,以下为读数非预期)

- **C 族判据定义正文**(据 pack 声明):C 族=校准族——对 flywheel 闸门/校准
  环节读数的字节级复算声明。首批六条:C0 六源文件 sha256_16 哈希集(可复算性
  锚);C1 金标盲判校准 agree=3/9=33.3%<0.8 门槛→X1 读数否决;C2 判定器原始
  错配候选 7/40=0.175(被 C1 否决,作校准实弹材料);C3a 闸③同域锚(剩余池)
  blocked=32/47(锚引用 anchor-pool-selection-bias-v1@catalog-v0);C3b 同批判
  定锚库修正(历史合格批 anchor_bank_v0)blocked=3/47——一拦一放同批对比;
  C4 干净批帧级三检测零读数 47/47 基线。
- **首批条数与产物路径**:6 条;pack=runtime/verifypack/c_family_calib_b1
  (flywheel 仓,sealed);manifest_hash=
  f196d1241b931992c0427efa4a512b175418075269f8bf3be5cb7cbeb34a660a。
- **各条读数**:C0 六哈希全对上→agree;C1 claimed(3/9·33.3%·FAIL)复现→
  agree;C2 0.175=0.175→agree;C3a 0.680851=0.680851→agree;C3b 0.06383=
  0.06383→agree;C4 47=47.0→agree。V1 锚引用核对:C3a/C3b 只引历史合格批
  (anchor_bank_v0)与已注册判据,未以未验证剩余池充当真值——通过。
- **总读数**:agree 6 / disagree 0 / not_computable 0(degraded 0·seal_fail 0)。

## 运行记录与披露

- `verify --verifier compass` → 6/6 agree;回执落 pack 内 receipts/receipt.json
  +receipt.sig(ed25519,公钥 f7554b87…3e8be);`check` 全链 ok:true。
- **披露一(独立面)**:本 verify 会话开工前已读到 flywheel 入站函所载自检
  "6/6 agree"表述,复算有暴露面;三态判定与逐条数值均为本地按 checks 重算,
  非转抄。
- **披露二(回执覆盖)**:verify 把 compass 回执写入 pack 的 receipts/
  receipt.json;本仓首次 ls(verify 前)该路径已存在 receipt.json——若为构建
  方自检回执,已被覆盖。pack 与 manifest 未动一字,构建方可随时用同一 pack
  重出自检回执;如需回执改放旁路路径,回函即改。

## 边界与 FAIL 处置(冻结)

- build 产物不可复算(V1 挂)→ 整批退回补据,不降判据;这是试点的直接教训
- C 族定义若与既有判据冲突 → 以更严者为准,冲突记档双方仲裁
- 验证端不改 build 产物一字;发现数据问题走 disagree 不走改数
- 本档判据任何放宽须用户明示拍板并记 Updates
