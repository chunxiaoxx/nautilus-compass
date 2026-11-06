# D3-D5 非实现者复算包(2026-11-05)

> 用法: **新鲜会话**(非本弧任何实现会话)只读本包+下列坐标,逐条复算并对照定谳文件。本包**不含任何预期读数**(报数纪律:交接档只给坐标与命令)。复算结论回写 `RECOMPUTE_RESULT.md`(自署会话 id+时间)。
> 定谳文件: D3_VERDICT / D4_VERDICT / D5_VERDICT(ops/distill_pilot/)·判据正本: docs/soul/SESSION_DISTILL_PILOT_20261104.md(J1-J6+§九 V2)
> 数据根: runtime/scratch_distill_pilot_20261104/(下称 $D)·工具: tools/distill_pilot/

## 一、机械判据复算(零 API,几分钟)

```bash
cd ~/Projects/nautilus-compass
D=runtime/scratch_distill_pilot_20261104

# J1(锚点回溯)+虚构计数: 4B 与 9B 两臂各跑一遍,对 d4_mech_{4b,9b}.json
python3 - <<'EOF'
import sys, json; sys.path.insert(0,'tools/distill_pilot')
from anchor_check import check
from pathlib import Path
for arm, d in [('4B','summaries_local'),('9B','summaries_9b')]:
    out=Path('runtime/scratch_distill_pilot_20261104'); valid=hit=0; fabs=set()
    for md in sorted((out/d).glob('*.md')):
        r=check(md.read_text(encoding='utf-8',errors='replace'),
                (out/'extracted'/f'{md.stem}.txt').read_text(encoding='utf-8',errors='replace'))
        valid+=r['n_valid']; hit+=r['n_matched']
        fabs|={a['value'] for a in r['anchors'] if not a['matched'] and 'note' not in a}
    print(arm,'pooled',round(hit/valid,4),'fabs',len(fabs))
EOF

# J3 生产形态(叙事+sidecar 合并口径)与 J4(叙事 md 口径):
# 按 D5_VERDICT §一 的口径重算 summaries_9b_prod/(.md + .anchors.txt 合并查显著锚点;
# 显著=源文出现≥3次的非CJK path/date/tag_id/url,与 d4_mech_*.json 的 salient 字段对照)

# J5: C 组定义性信号复核——sample_manifest.json 的 C_patrol_control 10 条,
#     其源 jsonl 首条用户消息应含"LOOP 轮指令"模板(可 head -c 300 各源文件核对)
```

## 二、仪器层复算(需 API key,可选)

- **J2-v2(声明级)**: 重跑需 kimi key(api.kimi.com·codex config 的 ANTHROPIC_AUTH_TOKEN)+`JUDGE_SKIP_GLM=1 JUDGE2_KEY=<key> JUDGE2_BASE_URL=https://api.kimi.com/coding/v1/messages`;命令同 j2v2_*.json 生成路径(judge_v2.py --ids <10 个 ref 会话 id> --arm-dir summaries_9b|summaries_local)。**注意**: LLM 输出非确定,复算读数与原读数有小差属预期——差异若 >3pt 才构成对定谳的挑战。
- **判官失效复证**(D4 核心): 用 v1 仪器(judge_eval.py j2,glm 判官)对同批 ref 纪要跑两轮,比对轮间差——D4 定谳依据即此差>5pt。

## 三、资产清点(零计算)

```bash
ls $D/summaries_9b_prod/*.md | wc -l        # 生产形态叙事(应与 D5 记载一致)
ls $D/summaries_9b_prod/*.anchors.txt | wc -l  # 锚点 sidecar
ls ~/.claude/projects/-Users-chunxiao-wang-Projects-nautilus-compass/memory/distill-* | wc -l  # 已发布 memory
wc -l $D/compress_stats_summaries_9b.jsonl    # 9B 全量统计
```

## 四、复算判据(什么算"定谳成立")

1. 机械读数(J1 池化/J3 生产形态/J5/J4 md 口径)与定谳文件记载**逐项一致**(±0.5pt 内,浮点/锚点集合边界差异可容);
2. 仪器层(J2-v2)读数方向一致(9B 显著低于 4B),绝对值容差 3pt;
3. 资产清点数量一致。任一不满足 → 回写差异并 @ 实现会话对质,定谳暂缓生效。

## 五、已知边界(复算前先读,防误判)

- anchor_check 为 v4(尾标点剥离等),若复算环境拿到旧版会出现假阴性差(仓库 HEAD 即 v4);
- ref 臂与 v1 判官同源(glm)的偏袒已由 kimi 判官实证,复算 J2 必须用 kimi;
- 显著锚点口径=≥3 次;若复算者改口径(如 ≥2),读数不同属口径差异非数据差异。

—— compass · 2026-11-05 · RECOMPUTE-PACK-D3D5-V1
