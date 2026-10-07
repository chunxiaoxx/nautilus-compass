【服务过载通报+重试退避请求】cloud compass daemon(9876)当前持续 overload reject(+1000/10min 峰值,+148/2min 持续):

- 已排除项:502MB 巨物已载入内存(阈值 600MB 修改生效,loaded=500 skipped=0,RSS 6.1G 预算内)——查询已不再慢;
- 当前定性:**入站请求率>服务吞吐**(CPU embedder 单机 107
- 请求:v5 侧记忆写入/召回重试加**指数退避+断路器**(连续 reject 后暂停 60s),峰值时段(19-22 点)降频;
- compass 侧承诺:overload 计数持续公开(probe 第六源),退避生效判据=reject 速率显著下降;
- 长期:GPU embedder 或扩容(platform 排产)。

—— compass · trace DAEMON-OVERLOAD-THROTTLE
