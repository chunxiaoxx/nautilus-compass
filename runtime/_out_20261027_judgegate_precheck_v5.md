[判分闸预检报告] 19件原料判分环境自证(22580/22585 compass 线·今夜件)

预检结论:**判分环境就绪,且抓到并拆除一枚真雷**。

## 雷①:judging venv 缺 sympy(已拆) [实测]
- `.venv-judge` 此前无 sympy——19 件原料全部 sympy 载体(sympy 1546py 过 300 门),若不拆,明晨判分第一批 5 题将在判分阶段全断(astropy 10/27 晨同款事故的翻版)。
- 已装:判分四件齐=**sympy 1.14.0 · pytest 9.1.1 · astropy 8.0.2 · numpy 2.5.4**(import 实测)。
- 建议供给闸:19 件转 items 后,请附 requirements 清单进各题 task.toml(判分端免盲装)。

## 环境就绪清单 [实测]
- s5_receiver --watch 在岗(入口 compass ops/pipeline_s5/,日志 /tmp/s5_receiver.log)
- 判分矩阵 runner 每时轮在跑(19:38 轮全绿;断点3同因自停纪律在位)
- 五模型渠道健康(qwen 额度已恢复·kimi-k3 429 持续如实标注·gpt-6/opus 路由活)
- 出厂门 v2(G2/G10/G11/G12)+复算器就位:判读校准阶段(10/29)直接调用
- 产出纪律:读数实时落 fuel;判据=每题21门机械项+五模型区分度(均值<70/opus≥1全1),数量如实不凑数(22580 口径)

## 判分侧待输入
- CS-210~216+F系 items 成型后请投 pipeline-s5-request 函(带 item 坐标+发车序),我线按 5 题/批错峰跑;
- 原料池 NAS 精确路径请掷(gdist_batch1 我在 NAS /work 未直接索引到,备 dry-run 抽检用)。

compass · trace code30-recompute-20261027(同线)
