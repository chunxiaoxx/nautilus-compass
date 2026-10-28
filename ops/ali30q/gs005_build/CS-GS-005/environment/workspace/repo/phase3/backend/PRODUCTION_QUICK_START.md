# 🚀 生产环境部署快速参考

## 📋 文档导航

### 🎯 从这里开始
1. **新手**: 先读 [PRODUCTION_DEPLOYMENT_INDEX.md](PRODUCTION_DEPLOYMENT_INDEX.md)
2. **项目经理**: 先读 [PRODUCTION_PREPARATION_REPORT.md](PRODUCTION_PREPARATION_REPORT.md)
3. **技术人员**: 先读 [PRODUCTION_DEPLOYMENT_PLAN.md](PRODUCTION_DEPLOYMENT_PLAN.md)

---

## 📚 核心文档（必读）

| 文档 | 用途 | 优先级 |
|------|------|--------|
| [PRODUCTION_DEPLOYMENT_INDEX.md](PRODUCTION_DEPLOYMENT_INDEX.md) | 文档索引和导航 | ⭐⭐⭐⭐⭐ |
| [PRODUCTION_PREPARATION_REPORT.md](PRODUCTION_PREPARATION_REPORT.md) | 就绪度评估（68%） | ⭐⭐⭐⭐⭐ |
| [PRODUCTION_DEPLOYMENT_PLAN.md](PRODUCTION_DEPLOYMENT_PLAN.md) | 4阶段部署计划 | ⭐⭐⭐⭐⭐ |
| [PRODUCTION_READINESS_CHECKLIST.md](PRODUCTION_READINESS_CHECKLIST.md) | 150+项检查清单 | ⭐⭐⭐⭐⭐ |

---

## 🔧 配置指南（按需阅读）

| 文档 | 适用人员 | 内容 |
|------|----------|------|
| [SSL_CERTIFICATE_GUIDE.md](SSL_CERTIFICATE_GUIDE.md) | 运维 | Let's Encrypt + 商业证书 |
| [DNS_CONFIGURATION_GUIDE.md](DNS_CONFIGURATION_GUIDE.md) | 运维 | DNS记录配置 |
| [PRODUCTION_DATABASE_GUIDE.md](PRODUCTION_DATABASE_GUIDE.md) | DBA | PostgreSQL生产配置 |
| [CLOUD_DEPLOYMENT_GUIDE.md](CLOUD_DEPLOYMENT_GUIDE.md) | DevOps | AWS/Azure/GCP/DO |

---

## ⚡ 快速命令

### SSL证书（Let's Encrypt）
```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx -y

# 获取证书（自动配置Nginx）
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# 测试自动续期
sudo certbot renew --dry-run
```

### DNS验证
```bash
# 查询A记录
dig yourdomain.com A

# 查询所有记录
dig yourdomain.com ANY

# 检查DNS传播
dig @8.8.8.8 yourdomain.com
dig @1.1.1.1 yourdomain.com
```

### 数据库备份
```bash
# 备份数据库
pg_dump -U nautilus_user nautilus_production | gzip > backup_$(date +%Y%m%d).sql.gz

# 恢复数据库
gunzip -c backup_20260226.sql.gz | psql -U nautilus_user nautilus_production
```

### Docker部署
```bash
# 构建镜像
docker build -t nautilus-backend:latest .

# 启动服务
docker-compose -f docker-compose.prod.yml up -d

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f

# 健康检查
curl http://localhost:8000/health
```

---

## ✅ 关键检查点

### 部署前必须完成（P0）
- [ ] 服务器已采购和配置
- [ ] 域名已注册
- [ ] DNS已配置
- [ ] SSL证书已安装
- [ ] 数据库已部署
- [ ] Redis已部署
- [ ] 所有密钥已生成
- [ ] 防火墙已配置
- [ ] 应用已部署
- [ ] 测试已通过

### 配置文件检查
- [ ] `.env.production` 已创建（从 `.env.production.example` 复制）
- [ ] `DATABASE_URL` 已配置
- [ ] `REDIS_URL` 已配置
- [ ] `JWT_SECRET_KEY` 已生成（强随机值）
- [ ] `CSRF_SECRET_KEY` 已生成（强随机值）
- [ ] `CORS_ORIGINS` 已配置（实际域名）
- [ ] `BLOCKCHAIN_RPC_URL` 已配置
- [ ] 智能合约地址已填入
- [ ] 区块链私钥已配置

---

## 📊 当前状态

### 就绪度评估
- **应用开发**: 100% ✅
- **文档准备**: 100% ✅
- **基础设施**: 30% ⚠️
- **总体就绪度**: 68% ⚠️

### 推荐上线时间
- **最早**: 2026-03-20（3周后）
- **推荐**: 2026-03-27（4周后）
- **保守**: 2026-04-03（5周后）

---

## 🎯 下一步行动

### 本周（立即行动）
1. 确认预算和资源
2. 采购服务器或选择云服务
3. 注册域名
4. 生成生产密钥

### 第2周
1. 服务器配置
2. SSL和DNS配置
3. 数据库部署

### 第3周
1. 应用部署
2. 监控配置
3. 功能测试

### 第4周
1. 性能测试
2. 安全审计
3. 生产上线

---

## 🔐 安全检查

### 必须修改的配置
```bash
# 生成JWT密钥
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 生成CSRF密钥
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 生成数据库密码
python -c "import secrets; print(secrets.token_urlsafe(24))"

# 生成Redis密码
python -c "import secrets; print(secrets.token_urlsafe(24))"
```

### 安全配置检查
- [ ] DEBUG=false
- [ ] ENABLE_API_DOCS=false
- [ ] ENABLE_SWAGGER=false
- [ ] FORCE_HTTPS=true
- [ ] RATE_LIMIT_ENABLED=true
- [ ] AUDIT_LOG_ENABLED=true

---

## 📈 性能指标

### 目标指标
- API响应时间: < 200ms (P95)
- 数据库查询: < 100ms (P95)
- 系统可用性: > 99.9%
- 错误率: < 0.1%
- 并发用户: > 100

### 资源配置（推荐）
- **应用服务器**: 2台 x (4核 8GB)
- **数据库服务器**: 2台 x (8核 16GB)
- **Redis服务器**: 2台 x (4核 8GB)

---

## 🆘 故障排查

### 常见问题

**问题1: 数据库连接失败**
```bash
# 检查数据库状态
sudo systemctl status postgresql

# 检查连接
psql -U nautilus_user -d nautilus_production -h localhost

# 查看日志
sudo tail -f /var/log/postgresql/postgresql-15-main.log
```

**问题2: Redis连接失败**
```bash
# 检查Redis状态
sudo systemctl status redis

# 测试连接
redis-cli -h localhost -p 6379 -a your_password ping

# 查看日志
sudo tail -f /var/log/redis/redis-server.log
```

**问题3: SSL证书问题**
```bash
# 检查证书
sudo certbot certificates

# 测试SSL配置
openssl s_client -connect yourdomain.com:443

# 在线测试
# https://www.ssllabs.com/ssltest/
```

**问题4: 应用无法启动**
```bash
# 查看Docker日志
docker-compose logs -f

# 检查配置
docker-compose config

# 重启服务
docker-compose restart
```

---

## 📞 联系方式

### 技术支持
- **DevOps团队**: 部署问题
- **DBA团队**: 数据库问题
- **运维团队**: 基础设施问题
- **安全团队**: 安全问题

### 应急联系
- **技术负责人**: -
- **运维值班**: -
- **DBA值班**: -

---

## 🔗 有用链接

### 在线工具
- [SSL Labs](https://www.ssllabs.com/ssltest/) - SSL测试
- [DNS Checker](https://dnschecker.org/) - DNS检查
- [What's My DNS](https://www.whatsmydns.net/) - DNS传播
- [MX Toolbox](https://mxtoolbox.com/) - DNS工具

### 官方文档
- [PostgreSQL](https://www.postgresql.org/docs/)
- [Redis](https://redis.io/documentation)
- [Nginx](https://nginx.org/en/docs/)
- [Docker](https://docs.docker.com/)
- [Let's Encrypt](https://letsencrypt.org/docs/)

### 云服务
- [AWS](https://aws.amazon.com/)
- [Azure](https://azure.microsoft.com/)
- [GCP](https://cloud.google.com/)
- [DigitalOcean](https://www.digitalocean.com/)

---

## 💡 最佳实践

### 部署原则
1. **测试优先**: 在测试环境充分验证
2. **备份优先**: 任何操作前先备份
3. **灰度发布**: 逐步切换流量
4. **监控告警**: 实时监控系统状态
5. **文档更新**: 及时更新文档

### 安全原则
1. **最小权限**: 仅授予必要权限
2. **强密码**: 使用强随机密码
3. **定期更新**: 定期更新系统和依赖
4. **审计日志**: 记录所有关键操作
5. **定期审计**: 定期进行安全审计

---

## 📝 快速备忘

### 生成密钥
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 备份数据库
```bash
pg_dump nautilus_production | gzip > backup.sql.gz
```

### 查看日志
```bash
docker-compose logs -f
tail -f /var/log/nginx/error.log
tail -f /var/log/postgresql/postgresql-15-main.log
```

### 重启服务
```bash
docker-compose restart
sudo systemctl restart nginx
sudo systemctl restart postgresql
```

### 健康检查
```bash
curl http://localhost:8000/health
curl https://yourdomain.com/health
```

---

**最后更新**: 2026-02-26
**文档版本**: 1.0.0
**状态**: ✅ 准备就绪

---

**祝部署顺利！** 🎉
