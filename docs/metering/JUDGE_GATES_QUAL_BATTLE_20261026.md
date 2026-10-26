# 资格战判读门 · 函 22064 六点纳入口径(2026-10-26)

> 来源: flywheel 函 22064(认知统一·SLA 今日 20:00)+ NAS 1012 原文 `docs/metering/ali_docs/ali_1012_txt_full.txt` L19-22
> 角色: compass=判读层执行,不改题。v5 改题/复测。
> 证据层: 本档条款为口径钉死[推断→upgrade_path=矩阵实弹后标实测];计算器 `ops/ali30q/discrimination_jaccard.py` 单测 8/8[实测]。

## 一、对六点的判读层落点

| # | 定谳原文要点 | compass 回执 | 落点 |
|---|---|---|---|
| 1 | 周一 10/27 A 批复验改题后提交;14 题新批 ≤周五 10/31 | 确认(日程知悉,不改题) | 周一起按本档复判 A 批;14 题按到卷 SLA 出卡 |
| 2 | qwen passrate 必须 25% 或 50%,禁 0;沙盒 qwen=3.8max;CS-003 类 qwen=0 须改题 | **确认且收紧既有 10/24 复盘**(该复盘曾把 qwen=0 当区分度达标) | G-QwenPoint |
| 3 | SOTA>qwen 分差>20;失败 UT 集合多样性≥50%+最大单一失败签名≤50%+跨模型 Jaccard÷同模型 4 轮平均≥1.25 | **确认**;1012 原文写「建议」,本函升硬门(判据只许更严,接受) | G-SotaGap + G-Sig |
| 4 | 五模型×4 轮纯 UT;gating 一票否决;蒙对≤0.30/等价≥0.90 | 确认(KEY_SPECS 已有,不新造) | 既有 G4/G-gating/校准四件套 |
| 5 | 代码须真实生产业务,附业务背景;飞轮七件双验在库 | 确认可核「附件在否」;「非 AI 生成」无 provenance 则标 UNVERIFIED 不冒充实测 | G-Provenance |
| 6 | 14 题=甲方第四反;30=内部产能/18=对外交付并存(#21983);badpattern 七表钉钉正本 | 确认;compass 按交卷物对照 1012 门,配额会计归 v5/soul | 不新造配额门 |

## 二、操作化定义(避免「建议」无法复算)

**二值 passrate**(与 1012「tests 全对为 1 否则为 0」对齐,不用 UT 通过率均值冒充):

```
binary(run) = 1  iff  ut_vector 全非 0(失败集空)
qwen_passrate = (# binary=1 的 qwen 轮) / 4
```

覆盖 <4 轮 → 该门 UNVERIFIED,不入交付。

**失败签名** = `frozenset(ut 名 | ut_vector[ut]==0)`。缺 `ut_vector` 的轮不进签名门。

**G-QwenPoint** PASS iff `qwen_passrate ∈ {0.25, 0.50}`。`0` 一律 FAIL(须改题)。`0.75/1.00` 亦 FAIL(过易,不在甲方两点位)。

**G-SotaGap** `mean(opus, gpt) - qwen > 0.20`。SOTA 缺 ≥1 腿 → UNVERIFIED(10/24 单腿教训,不入交付)。

**G-Sig**(三子门同时):

1. `|#唯一失败签名| / |非全过可用轮| ≥ 0.50`
2. `max(同一签名出现次数) / |非全过可用轮| ≤ 0.50`
3. `mean_{m≠m'} Jaccard_dist(Fail_m, Fail_m') / mean_m (同模型 4 轮两两 Jaccard_dist) ≥ 1.25`

Jaccard 距离 = `1 - |A∩B|/|A∪B|`;双空=0,单空=1。

**除零**:同模型平均距离 < ε 时——跨模型 >0 → 比记 `inf` 且 PASS;两者皆 0 → UNVERIFIED。无非全过轮 → G-Sig UNVERIFIED(全员满分=无区分信号,与 10/24 CS-010 同构,G-QwenPoint 会先红)。

**1012 原文「建议」升硬门声明**:flywheel 函把建议阈值钉成验收门。compass 按「判据只许更严」接受,不回退为建议。

## 三、与旧口径差(必须显式,防精神分裂)

| 项 | 10/24 `ALI_4Q_DISCRIMINATION_REVIEW` | 本档(22064) |
|---|---|---|
| qwen=0 | 可作「单腿区分度达标」 | **FAIL,须改题** |
| 区分度 | 国内组 vs SOTA ≥20pp(均值) | **SOTA vs qwen >20pp**(对照轴改为 qwen 单模型)+签名三子门 |
| 签名多样性 | KEY_SPECS 提炼漏列 | 硬门,计算器落地 |
| factory_gate G5 | 阈值 0.10+国内组均值 | 仍保留作观察列;交付以本档为准 |

CS-003 在旧复盘标 qwen=0 区分度达标——**本档起该结论作废**,候 v5 改题后再判。

## 四、计算器

- 脚本: `ops/ali30q/discrimination_jaccard.py <item_dir>`
- 单测: `tests/test_discrimination_jaccard.py` 8 例(无 pytest 时用模块内函数直跑)[实测 8/8]
- 渠道别名: `glm5.3-anthropic→glm5.3` / `kimi-k3-ark→kimi-k3` / `opus5.5-qixuw→opus5.5`(同模型多渠道不双计,按 canon 聚合)

## 五、KEY_SPECS 勘误

`docs/metering/ALI_1012_KEY_SPECS.md` 判分段漏「失败 UT 集合多样性 / 最大单一失败签名 / Jaccard 比」。本轮补三条,指向 1012 原文 L20-21。
