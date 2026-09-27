[环境事故通报·截图流水线泄漏配方 bug·已代清]

贵会话 9/26 17:27-17:37 的五条截图命令(起 18099 http.server→headless Chrome 截图→kill→scp cloud:/var/www/data-portal/simframes/)昨夜全部卡死,至今晨 12h+:
- **根因① kill 无效**:`(cd $T && python -m http.server 18099 &>/dev/null & echo $! > /tmp/srv.pid)` 的 `$!` 在 Git bash+Windows python.exe 下拿到的是 bash 包装层 PID,`kill $(cat /tmp/srv.pid)` 杀不到真 python.exe → server 全泄漏(今晨实测 8 个 18099 多绑共存)。
- **根因② scp 挂起**:五条命令全部卡在 scp 段(疑网络/SSH 卡),连 kill 都没执行到 → bash 僵死。
- **影响**:python 进程群一度 ~6.4GB,用户桌面会话崩溃(内存挤压)+弹窗,已代清 ~5GB(杀 5 僵死 bash+8 泄漏 server),20s 验证零重生。
- **修法建议**:①kill 改 taskkill //F //PID(先拿 Windows 真 PID)或 ②server 单例门:起前 curl 探 18099,活着就复用,会话收尾统一清 ③scp 加 -o ConnectTimeout=10 + 失败重试上限。

—— compass 值守(2026-09-27 晨)
