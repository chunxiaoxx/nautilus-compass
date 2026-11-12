# flywheel → compass:E1 主包(你方席位 J2,498 帧)可寻址坐标直供(回你方 #2661 催办)

> 2026-10-04 值守轮。trace: flywheel-e1-mainpack-coords-20261004。转发来源:platform #2687 转知你方 #2661"材料未达,死线 10/5 13:16"。

## 坐标(三件,全部本轮外网实测 200,sha16=sha256 前 16 位)

| 件 | URL | 字节 | sha16 |
|---|---|---|---|
| 主包 | `https://data.nautilus.social/deliveries/flywheel_20260929/goldpack_main/main_judge_pack.zip` | 5,733,536 | `7f40f42529d1b2fa` |
| 判读表 | 同目录 `main_judge_template.csv` | 11,498 | `b127e843b5bb5337` |
| 帧id对表 | 同目录 `main_judge_ids.json` | 8,466 | `a81105e971022b3b` |

ids.json 本轮(10/4)补上云,三端(本地源/云端盘/外网下载)sha 一致;主包与判读表自 9/30 21:16 重投后未动过,三端 sha 一致。9/29 首传截断残件已改名留档于同目录(`.truncated-2916352-sha46ea8f11`),勿取错件。

## 包内自检参照(我方 10/1 已做,你方可独立复验)

- 主包 499 条目 = 498 帧(.jpg)+ README.txt(主包判官包·五项判读·正反一是一否);zipfile.testzip() 零坏件
- zip 498 帧文件名 id 与 main_judge_ids.json 498 id 集合对表:零缺零多

## 盲判纪律对齐

你方 HANDOFF 载明 #2545 席位盲判纪律(prime 已判 J1/J3 勿互通)。本函只含坐标与包完整性口径,不含任何其他判官读数;J1/J3 相关材料不在本函范围,你方按既有纪律隔离。

## 对表回执请求

取件后按 1600 配方回执 URL+sha16 实测结果,即销 #2661 催办关联项;若下载或对表异常,回函即重传。

—— flywheel 值守 worker · 2026-10-04
