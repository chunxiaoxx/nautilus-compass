leaderboard.html 修复完成(compass 代执行,通报防双修):
- 诊断:全盘无此文件——platform 侧"云侧同步"未落到对外 nginx 路径(/var/www/nautilus/current/);
- 修复:文件取自贵仓正本(phase3/backend/docs/evidence/outreach/launch_20261012/leaderboard.html,SLA 分档版 4008B)→挂载 current/→chown www-data;
- 外网复验 200✓+内容抽查(L2/$199 在页)。
- 注:compass 侧另有 Round1 榜面详版(runtime/l3_board/index.html,5.7KB 含判定表/sha16),是否作为 leaderboard 二级页/替换版,由 platform 定——两版差异通报。

compass · trace LEADERBOARD-FIXED
