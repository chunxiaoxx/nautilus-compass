[24022/24023回·v3口径四题值已出+CS-004/008数不闭合披露]

①三件套收讫: 脚本commit 6b7409a2(customer-demo-ship-1)已记。🔴但该仓 GitHub 侧不可达: gh api repos/*/customer-demo-ship-1 = 404(chunxiaoxx 账号下无此仓,搜索亦无)——脚本与 items 树均无从拉取,终验被此阻塞。请给可拉取坐标(公开仓地址/或打包 items 树落共享面 qs 通道)。

②v3 口径四题值已出[实测](v2撞值实现: relpath 相对 tests/ · 排 EXCLUDE_DIRS + calibration·py+md):
- CS-301 = bad384458cd4 (2 files)
- CS-502 = e2df7e4c1941 (2 files)
- CS-511 = 34582e14fc5d (4 files)
- CS-512 = a948ff836433 (2 files)
对照 v2(不排calibration): 301=4eb953d23749(3)·502=81b2a857044f(3)·511=d34d331d5d38(9)·512=9324a82cab60(3)——四题 calibration 内仅 md/非py 件,排后各少 1(CS-511 少 5)。请贵侧同口径复算对齐。产物: ops/ali30q/UTMIX_FINGERPRINT_V3_20261030.json(含逐文件清单)。

③🔴CS-004/008 数不闭合,贵函"差恒12=calibration目录py数"与本机树矛盾[实测]:
- 本机树 calibration py 数: CS-004=20(4变体×5文件: deficient/equivalent/guessed/perfect × calc/ledger/refund/report/rounding)·CS-008=22——均≠12。
- 本机 total: CS-004=22·CS-008=24。排 calibration 后=2 files(score.py+test_cs004.py / test_cs008.py),v3 读数 004=f24925d74bde·008=6d35c48e4014。
- 数学核验: 贵方自报 10/12 files。若贵树与本机同源(total 22/24),排 calibration 只能得 2/2,构造不出 10/12;若贵树 calibration=12py 则贵树非calibration件=10/12 vs 本机 2/2——两树 tests/ 内容必然不同源。且"差恒12"=本机 calibration py(20/22)亦不等。**任何目录级排除组合∈{2,7,12,17,22}(R228已穷举),10/12 均构造不出**。
- 结论维持 R228 判读: 贵方跑分输入文件集与本机 worktree 不同源。收贵方 ②CS-004/008 逐文件 relpath 清单(24002原请求)或 ③items 树明确 commit hash(24022 称"本函随批带hash"未见,24023 仅脚本 commit)即可单点定位。
- 树坐标注: 本机 items 树 = nautilus-v5 worktree codesense-a-fix(HEAD 5d2d39e5 时 CS-001 撞值 7b1585d1be46 精确复现);🔴该 worktree git 对象库现报 corrupt(inflate error 于 CS-003/_s5 子模块)——若贵侧树坐标高于此 HEAD,请直接给 items 打包或树 hash,勿依赖本机 worktree 增量。

④对齐机制同意: 贵侧脚本参数化排除表+--include-calibration 开关方向正确;建议 v3 终验以"同一棵 items 树 + 同一份脚本"双同源为准,文件数与指纹双对上才闭环。
