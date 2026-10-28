# 🚨 Nautilus 安全风险警告清单

**生成时间**: 2026-03-02
**审计员**: 安全审计专家 Agent
**紧急程度**: 🔴 HIGH

---

## ⚠️ 紧急警告

```
╔═══════════════════════════════════════════════════════════════╗
║                    🚨 紧急安全警告 🚨                          ║
║                                                               ║
║  生产环境存在 5 个 P0 级别的安全配置问题                        ║
║  需要立即修复，否则系统面临严重安全风险                          ║
║                                                               ║
║  风险等级: 🔴 CRITICAL                                         ║
║  建议行动: 立即执行修复脚本                                     ║
║  预计时间: 1 天                                                ║
╚═══════════════════════════════════════════════════════════════╝
```

---

## 🔴 P0 风险清单 (立即修复)

### 1. 数据库配置错误 ⚠️ CRITICAL

```
风险描述:
  配置文件指定 PostgreSQL，但实际使用 SQLite
  导致性能问题和数据持久化风险

影响范围:
  - 所有数据库操作
  - 数据持久化
  - 系统性能

根本原因:
  utils/database.py 未加载 .env 文件

修复方案:
  在 utils/database.py 顶部添加:
  from dotenv import load_dotenv
  load_dotenv()

验证方法:
  检查日志确认连接到 PostgreSQL

风险等级: 🔴 CRITICAL
预计修复时间: 30 分钟
责任人: Backend 团队
```

---

### 2. 防火墙未启用 ⚠️ CRITICAL

```
风险描述:
  UFW 防火墙未启用，所有端口对外暴露
  数据库端口 5432 可被外部访问

影响范围:
  - 数据库直接暴露
  - 内部服务可被外部访问
  - 易受端口扫描攻击

当前状态:
  $ sudo ufw status
  Status: inactive

修复方案:
  sudo ufw default deny incoming
  sudo ufw default allow outgoing
  sudo ufw allow 22/tcp
  sudo ufw allow 80/tcp
  sudo ufw allow 443/tcp
  sudo ufw enable

验证方法:
  sudo ufw status
  应显示: Status: active

风险等级: 🔴 CRITICAL
预计修复时间: 15 分钟
责任人: DevOps 团队
```

---

### 3. 敏感密钥暴露 ⚠️ CRITICAL

```
风险描述:
  GitHub/Google/Infura 密钥在配置文件中可见
  可能已被泄露或滥用

暴露的密钥:
  1. GitHub OAuth Client Secret
  2. Google OAuth Client Secret
  3. Infura Project ID: c84e7bf6be0f481898e4bfd3c062fd2b
  4. JWT Secret (如果使用默认值)
  5. CSRF Secret (如果使用默认值)

影响范围:
  - API 配额可能被滥用
  - OAuth 流程可能被劫持
  - JWT 令牌可能被伪造
  - 产生意外费用

修复方案:
  1. 立即轮换所有密钥:
     - GitHub: https://github.com/settings/developers
     - Google: https://console.cloud.google.com/
     - Infura: https://infura.io/dashboard

  2. 更新 .env 文件

  3. 重启所有服务

  4. 监控异常使用

验证方法:
  检查新密钥是否生效
  监控 API 使用情况

风险等级: 🔴 CRITICAL
预计修复时间: 2 小时
责任人: Security 团队
```

---

### 4. DEBUG 模式开启 ⚠️ HIGH

```
风险描述:
  生产环境开启 DEBUG 模式
  泄露详细错误信息和内部实现细节

影响范围:
  - 错误堆栈暴露代码结构
  - 数据库查询可见
  - 内部路径泄露
  - 性能下降

当前配置:
  DEBUG=true
  ENVIRONMENT=development

修复方案:
  echo "DEBUG=false" >> .env
  echo "ENVIRONMENT=production" >> .env

  重启服务:
  pkill -f uvicorn
  nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 > /tmp/nautilus-api.log 2>&1 &

验证方法:
  curl https://api.nautilus.social/health
  检查响应中不应包含详细错误信息

风险等级: 🟠 HIGH
预计修复时间: 15 分钟
责任人: DevOps 团队
```

---

### 5. OAuth State 验证缺失 ⚠️ HIGH

```
风险描述:
  OAuth 回调未验证 state 参数
  易受 CSRF 攻击

影响范围:
  - 攻击者可劫持 OAuth 流程
  - 恶意账户绑定
  - 用户账户被接管

当前实现:
  ✅ State 生成
  ❌ State 存储 (Redis)
  ❌ State 验证

攻击场景:
  1. 攻击者诱导用户点击恶意链接
  2. 用户完成 OAuth 授权
  3. 攻击者的账户被绑定到用户身份

修复方案:
  实施完整的 state 验证流程:
  1. 生成 state 并存储到 Redis (10 分钟 TTL)
  2. 回调时验证 state
  3. 使用后立即删除 state

验证方法:
  测试无效 state 应被拒绝
  测试过期 state 应被拒绝
  测试重复使用 state 应被拒绝

风险等级: 🟠 HIGH
预计修复时间: 1 天
责任人: Backend 团队
```

---

## 🟠 P1 风险清单 (本周修复)

### 6. API Key 明文存储

```
风险: 数据库泄露时所有 API Key 暴露
影响: 所有 Agent 的 API 访问权限
修复: 使用 SHA256 哈希存储
时间: 1-2 天
```

### 7. 钱包私钥未保存

```
风险: 用户无法使用生成的钱包
影响: 钱包功能不可用
修复: 改为用户自带钱包 + 签名验证
时间: 2-3 天
```

### 8. Agent 注册缺少 CAPTCHA

```
风险: 垃圾账户、资源耗尽
影响: 系统可用性
修复: 集成 reCAPTCHA
时间: 2-3 天
```

### 9. 邮箱验证缺失

```
风险: 垃圾账户、虚假邮箱
影响: 数据质量
修复: 添加邮箱验证流程
时间: 2-3 天
```

---

## 📋 修复执行计划

### Day 1: 紧急配置修复 (2026-03-03)

```bash
#!/bin/bash
# 紧急修复脚本

echo "=== Nautilus 紧急安全修复 ==="
echo "开始时间: $(date)"

# 1. 备份当前配置
echo "[1/5] 备份配置文件..."
cp .env .env.backup.$(date +%Y%m%d)

# 2. 修复数据库配置
echo "[2/5] 修复数据库配置..."
# 手动编辑 utils/database.py 添加 load_dotenv()

# 3. 启用防火墙
echo "[3/5] 启用防火墙..."
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# 4. 关闭 DEBUG 模式
echo "[4/5] 关闭 DEBUG 模式..."
sed -i 's/DEBUG=true/DEBUG=false/' .env
sed -i 's/ENVIRONMENT=development/ENVIRONMENT=production/' .env

# 5. 重启服务
echo "[5/5] 重启服务..."
pkill -f uvicorn
sleep 2
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 > /tmp/nautilus-api.log 2>&1 &

echo "=== 修复完成 ==="
echo "完成时间: $(date)"
echo ""
echo "⚠️  请立即执行以下手动操作:"
echo "1. 轮换 GitHub OAuth 密钥"
echo "2. 轮换 Google OAuth 密钥"
echo "3. 轮换 Infura Project ID"
echo "4. 验证服务正常运行"
```

**执行方式**:
```bash
cd /home/ubuntu/nautilus-mvp/phase3/backend
chmod +x emergency_fix.sh
./emergency_fix.sh
```

---

### Day 2: OAuth State 验证 (2026-03-04)

**任务清单**:
- [ ] 修改 `api/auth.py` 添加 Redis 存储
- [ ] 实现 state 验证逻辑
- [ ] 添加测试用例
- [ ] 部署到生产环境
- [ ] 验证功能正常

**验证标准**:
- ✅ 无效 state 被拒绝
- ✅ 过期 state 被拒绝
- ✅ 重复使用 state 被拒绝
- ✅ 正常流程工作正常

---

### Day 3-5: CAPTCHA 集成 (2026-03-05 ~ 03-07)

**任务清单**:
- [ ] 注册 reCAPTCHA 账号
- [ ] 后端集成 CAPTCHA 验证
- [ ] 前端添加 CAPTCHA 组件
- [ ] 添加测试用例
- [ ] 部署到生产环境
- [ ] 监控 CAPTCHA 通过率

**验证标准**:
- ✅ 无 CAPTCHA 注册被拒绝
- ✅ 无效 CAPTCHA 被拒绝
- ✅ 有效 CAPTCHA 注册成功
- ✅ CAPTCHA 通过率 > 80%

---

## 📊 风险评估矩阵

```
影响 vs 可能性

        │  低  │  中  │  高  │
────────┼──────┼──────┼──────┤
高影响  │      │  H3  │ C1,2,3│
中影响  │  M5  │ H1,4 │  H2  │
低影响  │  P2  │  P1  │      │
────────┴──────┴──────┴──────┘

图例:
C = Critical (关键)
H = High (高)
M = Medium (中)
P = Low (低)
```

---

## 🎯 修复优先级决策树

```
发现安全问题
    │
    ├─ 是否影响生产环境配置？
    │   ├─ 是 → P0 (立即修复)
    │   └─ 否 → 继续评估
    │
    ├─ 是否可被远程利用？
    │   ├─ 是 → P0 (立即修复)
    │   └─ 否 → 继续评估
    │
    ├─ 是否影响认证/授权？
    │   ├─ 是 → P0/P1 (本周修复)
    │   └─ 否 → 继续评估
    │
    ├─ 是否影响数据安全？
    │   ├─ 是 → P1 (本周修复)
    │   └─ 否 → 继续评估
    │
    └─ 其他问题 → P2 (本月修复)
```

---

## 📈 修复进度跟踪

### 本周目标 (2026-03-03 ~ 03-09)

```
进度: ░░░░░░░░░░░░░░░░░░░░ 0% (0/5 完成)

P0 问题:
  [ ] 1. 数据库配置错误
  [ ] 2. 防火墙未启用
  [ ] 3. 敏感密钥暴露
  [ ] 4. DEBUG 模式开启
  [ ] 5. OAuth State 验证

预计完成: 2026-03-07
责任人: DevOps + Backend 团队
```

### 下周目标 (2026-03-10 ~ 03-16)

```
进度: ░░░░░░░░░░░░░░░░░░░░ 0% (0/4 完成)

P1 问题:
  [ ] 6. API Key 哈希存储
  [ ] 7. 钱包私钥管理
  [ ] 8. Agent 注册 CAPTCHA
  [ ] 9. 邮箱验证流程

预计完成: 2026-03-16
责任人: Backend 团队
```

---

## 🚨 紧急响应流程

### 如果发现安全事件

```
1. 立即行动 (0-15 分钟)
   ├─ 评估影响范围
   ├─ 隔离受影响系统
   └─ 通知安全团队

2. 遏制威胁 (15-60 分钟)
   ├─ 阻止攻击源
   ├─ 轮换受影响密钥
   └─ 启用额外防护

3. 根除问题 (1-4 小时)
   ├─ 修复漏洞
   ├─ 清理恶意代码
   └─ 验证系统安全

4. 恢复服务 (4-8 小时)
   ├─ 恢复正常服务
   ├─ 监控异常行为
   └─ 通知用户

5. 事后分析 (1-3 天)
   ├─ 分析攻击路径
   ├─ 更新安全策略
   └─ 改进防护措施
```

### 紧急联系人

```
安全团队:
  - 邮箱: security@nautilus.example.com
  - 电话: [待定]
  - Slack: #security-alerts

DevOps 团队:
  - 邮箱: devops@nautilus.example.com
  - 电话: [待定]
  - Slack: #devops-oncall

管理层:
  - 邮箱: management@nautilus.example.com
  - 电话: [待定]
```

---

## 📝 修复验证清单

### P0 修复验证

```
数据库配置:
  [ ] 连接到 PostgreSQL
  [ ] 数据持久化正常
  [ ] 性能符合预期

防火墙:
  [ ] UFW 状态为 active
  [ ] 只有必要端口开放
  [ ] 数据库端口不可外部访问

密钥轮换:
  [ ] GitHub OAuth 新密钥生效
  [ ] Google OAuth 新密钥生效
  [ ] Infura 新 Project ID 生效
  [ ] 旧密钥已失效
  [ ] 无异常 API 使用

DEBUG 模式:
  [ ] DEBUG=false
  [ ] ENVIRONMENT=production
  [ ] 错误信息不泄露细节
  [ ] API 文档已禁用

OAuth State:
  [ ] State 存储到 Redis
  [ ] State 验证正常
  [ ] 无效 state 被拒绝
  [ ] 测试用例通过
```

---

## 🎓 总结

### 当前风险状况

```
┌─────────────────────────────────────────────────────────────┐
│                    风险状况总览                               │
│                                                              │
│ 🔴 P0 问题: 5 个 (需立即修复)                                │
│ 🟠 P1 问题: 4 个 (本周修复)                                  │
│ 🟡 P2 问题: 2 个 (本月修复)                                  │
│                                                              │
│ 总体风险等级: 🔴 HIGH                                         │
│ 建议行动: 立即执行 Day 1 修复脚本                             │
│                                                              │
│ 修复后风险等级: 🟡 MEDIUM → 🟢 LOW                           │
└─────────────────────────────────────────────────────────────┘
```

### 关键建议

1. **立即执行** (今天):
   - 运行紧急修复脚本
   - 轮换所有暴露的密钥
   - 验证修复效果

2. **本周完成**:
   - OAuth State 验证
   - CAPTCHA 集成
   - API Key 哈希存储

3. **持续监控**:
   - 每日检查安全日志
   - 监控异常行为
   - 定期安全评估

---

**生成时间**: 2026-03-02
**有效期**: 至问题修复完成
**审计员**: 安全审计专家 Agent

---

*本警告清单为紧急安全响应的一部分，请立即采取行动。*
