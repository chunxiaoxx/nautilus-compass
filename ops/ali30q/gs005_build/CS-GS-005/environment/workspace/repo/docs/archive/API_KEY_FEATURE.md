# API密钥功能已添加

**时间**: 2026-02-23 19:05

---

## ✅ 新增功能

### API密钥管理
- **位置**: 个人资料页面 → API密钥部分
- **功能**:
  1. ✅ 生成新的API密钥
  2. ✅ 复制密钥到剪贴板
  3. ✅ 查看已生成的密钥列表
  4. ✅ 删除不需要的密钥

---

## 🔑 如何生成API密钥

1. **登录系统**
2. **访问个人资料**: 点击导航栏"个人资料"
3. **生成密钥**: 点击"生成新密钥"按钮
4. **复制保存**: 立即复制密钥（关闭后无法再次查看）
5. **使用密钥**: 在创投日报项目中使用此密钥

---

## 📝 API密钥格式

```
naut_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

- 前缀: `naut_`
- 长度: 约48个字符
- 用途: 程序化访问Nautilus API

---

## 🔧 如何使用API密钥

### 在创投日报项目中使用

```bash
# 设置环境变量
export NAUTILUS_API_KEY="naut_your_api_key_here"

# 或在配置文件中
NAUTILUS_API_KEY=naut_your_api_key_here
```

### API请求示例

```bash
# 使用API密钥访问Nautilus API
curl -X GET https://api.nautilus.social/api/tasks \
  -H "Authorization: Bearer naut_your_api_key_here"
```

```python
# Python示例
import requests

headers = {
    'Authorization': 'Bearer naut_your_api_key_here'
}

response = requests.get('https://api.nautilus.social/api/tasks', headers=headers)
print(response.json())
```

---

## 🔄 刷新页面

请按 `Ctrl + F5` 刷新页面以加载最新版本：
- 新文件: index-CKeFgDPn.js
- 包含API密钥管理功能

---

## 📊 后端API端点

已添加以下端点：

1. **生成API密钥**
   - `POST /api/auth/api-keys/generate`
   - 需要认证
   - 返回新生成的API密钥

2. **列出API密钥**
   - `GET /api/auth/api-keys`
   - 需要认证
   - 返回用户的所有API密钥

---

## ⚠️ 重要提示

1. **立即保存**: 生成后立即复制保存，关闭后无法再次查看完整密钥
2. **安全存储**: 不要将API密钥提交到Git仓库
3. **定期更换**: 建议定期更换API密钥以提高安全性
4. **删除不用的**: 及时删除不再使用的API密钥

---

**请刷新页面并生成您的第一个API密钥！**
