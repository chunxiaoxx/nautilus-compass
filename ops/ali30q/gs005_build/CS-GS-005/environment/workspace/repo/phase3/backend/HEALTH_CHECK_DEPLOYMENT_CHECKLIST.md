# 健康检查修复 - 快速部署检查清单

**修复内容**: 数据库健康检查 "Not an executable object" 错误
**预计时间**: 5 分钟
**风险等级**: 低

---

## ✅ 部署前 (2分钟)

### 准备工作
- [ ] 确认有服务器 SSH 访问权限 (ubuntu@115.159.62.192)
- [ ] 确认本地文件已修复 (monitoring_config.py)
- [ ] 记录当前时间: _______________

### 当前状态记录
```bash
curl -s http://115.159.62.192:8000/health | python3 -c "import sys,json; print(json.load(sys.stdin)['checks']['database'])"
```
- [ ] 当前状态: _______________
- [ ] 错误信息: _______________

---

## 🚀 部署执行 (3分钟)

### 步骤 1: 备份 (30秒)
```bash
ssh ubuntu@115.159.62.192 "cd /home/ubuntu/nautilus-mvp/phase3/backend && cp monitoring_config.py monitoring_config.py.backup.$(date +%Y%m%d_%H%M%S)"
```
- [ ] 备份完成
- [ ] 备份文件名: _______________

### 步骤 2: 上传 (30秒)
```bash
scp monitoring_config.py ubuntu@115.159.62.192:/home/ubuntu/nautilus-mvp/phase3/backend/
```
- [ ] 上传成功

### 步骤 3: 验证文件 (15秒)
```bash
ssh ubuntu@115.159.62.192 "cd /home/ubuntu/nautilus-mvp/phase3/backend && grep -A 1 'result = conn.execute' monitoring_config.py"
```
- [ ] 看到 `result = conn.execute(text("SELECT 1"))`
- [ ] 看到 `result.close()`

### 步骤 4: 重启服务 (1分钟)
```bash
ssh ubuntu@115.159.62.192 "sudo systemctl restart nautilus-backend"
sleep 15
```
- [ ] 重启命令执行成功
- [ ] 已等待 15 秒

### 步骤 5: 验证修复 (45秒)
```bash
curl http://115.159.62.192:8000/health
```
- [ ] HTTP 状态码: 200
- [ ] `status` = "healthy"
- [ ] `database.status` = "healthy"
- [ ] `database.connected` = true
- [ ] 无 "Not an executable object" 错误

---

## ✅ 验证测试 (可选，2分钟)

### 连续测试
```bash
for i in {1..5}; do curl -s http://115.159.62.192:8000/health | python3 -c "import sys,json; print(json.load(sys.stdin)['checks']['database']['status'])"; sleep 2; done
```
- [ ] 5次测试都返回 "healthy"

### 连接池检查
```bash
curl http://115.159.62.192:8000/database/pool
```
- [ ] 连接池状态正常

---

## 📊 部署结果

### 成功标准
- [ ] ✅ 健康检查返回 "healthy"
- [ ] ✅ 数据库连接正常
- [ ] ✅ 无错误信息
- [ ] ✅ 响应时间 < 1秒

### 部署信息
- **部署时间**: _______________
- **部署人员**: _______________
- **部署结果**: [ ] 成功 [ ] 失败
- **响应时间**: _______________

---

## 🔄 回滚方案（如需要）

```bash
ssh ubuntu@115.159.62.192 "cd /home/ubuntu/nautilus-mvp/phase3/backend && cp monitoring_config.py.backup.YYYYMMDD_HHMMSS monitoring_config.py && sudo systemctl restart nautilus-backend"
```
- [ ] 回滚执行
- [ ] 回滚验证

---

## 📝 备注

```
___________________________________________________________________________

___________________________________________________________________________

___________________________________________________________________________
```

---

**检查清单版本**: 1.0
**创建日期**: 2026-03-02
**适用场景**: 数据库健康检查修复
