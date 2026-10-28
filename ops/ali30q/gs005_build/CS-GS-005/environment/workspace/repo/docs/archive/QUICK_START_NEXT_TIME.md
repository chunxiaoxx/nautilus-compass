# 🚀 Nautilus 下次启动指南

**快速启动后端和前端服务**

---

## 启动后端服务

```bash
cd C:\Users\chunx\Projects\nautilus-core\phase3\backend
python main.py
```

**验证**: 访问 http://localhost:8000/health

---

## 启动前端服务

```bash
cd C:\Users\chunx\Projects\nautilus-core\phase3\frontend
npm run dev
```

**访问**: http://localhost:3000

---

## 数据库配置

**PostgreSQL**:
- 端口: 5433
- 用户: postgres
- 密码: postgres
- 数据库: nautilus

**连接字符串**:
```
postgresql://postgres:postgres@localhost:5433/nautilus
```

---

## Sepolia合约地址

```
IdentityContract:  0x1f4d8E8Bdfc0323c5a684452071fa71129d4D8A3
RewardContract:    0x69f258D20e5549236B5B68A33F26302B331379B6
TaskContract:      0x20B9A1FCd63197616F67fE2012f3c5BE43B25952
```

---

## 常用命令

### 运行测试
```bash
# 后端测试
cd phase3/backend
pytest tests/test_integration.py -v

# 前端测试
cd phase3/frontend
npm test

# 性能测试
cd phase3
python simple-performance-test.py
```

### 部署
```bash
# 部署前端到Vercel
cd phase3/frontend
npm run build
vercel --prod
```

---

## 快速参考

- 📖 详细文档: `QUICK_REFERENCE.md`
- 📋 下一步: `NEXT_STEPS_GUIDE.md`
- 📊 今天总结: `TODAY_WORK_SUMMARY.md`

---

**系统状态**: 🟢 就绪
**下次启动**: 只需运行后端和前端命令即可
