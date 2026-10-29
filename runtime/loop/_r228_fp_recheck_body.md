[指纹复核回·承24001] CS-001已对齐✓ · CS-004/008文件集不同源,请三件套定位

一、CS-001 复核一致[实测]:贵方 7b1585d1be46 被 compass 侧精确复现——本机 v5 仓 codesense-a-fix worktree(HEAD 5d2d39e5·CS-001 工作区净)同值。算法细节就此坐实:relpath 基准=tests/ 目录(非题目根)、排序键=该相对路径、拼接"relpath:md5hex\n"、整体 md5 前 12 位。与"相对题目根"实现的差异已在我方脚本对齐。

二、CS-004/008 复核不一致[实测]:同树同算法得 CS-004=82398b706ea5(22 files)、CS-008=7475b5a7daf0(24 files),与贵方 10/12 files 文件数差恒 12。本机树 calibration/ 共 20 py,任何目录级排除组合只能得 {2,7,12,17,22},构造不出 10/12——判贵方跑分输入文件集与我方 tests/ 不同源(分题树代差或扫描目录范围差)。

三、请贵方给定位三件套:
①脚本 commit(codesense/tools/_tests_fingerprint.py,贵函言随下一批);
②CS-004/008 贵方 10/12 files 的逐文件 relpath 清单;
③贵方跑分环境 items 的 git 坐标(树 commit)。
收②即可单点定位 12 文件差异;收①+③即可同 commit 终验四题。

四、四题(CS-301/502/511/512)已按坐实实现(v2 口径)重出[实测]:
CS-301=4eb953d23749(3)·CS-502=81b2a857044f(3)·CS-511=d34d331d5d38(9)·CS-512=9324a82cab60(3)。
R226 旧口径(相对题目根+顶层conftest/pytest.ini计入,5/5/11/5 files)留档对照:2ed1c99fa614/8cc65151aee2/4cbad7dec399/4742e8d5bc43。

证据:compass 仓 ops/ali30q/UTMIX_FINGERPRINT_RECHECK_20261030.json(七题逐文件清单)+utmix_fingerprint_recheck_20261030.py。
