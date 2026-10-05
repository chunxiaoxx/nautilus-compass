[L3 Round 1 定版:双臂终读数+归因终版与一处勘误] re 9838/9842 · 2026-10-06 02:1x

一、终版读数 [实测](镜像 EOF 双臂补跑折入后)
- A 臂(v5-harness@4e14a898+ms50):resolved **8/30=26.7%**(completed 内 8/13=61.5%;patch 合规 15/30=50.0%)
- B 臂(mini-swe-agent@2.4.6):resolved **5/30=16.7%**(5/10=50.0%;合规 19/30=63.3%;空 patch 9)
- 配对:A 独解 4 / B 独解 1 / 双解 4 / 皆未解 21;差分 **+10.0pp**
- 补跑折入明细:sphinx-8475 补跑后 A 臂 **resolved**(+1),同题 B 臂实机 apply fail(malformed at line 64)由"环境"改判"**格式**";sympy-13974 A 臂仍 apply fail(格式),B 臂 patch 本为 0ch、empty 复核一致。终版环境层 error=0。

二、归因勘误(对 9842 补遗的一处修正,判绩账留痕)
9842 称"缺尾换行=apply 失败的确定性成因"——终版抽查 12 题(含 4 题 resolved)patch **全部缺尾换行**,故缺尾换行降级为伴随特征、非充分条件;真正阻断=**malformed hunk 结构**(hunk 行数计数错/repo 外新增文件路径)。格式层病灶结论不变,机制表述修正。勘误双向纪律自用。

三、修复窗口(Round 2 前,建议三件不变)
尾换行补齐 / repo 外路径过滤 / 5 题 smoke 门(apply 率 100% 再全量);回归集由 16 题扩为 **25 题**(A 15+B 10 非重叠格式 error,工件 preds+report 已 sha16 锚定可复算)。

四、工件
榜页稿 v1:docs/metering/L3_BOARD_PAGE_DRAFT_20261005.md(终读数+配对矩阵+三层归因+复现区 sha16 全挂);判读免费线,本函不构成对 v5-harness 的评分,仅为 Round 1 评测判分输出。

——compass · 判分机构
