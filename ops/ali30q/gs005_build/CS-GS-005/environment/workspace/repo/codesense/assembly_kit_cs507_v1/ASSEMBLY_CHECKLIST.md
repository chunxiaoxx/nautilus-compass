# CS-507 v1 达标交付包组装清单(打包闸预演·2026-10-28)

> 判分数据回函后按此单组装,逐项勾选,缺一项不出包。
> 基包:NAS batch1/CS-507_v1_deep_1028.tar.gz(md5 e3541068ed4154cd51a7a9d03236cfe4)

## 一、达标前置门(数据不到不出包)

- [ ] 五条件①:五模型各 4 轮完成(kimi 本轮必须跑满)
- [ ] 五条件②:整体通过率(全过轮/20)< 70%
- [ ] 五条件③:opus 全过轮 ∈ [1,3]
- [ ] 五条件④:qwen ≥1 轮未全过,且平均 <opus 且 <gpt(双低)
- [ ] 五条件⑤:qwen passrate ∈ {25%, 50%}(禁止 0%/1.9% 类)
- [ ] 三指标 M1:不同失败集合数/非全过运行数 ≥ 0.50
- [ ] 三指标 M2:最大单一签名占比 ≤ 0.50
- [ ] 三指标 M3:跨/同模型 Jaccard 距离比 ≥ 1.25
- [ ] 判分连跑一致性:同版数据抽 1 模型重跑 1 轮,UT 矩阵可复现

## 二、题本体(与判分版字节一致·防"判 A 交 B")

- [ ] instruction.md / task.toml / environment/(repo 含 policy §5+坑版)/ tests(25UT+score.py)
- [ ] solution/:golden(service.py 防御式)+ golden.patch(应用=金标)+ solve.sh
- [ ] **基包 md5 复核**:解包后 environment/workspace/repo/skillapi/service.py == 判分所用坑版

## 三、文档证据层(判分后填数)

- [ ] equivalent.md:变体1 已换"类型守卫修正版"(预演实测旧版挂 10 条——**已在 v1 源修正,组装时确认在位**)
- [ ] model_failure_modes.md:4 条 FM 全部填上真实答卷引用(替换 [待判分] 标记)
- [ ] counterexample_507_v1.py + run.log 在 assets(已就位·日志含 python=3.13.16/darwin)
- [ ] assets 答卷:全部换 25UT 时代新答卷——**清除 21UT 旧答卷 22 件+旧 ut_results.json(混时代数据红线,CS-509 事故教训)**
- [ ] selfcheck.md:按新判分数据重写
- [ ] calibration 四件套逐条打分单:full_score/guessed/defective 按判分后金标/蒙对/坏版实测更新(等价变体已实测 25/25)

## 四、判分报告(两列指标+逐条明细)

- [ ] 主表:五模型×4 轮,主分(passrate 全对率)+UT 通过率两列
- [ ] 逐 UT 矩阵(ut_matrix.json 随包)+失败签名分组明细
- [ ] 三指标计算明细(调 flywheel codesense_discrimination_metrics.py,输出附包)
- [ ] 五条件逐条对照结论(平台终审签字位)

## 五、包外证据包

- [ ] 模型错误模式证据(=FM1-4 实录)
- [ ] 基线试测日志(判分渠道/版本/参数)
- [ ] 自检结论(金标自检+坑版基线+patch 一致性三态,已有实测定数)

## 六、打包与终审

- [ ] tar.gz+md5,入 NAS batch2_delivery 新目录(不覆写 batch1)
- [ ] 平台终审:对照 ALI_REQ_STANDARD_MAP_V1 全图 B 节十条机械项逐条过
- [ ] 用户放行 → 甲方通道(外发必经用户)

—— 组装脚本:assemble.py(本目录)·预演完成项已标
