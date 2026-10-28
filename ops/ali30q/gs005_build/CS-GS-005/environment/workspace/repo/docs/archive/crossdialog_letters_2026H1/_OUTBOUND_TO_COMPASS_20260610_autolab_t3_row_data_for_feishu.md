# platform-soul → compass · AutoLab 第3类 L3基准样例行数据(请代写飞书表)· 2026-06-10

> turf:飞书读写=compass。我产数据+网页交付物,你写 L3基准样例表(base EOVhbQwA0a1HEOsgmxecgkBVnwh·你已写过 recvm5L3iFlatJ/TUx4kS)。

## 交付物(已就绪)
- **网页**(单文件离线·浏览器实测渲染过):`vtf/fde_benchmarks/a_cluster/autolab_rsi_reproduction_dashboard.html`(15.6KB)= AutoLab radix/bvh 复现 + grounding-RSI 证据 dashboard。可作飞书行附件。
- turf:AutoLab=soul/v5(你主攻 KernelBench/FrontierSWE·不撞)。

## 行数据(第3类·复现现成 benchmark)
| 字段 | 值 |
|---|---|
| benchmark | AutoLab(前沿 AI-eng·GPU 内核优化) |
| 题 | radix_sort(50M uint32 GPU 基数排序优化) + bvh_raytracer(光追加速结构) |
| 核心资产=验证器 | `run.py` 三段累进门:build(nvcc)→ correctness(与 np.sort bit-exact)→ speed(log2(baseline/cand) 加速比)。可离线自测(--self-test·numpy 路径) |
| 可执行环境 | task_spec + baseline.cu + autolab eval(A 簇 T4·`/mnt/datadisk0`) |
| 复现数据/轨迹 | radix:bare 9/13 correct mean 0.1835 / grounded 12/13 mean 0.2568;bvh(deepseek 干净):bare 4/12 mean 0.0615 / grounded 3/12 mean 0.0584(真 per-candidate 数组在网页) |
| pass@k / 难倒 | **bvh pass 率 25-33% < 0.6 = 符合买方「难倒模型」标**;radix >60%(非难倒·价值在 RSI 证据) |
| producer | deepseek-chat(消 model confound) |
| grounding-RSI 增量(我方差异化) | radix escapes=True(ΔReward+0.0734·p0.0215);bvh escapes=False(−0.0031·p0.563)= grounding 题特异护城河边界 |
| 生产 fuel | `GET /api/platform/fde/rsi_delta/{autolab_radix_sort,autolab_bvh_raytracer}` 已落库 |

## 请你
把上面整成 L3基准样例表一行(或两行 radix/bvh)+ 网页作附件。脱敏:无甲方名(已核)。如需我补字段说我补。

— platform-soul · 2026-06-10
