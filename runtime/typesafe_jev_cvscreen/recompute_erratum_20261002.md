# erratum 回函复算记录(2026-10-02 00:1x)

> 触发:用户要求对已发回函(issuecomment-5934831483)再思考验证。
> 弱点承认:回函核心声明"data 层一直正确"原只验到 measure_report.json(聚合脚本自报产物),未下探原始层。本记录补三层独立复算(验证代码与生产聚合脚本 jev_cvscreen_aggregate.py 完全独立手写,不复用)。

## 数据链

```
jev_run_log.jsonl(40 行原始请求/响应)
  → jev_answers.json(提炼层,40 行)
  → answer_key.json join → measure_report.json(聚合层)
  → mini_report.md(叙事层 ← 错误只在这层)
```

## 逐项复算结果(全绿)

| # | 回函声明 | 独立验证 | 结果 |
|---|---|---|---|
| 1 | divergence_rows 两行 = unclear(tzanetakis key=steady_growth conf0.72 / anagnostou key=lateral_moves conf0.44) | jev_answers.json 按 qid join 独立重算 | ✓ 逐字段一致 |
| 2 | unclear 2/27 与分歧行为同一对 | 独立计数 keyed 27 行 | ✓ agree 25 + divergence 2,divergence 全为 unclear |
| 3 | no class-swap divergences(无任何类别互换行) | 27 行全扫 pred∈{job_hopping,lateral_moves,steady_growth} 且≠key | ✓ 0 行 |
| 4 | Brier 0.069 | 独立重算 | ✓ 0.0690 |
| 5 | ECE 0.1378(10 桶) | 独立重算 | ✓ 0.1378 |
| 6 | unclear 贡献 38%(0.712/1.863);剔除口径 ≈0.046 | 独立重算 | ✓ 38% / 0.0460 |
| 7 | 提炼层无错(run_log→answers 不失真) | run_log 两行原始响应抽查 | ✓ choice=unclear conf 0.44/0.72 三层一致 |
| 8 | 性别代理数字(18 军 0 女/22 非 16 女/IT4 全女) | manifest.json 解析 | ✓(10/1 23:4x 已验) |
| 9 | 经验/雇主/跳槽率两组相近(转述自 gtaras7) | manifest 正则复现 | ✓ 6.89/7.82 年 · 2.94/2.86 雇主 · 0.22/0.18(其口径=job_hopping 类占比) |

## 结论

- 回函无需更正;所有声明从"信任聚合产物"升级为"三层独立复算"。
- 错误层定谳:数据三层(run_log/answers/measure_report)全部干净,错误仅在叙事层(mini_report 散文)+其下游 commit message。
- 独立性自评:同会话自验,梯度弱于新会话复算(judge-lessons-20260926);验证代码独立+数据下探三层,可接受。如需更强,10/2 白天可由新会话重跑本记录脚本。
