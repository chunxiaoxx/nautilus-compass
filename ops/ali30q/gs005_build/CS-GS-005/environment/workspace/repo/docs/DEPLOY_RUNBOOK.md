# 部署四步 Runbook(2026-10-01 立 · 承 square crash-loop 2min 事故)

> 事故:10/1 00:18 square 挂载部署——本地 py_compile 通过,云端 SquarePost 模型缺失,
> backend crash-loop 5 次重启,502 窗口 2 分钟,回滚止血。同型前科:9/12 部署管线三处 fail-open。
> **肌肉:跳第②步禁止重启生产。**

## 四步(顺序不可换)

1. **本地编译**:`python -m py_compile <改动文件>`——只验语法,不验依赖
2. **云端 import 干跑**:`ssh cloud "cd /home/ubuntu/nautilus-mvp/phase3/backend && python3 -c 'from api.X import router'"`——本地/云端依赖差异在此暴露(square 事故本步即可拦下)
3. **回滚预案先行**:单文件改动记下 `git checkout <上一好commit> -- <file> && sudo systemctl restart nautilus-backend` 一行命令,再动手部署
4. **重启+三探针**:`systemctl is-active` + `/api/platform/health` 200 + 改动面端点 200(如挂载路由)

## 静态页(免重启)

scp 前先 `cp 备份`,失败回滚=cp 回来。不涉及 backend 进程。

## 部署窗纪律

- 生产重启避开 09:07 快照/整点函件高峰(13/43 分 loop 轮)
- 深夜赶工不部署:crash 止血靠清醒——22:00 后只备不发,晨窗执行

## 第②步升级(2026-10-02 晨,函数体盲区案)

云端干跑必须**调用级**而非仅模块级 import:`python3 -c 'from api.X import router'` 只测模块顶层,函数体内的 import/列名错误测不到(10/2 账本端点 500 实证:函数体内 `from models.database import CapabilityCapsule` 该名不存在,模块级干跑通过,调用即炸)。升级配方:干跑后加一次**真调用**(curl 对应端点或 python 调函数),冒烟不过不重启。
