# Nautilus 当前问题和解决方案

**时间**: 2026-02-23 19:10

---

## 🐛 当前存在的问题

### 1. API密钥生成失败 ❌
- **错误**: "生成失败: Network Error"
- **原因**: 后端API端点可能未正确添加或服务器连接问题
- **状态**: 需要修复

### 2. 钱包地址保存问题 ❌
- **问题**: 填写后没有显示保存的地址
- **原因**: 保存功能只是模拟，没有实际调用后端API
- **状态**: 需要实现真实的保存功能

### 3. /tasks 页面嵌套问题 ❌
- **问题**: 显示网页标题嵌套
- **状态**: 需要调查

### 4. /agents 页面无法打开 ❌
- **问题**: 页面无法正常显示
- **状态**: 之前修复了参数问题，但可能还有其他问题

---

## 🔧 需要的修复步骤

### 修复1: API密钥生成

**后端** - 确保 `auth.py` 包含以下代码：

```python
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
    return {
        'api_keys': [],
        'count': 0
    }
```

**重启后端**:
```bash
ssh cloud "pkill -f 'uvicorn main:app' && cd ~/nautilus-mvp/phase3/backend && nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload > ~/backend.log 2>&1 &"
```

---

### 修复2: 钱包地址保存

**需要添加后端API**:

```python
@router.put('/users/wallet')
async def update_wallet(
    wallet_data: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == current_user['id']).first()
    user.wallet_address = wallet_data.get('wallet_address')
    db.commit()

    return {'message': 'Wallet address updated'}
```

**前端修改** - `ProfilePage.tsx`:

```typescript
const handleSaveWallet = async () => {
  setLoading(true)
  setMessage('')
  try {
    await axios.put('https://api.nautilus.social/api/auth/users/wallet',
      { wallet_address: walletAddress },
      { headers: { Authorization: `Bearer ${token}` }}
    )
    setMessage('钱包地址已保存')

    // 更新store中的用户信息
    useAuthStore.setState({
      user: { ...user, wallet_address: walletAddress }
    })
  } catch (err: any) {
    setMessage('保存失败: ' + (err.response?.data?.detail || err.message))
  } finally {
    setLoading(false)
  }
}
```

---

### 修复3 & 4: Tasks和Agents页面

**检查步骤**:

1. 清除浏览器缓存
2. 检查浏览器控制台错误
3. 验证API响应：
   ```bash
   curl https://api.nautilus.social/api/tasks
   curl https://api.nautilus.social/api/agents
   ```

---

## 📊 当前系统状态

### 正常工作的功能 ✅
- 用户登录
- 仪表板
- 个人资料页面（基本信息显示）

### 需要修复的功能 ❌
- API密钥生成
- 钱包地址保存
- Tasks页面显示
- Agents页面显示

---

## 🚨 SSH连接问题

当前SSH连接频繁断开，可能原因：
1. 服务器网络不稳定
2. SSH超时设置
3. 防火墙规则

**临时解决方案**:
- 使用更短的命令
- 分批执行操作
- 考虑使用screen或tmux保持会话

---

## 📝 下一步行动

1. **重新建立SSH连接**
2. **检查后端服务状态**
3. **验证API端点是否存在**
4. **修复API密钥生成功能**
5. **实现钱包地址保存**
6. **调查Tasks和Agents页面问题**

---

**建议**: 由于SSH连接不稳定，可能需要直接在服务器上操作或等待网络稳定后继续。
