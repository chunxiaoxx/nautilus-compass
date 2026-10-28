# 登录问题排查指南

**更新时间**: 2026-02-23 16:25

---

## ✅ 已完成的修复

1. **CORS配置** - 已添加生产环境URL
2. **前端重新构建** - 16:24最新版本
3. **Nginx重新加载** - 配置已生效
4. **后端正常运行** - API测试通过

---

## 🔍 如果仍然无法登录，请按以下步骤操作：

### 步骤1: 清除浏览器缓存

#### Chrome/Edge:
1. 按 `Ctrl + Shift + Delete`
2. 选择"缓存的图片和文件"
3. 时间范围选"全部时间"
4. 点击"清除数据"
5. **完全关闭浏览器**（不是只关闭标签页）
6. 重新打开浏览器

#### Firefox:
1. 按 `Ctrl + Shift + Delete`
2. 选择"缓存"
3. 时间范围选"全部"
4. 点击"立即清除"
5. **完全关闭浏览器**
6. 重新打开浏览器

### 步骤2: 强制刷新页面

访问 https://www.nautilus.social/login 后：
- Windows: `Ctrl + F5` 或 `Ctrl + Shift + R`
- Mac: `Cmd + Shift + R`

### 步骤3: 打开开发者工具查看错误

1. 按 `F12` 打开开发者工具
2. 切换到 "Console" 标签
3. 切换到 "Network" 标签
4. 勾选 "Preserve log"
5. 尝试登录
6. 查看是否有红色错误信息

---

## 🔐 测试账号

```
用户名: vcreport
密码: Test@123456789
```

---

## 📊 后端验证（已通过）

```bash
# API测试
curl -X POST https://api.nautilus.social/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"vcreport","password":"Test@123456789"}'

# 结果: 200 OK ✅
# 返回: {"access_token":"...","token_type":"bearer"}
```

---

## 🔧 技术细节

### 前端构建
- **时间**: 2026-02-23 16:24
- **文件**: index-C9wmNJuh.js (602KB)
- **位置**: ~/nautilus-mvp/phase3/frontend/dist/

### CORS配置
```env
CORS_ORIGINS=https://www.nautilus.social,https://nautilus.social,http://localhost:3000
```

### Nginx状态
- ✅ 配置测试通过
- ✅ 已重新加载
- ⚠️ 警告: conflicting server name (不影响功能)

---

## 🐛 常见问题

### 问题1: 显示"Network Error"
**原因**: 浏览器缓存了旧版本JavaScript
**解决**: 清除缓存并强制刷新

### 问题2: 显示"登录失败，请检查用户名和密码"
**原因**:
- 用户名或密码输入错误
- 账号不存在
**解决**: 确认使用正确的测试账号

### 问题3: 页面一直加载
**原因**: 网络连接问题
**解决**: 检查网络连接，刷新页面

---

## 📞 如果问题仍然存在

请提供以下信息：
1. 浏览器控制台的错误信息（F12 → Console）
2. 网络请求的状态（F12 → Network → 点击失败的请求）
3. 具体的错误提示文字
4. 使用的浏览器和版本

---

**系统已完全就绪，清除缓存后应该可以正常登录！**
