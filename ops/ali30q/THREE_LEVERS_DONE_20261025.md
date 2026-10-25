# 三杠杆执行战报(2026-10-25)

## 杠杆1:判分环境固化 ✅
- requirements.freeze(判分四件套精确)+rebuild_judge_env.sh(一键重建)
- 修正记录:首版冻结混入题面依赖(astropy/django)——已修正为判分器最小依赖(pytest/iniconfig/pluggy/packaging/Pygments/pyyaml)

## 杠杆2:标定自动化 ✅(降为 shell 版)
- s3_calibrate.sh:坑版/金标/变体三态自动跑(复用 CS-511 实测配方)
- python 封装版修正 2 轮未收敛→按纪律降级 shell 版(已验证)
- 附加 finding:CS-511 金标 20/20 全过(此前"5 failed"系脚本输出顺序混淆)

## 杠杆3:例检自动化 ✅(前轮已落,此处收口)
- 金标自检(tools/gold_check.py)入 v5 仓 tools/
- verify_pack v1.2 双口径列(甲方口径)
- CS-010 path 缺陷 15 题批量修(前轮)

## 循环接管
- 三脚本入 ops/ali30q/ 与 judge_env/,值守轮按需执行(出包前必跑 s3_calibrate.sh)
