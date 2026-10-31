# 迁移遗留审计档(MIGRATION_AUDIT)·2026-10-31

> 触发:用户令"同步全部对话框最近疏漏和缺失问题,查漏补缺,迁移前后的问题还是很多,尤其是 compass 和 assay"。
> 范围:compass 框 + assay 发布面(=本仓 OSS:PyPI nautilus_compass/CASSAY 品牌,经核实 assay 无独立框架目录,与 compass 同仓两面)。
> 方法:launchd 全量死路径扫描·仓内 Win 残留 grep·OSS 三面探针·CI 运行史·变体目录逐个验尸·Win 会话记忆残骸差分·COLLAB_BOARD 未决清点。

## 一、✅今日已修(全部实证,commit 见 git log 10/31)

| # | 问题 | 修复 | 实证 |
|---|---|---|---|
| 1 | 部署件 daemon.py 停迁移旧版,daemon_env 加载自 5/22 静默失效(Path 后置) | 仓源部署+重启 | 进程日志 re-embed 循环+M5 冒烟 |
| 2 | mcp_server.py 双向漂移(插件带 `C:\Users\chunx\` Windows 热修) | 热修正本回收进仓(Mac 默认路径+env 覆盖) | deploy --check 全绿 |
| 3 | memgate_stamp.py 仓缺(插件独苗) | 纳管入仓+manifest 3→7 | md5 一致 |
| 4 | v5 main_singleton 无 token 直连=两月 auth_failed(迁移孤儿进程) | 一行修+精确 kill+guard 复活 | 首笔 via=bge_daemon_socket+180s 零复发 |
| 5 | genesis_watch 未入值守例巡(两外部回复挂 9-11 天) | 入 round_prompt 3b | R553 已实证跑通 |
| 6 | Gmail token 死+urllib 对 Gmail 无限挂起 | 非交互刷新(3599s 绿)+全程 curl 化 | 探针 3 次实测 |
| 7 | GITHUB_TOKEN 脏 \r:zshrc 消毒只盖交互壳(Bash 工具壳实测仍 41B) | **~/.zshenv 全域消毒**(新建,覆盖非交互) | zsh -c 实测 40B |
| 8 | Win 会话记忆残骸 `~/Projects/C--Users-chunx-*/memory`(迁移会话合并漏网) | 差分比对:唯一缺失条目 outreach-triple-launch-20260930.md 已合并归位+入索引 | diff 实测 |
| 9 | 阿里线三 loop 残留(bait/ali30q/production 空转) | launchctl bootout(plist 留存) | 复验离场 |
| 10 | CI 10/26-29 红波(通知积压未读) | 定谳=41a5676f 已修(清 27 处 ruff),10/30 22:57 起 8 连绿 | gh run list 实测 |

## 二、🔴候用户(安全+拍板)

11. **🔴安全亮牌(最优先)**:GitHub 账号邮箱批量变更通知(9 移 1 增·10/30 20:12-24 北京)——值守轮无法确认是否本人操作,挂至今。**请登录 GitHub → Settings → Emails 核对**;非本人=立即改密码+撤销未知授权 token+查安全日志。坐标:R250 亮牌原文。
12. 六个空壳目录删除候选(全部 0 项非 git 空目录,零数据损失):`nautilus-compass-{cjk-fix,cloud-design,fde-dim,feishu-settle,tag-doc,wt-readme}` + `C--Users-chunx-Projects-nautilus-compass`(memory 已合并)。~/Projects 共 98 目录,legacy 实验目录(arm-worker-*/cloud_clone/body 等)另批盘点。
13. compass_hud_wrapper.py 仓缺(deploy manifest 每轮跳过,插件独苗)——与 memgate_stamp 同款病,纳管候拍板。

## 三、🟡候外部/维护窗

14. ai.nautilus.v5-brain 标签 gui 域未加载(进程靠 guard 复活)——建议 bootstrap 收编,恢复 KeepAlive 正常管理(v5 维护窗,已随回执函 24319 通报)。
15. Glama 三步(claim/测试 profile/构建日志)——登录墙后,候用户浏览器(方案已给,上轮)。
16. dev.to comments GET 端点 404(上游变更)——监控降级已适配(计数走 articles 端点),留档观察。
17. venture_daily_report 部署连败 6 条——非 compass 域(值守轮持续亮牌,候用户处理其部署配置)。

## 四、✅面上健康(实测)

- PyPI nautilus-compass latest=3.3.0=本地版本 ✅ · compass.nautilus.social 200 · www.nautilus.social 200
- compass CI 8 连绿 · daemon 9876 ping 绿(含新探针) · 值守轮/genesis_watch/哨兵全绿
- **assay 发布面无独立迁移债**(与 compass 同仓,发布链活,版本同步)
- 其余 7 活会话:flywheel 框独立 session 自查(其 3354 文件);core-de 通报已收记(COLLAB_BOARD,判据锁三条被其新战线采纳=判据工程化外溢首次实证)

## 五、配方沉淀(本审计新增可复用件)

- launchd 死路径/Win 残留一行扫描(plist ProgramArguments 存在性+Win 特征 grep)
- Win 会话记忆残骸差分合并法(目录名=C--Users-chunx-* 特征)
- zshenv vs zshrc 覆盖域差异:非交互壳只读 zshenv——env 消毒必须放 zshenv
