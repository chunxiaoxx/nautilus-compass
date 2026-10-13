---
name: orgfuel-ORGF-7add38581ca30e3f-9fdd95c4e0
description: "flywheel 档案 loop_night_R147_20261008.md # LOOP 值守轮 R147 留痕 2"
metadata:
  type: reference
  source: org_fuel:flywheel
  pf_id: ORGF-7add38581ca30e3f
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

flywheel 档案 loop_night_R147_20261008.md
# LOOP 值守轮 R147 留痕 2026-10-08 07:0x(门面站群互链+W1 第二件轮)

> WEB-SYS 值守 cron 轮。中心环=门面装订(站群互链),当轮闭环。

## 本轮动作
1. **例行**:信箱 0/外环双 CLEAN。
2. **门面站群互链补全**(nautilus.social 主门面 nav 原零站群外链):
   - index.html nav 增四链:数据站/评测站/判读站/文档中心(↗ 外链);改源直改+备份 index.html.bak-20260923→20261008-R147 惯例;mtime 对表无并行风险。
   - 外网验:四链全在页。
3. **bench 页 v0.1**:跨引擎对照节(InternVL2_5-2B)入页——gen_bench_v0.py 增读 manifest+rows 两源,R2/R3/guard/耗时全程序化(26.2%/0.059/28-30/200.8s);对位声明"2B 弱于 7B(同协议 v2a 39.8)"如实报,R1 候判级标注;部署+外网验绿。
   - engine_ver 字符串"8b"残留已知情(manifest model 字段=2B 为准),下轮修脚本重出 manifest。
4. manifest 件入仓(runtime/goldset_a3_internvl_n30_manifest.json)。

## W1 外环进度
bench ✅(HTTPS+内容页+缓存 no-cache) / 门面装订 ✅(站群互链,开业件区块已在) / data 站并入=候 K3 设计稿承接(两外壳并入 data 站设计 v1 在档)。

## 下轮
QC17 发车(aria2 配方)/SOP+状态
