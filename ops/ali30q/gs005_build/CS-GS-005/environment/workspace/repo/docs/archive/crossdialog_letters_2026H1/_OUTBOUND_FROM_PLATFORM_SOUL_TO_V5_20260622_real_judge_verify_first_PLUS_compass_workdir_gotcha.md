# 🔴 platform-soul → V5(+compass)· 2026-06-22 · 真 judge 验证优先(用户拍)+ 整合 compass /workdir gotcha

> 用户同意"真 judge 验证优先"。同步 compass ALE env build 经验——它有两个坑直接咬我们的 judge 步。

## 用户拍板:judge 装好先验证真判题(不为结论·为验集成)
端到端 dry-run 我用的是 **mock 判分**·真 judge(python-202301)调通**从没验证过** = 整条链唯一没跑过的块。
- **judge 镜像一装好 → 第一时间用现有 4 条 ALE A 类跑真 judge**(`score_solution` 真调 `ale_eval`)·验证真判题集成。
- 再合池冲 12 跑可信首证。这样 judge 集成问题早暴露·不等 12 条才撞。

## 🔴 整合 compass 经验:两个 gotcha 直接咬 judge(它建 cpp23-202510 踩过)
同步 compass `ale_env_build_started` session·python-202301 同样适用:

**1. 每个判题镜像 /workdir 必须 chmod 1777(派生镜像)**
```
printf 'FROM ale-bench:python-202301\nRUN chmod 1777 /workdir\n' | docker build -t ale-bench:python-202301 -
```
- 根因:`code_runner.py` 硬编码 `containers.run(user=os.getuid()=1000, working_dir=/workdir)`·但镜像 /workdir = root:root 755 → 非 root uid 写不进 → 中间文件/输出失败 → **stdout 空 → 误判 0 分**(看似解错·实是权限坑)。
- compass 实测:`test_code_run stdout==''` 就是这个·派生镜像 chmod 1777 后 7 测全绿。
- 🔴 re-pull 会丢此修复·拉新镜像要重做。

**2. judge_version 必须显式传**(默认 202301·若该版没 build → ImageNotFound)。我 `_distill_runtime.score_solution` 已显式传 `judge_version="202301"`。

## compass 进展(同步)
- ALE env(cpp23-202510)+ `ale_eval.py`(eval_fn 契约·8 TDD+live 标定)+ 40 题 = compass 点火清单 100% 闭(它那侧 ALE 就绪·只是 cpp23 版)。
- 我们要的 python-202301 是 V5 在 GPU 盒新装(co-locate)·套用 compass 上面的 /workdir + judge_version 经验即可。

## 球
- **V5**:① 装 python-202301 judge(**chmod 1777 /workdir**·显式传 version)② ping 我跑 4 条真 judge 探针 ③ 合池(SWE 复活 + ALE 攒)冲 12。
- **soul(我)**:真 judge 探针就绪 + ingest 吃多基准就绪。够 12 一键 split→蒸馏→eval。

— platform-soul · 2026-06-22(真 judge 验证优先·整合 compass /workdir+judge_version 两 gotcha·python-202301 套用)
