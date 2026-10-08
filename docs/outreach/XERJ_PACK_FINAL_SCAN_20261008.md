# XERJ 包逐字终扫报告(R364 · 2026-10-08)

> 承 R343"发 PR 前最后一步=逐字终扫一遍"。工具 `tools/xerj_pack_scan.py`(幂等可复跑,判据内嵌)。

## 判据(先声明后执行,单次全量,零豁免;判据零放宽)

- **FAIL** = 任何原始凭据/PII 残留(已知字面量 `iefe4Eey`/`Coh9ech3`·`sk/hf/ghp/gho/ghs/xoxb/AKID_` token·gmail/outlook/qq/163 邮箱·裸 IPv4·password 赋值)或 schema 破损(json 解析失败/缺 10 必备键/id 非 `nst-` 前缀或重复/`failed_attempts` 空/`sanitized` 非 True/verdict 出 {pass,fail,partial} 枚举)。
- **WARN** = 内部路径(`.claude/`/`.cache/`/`/root/`/`/home/`)或内部 env 名(`a100_env`/`cloud_permanent`/`.ark_env`)——列单供人判,不计 FAIL。
- **检测力门**:`--selftest` 5 合成样例必须全命中,否则全量结果不可信。

## 结果[实测]

- selftest:**PASS 5/5**(检测力自证,先于全量跑)。
- FINAL-SCAN:**CLEAN(fails=0 · warns=17)**。
- 记录:70 条,schema 全过;topics=eval-judging 46 / infra-diagnosis 13 / ledger-audit 6 / ops-misc 5(与 R319 首跑一致)。
- WARN 17 条全为 `/root/` 路径提及,分布 3 条记录:
  - nst-r184(`/root/vdd4` swebench venv+docker data-root,×8)
  - nst-r118(`/root/venv` GPU 判分 python,×4)
  - nst-r303(`/root/vdd4/embed_server.py`,×5)
  - **处置=保留**:通用 Linux 路径,无凭据/无 PII/无主机名/无用户身份;10% 人工复核(7/7,seed 1010)已覆盖同类文本并 PASS;且属"诊断 verbatim"设计价值的一部分。
- 抽样目检:r238/r91/r316 三条头尾字段完整,失败锚与 final_fix 在位。

## 三件套 sha256(终态锚)

| 文件 | sha256 |
|---|---|
| agent-session-trajectories.jsonl | ea7fab54076f27e5161a7bdb40ae5d6dcfae2d033a9a7a08310fcca3685653e1 |
| README.md | 328247c393aa92cb029a22c789be8bf3d281b0f025009ed0c506d05c4e84d44c |
| recipe.toml | 572b4205bbb2f56e0c6428636449d0aa140133aaccde7d200dcb1bf5b2fd355b |

## gitignore 静默挡修复(R363 同型第二例)

- `.gitignore:7` 的 `*.jsonl` 挡住 `runtime/xerj_pack/pr_ready/agent-session-trajectories.jsonl`(README/recipe/sessions.jsonl 均已跟踪,唯 PR 提交源副本漏网)→ `git add -f` 补入仓。
- PR 提交源自此 GitHub 可寻址,审计链闭合。

## 效力条款

- 三件 sha 不变 → 本报告有效至 PR 日;PR 日复跑同脚本(幂等)或验 sha 等价即可。
- 任何材料变更(新增记录/README/recipe 改动)→ 重扫+复核重新走判据,旧报告作废。
- PR 形态不变:recipe.toml+README 提 corpus-hub 分支,built pack 不入 PR(maintainer 构建+签名,10536 确认口径);发窗=10/12 开业后,发后回函链接(10536 ack 承诺)。

—— compass · XERJ-PACK-FINAL-SCAN · R364

## 变更记录(R373 · 2026-10-08 深夜 · PR 预检后材料修订)

- 触发:XERJ hub CONTRIBUTING.md 对标预检——recipe.toml 按 TEMPLATE schema 重写(format=1/sources slug+kind=git 指公开仓+envelope/identity/merge/emit 全段;原 [corpus]/path 骨架不符);README Identity 段补 identity-resolution 数(70→70)。
- 重扫[实测]:**CLEAN(fails=0 · warns=18)**——jsonl 不变(ea7fab54…),README 新锚 a1081ad1cdf6638c343585304d2ac76a22a195c10c7310836c9036558a84b61e,recipe 新锚 344fef9a89559b2c45bad8eaca8b21c11bd5c689f7f49822b01f7884d8da6f12;warns +1=recipe 注释中"/root/"字样(自指,无害)。
- 上表 sha256 即行作废,以本记录三锚为准(效力条款执行:变更→重扫→新锚)。
- PR 提交件定案=recipe.toml+README 两件;jsonl 为我方 repo 侧 build 源(sources.url+glob 寻址);草稿=runtime/loop/_xerj_pr_draft.md。
