# 完整修复命令集合

**当SSH恢复后，按顺序执行以下命令**

---

## 1️⃣ 修复API密钥生成（datetime导入）

```bash
# 添加datetime导入
sed -i '1i from datetime import datetime' ~/nautilus-mvp/phase3/backend/api/auth.py

# 验证
head -5 ~/nautilus-mvp/phase3/backend/api/auth.py

# 等待后端自动重新加载（约3秒）
sleep 3

# 检查日志确认无错误
tail -20 ~/backend.log
```

---

## 2️⃣ 测试API密钥生成

```bash
# 登录获取token
TOKEN=$(curl -s -X POST https://api.nautilus.social/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"testuser999","password":"Test@123456789"}' | \
  grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

echo "Token: $TOKEN"

# 测试生成API密钥
curl -X POST https://api.nautilus.social/api/auth/api-keys/generate \
  -H "Authorization: Bearer $TOKEN"

# 应该返回：{"api_key":"naut_xxxxx","created_at":"...","user_id":1}
```

---

## 3️⃣ 添加钱包地址保存功能

```bash
# 在auth.py末尾添加钱包地址更新端点
cat >> ~/nautilus-mvp/phase3/backend/api/auth.py << 'EOF'

@router.put('/users/wallet')
async def update_wallet(
    wallet_data: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户钱包地址"""
    from models.user import User
    user = db.query(User).filter(User.id == current_user['id']).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.wallet_address = wallet_data.get('wallet_address')
    db.commit()
    db.refresh(user)

    return {
        'message': 'Wallet address updated',
        'wallet_address': user.wallet_address
    }
EOF

# 等待重新加载
sleep 3

# 检查日志
tail -20 ~/backend.log
```

---

## 4️⃣ 测试钱包地址保存

```bash
# 使用之前的token测试
curl -X PUT https://api.nautilus.social/api/auth/users/wallet \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"wallet_address":"0x1234567890abcdef1234567890abcdef12345678"}'

# 应该返回：{"message":"Wallet address updated","wallet_address":"0x..."}
```

---

## 5️⃣ 更新前端ProfilePage（钱包保存功能）

前端文件位置：`~/nautilus-mvp/phase3/frontend/src/pages/ProfilePage.tsx`

需要修改 `handleSaveWallet` 函数（第53-64行）：

```typescript
const handleSaveWallet = async () => {
  setLoading(true)
  setMessage('')
  try {
    await axios.put(
      'https://api.nautilus.social/api/auth/users/wallet',
      { wallet_address: walletAddress },
      { headers: { Authorization: `Bearer ${token}` }}
    )

    // 更新store
    useAuthStore.setState({
      user: { ...user, wallet_address: walletAddress }
    })

    setMessage('钱包地址已保存')
  } catch (err: any) {
    setMessage('保存失败: ' + (err.response?.data?.detail || err.message))
  } finally {
    setLoading(false)
  }
}
```

---

## 6️⃣ 重新构建前端

```bash
cd ~/nautilus-mvp/phase3/frontend

# 构建
npm run build

# 部署到Nginx
sudo rm -rf /var/www/nautilus-social/*
sudo cp -r dist/* /var/www/nautilus-social/

# 验证
ls -lh /var/www/nautilus-social/
```

---

## 7️⃣ 检查Tasks和Agents页面

```bash
# 测试API是否正常返回数据
curl https://api.nautilus.social/api/tasks
curl https://api.nautilus.social/api/agents

# 如果API正常，问题在前端
# 需要用户提供浏览器控制台错误信息（F12）
```

---

## 🔍 调试Tasks/Agents页面问题

如果页面仍有问题，需要：

1. **清除浏览器缓存**
   - 按 `Ctrl + Shift + Delete`
   - 选择"全部时间"
   - 清除缓存和Cookie
   - 完全关闭浏览器重新打开

2. **检查浏览器控制台**
   - 按 `F12` 打开开发者工具
   - 查看 Console 标签的错误
   - 查看 Network 标签的失败请求
   - 截图或复制错误信息

3. **验证构建文件**
   ```bash
   # 检查最新构建时间
   ls -lh /var/www/nautilus-social/assets/*.js

   # 检查文件内容是否包含offset参数
   grep -n "offset:" /var/www/nautilus-social/assets/index-*.js | head -5
   ```

---

## ✅ 完整验证清单

- [ ] API密钥生成成功
- [ ] 钱包地址保存成功
- [ ] 刷新页面后钱包地址仍然显示
- [ ] /tasks 页面正常显示任务列表
- [ ] /agents 页面正常显示智能体列表
- [ ] 浏览器控制台无错误

---

## 🚨 如果SSH仍然无法连接

**通过云服务器控制台（Web Terminal）执行：**

1. 检查SSH服务状态
   ```bash
   sudo systemctl status sshd
   ```

2. 重启SSH服务
   ```bash
   sudo systemctl restart sshd
   ```

3. 检查SSH配置
   ```bash
   sudo tail -20 /var/log/auth.log
   ```

4. 检查连接数限制
   ```bash
   sudo netstat -ant | grep :22 | wc -l
   ```

---

**执行完成后，访问 https://www.nautilus.social/profile 测试所有功能**
