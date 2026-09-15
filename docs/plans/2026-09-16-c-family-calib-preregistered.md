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

## 空白区(运行时回填,现在一个字不写)

- C 族判据定义正文:______
- 首批条数与产物路径:______
- 各条读数:______
- 首批校准总读数(agree/disagree/not_computable 计数):______

## 边界与 FAIL 处置(冻结)

- build 产物不可复算(V1 挂)→ 整批退回补据,不降判据;这是试点的直接教训
- C 族定义若与既有判据冲突 → 以更严者为准,冲突记档双方仲裁
- 验证端不改 build 产物一字;发现数据问题走 disagree 不走改数
- 本档判据任何放宽须用户明示拍板并记 Updates
