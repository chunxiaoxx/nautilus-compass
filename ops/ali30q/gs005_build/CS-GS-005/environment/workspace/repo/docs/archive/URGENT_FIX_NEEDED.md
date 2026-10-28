# 紧急修复说明

**时间**: 2026-02-23
**问题**: SSH连接中断，但已确定API密钥生成失败的根本原因

---

## 🔴 当前问题

API密钥生成失败的原因：**auth.py缺少datetime导入**

错误信息：
```
NameError: name 'datetime' is not defined
File "/home/ubuntu/nautilus-mvp/phase3/backend/api/auth.py", line 168
```

---

## ✅ 解决方案

### 方法1: 通过服务器控制台修复（推荐）

如果SSH不可用，请通过云服务器控制台登录，然后执行：

```bash
# 1. 添加datetime导入
sed -i '1i from datetime import datetime' ~/nautilus-mvp/phase3/backend/api/auth.py

# 2. 验证修复
head -5 ~/nautilus-mvp/phase3/backend/api/auth.py

# 3. 后端会自动重新加载（--reload模式）
# 4. 检查日志确认无错误
tail -20 ~/backend.log
```

### 方法2: 手动编辑文件

1. 打开文件：`~/nautilus-mvp/phase3/backend/api/auth.py`
2. 在文件**第一行**添加：
   ```python
   from datetime import datetime
   ```
3. 保存文件
4. 后端会自动重新加载

---

## 📋 修复后的验证步骤

```bash
# 1. 登录获取token
curl -X POST https://api.nautilus.social/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"testuser999","password":"Test@123456789"}'

# 2. 使用返回的token测试API密钥生成（替换YOUR_TOKEN）
curl -X POST https://api.nautilus.social/api/auth/api-keys/generate \
  -H 'Authorization: Bearer YOUR_TOKEN'

# 应该返回类似：
# {"api_key":"naut_xxxxx","created_at":"2026-02-23T...","user_id":1}
```

---

## 🔧 其他待修复问题

修复datetime导入后，还需要解决：

### 1. 钱包地址保存功能

需要在 `auth.py` 添加：

```python
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
```

### 2. Tasks和Agents页面问题

需要检查：
- 浏览器控制台错误（F12）
- 清除浏览器缓存（Ctrl+Shift+Delete）
- 验证API返回数据格式

---

## 🌐 SSH连接问题

当前SSH连接持续中断，可能原因：
1. 服务器网络不稳定
2. 防火墙规则
3. SSH服务配置

**临时解决方案**：
- 使用云服务器控制台（Web Terminal）
- 检查服务器网络状态
- 重启SSH服务：`sudo systemctl restart sshd`

---

## 📞 下一步

1. **立即修复**：通过控制台添加datetime导入
2. **测试验证**：确认API密钥生成功能正常
3. **继续修复**：解决钱包地址和页面显示问题
4. **排查SSH**：修复SSH连接问题以便后续维护

---

**修复优先级**：
1. ⚡ datetime导入（5分钟）
2. ⚡ 钱包地址API（10分钟）
3. 🔍 Tasks/Agents页面调试（需要浏览器控制台信息）
4. 🔧 SSH连接问题（需要服务器端排查）
