# 素材卡 #006 领卡工作日志 · mac-v5(2026-10-29)

> 回函平台函 #23251(素材主线进度锚启用),依 `REAL_LESSON_PIPELINE_V1.md` §十二开工位次(#006 置首)领卡。
> 领卡理由:卡 #006 真实代码载体在 nautilus-v5 本仓(`nautilus_v5/api/openai_api.py`),载体主权与考古路径都在 mac-v5。
> 纪律:不动判据 · 不动 git remote · 不对外承诺。本件=内部管线里程碑,非甲方达标(双标尺 §七)。

## 一、双锚实证(四判据第 1/2 条·全部本机实测,非转述)

| 锚 | 坐标 | 实测 |
|---|---|---|
| 坑版 | nautilus-v5 @ `7265fc50718ebff9941add8a84c01b76c0957902`(= `5ee7897e^`)· `nautilus_v5/api/openai_api.py` 行 371-380 | ✅ 查询引用 `ts` 列(schema 实列 `called_at`) |
| 坑版第二处(同 commit 内) | 同 blob 行 414-415(dmas var 段两条件查询) | ✅ 同引 `ts` |
| 修复 | `5ee7897eb5fef47cbc713e8d6e2c0f48a37e1146`(2026-10-20 01:14 +0800)· `ts`→`called_at` | ✅ diff 在案 |
| 修复后现行形态 | 正本线 `laptop-latest`(含 `fbcd105a` 10/24 推送)· `openai_api.py:398-401` | ✅ `called_at` ×4 |

复现命令(任何人可验):
```bash
cd ~/Projects/nautilus-v5
git show 5ee7897e^:nautilus_v5/api/openai_api.py | sed -n '371,382p'   # 坑版
git show 5ee7897e -- nautilus_v5/api/openai_api.py                      # 修复 diff
git show laptop-latest:nautilus_v5/api/openai_api.py | sed -n '395,402p' # 修复后现行
```

## 二、坑版 verbatim(@7265fc50 行 373-380)

```sql
SELECT
  COUNT(*) FILTER (WHERE tool_name='self_modify'         AND ts > NOW()-INTERVAL '24h'),
  COUNT(*) FILTER (WHERE tool_name='propose_code_change' AND ts > NOW()-INTERVAL '24h'),
  COUNT(*) FILTER (WHERE tool_name='compass_recall'      AND ts > NOW()-INTERVAL '24h'),
  COUNT(*) FILTER (WHERE tool_name='compass_drift_check' AND ts > NOW()-INTERVAL '24h')
FROM agent_tool_calls
```
坑面:查询口径引用过时列名(schema 演进 `ts`→`called_at`),执行即 `column does not exist`;外层 try/except 吞掉→kpi 默认 0 静默降级(降级本身即素材,与 #005 同族但主坑独立=列名漂移)。

## 三、修复 diff 要点(5ee7897e)

四条 FILTER 条件 `ts` → `called_at`,其余不动。同 commit 三修(auth 15s+DDL豁免 / kpi_trend列名 / fdw预检)——fdw 部分属卡 #007,坐标同源:`platform_snapshot_mixin.py` 预检段(laptop-latest 行 109-140,`foreign_table_schema='phase3_fdw'` 存在性预检+LookupError 拒载留痕)。

## 四、新发现(本回合增量·如实)

**同族残留未清**:`laptop-latest` `openai_api.py:437-438`(dmas var 段)仍有一处
`SELECT COUNT(*) FROM agent_tool_calls WHERE ts > NOW()-INTERVAL '24h'`
未随 5ee7897e 修复——同坑第二实例。素材价值:坑版可双处提取/UT 可加"修复完备性"断言。
定性边界(如实):该段是否"每轮必炸"取决于现库 `agent_tool_calls` 实列与该查询触发路径,候实测(建表 DDL 未在本仓 py 中检得,库权属候考古);不动摇 #006 主坑定性。

## 五、UT 锚点初设(§十二 三条件具体化,候载体 repo 落 UT)

1. **schema 可执行**:修复后查询在 `called_at` schema 上执行返回 4 计数(坑版同查询报 undefined column)
2. **降级可见**:列名错误被捕获→warning 留痕→kpi 字段默认 0(不许静默无痕)
3. **口径漂移识别**:对表结构 introspection 断言时间列=`called_at`,查询引用列∉表列即 fail(防复发锚)

## 六、四判据对照(现状·不充数)

| 判据 | 状态 |
|---|---|
| 1 载体真实(源仓+commit 可溯) | 坑版/修复双锚✅;载体 repo(>300 文件聚合)候组装(样板 CS-GS-001 形态复制) |
| 2 坑真实(修复 commit 对照) | ✅ 坑版=7265fc50·修复=5ee7897e(diff 逐行对照) |
| 3 规模合规 >300 文件 | ⬜ 候载体聚合 |
| 4 UT 锚定 badpattern ≥2 | 锚点初设 3 条(§五),候载体落 UT+甲方 badpattern 表对挂 |

## 七、下一步(领卡后开工序)

坑版模块提取(371-380+414-415 两处)→ 载体 repo 聚合(v5 真实模块群+嵌依赖,过 300 门)→ 坑版植入+UT 三锚 → 打包闸(带素材卡号 #006)。
**当前账(沿正本口径):卡 7 · 题 1 · 门 0**(领卡不增卡;#006 状态:达开工深度→已领开工)。
