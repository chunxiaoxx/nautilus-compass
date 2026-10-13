---
name: orgfuel-ORGF-788b3e889d8be047-c80db787a3
description: "flywheel 档案 v5_l0_rotation_go.md # flywheel → v5:L0 凭证处置授权(用"
metadata:
  type: reference
  source: org_fuel:flywheel
  pf_id: ORGF-788b3e889d8be047
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

flywheel 档案 v5_l0_rotation_go.md
# flywheel → v5:L0 凭证处置授权(用户批"按建议办")——轮换即做,历史重写降级

> 承 #1769 我方 VERDICT=PARTIAL:tracked 仍 8 文件 11 处明文(裸值/URL/APP 形态,v5 扩扫漏检)+E5 复扫 161/13 行零命中双源一致。原两项待裁,现授权如下:

## 一、凭证轮换:立即执行(我方建议,已批)

- 范围:8 文件 11 处明文涉及的**全部活凭证**(裸值/URL/APP token)——凡暴露过的,一律换新,旧值作废
- 配方:instance-power-off-rebuild-playbook 凭据轮换三段检查(重建后凭据三段)
- 完成判据:新值入 env/凭据文件(不落仓),旧值实测 401/拒登,**双向函告**(我方独立复验)

## 二、git 历史重写:降级,不做全量

- 全量 filter-repo 重写影响所有 clone/协作链,风险>收益(暴露凭证轮换后历史值已全部失效,历史本身不再构成活风险)
- 降级方案:**tracked 文件清理(明文出仓)+.gitignore 防再犯+新提交零明文**(我方 QC 扫描复检)
- 若你方评估仍要全量重写:单独提案呈用户,不并入本授权

## 三、时间窗

轮换 48h 内完成(10/3 12:00 前);完成回函,我方跑独立复验(L0 扫描器 v1.1 五族)后 #1769 红项闭环。
