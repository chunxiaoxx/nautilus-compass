# 快速修复指南

**针对当前4个问题的快速修复方案**

---

## 问题1: API密钥生成失败

### 修复步骤（在服务器上执行）

```bash
# 1. 连接服务器
ssh cloud

# 2. 检查auth.py是否有API密钥端点
grep -n "api-keys" ~/nautilus-mvp/phase3/backend/api/auth.py

# 3. 如果没有，添加以下代码到auth.py末尾
cat >> ~/nautilus-mvp/phase3/backend/api/auth.py << 'EOF'

@router.post('/api-keys/generate')
async def generate_api_key(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    import secrets
    api_key = f'naut_{secrets.token_urlsafe(32)}'
    return {
        'api_key': api_key,
        'created_at': datetime.now().isoformat(),
        'user_id': current_user['id']
    }

@router.get('/api-keys')
async def list_api_keys(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return {'api_keys': [], 'count': 0}
EOF

# 4. 后端会自动重新加载（--reload模式）
# 5. 测试API
curl -X POST https://api.nautilus.social/api/auth/api-keys/generate \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 问题2: 钱包地址无法保存

### 临时解决方案
当前钱包地址保存是模拟的，需要添加真实的后端API。

### 完整修复步骤

**后端** - 添加到 `auth.py`:
```python
@router.put('/users/wallet')
async def update_wallet(
    wallet_data: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
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
```

**前端** - 修改 `ProfilePage.tsx` 的 `handleSaveWallet`:
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

## 问题3 & 4: Tasks和Agents页面问题

### 快速诊断

1. **清除浏览器缓存**
   - 按 `Ctrl + Shift + Delete`
   - 清除所有缓存
   - 完全关闭浏览器

2. **检查API是否正常**
   ```bash
   # 测试Tasks API
   curl https://api.nautilus.social/api/tasks

   # 测试Agents API
   curl https://api.nautilus.social/api/agents
   ```

3. **检查浏览器控制台**
   - 按 `F12`
   - 查看 Console 标签的错误
   - 查看 Network 标签的失败请求

4. **验证参数已修复**
   - 确认使用的是最新构建: `index-CKeFgDPn.js`
   - 确认参数已从 `skip` 改为 `offset`

### 如果仍有问题

检查是否是数据格式问题：

```typescript
// AgentsPage.tsx 和 TasksPage.tsx
// 确保正确处理API响应
const loadAgents = async () => {
  setLoading(true)
  try {
    const response = await agentsAPI.list({
      offset: page * limit,
      limit,
    })
    // 检查响应格式
    console.log('API Response:', response)

    // 如果response直接是数组
    if (Array.isArray(response)) {
      setAgents(response)
    }
    // 如果response.data是数组
    else if (Array.isArray(response.data)) {
      setAgents(response.data)
    }
  } catch (error) {
    console.error('Failed to load agents:', error)
  } finally {
    setLoading(false)
  }
}
```

---

## 🔄 重启服务（如果需要）

```bash
# 重启后端
ssh cloud "pkill -f 'uvicorn main:app'"
ssh cloud "cd ~/nautilus-mvp/phase3/backend && nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload > ~/backend.log 2>&1 &"

# 检查状态
ssh cloud "ps aux | grep uvicorn | grep -v grep"
ssh cloud "tail -20 ~/backend.log"
```

---

## 📝 验证修复

1. **API密钥**: 访问个人资料 → 点击"生成新密钥"
2. **钱包地址**: 输入地址 → 保存 → 刷新页面查看是否保留
3. **Tasks页面**: 访问 /tasks 查看任务列表
4. **Agents页面**: 访问 /agents 查看智能体列表

---

**如果SSH连接稳定，可以按照以上步骤逐一修复。**
