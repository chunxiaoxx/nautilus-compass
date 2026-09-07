# P-0002 · fail 残骸自动清理挂 watchdog

- 日期：2026-09-07
- 来源：disk-full-stage-tmp-hazard 记忆（9/6 盘满真凶=fail 残骸 PNG 单条 10-23G）
- 级别：L1
- 状态：draft

## 问题
转换失败的条目只落 _CONVERT_FAIL.json，images/ 暂存不清理，单条残骸 10-23G——本周两次盘满事故元凶；现在靠人记着手动清。

## 方案
双保险：①核对 GPU 实例上 mcap2lerobot_convert.py 是否为已修版（本地仓 38b3e93 已在 convert() 失败分支补 rmtree——实例脚本在 /root/ego_open100k_t1/scripts/ 是拷贝版，需 diff 确认后同步）；②watchdog.sh 每 600s 循环追加：扫描含 _CONVERT_FAIL.json 的条目目录→删该条目 images/（保留 FAIL json 作归因）+df<15G 触发 clean_partial.py。

## 验证
实例上人为触发一次失败（或等自然失败），watchdog 下一轮清掉残骸且 FAIL json 保留；df 曲线不再下探。

## 预期收益
消除盘满类停机（本周两次≈数小时处理+整晚跑批中断风险）；省人工巡检。

## 风险与红线
删除类操作白名单：仅删"含 _CONVERT_FAIL.json 的条目目录内文件"+_stage_tmp，禁通配、禁碰 DONE 目录；clean_partial 仅 df 阈值触发。
