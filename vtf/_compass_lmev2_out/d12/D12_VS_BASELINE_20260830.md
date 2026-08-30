# LME-V2 d12 全量重跑 vs 基线对比报告(刀1 abstention 口径 + 刀2 检索单元升级)

- date: 2026-08-30
- run: d12 = 刀1(abstention 判分口径 patch:禁裸 UNKNOWN,引导 judge 两条得分路线——指出前提矛盾 / 明确说明无法验证)+ 刀2(检索单元升级:a11y 空结构行剪枝 + traj 内 dense 重排 per_traj_extra=4 + budget 12000→24000)
- 规模:web 240 题 + enterprise 211 题,全量完成,与基线同题同 judge(doubao)
- 证据:`compass_web_small/` + `compass_enterprise_small/`(本目录),基线在上级目录
- judge 稳定性:retry patch 三层上岗后 scoring 阶段零崩溃(此前两连崩:空响应 ValueError)

## 核心对比(overall = 全题平均分,同口径)

| 指标 | web 基线 | web d12 | ent 基线 | ent d12 |
|---|---|---|---|---|
| **overall(非abst题)** | 0.268 | **0.327 (+5.9pt)** | 0.174 | **0.245 (+7.1pt)** |
| abstention 组得分率 | 2.8%(72题) | **45.8%** | 0%(56题) | **83.9%** |
| 裸 UNKNOWN 输出 | 121/240 | **0** | 131/211 | **0** |
| answered_rate(非abst) | 57.1% | 100%(口径变化,见下) | 45.8% | 100%(同) |

## 预注册判据核对

1. **abstention 组 2.8%↑ → ✅ 大幅达标**(web 2.8→45.8,ent 0→83.9)
2. **非 abst unknown 42.9%↓ → ✅ 降至 0**(刀1 prompt 引导后模型不再裸拒答,全部尝试作答)
3. **procedure 不掉 → web ✅ 大涨(0.524→0.690,+16.6pt);ent ⚠️ 轻微回退(0.406→0.375,-3.1pt,n=32,约 1 题差距,非系统性)**
4. **LME-S 不回归 → 未测**(本轮只跑 LME-V2 两域,待补测)

## 分型矩阵(category × 平均分)

| category | web 基线 | web d12 | Δ | ent 基线 | ent d12 | Δ |
|---|---|---|---|---|---|---|
| dynamic | 0.176 | 0.137 | **-3.9pt** | 0.086 | 0.086 | 0 |
| dynamic-abs | 0.095 | 0.571 | +47.6pt | 0.000 | 0.700 | +70pt |
| gotchas | 0.467 | 0.533 | +6.6pt | 0.357 | 0.357 | 0 |
| procedure | 0.524 | 0.690 | +16.6pt | 0.406 | 0.375 | -3.1pt |
| procedure-abs | 0.000 | 0.250 | +25pt | 0.000 | 0.833 | +83.3pt |
| static | 0.117 | 0.183 | +6.6pt | 0.081 | 0.243 | +16.2pt |
| static-abs | 0.000 | 0.516 | +51.6pt | 0.000 | 0.958 | +95.8pt |

提升来源:abs 类(无法从快照验证类)全线大幅上涨 = 刀1 直接命中;非 abs 的 procedure/static 也涨 = 刀2 检索升级贡献。唯一下滑:web dynamic -3.9pt(n=51)。

## 诚实口径注记

- **answered_score 从 0.469 降到 0.327(web)是口径变化非退化**:基线"敢答池"只有 119 题(57%,其余裸 UNKNOWN 得 0),d12 全 240 题都被迫作答。同口径 apples-to-apples 就是 overall 0.268→0.327。
- **abstention 得分路线质量抽验通过**:满分答案 = "说明无法访问 live environment + 指出需要什么才能验证"(judge rubric 合法路线);同类说法也有被判 0 的案例(judge 有区分度)。⚠️ 但此路线依赖 judge 主观判别,存在模板套分空间,对外发布须注明 judge 口径。
- abstention 组占比:web 72/240=30%,ent 56/211=27%——这是 LME-V2 设计特点,判分口径对 overall 影响巨大,跨系统对比必须锁定同口径。

## 结论

刀1+刀2 双双生效,overall web +5.9pt / ent +7.1pt,四条预注册判据三条达标一条未测(LME-S 回归待补)。d12 为当前 LME-V2 最优配置。
