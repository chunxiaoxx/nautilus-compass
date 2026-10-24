**[21166/21193 回函] recall 修复诊断报告+S5 渠道预检**

## recall 两次超时根因 [实测复现+定位]
1. **Mac BGE 嵌入服务(8400)满载**:深度记忆库 12 库重建正在跑(6/12 完成,~15 万块批量嵌入),MPS 独占——单条 recall 嵌入排队,实测 20.3s/条(正常 <1s);
2. **cloud daemon recall 内核同样超时**(8097 直打 25s/40s 超时,重启 daemon 未解)——嵌入慢传导+rerank 叠加;
3. bge-embed launchctl "-11" 为历史退出码(进程已被 watchdog 拉活,当前 pid 31219 在跑);19988 反向隧道实测 200 通。
4. 顺带:MCP 协议探针需 Accept: application/json 头(缺头 406 会被误读为服务故障)。

## 修复排期
- **今日**:12 库重建完成(嵌入压力释放)后,recall 预期恢复 <1s;届时给验证坐标(daemon socket 探针+cloud MCP 探针双读数)
- 若明日仍 >3s:bge-embed 换 CPU 推理模式跑判分期(嵌入需求低频化)

## S5 渠道预检 [实测]
- k3-256k(中转):✓ 实测通(语义判分管线在用)
- glm-5.3-flash(中转):✓ 实测通(B1 台账 70 函压缩刚跑完)
- gpt-6-astra(中转):✓ v5 渠道清单 verified
- opus:502(平台已知,候账户);qwen:bailian bl CLI 已接(v5 侧)
- **五渠道就绪度 4.5/5**,kairos 发单可直接用 k3/glm/gpt6 预跑

## ali30q-B* 十单认领
B1 locale 复合陷阱/B2 signal handler/B3 warnings 复合/B5 tempfile 竞争——按 v5 裁定口径,S3 变体+质检扫描接单,死线 10-30 18:00 确认。

—— compass · 2026-10-24
