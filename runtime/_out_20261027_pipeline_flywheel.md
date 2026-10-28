[管道化·协同件] 快筛上游环已补+全链贯通——六环分工建议(22646 配套)

你侧 quickscreen_verdict.py(快筛三判据·22646 裁定配套)已实测接入 compass 读数流——**45 题读数一键汇总→快筛秒出判定**,首跑实录:CS-513 过筛✅、CS-517(qwen 全挂)不过筛如实暴露。

## 补上的上游环(你管道缺的一环)
compass 仓 `ops/ali30q/collect_for_quickscreen.py`:
- 从 items 目录树自动收集 qwen/opus 读数 → 输出你快筛器的标准输入 JSON(A 口径二值化,与 22646 对齐)
- `--v5 --scratch` 快捷扫 v5 items + compass 改造件 scratch;支持任意 --items-dir 多路
- 用法: `python3 collect_for_quickscreen.py --v5 --scratch > qs.json && python3 scripts/quickscreen_verdict.py < qs.json`

## 六环管道全景(谁在哪环)
```
①装配 harbor→items   compass harbor_assembler.py(smoke✅)
②出厂门 21门预检     compass factory_gate v2(G2/G10/G11/G12+tomllib门F-008后)
③判分 五模型×4轮     compass matrix runner(ali30q-loop 每时轮)+s5_receiver(watch在岗)
④汇总 读数→快筛JSON  compass collect_for_quickscreen.py(今夜新补✅)
⑤快筛 三判据判定     flywheel quickscreen_verdict.py(22646✅)
⑥打包 证据包+追溯矩阵 flywheel make_verify_pack 线(已认领)
```
任一新题从 harbor 到快筛判定,现已一条命令链可达。

## 两个口径细节(管道健壮性,请快筛器作者定夺)
1. c1"均值<70"无下限——qwen 全挂(均值 0)也过①(靠③拦);若甲方后续加"禁 0"硬门,c1 需补下限,一行改动;
2. collect 口径=score==1.0 记 1 否则 0(None 跳过)——与你的 A 口径一致;opus 读数缺失的题 c2 自动不过(如实)。

## 批次2 现势快照(首跑实录)
- 过筛: CS-513 ✅(二值化均值 0.5·opus 全 1)
- 不过筛: CS-517(新题 qwen 全挂——需调档)/CS-515B(opus 无全 1 轮)/超档众(CS-506~516 qwen 全 1)
- 完整 45 题判定表见快筛输出,坐标 /tmp/qs.json(临时,正式落 runtime 后同步)

compass · trace code30-judgegate-20261027(同线)
