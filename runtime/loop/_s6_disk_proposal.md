# S6 磁盘决策件:cloud 全盘实测盘点+清理候选列单+三方案(呈用户批 · 承 10690)

> 承 10690(v5):"列单直呈用户,勿在框间空转"。以下全部 ssh 实测(sudo du/ctr/crictl),非转述。

## 一、实测全貌(/dev/vda2 178G · 已用 105G · 余 66G)

大头:/home 36G · /var 33G(containerd 16G+docker 5.6G+pg 2.3G)· /opt 14G · /usr 11G。

## 二、清理候选列单(分级 · 风险标注)

| # | 候选 | 释放量 | 风险 | 说明 |
|---|---|---|---|---|
| A1 | pnpm store prune | ~5-6G | 无害 | 官方 prune,缓存可再下 |
| A2 | snapd cache | ~1G | 无害 | /var/lib/snapd/cache |
| A3 | containerd 残留层 | ~14G | 低-中 | k8s.io ns 零容器(crictl ps=0 实测),全为残留;docker 卷独立不受影响;执行时再复验 |
| A4 | /opt/ecc-shared/scripts/.venv | 5.0G | 低 | 纯 venv,可 pip 重装重建;ecc 用途待主人确认 |
| A5 | /opt/flywheel/venv | 8.1G | 中 | flywheel 进程在跑(实测 2 个)——占用中不可删;需停机窗+重建 |
| A6 | ~/.local/lib(pip --user) | ~10G | 中 | 删后用户级 python 包失效,需逐服务盘点依赖 |
| — | **不可动(生产数据)** | — | — | espocrm_mysql 4.7G · postgresql 2.3G · compass_cold_archive 4.3G · .claude 1.8G |

**安全级合计(A1-A4):~25G → 余 66G→约 91G**;A5/A6 再 +18G 需窗口与盘点。

## 三、S6 缺口三方案(30 镜像 ~60-120G vs 现 66G)

- **方案一(建议 · 零花钱)**:清 A1-A4→约 91G;swebench 镜像**按需 pull+用完即删**(同窗 1-2 个,峰值 ~10G),30 个分 4-5 批,排期 10/9-10/14(在 10647 已报缓冲带内);判据 sha 不变。
- **方案二(花钱快)**:清 A1-A4+云盘扩容 +100G(约 ¥xx/月级,用户批);镜像一次全拉,排期 10/9-11 不变。
- **方案三(异地)**:S6 复算迁 GPU 机执行——但 swebench 5.0.2 环境已在 cloud 装妥,迁移成本高,不推荐。

## 四、请用户批

①A1-A4 是否执行(一条令即跑,30 分钟内完成);②方案一/二择一;③A5/A6 是否列入窗口件。

—— compass · S6-DISK-CLEANUP-PROPOSAL · 2026-10-08
